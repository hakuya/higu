import threading
import time
import uuid

import hdbfs

class Cacheable:

    def __init__( self ):

        self.uuid = uuid.uuid4().hex
        self.access_time = time.time()

    def get_uuid( self ):

        return self.uuid

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

        self.items[item.get_uuid()] = item

    def get( self, item_uuid ):

        item = self.items[item_uuid]
        item.touch()
        
        return item

    def remove( self, item_uuid ):

        del self.items[item_uuid]

    def flush( self ):

        for item in self.items.values():
            item.flush()

        for item in [item for item in self.items.values()
                        if( item.is_expired() ) ]:

            del self.items[item.get_uuid()]

class Selection( Cacheable ):

    def __init__( self, results ):

        Cacheable.__init__( self )

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

    def __init__( self ):

        Cacheable.__init__( self )
        
        self.selections = CacheSet()
        self.write_access = False

    def flush( self ):

        self.selections.flush()

    def enable_write_access( self ):

        self.write_access = True

    def register_selection( self, selection ):

        sel = Selection( selection )
        self.selections.register( sel )

        return sel

    def fetch_selection( self, sel_id ):

        return self.selections.get( sel_id )

    def close_selection( self, sel_id ):

        self.selections.remove( sel_id )

    def get_db( self ):

        db = hdbfs.Database()
        if( self.write_access ):
            db.enable_write_access()

        return db

class SessionCache:

    def __init__( self ):

        self.lock = threading.Lock()
        self.sessions = CacheSet()

    def flush( self ):

        with self.lock:
            self.sessions.flush()

    def new( self ):

        with self.lock:
            session = Session()
            self.sessions.register( session )

            return session.get_uuid()

    def enable_write_access( self, session_id ):

        with self.lock:
            session = self.sessions.get( session_id )
            session.enable_write_access()

    def close( self, session_id ):

        with self.lock:
            self.sessions.remove( session_id )

    def get_db( self, session_id ):

        with self.lock:
            session = self.sessions.get( session_id )
            return session.get_db()

    def register_selection( self, session_id, selection ):

        with self.lock:
            session = self.sessions.get( session_id )
            return session.register_selection( selection )

    def fetch_selection( self, session_id, selection_id ):

        with self.lock:
            session = self.sessions.get( session_id )
            return session.fetch_selection( selection_id )

    def close_selection( self, session_id, selection_id ):

        with self.lock:
            session = self.sessions.get( session_id )
            session.close_selection( selection_id )

default_cache = None

def get_default_cache():
    global default_cache

    if( default_cache is None ):
        default_cache = SessionCache()

    return default_cache
