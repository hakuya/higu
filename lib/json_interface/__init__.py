import inspect
import sys

import hdbfs

import cache

VERSION = 0
REVISION = 0

def get_type_str( obj ):

    type = obj.get_type()
    if( type == hdbfs.TYPE_FILE
     or type == hdbfs.TYPE_FILE_DUP
     or type == hdbfs.TYPE_FILE_VAR ):
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
                    assert data.has_key( arg )
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

        targets = map( db.get_object_by_id, targets )

        def fetch_info( target ):

            if( target is None ):
                return { 'type' : 'invalid' }

            info = {}

            if( 'type' in items ):
                info['type'] = get_type_str( target )
            if( 'text' in items ):
                info['text'] = target.get_text()
            if( 'repr' in items ):
                info['repr'] = target.get_repr()
            if( isinstance( target, hdbfs.File ) and 'mime' in items ):
                info['mime'] = target.get_mime()
            if( 'tags' in items ):
                tags = target.get_tags()
                info['tags'] = map( lambda x: x.get_name(), tags )
            if( 'names' in items ):
                info['names'] = target.get_names()
            if( isinstance( target, hdbfs.File ) and 'duplication' in items ):
                if( target.is_duplicate() ):
                    info['duplication'] = 'duplicate'
                elif( target.is_variant() ):
                    info['duplication'] = 'variant'
                else:
                    info['duplication'] = 'original'
            if( isinstance( target, hdbfs.File ) and 'similar_to' in items ):
                similar = target.get_similar_to()
                if( similar is not None ):
                    info['similar_to'] = [ similar.get_id(), similar.get_repr() ]
            if( isinstance( target, hdbfs.File ) and 'duplicates' in items ):
                duplicates = target.get_duplicates()
                info['duplicates'] = map( make_obj_tuple, duplicates )
            if( isinstance( target, hdbfs.File ) and 'variants' in items ):
                variants = target.get_variants()
                info['variants'] = map( make_obj_tuple, variants )
            if( isinstance( target, hdbfs.File ) and 'albums' in items ):
                albums = target.get_albums()
                info['albums'] = map( make_obj_tuple, albums )
            if( isinstance( target, hdbfs.Album ) and 'files' in items ):
                files = target.get_files()
                info['files'] = map( make_obj_tuple, files )
            if( isinstance( target, hdbfs.File ) and 'thumb_gen' in items ):
                try:
                    info['thumb_gen'] = target['thumb-gen']
                except:
                    info['thumb_gen'] = 0
            if( isinstance( target, hdbfs.File ) and 'width' in items ):
                try:
                    info['width'] = target['width']
                except:
                    info['width'] = 0
            if( isinstance( target, hdbfs.File ) and 'height' in items ):
                try:
                    info['height'] = target['height']
                except:
                    info['height'] = 0

            return info

        results = map( fetch_info, targets )

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
        target.set_name( name, saveold )

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
                # Search by query
                query = data['query']
                strict = False
                order = 'rand'
                rsort = False
                obj_type = None

                clauses = query.split( ' ' )
                clauses = [i for i in clauses if( len( i ) > 0 )]

                commands = [i[1:] for i in clauses if( i[0] == '$' )]
                add = [i[1:] for i in clauses if( i[0] == '?' )]
                sub = [i[1:] for i in clauses if( i[0] == '!' )]
                req = [i for i in clauses if( i[0] != '$' and i[0] != '?' and i[0] != '!' )]

                for cmd in commands:
                    if( cmd == 'strict' ):
                        strict = True
                    elif( cmd == 'sort:add' ):
                        order = 'add'
                    elif( cmd == 'sort:radd' ):
                        order = 'add'
                        rsort = True
                    elif( cmd == 'type:orig' ):
                        obj_type = hdbfs.TYPE_FILE;
                    elif( cmd == 'type:dup' ):
                        obj_type = hdbfs.TYPE_FILE_DUP;
                    elif( cmd == 'type:var' ):
                        obj_type = hdbfs.TYPE_FILE_VAR;
                    elif( cmd == 'type:album' ):
                        obj_type = hdbfs.TYPE_ALBUM;
                    else:
                        raise ValueError, 'Bad Command'

            else:
                # Search by parts
                if( data.has_key( 'strict' ) and data['strict'] ):
                    strict = True
                else:
                    strict = False

                if( data.has_key( 'sort' ) and not data['randomize'] ):
                    order = data['sort']

                if( data.has_key( 'rsort' ) and data['rsort'] ):
                    rsort = True
                else:
                    rsort = False

                req = data['req'] if data.has_key( 'req' ) else []
                add = data['add'] if data.has_key( 'add' ) else []
                sub = data['sub'] if data.has_key( 'sub' ) else []

            def create_constraint( pstr ):

                ops = [ ( '>=', hdbfs.ParameterConstraint.Set_ge, ),
                        ( '<=', hdbfs.ParameterConstraint.Set_le, ),
                        ( '>', hdbfs.ParameterConstraint.Set_gt, ),
                        ( '<', hdbfs.ParameterConstraint.Set_lt, ),
                        ( '!=', hdbfs.ParameterConstraint.Set_ne, ),
                        ( '=', hdbfs.ParameterConstraint.Set_eq, ), ]
                int_ops = [ '>=', '<=', '>', '<' ]

                key = None
                op = None
                value = None

                for i in ops:
                    try:
                        idx = pstr.index( i[0] )
                        key = pstr[0:idx]
                        op = i
                        value = pstr[idx+len(i[0]):]
                        break
                    except:
                        pass

                if( key is None ):
                    return db.get_tag( pstr )

                if( len( key ) == 0 ):
                    raise ValueError, 'Bad Parameter Constraint'

                if( op[0] in int_ops ):
                    value = int( value )

                c = hdbfs.ParameterConstraint( key )
                i[1]( c, value )

                return c


            try:
                req = map( create_constraint, req )
                add = map( create_constraint, add )
                sub = map( create_constraint, sub )
            except ( KeyError, ValueError, ), e:
                return json_err( e )

            rs = db.lookup_objects( req, add, sub,
                    strict, type = obj_type,
                    order = order, rsort = rsort )

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

        elif( isinstance( obj, hdbfs.File ) ):
            files = obj.get_duplicates()

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

    def cmd_set_duplication( self, original,
                             duplicates = [], variants = [] ):

        db = self.__db

        original = db.get_object_by_id( original )
        
        dups = map( db.get_object_by_id, duplicates )
        for dup in dups:
            dup.set_duplicate_of( original )

        vars = map( db.get_object_by_id, variants )
        for var in vars:
            var.set_variant_of( original )

        return json_ok()

    def cmd_clear_duplication( self, targets ):

        db = self.__db

        targets = map( db.get_object_by_id, targets )

        for target in targets:
            target.clear_duplication()

        return json_ok()

    def cmd_rotate( self, target, rot ):

        db = self.__db

        target = db.get_object_by_id( target )
        target.rotate( rot )

        return json_ok()

init = hdbfs.init
