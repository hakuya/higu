""" Database session management.

This module provides the core Session class for managing the higu database
and image archive. Sessions coordinate between the metadata database and
image file storage, providing transaction support and access control.

Key classes:
    - Session: Manages higu database and image archive with transaction support
    - Hooks: Pre/post commit hook management
    - SessionObject: Base class for objects bound to a session
    - SessionObjectFactoryIterator: Iterator that constructs session objects

The Session class uses a context manager pattern for automatic cleanup and
provides transaction support with rollback capability.
"""

import sys

from hdbfs.access import SessionAccess, AccessManager

from hdbfs.defs import *

import hdbfs.ark as ark
import hdbfs.model as model

from typing import Callable, List, Any, Iterator, Optional

HookCallback = Callable[ ['Session', bool], None ]
SessionObjectFactory = Callable[ ['Session', Any], Optional['SessionObject'] ]

class Hooks:
    """ Manages pre-commit and post-commit hooks for database sessions.

    Hooks allow registering callbacks that execute before and after transaction
    commits or rollbacks. Failed hooks log warnings but don't abort the
    transaction.

    Attributes:
        _pre_commit_hooks: List of callbacks to run before commit/rollback
        _post_commit_hooks: List of callbacks to run after commit/rollback
    """

    def __init__( self ):
        """ Initialize empty hook lists. """

        self._pre_commit_hooks: List[HookCallback] = []
        self._post_commit_hooks: List[HookCallback] = []

    def add_pre_commit_hook( self, hook: HookCallback ) -> None:
        """ Register a hook to run before commits/rollbacks.

        Args:
            hook: Callback function(session, is_rollback) -> None
        """

        self._pre_commit_hooks.append( hook )

    def add_post_commit_hook( self, hook: HookCallback ) -> None:
        """ Register a hook to run after commits/rollbacks.

        Args:
            hook: Callback function(session, is_rollback) -> None
        """

        self._post_commit_hooks.append( hook )

    def trigger_pre_commit_hooks( self, session: 'Session', is_rollback: bool ) -> None:
        """ Execute all pre-commit hooks.

        Args:
            session: Current database session
            is_rollback: True if rolling back, False if committing
        """

        for hook in self._pre_commit_hooks:
            try:
                hook( session, is_rollback )
            except:
                LOG.warning( f'Pre commit hook "{str( hook )}" failed: {str( sys.exc_info()[1] )}' )

    def trigger_post_commit_hooks( self, session: 'Session', is_rollback: bool ) -> None:
        """ Execute all post-commit hooks.

        Args:
            session: Current database session
            is_rollback: True if rolling back, False if committing
        """

        for hook in self._post_commit_hooks:
            try:
                hook( session, is_rollback )
            except:
                LOG.warning( f'Post commit hook "{str( hook )}" failed: {str( sys.exc_info()[1] )}' )

