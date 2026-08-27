""" Access control and transaction management for database sessions.

This module provides context managers and protocols for managing database
access permissions (read/write) and transactions. It ensures proper
transaction handling with automatic commit/rollback on context exit.
"""

from typing import Protocol

class SessionAccess( Protocol ):
    """ Protocol for objects that provide transaction support.

    Defines the interface that session objects must implement to support
    transaction management through AccessManager.
    """

    def _begin( self ) -> None:
        """ Begin a transaction. """
        ...

    def _commit( self ) -> None:
        """ Commit the current transaction. """
        ...

    def _rollback( self ) -> None:
        """ Rollback the current transaction. """
        ...

class _AccessContext:
    """ Context manager for database access sessions.

    Provides a context manager that ensures proper transaction handling,
    automatically committing on success or rolling back on exception.
    Tracks the access mode (read/write) and whether transaction semantics
    are being used.

    Internal class used by AccessManager. Not intended for direct use.

    Attributes:
        __manager: The AccessManager controlling this context
        __write: Whether this is a write-access context
        __transaction: Whether this is a transaction-mode context
        __active: Whether this context is currently active
    """

    def __init__( self,
                manager: 'AccessManager',
                write: bool = False,
                transaction: bool = False
            ):

        self.__manager = manager
        self.__write = write
        self.__transaction = transaction
        self.__active = False

    def __enter__( self ) -> '_AccessContext':
        """ Enter the access context.

        Notifies the manager to begin access tracking and start a
        transaction if write access is needed.

        Returns:
            Self for use in with statements
        """

        self.__manager._begin_access( self )
        self.__active = True

        return self

    def __exit__( self, type, value, trace ) -> None:
        """ Exit the access context.

        Notifies the manager to end access tracking. If an exception
        occurred, triggers rollback; otherwise commits if appropriate.

        Args:
            type: Exception type if an exception occurred
            value: Exception value if an exception occurred
            trace: Exception traceback if an exception occurred
        """

        self.__active = False
        self.__manager._end_access( self, type is not None )

        if( type is not None ):
            raise type.with_traceback( value, trace )

    def is_transaction( self ) -> bool:
        """ Check if this is a transaction-mode context.

        Returns:
            True if this context was created with transaction=True
        """
        return self.__transaction

    def is_write( self ) -> bool:
        """ Check if this is a write-access context.

        Returns:
            True if this context was created with write=True
        """
        return self.__write

    def commit( self ) -> None:
        """ Explicitly commit within this transaction context.

        Only valid for transaction-mode contexts.
        """
        self.__manager._commit( self )

    def rollback( self ) -> None:
        """ Explicitly rollback within this transaction context.

        Only valid for transaction-mode contexts.
        """
        self.__manager._rollback( self )

class AccessManager:
    """ Manages database access contexts and transaction lifecycle.

    AccessManager coordinates multiple nested access contexts, ensuring proper
    transaction handling and access control. It tracks:
    - Whether write access is permitted
    - Active access context stack
    - Transaction state (locked/unlocked)

    Features:
    - Automatic transaction begin/commit/rollback
    - Nested context support (inner contexts share outer transaction)
    - Read-only mode enforcement
    - Transaction-level explicit commit/rollback support

    Attributes:
        __session: The session object implementing SessionAccess protocol
        __write_permitted: Whether write operations are allowed
        __accesses: Stack of active access contexts
        __locked: Whether a transaction is currently active
        __failed: Whether the transaction has failed (unused currently)
    """

    def __init__( self, session: SessionAccess ):

        self.__session = session
        self.__write_permitted = False

        self.__accesses = []
        self.__locked = False
        self.__failed = False

    def _begin_access( self, dba: _AccessContext ) -> None:
        """ Begin an access context.

        Adds the context to the active access stack. If write access is
        requested and no transaction is active, begins a new transaction.

        Args:
            dba: The access context being entered

        Raises:
            AssertionError: If write access requested but not permitted,
                          or if transaction mode requested with nested contexts
        """

        assert not dba.is_write() or self.__write_permitted, 'Read-Only Access'

        if( dba.is_transaction() ):
            assert len( self.__accesses ) == 0

        if( dba.is_write() and not self.__locked ):
            self.__session._begin()
            self.__locked = True

        # Add our context last: we don't want to add
        # if beginning of the session fails.
        self.__accesses.append( dba )

    def _end_access( self, dba: _AccessContext, is_except: bool ) -> None:
        """ End an access context.

        Removes the context from the active access stack. If this is the
        outermost context and a transaction is active, commits (on success)
        or rolls back (on exception).

        Args:
            dba: The access context being exited
            is_except: True if exiting due to an exception

        Raises:
            AssertionError: If context order is violated
        """

        # Don't pop yet! we may be within the pre-commit hook!
        assert dba == self.__accesses[-1]

        if( len( self.__accesses ) == 1 ):
            if( self.__locked ):
                committed = False

                if( not is_except ):
                    try:
                        self.__session._commit()
                        committed = True

                    except:
                        pass

                if( not committed ):
                    self.__session._rollback()

            self.__locked = False

        assert dba == self.__accesses.pop()

    def _commit( self, dba: _AccessContext ) -> None:
        """ Explicitly commit within an access context.

        Commits the current transaction and begins a new one if the
        transaction is still active.

        Args:
            dba: The access context requesting commit

        Raises:
            AssertionError: If not in write mode or if not the transaction owner
        """

        assert self.__locked, 'Can only commit with write access'
        assert self.__accesses[0] == dba, 'Only transaction may commit'

        self.__session._commit()
        if( self.__locked ):
            self.__session._begin()

    def _rollback( self, dba: _AccessContext ) -> None:
        """ Explicitly rollback within an access context.

        Rolls back the current transaction and begins a new one if the
        transaction is still active.

        Args:
            dba: The access context requesting rollback

        Raises:
            AssertionError: If not in write mode or if not the transaction owner
        """

        assert self.__locked, 'Can only rollback with write access'
        assert self.__accesses[0] == dba, 'Only transaction may rollback'

        self.__session._rollback()
        if( self.__locked ):
            self.__session._begin()

    def enable_writes( self ) -> None:
        """ Enable write access for this access manager.

        Must be called before any write-mode contexts can be created.
        Typically called once during session initialization to grant
        write permissions.
        """

        self.__write_permitted = True

    def __call__( self, **kwargs ) -> _AccessContext:
        """ Create a new access context.

        Factory method for creating access contexts with specified options.
        Use via with statement:
            with access_manager(write=True):
                # write operations

        Args:
            **kwargs: Options passed to _AccessContext:
                     - write: bool, whether write access is needed
                     - transaction: bool, whether transaction mode is needed

        Returns:
            New _AccessContext instance
        """

        return _AccessContext( self, **kwargs )