import datetime
import inspect
import sys

import hdbfs

import cache

VERSION = 0
REVISION = 0

def get_type_str( obj ):

    type = obj.get_type()
    if( type == hdbfs.TYPE_FILE ):
        return 'file'
    elif( type == hdbfs.TYPE_ALBUM ):
        return 'album'
    elif( type == hdbfs.TYPE_CLASSIFIER ):
        return 'tag'
    else:
        return 'unknown'

def make_obj_tuple( obj ):

    return [ obj.get_id(), obj.get_repr(), get_type_str( obj ) ]

def json_ok( **args ):

    args['result'] = 'ok'
    return args

def json_err( err, emsg = None ):

    if( isinstance( err, KeyError ) ):
        etype = 'key'
        emsg = err.message
    elif( isinstance( err, ValueError ) ):
        etype = 'value'
        emsg = err.message
    elif( isinstance( err, str ) ):
        etype = err
        if( emsg is None ):
            emsg = 'An %s error has occured' % ( etype, )
    else:
        etype = 'unknown'
        emsg = 'An %s error has occured' % ( str( etype ), )

    if( emsg is None ):
        return {
            'result' : 'err',
            'except' : etype,
        }
    else:
        return {
            'result' : 'err',
            'except' : etype,
            'msg'    : emsg,
        }

def fetch_info( items, target, stream = None ):

    if( target is None ):
        return { 'type' : 'invalid' }

    info = {}
    target.check_metadata()
    if( stream is not None ):
        stream.check_metadata()

    if( 'type' in items ):
        info['type'] = get_type_str( target )
    if( 'text' in items ):
        info['text'] = target.get_text()
    if( 'repr' in items ):
        info['repr'] = target.get_repr()
    if( 'tags' in items ):
        tags = target.get_tags()
        info['tags'] = map( lambda x: x.get_name(), tags )
    if( 'names' in items ):
        if( isinstance( target, hdbfs.File ) ):
            info['names'] = target.get_origin_names()
        else:
            name = target.get_name()
            if( name is not None ):
                info['names'] = [ target.get_name(), ]
            else:
                info['names'] = []
    if( isinstance( target, hdbfs.File ) and 'variants' in items ):
        variants = target.get_variants()
        info['variants'] = map( make_obj_tuple, variants )
    if( isinstance( target, hdbfs.File ) and 'variants_of' in items ):
        variants_of = target.get_variants_of()
        info['variants_of'] = map( make_obj_tuple, variants_of )
    if( isinstance( target, hdbfs.File ) and 'dup_streams' in items ):
        dups = target.get_duplicate_streams()
        info['dup_streams'] = map( lambda x: x.get_stream_id(), dups )
    if( isinstance( target, hdbfs.File ) and 'albums' in items ):
        albums = target.get_albums()
        info['albums'] = map( make_obj_tuple, albums )
    if( isinstance( target, hdbfs.Album ) and 'files' in items ):
        files = target.get_files()
        info['files'] = map( make_obj_tuple, files )
    if( isinstance( target, hdbfs.File ) and 'thumb_gen' in items ):
        try:
            info['thumb_gen'] = int( target['.tbinfo'].split( ':' )[0] )
        except:
            info['thumb_gen'] = 0
    if( 'width' in items or 'height' in items ):
        if( stream is not None ):
            if( isinstance( stream, hdbfs.ImageStream ) ):
                try:
                    w, h = stream.get_dimensions()
                except:
                    w = None
                    h = None
                info['width'] = w
                info['height'] = h
        elif( isinstance( target, hdbfs.ImageFile ) ):
            try:
                w, h = target.get_dimensions()
            except:
                w = None
                h = None
            info['width'] = w
            info['height'] = h
    if( 'origin_time' in items ):
        if( stream is not None ):
            origin_ts = stream.get_origin_time()
        else:
            origin_ts = target.get_origin_time()
        if( origin_ts is not None ):
            info['origin_time'] = origin_ts.strftime( '%Y/%m/%d %H:%M:%S' )
        else:
            info['origin_time'] = None
    if( 'creation_time' in items ):
        if( stream is not None ):
            creation_ts = stream.get_creation_time()
        else:
            creation_ts = target.get_creation_time()
        if( creation_ts is not None ):
            info['creation_time'] = creation_ts.strftime( '%Y/%m/%d %H:%M:%S' )
        else:
            info['creation_time'] = None

    return info

