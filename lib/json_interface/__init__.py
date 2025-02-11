import datetime
import inspect
import sys

import hdbfs

import json_interface.cache as cache

from hdbfs import ImageRequestPriority

from typing import List, Optional

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

def make_obj_tuple( obj: hdbfs.Obj ):

    return [
        obj.get_id(),
        obj.get_repr(),
        get_type_str( obj ),
    ]

def json_ok( **args ) -> dict:

    args['result'] = 'ok'
    return args

def json_err( err: any, emsg: Optional[str] = None ) -> dict:

    if( isinstance( err, KeyError ) ):
        etype = 'key'
        emsg = str( err )
    elif( isinstance( err, ValueError ) ):
        etype = 'value'
        emsg = str( err )
    elif( isinstance( err, str ) ):
        etype = err
        if( emsg is None ):
            emsg = f'An {etype} error has occured'
    else:
        etype = 'unknown'
        emsg = f'An {etype!s} error has occured'

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

    def __init__( self, db: hdbfs.Database, session_id: str ):

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
            info['tags'] = list( map( lambda x: x.get_name(), tags ) )
        if( 'names' in items ):
            if( isinstance( target, hdbfs.File ) ):
                info['names'] = target.get_origin_names()
            else:
                name = target.get_name()
                if( name is not None ):
                    info['names'] = [ target.get_name(), ]
                else:
                    info['names'] = []

        if( isinstance( target, hdbfs.ImageFile ) and 'thumb_gen' in items ):
            try:
                info['thumb_gen'] = target.get_generation()
            except:
                info['thumb_gen'] = 0

        if( isinstance( target, hdbfs.File ) ):
            if( 'variants' in items ):
                variants = target.get_variants()
                info['variants'] = list( map( make_obj_tuple, variants ) )
            if( 'variants_of' in items ):
                variants_of = target.get_variants_of()
                info['variants_of'] = list( map( make_obj_tuple, variants_of ) )
            if( 'duplicates' in items ):
                dups = target.get_duplicates()
                info['duplicates'] = list( map( make_obj_tuple, dups ) )
            if( 'original_file' in items ):
                orig = target.get_original_file()
                info['original_file'] = make_obj_tuple( orig ) if( orig is not None ) else None

            if( 'width' in items or 'height' in items or 'sizes' in items ):

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

                if( 'sizes' in items ):
                    info['sizes'] = target.get_thumb_sizes()

            if( 'exif' in items ):
                info['exif'] = target.get_exif()

        if( isinstance( target, hdbfs.File ) or isinstance( target, hdbfs.Album ) ):
            if( 'albums' in items ):
                albums = target.get_member_of()
                info['albums'] = list( map( make_obj_tuple, albums ) )

        if( isinstance( target, hdbfs.Album ) ):
            if( 'short_files' in items ):
                files = target.get_items( limit = 10 )
                info['files'] = list( map( make_obj_tuple, files ) )
            if( 'files' in items ):
                files = target.get_items()
                info['files'] = list( map( make_obj_tuple, files ) )

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

    def __fetch_fields( self, fields, target ):

        def read_field( target, field ):

            try:
                return target[field]
            except KeyError:
                return None

        return {
            f : read_field( target, f )
            for f in fields
        }

    def close( self ):

        pass

    def execute( self, data ):

        if( self.__db is None or self.__session_id is None ):
            return json_err( 'nosession' )

        try:
            with self.__db.transaction():
                fn = getattr( self, 'cmd_' + data['action'] )
                argspec = inspect.getfullargspec( fn )
                if( 'data' in argspec.args ):
                    # Old style
                    return fn( data )
                elif( argspec.varkw is None ):
                    # Grab the required and optional
                    if( argspec.defaults is None ):
                        req_args = argspec.args[1:]
                        opt_args = []
                    else:
                        req_args = argspec.args[1:-len( argspec.defaults )]
                        opt_args = argspec.args[-len( argspec.defaults ):]

                    args = {}
                    for arg in req_args:
                        assert arg in data, f'{arg} not provided for {data["action"]}'
                        args[arg] = data[arg]
                    for arg in opt_args:
                        if( arg in data ):
                            args[arg] = data[arg]
                    return fn( **args )
                else:
                    # Just make sure required arguments are present
                    if( argspec.defaults is None ):
                        req_args = argspec.args[1:]
                    else:
                        req_args = argspec.args[1:-len( argspec.defaults )]

                    for arg in req_args:
                        assert arg in data, f'Missing arg {arg}'
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

    def cmd_info( self, target = None, targets = None, items = None, fields = None ):

        db = self.__db

        results = {}

        if( target is not None ):
            target = db.get_object_by_id( target )

            if( items is not None ):
                results['info'] = self.__fetch_info( items, target )

            if( fields is not None ):
                results['fields'] = self.__fetch_fields( fields, target )

        if( targets is not None ):
            targets = list( map( db.get_object_by_id, targets ) )

            if( items is not None ):
                results['info'] = list( map( lambda it: self.__fetch_info( items, it ), targets ) )

            if( fields is not None ):
                results['fields'] = list( map( lambda it: self.__fetch_fields( fields, it ), targets ) )

        return json_ok( **results )

    def cmd_stream_info( self, target, stream, items ):

        db = self.__db
        target = db.get_object_by_id( target )
        if( stream is not None ):
            stream = db.get_stream_by_id( stream )

        results = self.__fetch_info( items, target, stream = stream )
        return json_ok( info = results )

    def cmd_set_field( self, target, field, value ):

        target = self.__db.get_object_by_id( target )
        target[field] = value

        return json_ok()

    def cmd_tag( self, targets: List[int], **args ) -> dict:

        db = self.__db

        if( 'query' in args ):
            tags = [t for t in args['query'].split( ' ' ) if t != '']

            add = [t for t in tags if t[0] != '-' and t[0] != '!']
            new = [t[1:] for t in tags if t[0] == '!']
            sub = [t[1:] for t in tags if t[0] == '-']

        else:
            add = args['add_tags'] if( 'add_tags' in args ) else []
            sub = args['sub_tags'] if( 'sub_tags' in args ) else []
            new = args['new_tags'] if( 'new_tags' in args ) else []

        try:
            add = list( map( lambda n: db.get_tag( n, True ), add ) )
            sub = list( map( lambda n: db.get_tag( n, True ), sub ) )
            add += list( map( db.make_tag, new ) )
        except ( KeyError, ValueError, ) as e:
            return json_err( e )

        for obj in map( db.get_object_by_id, targets ):
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

        items = list( map( db.get_object_by_id, items ) )
        group.set_order( items )

        return json_ok()

    def cmd_taglist( self ):

        db = self.__db

        tags = db.all_tags()
        tags = list( map( lambda x: ( x, tags[x][1] ), tags ) )

        return json_ok( tags = tags )

    def __exec_search( self, data ):

        db = self.__db

        if( 'mode' in data ):
            # Search by directive
            if( data['mode'] == 'all' ):
                return hdbfs.query.Query().execute( db ), {}
            elif( data['mode'] == 'untagged' ):
                return hdbfs.query.Query().set_untagged().execute( db ), {}
            elif( data['mode'] == 'album' ):
                album = db.get_object_by_id( data['album'] )
                return list( map( lambda x: x.get_id(), album.get_items() ) ), \
                                    { 'album' : data['album'] }

        else:
            if( 'query' in data ):
                #try:
                if( 1 ):
                    query = hdbfs.query.Query().from_string( data['query'] )
                #except ( KeyError, ValueError, ), e:
                #    return json_err( e )

            else:
                query = hdbfs.query.Query()

                # Search by parts
                if( 'strict' in data and data['strict'] ):
                    query.set_strict()

                if( 'sort' in data and not data['randomize'] ):
                    if( 'rsort' in data and data['rsort'] ):
                        desc = True
                    else:
                        desc = False

                    query.add_sort( data['sort'], desc )


                req = data['req'] if 'req' in data else []
                add = data['add'] if 'add' in data else []
                sub = data['sub'] if 'sub' in data else []

                try:
                    req = list( map( higu.query.create_constraint, req ) )
                    add = list( map( higu.query.create_constraint, req ) )
                    sub = list( map( higu.query.create_constraint, req ) )
                except ( KeyError, ValueError, ) as e:
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

        oneshot = data['oneshot'] if( 'oneshot' in data ) else False
        idx = data['index'] if( 'index' in data ) else 0
        count = data['count'] if( 'count' in data ) else None
        info = data['info'] if( 'info' in data ) else None
        fields = data['fields'] if( 'fields' in data ) else None

        if( idx < 0 or idx >= results ):
            idx = 0

        if( count is not None and (idx + count) > results ):
            count = results - idx

        result = {
            'results' : results,
            'index' : idx,
        }

        if( count is None ):
            if( info is not None ):
                target = self.__db.get_object_by_id( sel[idx] )
                result['first'] = self.__fetch_info( info, target, **ctx )
            else:
                result['first'] = sel[idx]

            if( fields is not None ):
                result['fields'] = self.__fetch_fields( fields, target )
        else:
            if( info is not None ):
                targets = map( lambda i: self.__db.get_object_by_id( sel[i] ),
                               range( idx, idx + count ) )
                result['items'] = list( map( lambda it: self.__fetch_info( info, it, **ctx ), targets ) )
            else:
                result['items'] = list( map( sel[i], range( idx, idx + count ) ) )

            if( fields is not None ):
                result['fields'] = list( map( lambda it: self.__fetch_fields( fields, it ), targets ) )

        if( oneshot ):
            self.__cache.close_selection( self.__session_id, selid )
        else:
            result['selection'] = selid

        return json_ok( **result )

    def cmd_bulk( self, data ):

        rs, ctx = self.__exec_search( data )

        count = 0
        items = []

        if( 'exec' not in data ):
            return json_err( 'argument', 'Expected an execution' )

        try:
            bulk_op = hdbfs.bulk.op_from_string( self.__db, data['exec'] )
        except hdbfs.bulk.ParseError:
            return json_err( 'argument', 'Bad execution format' )
        except hdbfs.bulk.BadArgument:
            return json_err( 'argument', 'Bad operation argument' )

        bulk_op.set_commit( 'commit' in data and data['commit'] )

        items = [
            ( it.get_id() if it is not None else None, msg )
            for it, msg in bulk_op.execute( self.__db, list( rs ) )
        ]

        return json_ok( affected = len( items ), changes = items )

    def cmd_selection_fetch( self, selection, index, info = None, fields = None ):

        sel_id = selection
        idx = index

        sel = self.__cache.fetch_selection( self.__session_id, sel_id )
        if( sel is None ):
            return json_err( 'badsel' )

        try:
            obj_id = sel[idx]
        except IndexError:
            return json_err( 'index', 'Invalid index' )

        result = { 'object_id' : obj_id }
        target = self.__db.get_object_by_id( obj_id )

        if( info is not None ):
            result['info'] = self.__fetch_info( info, target, **sel.state )

        if( fields is not None ):
            result['fields'] = self.__fetch_fields( fields, target )

        return json_ok( **result )

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

        targets = list( map( db.get_object_by_id, targets ) )

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

        for target in map( db.get_object_by_id, targets ):
            assert( isinstance( target, hdbfs.File )
                 or isinstance( target, hdbfs.Album ) )
            target.assign( group )

        return json_ok()

    def cmd_group_remove( self, group, targets ):

        db = self.__db

        group = db.get_object_by_id( group )
        assert( isinstance( group, hdbfs.Album ) )

        for target in map( db.get_object_by_id, targets ):
            target.unassign( group )

        return json_ok()

    def cmd_gather_tags( self, target ):

        db = self.__db

        obj = db.get_object_by_id( target )

        if( isinstance( obj, hdbfs.Album ) ):
            files = obj.get_items()

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
            files = obj.get_items()

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
