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
    elif( type == hdbfs.TYPE_DUPLICATE ):
        return 'duplicate'
    elif( type == hdbfs.TYPE_ALBUM ):
        return 'album'
    elif( type == hdbfs.TYPE_PUBLISHED ):
        return 'published'
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

class JsonInterface:

    def __init__( self, db, session_id ):

        self.__cache = cache.get_default_cache()
        self.__db = db
        self.__session_id = session_id

    def __fetch_info( self, items, target, album = None, stream = None ):

        if( target is None ):
            return { 'type' : 'invalid' }

        if( isinstance( target, int ) ):
            target = self.__db.get_object_by_id( target )

        if( album is not None and isinstance( album, int ) ):
            album = self.__db.get_object_by_id( album )

        info = {}
        target.check_metadata()
        if( stream is not None ):
            stream.check_metadata()
        else:
            #if( isinstance( target, hdbfs.File ) ):
            #    stream = target.get_root_stream( album )
            pass

        info['object_id'] = target.get_id()

        if( stream is not None ):
            info['stream_id'] = stream.get_stream_id()

        if( album is not None ):
            info['album'] = make_obj_tuple( album )

        if( 'type' in items ):
            info['type'] = get_type_str( target )
        if( 'text' in items ):
            info['text'] = target.get_text()
        if( 'repr' in items ):
            info['repr'] = target.get_repr( album )
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
        if( isinstance( target, hdbfs.File ) and 'duplicates' in items ):
            dups = target.get_duplicates()
            info['duplicates'] = map( make_obj_tuple, dups )
        if( isinstance( target, hdbfs.File ) and 'original_file' in items ):
            orig = target.get_original_file()
            info['original_file'] = make_obj_tuple( orig ) if( orig is not None ) else None
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

        if( isinstance( target, hdbfs.File )
        and ('width' in items
          or 'height' in items
          or 'sizes' in items) ):

            w = None
            h = None

            if( stream is not None ):
                if( isinstance( stream, hdbfs.ImageStream ) ):
                    try:
                        w, h = stream.get_dimensions()
                    except:
                        pass
            elif( isinstance( target, hdbfs.ImageFile ) ):
                try:
                    w, h = target.get_dimensions()
                except:
                    pass
            
            info['width'] = w
            info['height'] = h

            if( 'sizes' in items and w is not None ):
                maxdim = w if( w > h ) else h
                sizes = [ 1 << hdbfs.imgdb.MIN_THUMB_EXP ]
                exps = [ hdbfs.imgdb.MIN_THUMB_EXP ]

                while( sizes[-1] < maxdim ):
                    sizes.append( sizes[-1] * 2 )
                    exps.append( exps[-1] + 1 )

                sizes[-1] = maxdim

                if( w > h ):
                    sizes = map( lambda x, e: ( e, x, x * h / w ), sizes, exps )
                else:
                    sizes = map( lambda y, e: ( e, y * w / h, y ), sizes, exps )

                info['sizes'] = sizes

            elif( 'sizes' in items ):
                info['sizes'] = []

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

    def close( self ):

        pass

    def execute( self, data ):

        if( self.__db is None or self.__session_id is None ):
            return json_err( 'nosession' )

        try:
            with self.__db.transaction():
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
            return self.__fetch_info( items, target )

        targets = map( db.get_object_by_id, targets )
        results = map( fetch_info_fn, targets )

        return json_ok( info = results )

    def cmd_stream_info( self, target, stream, items ):

        db = self.__db
        target = db.get_object_by_id( target )
        if( stream is not None ):
            stream = db.get_stream_by_id( stream )

        results = self.__fetch_info( items, target, stream = stream )
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

    def __exec_search( self, data ):

        db = self.__db

        if( data.has_key( 'mode' ) ):
            # Search by directive
            if( data['mode'] == 'all' ):
                return hdbfs.query.Query().execute( db ), {}
            elif( data['mode'] == 'untagged' ):
                return hdbfs.query.Query().set_untagged().execute( db ), {}
            elif( data['mode'] == 'album' ):
                album = db.get_object_by_id( data['album'] )
                return map( lambda x: x.get_id(), album.get_files() ), \
                       { 'album' : data['album'] }

        else:
            if( data.has_key( 'query' ) ):
                #try:
                if( 1 ):
                    query = hdbfs.query.Query().from_string( data['query'] )
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
                    return json_err( e ), {}

            return query.execute( db ), {}

    def cmd_search( self, data ):

        rs, ctx = self.__exec_search( data )

        # Register the result set
        sel = self.__cache.register_selection(
                        self.__session_id, rs, ctx )
        selid = sel.get_id()
        results = len( sel )

        # Any results?
        if( results == 0 ):
            self.__cache.close_selection(
                    self.__session_id, selid )
            return json_ok( results = 0 )

        idx = data['index'] if( 'index' in data ) else 0
        count = data['count'] if( 'count' in data ) else None
        info = data['info'] if( 'info' in data ) else None

        if( idx < 0 or idx >= results ):
            idx = 0

        if( count is not None and (idx + count) > results ):
            count = results - idx

        result = {
            'selection' : selid,
            'results' : results,
            'index' : idx,
        }

        if( count is None ):
            if( info is not None ):
                target = self.__db.get_object_by_id( sel[idx] )
                result['first'] = self.__fetch_info( info, target, **ctx )
            else:
                result['first'] = sel[idx]
        else:
            if( info is not None ):
                def fetch_info_fn( target ):
                    return self.__fetch_info( items, target, **ctx )

                targets = map( self.__db.get_object_by_id, sel[idx:idx+count] )
                result['items'] = map( fetch_info_fn, targets )
            else:
                result['items'] = sel[idx:idx+count]

        return json_ok( **result )

    def cmd_bulk( self, data ):

        rs, ctx = self.__exec_search( data )
        count = 0

        if( 'exec' not in data ):
            return json_err( 'argument', 'Expected an execution' )

        try:
            action, operand = map( lambda x: x.strip(), data['exec'].split( ':', 1 ) )
        except:
            return json_err( 'argument', 'Bad execution format' )

        if( action == 'name' ):
            import re

            parts = map( lambda x: x.replace( '\0', '/' ),
                         operand.replace( '\\/', '\0' ).split( '/' ) )

            items = []

            if( parts[0] == 's' and len( parts ) >= 3 ):
                op, pattern, repl = parts

                for r in rs:
                    name = r.get_name()
                    if( name is None ):
                        continue

                    subd = re.sub( pattern, repl, name )

                    if( subd != name ):
                        count += 1
                        if( 'commit' in data and data['commit'] ):
                            r.set_name( subd )

                        items.append( ( r.get_id(), name + ' -> ' + subd ) )

            elif( parts[0] == 'del' ):
                for r in rs:
                    name = r.get_name()
                    if( name is None ):
                        continue

                    if( name is not None ):
                        process = (len( parts ) == 1 or re.match( parts[1], name ))
                    else:
                        process = False

                    if( process ):
                        count += 1
                        if( 'commit' in data and data['commit'] ):
                            r.set_name( None )

                        items.append( ( r.get_id(), name + ' -> [none]' ) )

            elif( parts[0] == 'select' or parts[0] == 'select!' ):
                for r in rs:
                    if( r.get_type() != hdbfs.TYPE_FILE ):
                        continue

                    name = r.get_name()
                    if( name is not None and parts[0] != 'select!' ):
                        continue

                    new_name = None
                    for n in r.get_origin_names():
                        if( len( parts ) == 1 or re.match( parts[1], n ) ):
                            new_name = n
                            break

                    if( new_name is not None and new_name != name ):
                        count += 1
                        if( 'commit' in data and data['commit'] ):
                            r.set_name( new_name )

                        if( name is not None ):
                            items.append( ( r.get_id(), name + ' -> ' + new_name ) )
                        else:
                            items.append( ( r.get_id(), '[none] -> ' + new_name ) )
            else:
                return json_err( 'argument', 'Invalid string operation' )

            return json_ok( affected = count, changes = items )
        else:
            return json_err( 'argument', 'Unsupported execution action' )

    def cmd_selection_fetch( self, selection, index, info = None ):

        sel_id = selection
        idx = index

        sel = self.__cache.fetch_selection( self.__session_id, sel_id )
        try:
            obj_id = sel[idx]
        except IndexError:
            return json_err( 'index', 'Invalid index' )

        if( info is not None ):
            target = self.__db.get_object_by_id( obj_id )
            return json_ok( **self.__fetch_info( info, target, **sel.state ) )
        else:
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

    def cmd_link_files( self, original, variant, is_duplicate = False ):

        db = self.__db

        original = db.get_object_by_id( original )
        variant = db.get_object_by_id( variant )

        variant.assign( original, is_duplicate = is_duplicate )

        return json_ok()

    def cmd_unlink_files( self, original, variant ):

        db = self.__db

        original = db.get_object_by_id( original )
        variant = db.get_object_by_id( variant )

        variant.unassign( original )

        return json_ok()

    def cmd_clear_variant( self, original, variant ):

        db = self.__db

        original = db.get_object_by_id( original )
        variant = db.get_object_by_id( variant )

        variant.clear_variant_of( original )

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