class JsonInterface:

    def __init__( self, db, session_id ):

        self.__cache = cache.get_default_cache()
        self.__db = db
        self.__session_id = session_id

    def close( self ):

        pass

    def execute( self, data ):

        try:
            fn = getattr( self, 'cmd_' + data['action'] )
            argspec = inspect.getargspec( fn )
            if( 'data' in argspec.args ):
                # Old style
                return fn( data )
            elif( argspec.keywords is None ):
                # Grab the required and optional
                if( argspec.defaults is None ):
                    req_args = argspec.args[1:]
                    opt_args = []
                else:
                    req_args = argspec.args[1:-len( argspec.defaults )]
                    opt_args = argspec.args[-len( argspec.defaults ):]

                args = {}
                for arg in req_args:
                    assert data.has_key( arg ), "%s not provided" % ( arg, )
                    args[arg] = data[arg]
                for arg in opt_args:
                    if( data.has_key( arg ) ):
                        args[arg] = data[arg]
                return fn( **args )
            else:
                # Just make sure required arguments are present
                if( argspec.defaults is None ):
                    req_args = argspec.args[1:]
                else:
                    req_args = argspec.args[1:-len( argspec.defaults )]

                for arg in req_args:
                    assert data.has_key( arg ), 'Missing arg ' + arg
                return fn( **data )
        finally:
            pass
        #except:
        #    return {
        #        'result' : 'error',
        #        'errmsg' : sys.exc_info()[0],
        #    }

    def cmd_version( self ):

        return json_ok(
            json_ver = [ VERSION, REVISION ],
            higu_ver = [ hdbfs.VERSION, hdbfs.REVISION ],
            db_ver   = [ hdbfs.DB_VERSION, hdbfs.DB_REVISION ] )

    def cmd_info( self, targets, items ):

        db = self.__db

        def fetch_info_fn( target ):
            return fetch_info( items, target )

        targets = map( db.get_object_by_id, targets )
        results = map( fetch_info_fn, targets )

        return json_ok( info = results )

    def cmd_stream_info( self, target, stream, items ):

        db = self.__db
        target = db.get_object_by_id( target )
        if( stream is not None ):
            stream = db.get_stream_by_id( stream )

        results = fetch_info( items, target, stream )
        return json_ok( info = results )

    def cmd_tag( self, targets, **args ):

        db = self.__db

        targets = map( db.get_object_by_id, targets )

        if( args.has_key( 'query' ) ):
            tags = filter( lambda x: x != '', args['query'].split( ' ' ) )

            add = [t for t in tags if t[0] != '-' and t[0] != '!']
            new = [t[1:] for t in tags if t[0] == '!']
            sub = [t[1:] for t in tags if t[0] == '-']

        else:
            add = args['add_tags'] if( args.has_key( 'add_tags' ) ) else []
            sub = args['sub_tags'] if( args.has_key( 'sub_tags' ) ) else []
            new = args['new_tags'] if( args.has_key( 'new_tags' ) ) else []

        try:
            add = map( db.get_tag, add )
            sub = map( db.get_tag, sub )
            add += map( db.make_tag, new )
        except ( KeyError, ValueError, ), e:
            return json_err( e )

        for obj in targets:
            for t in sub:
                obj.unassign( t )
            for t in add:
                obj.assign( t )

        return json_ok()

    def cmd_rename( self, target, name, saveold = False ):

        db = self.__db

        target = db.get_object_by_id( target )
        target.set_name( name )

        return json_ok()

    def cmd_group_deorder( self, group ):

        db = self.__db

        group = db.get_object_by_id( group )
        assert( isinstance( group, hdbfs.OrderedGroup ) )

        group.clear_order()

        return json_ok()

    def cmd_group_reorder( self, group, items ):

        db = self.__db

        group = db.get_object_by_id( group )
        assert( isinstance( group, hdbfs.OrderedGroup ) )

        items = map( db.get_object_by_id, items )
        group.set_order( items )

        return json_ok()

    def cmd_taglist( self ):

        db = self.__db

        tags = db.all_tags()
        tags = map( lambda x: x.get_name(), tags )

        return json_ok( tags = tags )

    def cmd_search( self, data ):

        db = self.__db

        if( data.has_key( 'mode' ) ):
            # Search by directive
            if( data['mode'] == 'all' ):
                rs = db.all_albums_or_free_files()
            elif( data['mode'] == 'untagged' ):
                rs = db.unowned_files()
            elif( data['mode'] == 'album' ):
                album = db.get_object_by_id( data['album'] )
                rs = map( lambda x: x.get_id(), album.get_files() )

        else:
            if( data.has_key( 'query' ) ):
                #try:
                if( 1 ):
                    query = hdbfs.query.build_query( data['query'] )
                #except ( KeyError, ValueError, ), e:
                #    return json_err( e )

            else:
                query = hdbfs.query.Query()

                # Search by parts
                if( data.has_key( 'strict' ) and data['strict'] ):
                    query.set_strict()

                if( data.has_key( 'sort' ) and not data['randomize'] ):
                    if( data.has_key( 'rsort' ) and data['rsort'] ):
                        desc = True
                    else:
                        desc = False

                    query.add_sort( data['sort'], desc )


                req = data['req'] if data.has_key( 'req' ) else []
                add = data['add'] if data.has_key( 'add' ) else []
                sub = data['sub'] if data.has_key( 'sub' ) else []

                try:
                    req = map( higu.query.create_constraint, req )
                    add = map( higu.query.create_constraint, req )
                    sub = map( higu.query.create_constraint, req )
                except ( KeyError, ValueError, ), e:
                    return json_err( e )

            rs = query.execute( db )

        # Register the result set
        sel = self.__cache.register_selection(
                        self.__session_id, rs )
        selid = sel.get_id()

        if( data.has_key( 'index' ) ):
            idx = data['index']
        else:
            idx = 0

        results = len( sel )
        if( results > 0 ):
            if( idx == 0 or idx >= results ):
                return json_ok(
                    selection = selid,
                    results = results,
                    index = 0,
                    first = sel[0], )
            else:
                return json_ok(
                    selection = selid,
                    results = results,
                    index = idx,
                    first = sel[idx], )
        else:
            self.__cache.close_selection(
                    self.__session_id, selid )
            return json_ok( results = 0 )

    def cmd_selection_fetch( self, selection, index ):

        sel_id = selection
        idx = index

        sel = self.__cache.fetch_selection( self.__session_id, sel_id )
        try:
            obj_id = sel[idx]
        except IndexError:
            return json_err( 'index', 'Invalid index' )

        return json_ok( object_id = obj_id )

    def cmd_selection_close( self, selection ):

        if( not isinstance( selection, str ) ):
            return json_err( 'argument', 'selection is not a valid selection id' )

        try:
            self.__cache.close_selection( self.__session_id, selection )
        except KeyError:
            pass
        
        return json_ok()

    def cmd_group_create( self, targets ):

        db = self.__db

        targets = map( db.get_object_by_id, targets )
        for target in targets:
            assert( isinstance( target, hdbfs.File ) )

        group = db.create_album()
        assert( isinstance( group, hdbfs.Album ) )

        for target in targets:
            target.assign( group )

        return json_ok( group = group.get_id() )

    def cmd_group_delete( self, group ):

        db = self.__db

        group = db.get_object_by_id( group )
        assert( isinstance( group, hdbfs.Album ) )

        db.delete_object( group )

        return json_ok()

    def cmd_group_append( self, group, targets ):

        db = self.__db

        group = db.get_object_by_id( group )
        assert( isinstance( group, hdbfs.Album ) )

        targets = map( db.get_object_by_id, targets )
        for target in targets:
            assert( isinstance( target, hdbfs.File ) )
            target.assign( group )

        return json_ok()

    def cmd_group_remove( self, group, targets ):

        db = self.__db

        group = db.get_object_by_id( group )
        assert( isinstance( group, hdbfs.Album ) )

        targets = map( db.get_object_by_id, targets )
        for target in targets:
            assert( isinstance( target, hdbfs.File ) )
            target.unassign( group )

        return json_ok()

    def cmd_gather_tags( self, target ):

        db = self.__db

        obj = db.get_object_by_id( target )

        if( isinstance( obj, hdbfs.Album ) ):
            files = obj.get_files()

        else:
            assert False

        tags = []

        for f in files:
            for t in f.get_tags():
                if( t not in tags ):
                    tags.append( t )

        for t in tags:
            obj.assign( t )
            for f in files:
                f.unassign( t )

        return json_ok()

    def cmd_set_creation( self, target ):

        db = self.__db

        obj = db.get_object_by_id( target )

        if( isinstance( obj, hdbfs.Album ) ):
            files = obj.get_files()

        else:
            assert False

        min_ts = None

        for f in files:
            f_ts = f.get_creation_time()
            if( f_ts is not None
            and (min_ts is None or f_ts < min_ts) ):
                min_ts = f_ts

        if( min_ts is not None ):
            obj.set_creation_time( min_ts )

        return json_ok()

    def cmd_tag_delete( self, tag ):

        db = self.__db

        db.delete_tag( tag )
        return json_ok()

    def cmd_tag_move( self, tag, target ):

        db = self.__db

        db.move_tag( tag, target )
        return json_ok()

    def cmd_tag_copy( self, tag, target ):

        db = self.__db

        db.copy_tag( tag, target )
        return json_ok()

    def cmd_set_variant( self, original, variant ):

        db = self.__db

        original = db.get_object_by_id( original )
        variant = db.get_object_by_id( variant )

        variant.set_variant_of( original )

        return json_ok()

    def cmd_clear_variant( self, original, variant ):

        db = self.__db

        original = db.get_object_by_id( original )
        variant = db.get_object_by_id( variant )

        variant.clear_variant_of( original )

        return json_ok()

    def cmd_merge_duplicates( self, original, duplicate ):

        db = self.__db

        original = db.get_object_by_id( original )
        duplicate = db.get_object_by_id( duplicate )

        db.merge_objects( original, duplicate )

        return json_ok()

    def cmd_set_root_stream( self, target, stream ):

        db = self.__db

        target = db.get_object_by_id( target )
        stream = db.get_stream_by_id( stream )

        target.set_root_stream( stream )

        return json_ok()

    def cmd_auto_orientation( self, target ):

        db = self.__db

        target = db.get_object_by_id( target )
        target.auto_orientation()

        return json_ok()

    def cmd_rotate_cw( self, target ):

        db = self.__db

        target = db.get_object_by_id( target )
        target.rotate_cw()

        return json_ok()

    def cmd_rotate_ccw( self, target ):

        db = self.__db

        target = db.get_object_by_id( target )
        target.rotate_ccw()

        return json_ok()

    def cmd_mirror( self, target ):

        db = self.__db

        target = db.get_object_by_id( target )
        target.mirror()

        return json_ok()

init = hdbfs.init
