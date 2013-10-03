import higu
import model
import sys
import uuid
import time
import threading

VERSION = 0
REVISION = 0

def get_type_str( obj ):

    type = obj.get_type()
    if( type == higu.TYPE_FILE
     or type == higu.TYPE_FILE_DUP
     or type == higu.TYPE_FILE_VAR ):
        return 'file'
    elif( type == higu.TYPE_ALBUM ):
        return 'album'
    elif( type == higu.TYPE_CLASSIFIER ):
        return 'tag'
    else:
        return 'unknown'

def make_obj_tuple( obj ):

    return [ obj.get_id(), obj.get_repr(), get_type_str( obj ) ]

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

        try:
            fn = getattr( self, 'cmd_' + data['action'] )
            return fn( data )
        finally:
            self.db.rollback()
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

            if( target is None ):
                return { 'type' : 'invalid' }

            info = {}

            if( 'type' in items ):
                info['type'] = get_type_str( target )
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
                info['duplicates'] = map( make_obj_tuple, duplicates )
            if( isinstance( target, higu.File ) and 'variants' in items ):
                variants = target.get_variants()
                info['variants'] = map( make_obj_tuple, variants )
            if( isinstance( target, higu.File ) and 'albums' in items ):
                albums = target.get_albums()
                info['albums'] = map( make_obj_tuple, albums )
            if( isinstance( target, higu.Album ) and 'files' in items ):
                files = target.get_files()
                info['files'] = map( make_obj_tuple, files )

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

    def cmd_rename( self, data ):

        target = self.db.get_object_by_id( data['target'] )

        if( data.has_key( 'saveold' ) and data['saveold'] ):
            saveold = True
        else:
            saveold = False

        target.set_name( data['name'], saveold )
        self.db.commit()

        return { 'result' : 'ok' }

    def cmd_group_deorder( self, data ):

        group = self.db.get_object_by_id( data['group'] )
        assert( isinstance( group, higu.OrderedGroup ) )

        group.clear_order()

        return { 'result' : 'ok' }

    def cmd_group_reorder( self, data ):

        group = data['group']
        items = data['items']

        group = self.db.get_object_by_id( group )
        assert( isinstance( group, higu.OrderedGroup ) )

        items = map( self.db.get_object_by_id, items )

        group.set_order( items )

        self.db.commit()

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

            if( data.has_key( 'randomize' ) and not data['randomize'] ):
                randomize = False
            else:
                randomize = True

            req = data['req'] if data.has_key( 'req' ) else []
            add = data['add'] if data.has_key( 'add' ) else []
            sub = data['sub'] if data.has_key( 'sub' ) else []

            req = map( self.db.get_tag, req )
            add = map( self.db.get_tag, add )
            sub = map( self.db.get_tag, sub )

            rs = self.db.lookup_ids_by_tags( req, add, sub, strict,
                    random_order = randomize )

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

    def cmd_group_create( self, data ):

        targets = map( self.db.get_object_by_id, data['targets'] )
        for target in targets:
            assert( isinstance( target, higu.File ) )

        group = self.db.create_album()
        assert( isinstance( group, higu.Album ) )

        for target in targets:
            target.assign( group )

        self.db.commit()

        return {
            'result' :  'ok',
            'group' :   group.get_id(),
        }

    def cmd_group_delete( self, data ):

        group = self.db.get_object_by_id( data['group'] )
        assert( isinstance( group, higu.Album ) )

        self.db.delete_object( group )
        self.db.commit()

        return {
            'result' : 'ok',
        }

    def cmd_group_append( self, data ):

        group = self.db.get_object_by_id( data['group'] )
        assert( isinstance( group, higu.Album ) )

        targets = map( self.db.get_object_by_id, data['targets'] )
        for target in targets:
            assert( isinstance( target, higu.File ) )
            target.assign( group )

        self.db.commit()

        return {
            'result' : 'ok',
        }

    def cmd_group_remove( self, data ):

        group = self.db.get_object_by_id( data['group'] )
        assert( isinstance( group, higu.Album ) )

        targets = map( self.db.get_object_by_id, data['targets'] )
        for target in targets:
            assert( isinstance( target, higu.File ) )
            target.unassign( group )

        self.db.commit()

        return {
            'result' : 'ok',
        }

    def cmd_group_gather_tags( self, data ):

        group = self.db.get_object_by_id( data['group'] )
        assert( isinstance( group, higu.Album ) )

        files = group.get_files()
        tags = []

        for f in files:
            for t in f.get_tags():
                if( t not in tags ):
                    tags.append( t )

        for t in tags:
            group.assign( t )
            for f in files:
                f.unassign( t )

        self.db.commit()

        return {
            'result' : 'ok'
        }

    def cmd_tag_delete( self, data ):

        self.db.delete_tag( data['tag'] )
        self.db.commit()

        return {
            'result' : 'ok',
        }

    def cmd_tag_move( self, data ):

        self.db.move_tag( data['tag'], data['target'] )
        self.db.commit()

        return {
            'result' : 'ok',
        }

    def cmd_tag_copy( self, data ):

        self.db.copy_tag( data['tag'], data['target'] )
        self.db.commit()

        return {
            'result' : 'ok',
        }


    def cmd_set_duplication( self, data ):

        original = self.db.get_object_by_id( data['original'] )
        
        if( data.has_key( 'duplicates' ) ):
            dups = map( self.db.get_object_by_id, data['duplicates'] )
            for dup in dups:
                dup.set_duplicate_of( original )

        if( data.has_key( 'variants' ) ):
            vars = map( self.db.get_object_by_id, data['variants'] )
            for var in vars:
                var.set_varient_of( original )

        self.db.commit()

        return {
            'result' : 'ok',
        }

    def cmd_clear_duplication( self, data ):

        targets = data['targets']
        targets = map( self.db.get_object_by_id, targets )

        for target in targets:
            target.clear_duplication()

        self.db.commit()

        return {
            'result' : 'ok',
        }

init = higu.init
init_default = higu.init_default
