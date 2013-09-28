import higu
import model
import sys
import uuid
import time
import threading

VERSION = 0
REVISION = 0

class Selection:

    def __init__( self, results ):

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

    def fetch( self, idx ):

        assert( isinstance( idx, int ) )
        if( idx < 0 or idx >= len( self.loaded ) ):
            raise StopIteration

        return self.loaded[idx]

class SelectionCache:

    def __init__( self ):

        self.selections = {}
        self.lock = threading.Lock()

    def flush( self ):

        with self.lock:
            clear_list = []

            for sel in self.selections:
                ot, rs = self.selections[sel]
                if( time.time() > ot + 3600 ):
                    clear_list.append( sel )

            for sel in clear_list:
                del self.selections[sel]

    def close( self, sel_id ):

        with self.lock:
            del self.selections[sel_id]

    def register( self, sel ):

        self.flush()

        with self.lock:
            sel_id = uuid.uuid4().hex
            self.selections[sel_id] = ( time.time(), sel, )
            return sel_id

    def fetch( self, sel_id ):

        self.flush()

        with self.lock:
            ot, sel = self.selections[sel_id]
            self.selections[sel_id] = ( time.time(), sel, )

            return sel

default_cache = None

def get_default_cache():
    global default_cache

    if( default_cache is None ):
        default_cache = SelectionCache()

    return default_cache

class JsonInterface:

    def __init__( self ):

        self.db = higu.Database()
        self.cache = get_default_cache()

    def close( self ):

        self.db.close()

    def execute( self, data ):

        #try:
        fn = getattr( self, 'cmd_' + data['action'] )
        return fn( data )
        #except:
        #    return {
        #        'result' : 'error',
        #        'errmsg' : sys.exc_info()[0],
        #    }

    def cmd_version( self, data ):

        return {
            'result'    : 'ok',
            'json_ver'  : [ VERSION, REVISION ],
            'higu_ver'  : [ higu.VERSION, higu.REVISION ],
            'db_ver'    : [ model.VERSION, model.REVISION ],
        }

    def cmd_info( self, data ):

        targets = data['targets']
        targets = map( self.db.get_object_by_id, targets )

        items = data['items']

        def fetch_info( target ):

            info = {}

            if( 'type' in items ):
                type = target.get_type()
                if( type == higu.TYPE_FILE
                 or type == higu.TYPE_FILE_DUP
                 or type == higu.TYPE_FILE_VAR ):
                    info['type'] = 'file'
                elif( type == higu.TYPE_ALBUM ):
                    info['type'] = 'album'
                elif( type == higu.TYPE_CLASSIFIER ):
                    info['type'] = 'tag'
                else:
                    info['type'] = 'unknown'
            if( 'repr' in items ):
                info['repr'] = target.get_repr()
            if( isinstance( target, higu.File ) and 'path' in items ):
                info['path'] = target.get_path()
            if( 'tags' in items ):
                tags = target.get_tags()
                info['tags'] = map( lambda x: x.get_name(), tags )
            if( 'names' in items ):
                info['names'] = target.get_names()
            if( isinstance( target, higu.File ) and 'duplication' in items ):
                if( target.is_duplicate() ):
                    info['duplication'] = 'duplicate'
                elif( target.is_variant() ):
                    info['duplication'] = 'variant'
                else:
                    info['duplication'] = 'original'
            if( isinstance( target, higu.File ) and 'similar_to' in items ):
                similar = target.get_similar_to()
                if( similar is not None ):
                    info['similar_to'] = [ similar.get_id(), similar.get_repr() ]
            if( isinstance( target, higu.File ) and 'duplicates' in items ):
                duplicates = target.get_duplicates()
                info['duplicates'] = map(
                        lambda x: [ x.get_id(), x.get_repr() ],
                        duplicates )
            if( isinstance( target, higu.File ) and 'variants' in items ):
                variants = target.get_variants()
                info['variants'] = map(
                        lambda x: [ x.get_id(), x.get_repr() ],
                        variants )
            if( isinstance( target, higu.File ) and 'albums' in items ):
                albums = target.get_albums()
                info['albums'] = map(
                        lambda x: [ x.get_id(), x.get_repr() ],
                        albums )
            if( isinstance( target, higu.Album ) and 'files' in items ):
                files = target.get_files()
                info['files'] = map(
                        lambda x: [ x.get_id(), x.get_repr() ],
                        files )

            return info

        results = map( fetch_info, targets )
        return {
            'info' : results,
            'result' : 'ok',
        }

    def cmd_tag( self, data ):

        targets = data['targets']
        targets = map( self.db.get_object_by_id, targets )

        add_tags = data['add_tags']
        sub_tags = data['sub_tags']
        new_tags = data['new_tags']

        add = map( self.db.get_tag, add_tags )
        sub = map( self.db.get_tag, sub_tags )
        add += map( self.db.make_tag, new_tags )

        for obj in targets:
            for t in sub:
                obj.unassign( t )
            for t in add:
                obj.assign( t )

        self.db.commit()

        return { 'result' : 'ok' }

    def cmd_deorder( self, data ):

        group = self.db.get_object_by_id( data['group'] )
        assert( isinstance( group, higu.OrderedGroup ) )

        group.clear_order()

        return { 'result' : 'ok' }

    def cmd_reorder( self, data ):

        group = data['group']
        items = data['items']

        group = self.db.get_object_by_id( group )
        assert( isinstance( group, higu.OrderedGroup ) )

        items = map( self.db.get_object_by_id, items )

        group.set_order( items )

        return { 'result' : 'ok' }

    def cmd_taglist( self, data ):

        tags = self.db.all_tags()
        tags = map( lambda x: x.get_name(), tags )

        return {
            'result'    : 'ok',
            'tags'      : tags,
        }

    def cmd_search( self, data ):

        if( data.has_key( 'mode' ) ):
            if( data['mode'] == 'all' ):
                rs = self.db.all_albums_or_free_files()
            elif( data['mode'] == 'untagged' ):
                rs = self.db.unowned_files()
            elif( data['mode'] == 'albums' ):
                rs = self.db.all_albums()
            elif( data['mode'] == 'album' ):
                album = self.db.get_object_by_id( data['album'] )
                rs = map( lambda x: x.get_id(), album.get_files() )

        else:
            if( data.has_key( 'strict' ) and data['strict'] ):
                strict = True
            else:
                strict = False

            req = data['req'] if data.has_key( 'req' ) else []
            add = data['add'] if data.has_key( 'add' ) else []
            sub = data['sub'] if data.has_key( 'sub' ) else []

            req = map( self.db.get_tag, req )
            add = map( self.db.get_tag, add )
            sub = map( self.db.get_tag, sub )

            rs = self.db.lookup_ids_by_tags( req, add, sub, strict,
                    random_order = True )

        sel = Selection( rs )
        selid = self.cache.register( sel )

        if( data.has_key( 'index' ) ):
            idx = data['index']
        else:
            idx = 0

        return {
            'result' : 'ok',
            'selection' : selid,
            'index' : idx,
            'first' : sel.fetch( idx ),
        }

    def cmd_selection_fetch( self, data ):

        sel_id = data['selection']
        idx = data['index']

        sel = self.cache.fetch( sel_id )
        obj_id = sel.fetch( idx )

        return {
            'result' : 'ok',
            'object_id' : obj_id
        }

    def cmd_selection_close( self, data ):

        sel_id = data['selection']
        self.cache.close( sel_id )
        
        return {
            'result' : 'ok',
        }

init = higu.init
init_default = higu.init_default
