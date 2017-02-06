import threading
import time
import uuid

import hdbfs

class Cacheable:

    def __init__( self, item_id ):

        self.item_id = item_id
        self.access_time = time.time()

    def get_id( self ):

        return self.item_id

    def touch( self ):

        self.access_time = time.time()

    def flush( self ):

        pass

    def is_expired( self ):

        return time.time() > self.access_time + 3600

class CacheSet:

    def __init__( self ):

        self.items = {}

    def register( self, item ):

        self.items[item.get_id()] = item

    def get( self, item_id ):

        item = self.items[item_id]
        item.touch()
        
        return item

    def remove( self, item_id ):

        del self.items[item_id]

    def flush( self ):

        for item in self.items.values():
            item.flush()

        for item in [item for item in self.items.values()
                        if( item.is_expired() ) ]:

            del self.items[item.get_id()]

class Selection( Cacheable ):

    def __init__( self, results ):

        Cacheable.__init__( self, uuid.uuid4().hex )

        if( isinstance( results, list ) ):
            self.loaded = results
        else:
            self.loaded = []
            self.preload( results.__iter__() )

    def preload( self, results ):

        i = 0

        try:
            self.loaded = [ 0 ] * 10000
            for i in range( 10000 ):
                self.loaded[i] = results.next().get_id()
        except StopIteration:
            self.loaded = self.loaded[:i]

    def __len__( self ):

        return len( self.loaded )

    def __getitem__( self, idx ):

        assert( isinstance( idx, int ) )
        if( idx < 0 or idx >= len( self.loaded ) ):
            raise IndexError

        return self.loaded[idx]

class Session( Cacheable ):

    def __init__( self, session_id ):

        Cacheable.__init__( self, session_id )
        
        self.selections = CacheSet()

    def flush( self ):

        self.selections.flush()

    def register_selection( self, selection ):

        sel = Selection( selection )
        self.selections.register( sel )

        return sel

    def fetch_selection( self, sel_id ):

        return self.selections.get( sel_id )

    def close_selection( self, sel_id ):

        self.selections.remove( sel_id )

class SessionCache:

    def __init__( self ):

        self.lock = threading.Lock()
        self.sessions = CacheSet()

    def flush( self ):

        with self.lock:
            self.sessions.flush()

    def drop( self, session_id ):

        with self.lock:
            try:
                self.sessions.remove( session_id )
            except KeyError:
                pass

    def register_selection( self, session_id, selection ):

        with self.lock:
            try:
                session = self.sessions.get( session_id )
            except KeyError:
                session = Session( session_id )
                self.sessions.register( session )

            return session.register_selection( selection )

    def fetch_selection( self, session_id, selection_id ):

        with self.lock:
            try:
                session = self.sessions.get( session_id )
            except KeyError:
                return None

            try:
                return session.fetch_selection( selection_id )
            except KeyError:
                return None

    def close_selection( self, session_id, selection_id ):

        with self.lock:
            try:
                session = self.sessions.get( session_id )
            except KeyError:
                return

            try:
                session.close_selection( selection_id )
            except KeyError:
                return

default_cache = None

def get_default_cache():
    global default_cache

    if( default_cache is None ):
        default_cache = SessionCache()

    return default_cache
