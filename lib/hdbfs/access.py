from typing import Protocol

class SessionAccess( Protocol ):

    def _begin() -> None:
        '''Begins a transaction.'''
        ...

    def _commit() -> None:
        '''Commits the transaction.'''
        ...

    def _rollback() -> None:
        '''Performs a rollback on the transaction.'''
        ...

class _AccessContext:
    '''Context instance for accessing a session'''

    def __init__( self,
                  manager: 'AccessManager',
                  write: bool = False,
                  transaction: bool = False ):

        self.__manager = manager
        self.__write = write
        self.__transaction = transaction
        self.__active = False

    def __enter__( self ) -> '_AccessContext':

        self.__manager._begin_access( self )
        self.__active = True

        return self

    def __exit__( self, type, value, trace ):

        self.__active = False
        self.__manager._end_access( self, type is not None )

        if( type is not None ):
            raise type.with_traceback( value, trace )

    def is_transaction( self ):
        return self.__transaction

    def is_write( self ):
        return self.__write

    def commit( self ):
        self.__manager._commit( self )

    def rollback( self ):
        self.__manager._rollback( self )

class AccessManager:

    def __init__( self, session: SessionAccess ):

        self.__session = session
        self.__write_permitted = False

        self.__accesses = []
        self.__locked = False
        self.__failed = False

    def _begin_access( self, dba: _AccessContext ):
        '''Begins an access context.'''

        assert not dba.is_write() or self.__write_permitted, 'Read-Only Access'

        if( dba.is_transaction() ):
            assert len( self.__accesses ) == 0

        if( dba.is_write() and not self.__locked ):
            self.__session._begin()
            self.__locked = True

        # Add our context last: we don't want to add
        # if beginning of the session fails.
        self.__accesses.append( dba )

    def _end_access( self, dba: _AccessContext, is_except: bool ):
        '''Ends an access context.'''

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

    def _commit( self, dba: _AccessContext ):
        '''Commits within the access context.'''

        assert self.__locked, 'Can only commit with write access'
        assert self.__accesses[0] == dba, 'Only transaction may commit'

        self.__session._commit()
        if( self.__locked ):
            self.__session._begin()

    def _rollback( self, dba: _AccessContext ):
        '''Performs a rollback within the access context.'''

        assert self.__locked, 'Can only rollback with write access'
        assert self.__accesses[0] == dba, 'Only transaction may rollback'

        self.__session._rollback()
        if( self.__locked ):
            self.__session._begin()

    def enable_writes( self ):
        '''Enables write access.'''

        self.__write_permitted = True

    def __call__( self, **kwargs ):

        return _AccessContext( self, **kwargs )