class Session( SessionAccess ):
    """ Manages the higu database and image archive.

    Coordinates operations between the higu metadata database and image
    archive. Provides transaction support, access control, and hook management
    for database operations.

    Sessions should be used as context managers to ensure proper cleanup.

    Attributes:
        hooks: Pre/post commit hook manager
        model: Higu metadata database session
        imgdb: Image archive (StreamDatabase)
        obj_del_list: List of objects marked for deletion
        _access: Access control manager
        _trans_write: True if currently in a write transaction
        _so_factories: List of SessionObject factory functions

    Example:
        >>> with Session(config) as session:
        ...     session.enable_write_access()
        ...     with session.transaction():
        ...         # Do work
        ...         pass
    """

    def __init__( self, imgdat_config: 'ImageDbDataConfig' ):
        """ Initialize a new database session.

        Args:
            imgdat_config: Image database configuration
        """

        self.hooks = Hooks()

        self.model = model.Session()

        self.imgdb = ark.StreamDatabase( imgdat_config )

        self._access = AccessManager( self )
        self._trans_write = False

        self._so_factories: List[SessionObjectFactory] = []

        self.obj_del_list: List[Any] = []

    def __enter__( self ) -> 'Session':
        """ Enter context manager.

        Returns:
            Self for context manager protocol
        """

        return self

    def __exit__( self, type, value, tb ) -> None:
        """ Exit context manager, closing the session. """

        self.close()

    def _with_access( *access_args, **access_kwargs ):
        """ Decorator that wraps method calls with access control context.

        This is a decorator factory for Session methods that need access control.
        """

        def decorator( f ):

            def wrapper( self, *args, **kwargs ):
                with self._access( *access_args, **access_kwargs ):
                    return f( self, *args, **kwargs )

            return wrapper

        return decorator

    def _begin( self ) -> None:
        """ Begin an exclusive write transaction.

        Starts a SQLite exclusive transaction. Asserts that no transaction
        is currently active.
        """

        assert not self._trans_write
        self.model.execute( 'BEGIN EXCLUSIVE' )
        self._trans_write = True

    def _commit( self ) -> None:
        """ Commit the current transaction.

        Commits changes to both higu database and image archive.
        Triggers pre-commit hooks before committing, post-commit hooks after.
        Clears obj_del_list on successful commit.

        If not in a transaction, this is a no-op.

        Raises:
            Exception: If commit fails (rolls back image archive changes)
        """

        if( not self._trans_write ):
            return

        self.imgdb.prepare_commit()

        try:
            self.hooks.trigger_pre_commit_hooks( self, False )
            self.model.commit()
            self.imgdb.complete_commit()
        except:
            self.imgdb.unprepare_commit()
            raise

        self.obj_del_list = []
        self._trans_write = False

        self.hooks.trigger_post_commit_hooks( self, False )

    def _rollback( self ) -> None:
        """ Roll back the current transaction.

        Discards changes to both higu database and image archive.
        Triggers pre-commit hooks (with is_rollback=True) before rollback,
        post-commit hooks after.

        If not in a transaction, this is a no-op.
        """

        if( not self._trans_write ):
            return

        self.hooks.trigger_pre_commit_hooks( self, True )

        self.imgdb.rollback()
        self.model.rollback()
        self._trans_write = False

        self.hooks.trigger_post_commit_hooks( self, True )

    def _add_session_object_factory( self, factory: SessionObjectFactory ) -> None:
        """ Register a SessionObject factory function.

        Factory functions convert model objects into SessionObject instances.
        They are tried in registration order until one returns non-None.

        Args:
            factory: Function(session, model_obj) -> SessionObject or None
        """

        self._so_factories.append( factory )

    def _construct_session_object( self, model_obj: Any ) -> 'SessionObject':
        """ Construct a SessionObject from a model object.

        Tries registered factories in order until one returns a SessionObject.

        Args:
            model_obj: Model object to wrap

        Returns:
            Appropriate SessionObject subclass instance

        Raises:
            AssertionError: If no factory can handle the model object
        """

        for f in self._so_factories:
            r = f( self, model_obj )
            if( r is not None ):
                return r
        else:
            assert False

    def close( self ) -> None:
        """ Close the session and release resources.

        Closes the higu database connection. Should be called when
        done with the session, or use context manager for automatic cleanup.
        """

        self.model.close()
        self.model = None

    def enable_write_access( self ) -> None:
        """ Enable write access for this session.

        Must be called before performing any write operations or starting
        transactions.
        """

        self._access.enable_writes()

    def transaction( self ):
        """ Create a transaction context manager.

        Returns:
            Context manager that handles transaction begin/commit/rollback

        Example:
            >>> with session.transaction():
            ...     # Perform database operations
            ...     pass  # Auto-commits on success, rolls back on exception
        """

        return self._access( transaction = True )

class SessionObject:
    """ Base class for objects bound to a database session.

    SessionObjects provide access to database operations and maintain
    a reference to their parent session. They use the session's access
    control system for all operations.

    Attributes:
        session: Parent database session
    """

    def __init__( self, session: Session ):
        """ Initialize a session object.

        Args:
            session: Parent database session
        """

        self.session = session

    def _with_access( *access_args, **access_kwargs ):
        """ Decorator that wraps method calls with access control context.

        This is a decorator factory for SessionObject methods that need
        access control, delegating to the parent session's access manager.
        """

        def decorator( f ):

            def wrapper( self: SessionObject, *args, **kwargs ):
                with self.session._access( *access_args, **access_kwargs ):
                    return f( self, *args, **kwargs )

            return wrapper

        return decorator

class SessionObjectFactoryIterator:
    """ Iterator that constructs SessionObjects from model objects on-demand.

    Wraps an iterable of model objects, lazily converting each to a
    SessionObject via the session's factory system. Useful for efficient
    iteration over query results.

    Attributes:
        session: Database session for factory construction
        it: Underlying iterator of model objects
    """

    def __init__( self, session: 'Session', iterable: List[Any] ):
        """ Initialize the factory iterator.

        Args:
            session: Database session
            iterable: List or iterable of model objects
        """

        self.session = session
        self.it = iterable.__iter__()

    def __iter__( self ) -> 'SessionObjectFactoryIterator':
        """ Return a new iterator over the same underlying iterable.

        Returns:
            New SessionObjectFactoryIterator instance
        """

        return SessionObjectFactoryIterator( self.session, self.it )

    def __next__( self ) -> SessionObject:
        """ Get the next SessionObject.

        Returns:
            Next model object converted to SessionObject

        Raises:
            StopIteration: When underlying iterator is exhausted
        """

        return self.session._construct_session_object( self.it.__next__() )
