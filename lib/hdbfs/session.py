import sys

from hdbfs.access import SessionAccess, AccessManager

from hdbfs.defs import *

import hdbfs.ark as ark
import hdbfs.model as model

from typing import Callable

HookCallback = Callable[ ['Session',bool], None ]

class Hooks:

    def __init__( self ):

        self._pre_commit_hooks = []
        self._post_commit_hooks = []

    def add_pre_commit_hook( self, hook: HookCallback ):

        self._pre_commit_hooks.append( hook )

    def add_post_commit_hook( self, hook: HookCallback ):

        self._post_commit_hooks.append( hook )

    def trigger_pre_commit_hooks( self, session: 'Session', is_rollback: bool ):

        for hook in self._pre_commit_hooks:
            try:
                hook( session, is_rollback )
            except:
                LOG.warning( f'Pre commit hook "{str( hook )}" failed: {str( sys.exc_info()[1] )}' )

    def trigger_post_commit_hooks( self, session: 'Session', is_rollback: bool ):

        for hook in self._post_commit_hooks:
            try:
                hook( session, is_rollback )
            except:
                LOG.warning( f'Post commit hook "{str( hook )}" failed: {str( sys.exc_info()[1] )}' )

class Session( SessionAccess ):
    '''Basic higu database session.'''

    def __init__( self, imgdat_config ):

        self.hooks = Hooks()

        self.model = model.Session()

        self.imgdb = ark.StreamDatabase( imgdat_config )

        self._access = AccessManager( self )
        self._trans_write = False

        self._so_factories = []

        self.obj_del_list = []

    def __enter__( self ):

        return self

    def __exit__( self, type, value, tb ):

        self.close()

    def _with_access( *access_args, **access_kwargs ):

        def decorator( f ):

            def wrapper( self, *args, **kwargs ):
                with self._access( *access_args, **access_kwargs ):
                    return f( self, *args, **kwargs )

            return wrapper

        return decorator

    def _begin( self ):

        assert not self._trans_write
        self.model.execute( 'BEGIN EXCLUSIVE' )
        self._trans_write = True

    def _commit( self ):

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

    def _rollback( self ):

        if( not self._trans_write ):
            return

        self.hooks.trigger_pre_commit_hooks( self, True )

        self.imgdb.rollback()
        self.model.rollback()
        self._trans_write = False

        self.hooks.trigger_post_commit_hooks( self, True )

    def _add_session_object_factory( self,
                            factory: Callable[ ['Session',any], 'SessionObject' ]
                        ) -> None:

        self._so_factories.append( factory )

    def _construct_session_object( self, model_obj: any ) -> 'SessionObject':

        for f in self._so_factories:
            r = f( self, model_obj )
            if( r is not None ):
                return r
        else:
            assert False

    def close( self ):

        self.model.close()
        self.model = None

    def enable_write_access( self ):

        self._access.enable_writes()

    def transaction( self ):

        return self._access( transaction = True )

class SessionObject:

    def __init__( self, session: Session ):

        self.session = session

    def _with_access( *access_args, **access_kwargs ):

        def decorator( f ):

            def wrapper( self: SessionObject, *args, **kwargs ):
                with self.session._access( *access_args, **access_kwargs ):
                    return f( self, *args, **kwargs )

            return wrapper

        return decorator

class SessionObjectFactoryIterator:

    def __init__( self, session: 'Session', iterable: list ):

        self.session = session
        self.it = iterable.__iter__()

    def __iter__( self ):

        return SessionObjectFactoryIterator( self.session, self.it )

    def __next__( self ):

        return self.session._construct_session_object( self.it.__next__() )
