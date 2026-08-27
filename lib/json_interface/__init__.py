import datetime
import inspect
import sys

import hdbfs

import hdbfs.objects.groups
import json_interface.cache as cache

from typing import List, Optional, Dict, Any, Tuple, Union

# Type alias for JSON response dictionaries
JsonResponse = Dict[str, Any]

VERSION = 0
REVISION = 0

def get_type_str( obj: hdbfs.Obj ) -> str:
    """ Get the type string representation for an object.

    Args:
        obj: The object to get the type string for

    Returns:
        A string like 'file:original', 'album:free', 'tag:unordered', etc.
    """

    TYPE_MAP = {
        hdbfs.ObjectType.FILE                  : 'file:original',
        hdbfs.ObjectType.DUPLICATE             : 'file:duplicate',
        hdbfs.ObjectType.ALBUM_FREE            : 'album:free',
        hdbfs.ObjectType.ALBUM_FORMAL          : 'album:formal',
        hdbfs.ObjectType.ALBUM_CLOSED          : 'album:closed',
        hdbfs.ObjectType.IMPORT_OPEN           : 'import:open',
        hdbfs.ObjectType.IMPORT_CLOSED         : 'import:closed',
        hdbfs.ObjectType.CLASSIFIER_UNORDERED  : 'tag:unordered',
        hdbfs.ObjectType.CLASSIFIER_ORDERED    : 'tag:ordered',
        hdbfs.ObjectType.CLASSIFIER_NAME_ORDER : 'tag:nameorder',
        hdbfs.ObjectType.CLASSIFIER_DATE_ORDER : 'tag:dateorder',
    }

    return TYPE_MAP.get( obj.get_type(), 'unknown' )

def make_obj_tuple( obj: hdbfs.Obj ) -> List[Union[int, str]]:
    """ Create a [id, repr, type] tuple for an object.

    Args:
        obj: The object to create a tuple for

    Returns:
        A list containing [object_id, repr_string, type_string]
    """

    return [
        obj.get_id(),
        obj.get_repr(),
        get_type_str( obj ),
    ]

def json_ok( **args ) -> JsonResponse:
    """ Create a successful JSON response.

    Args:
        **args: Additional fields to include in the response

    Returns:
        JSON response dictionary

    Example:
        {'result': 'ok', 'data': 'value', 'count': 42}
    """

    args['result'] = 'ok'
    return args

def json_err( err: Union[str, Exception], emsg: Optional[str] = None ) -> JsonResponse:
    """ Create an error JSON response.

    Args:
        err: Either an exception object or error type string
        emsg: Optional error message (auto-generated if not provided)

    Returns:
        JSON response dictionary

    Example:
        {'result': 'err', 'except': 'value', 'msg': 'Invalid input'}
    """

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
    """ JSON RPC interface for database operations.

    Provides a command-based API for interacting with the higurashi database
    via JSON requests. Handles object queries, modifications, tagging, albums,
    and bulk operations.
    """

    def __init__( self, db: hdbfs.Database, session_id: str ):
        """ Initialize the JSON interface.

        Args:
            db: Database instance to operate on
            session_id: Session identifier for this interface
        """

        self.__cache = cache.get_default_cache()
        self.__db = db
        self.__session_id = session_id

    def __fetch_info( self,
                items: List[str],
                target: Union[int, hdbfs.Obj],
                parent: Optional[Union[int, hdbfs.Obj]] = None,
                stream: Optional[hdbfs.Stream] = None
            ) -> JsonResponse:
        """ Fetch information about an object.

        Internal method that retrieves various metadata fields based on
        the requested items list.

        Args:
            items: List of field names to fetch
            target: Object ID or object to fetch info for
            parent: Optional parent object or ID
            stream: Optional stream to fetch info for

        Returns:
            Dictionary containing requested information fields
        """

        if( target is None ):
            return { 'type' : 'invalid' }

        if( isinstance( target, int ) ):
            target = self.__db.get_object_by_id( target )

        if( parent is not None and isinstance( parent, int ) ):
            parent = self.__db.get_object_by_id( parent )

        info = {}

        if( isinstance( target, hdbfs.ImageFile )
           or isinstance( target, hdbfs.Album ) ):

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

        if( parent is not None ):
            info['parent'] = make_obj_tuple( parent )

        if( 'type' in items ):
            info['type'] = get_type_str( target )
        if( 'repr' in items ):
            info['repr'] = target.get_repr( parent )
        if( 'tags' in items ):
            info['tags'] = [
                    ( t.get_name(), t.get_id() )
                    for t in target.get_tags()
                ]
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
                # TODO: Consider catching specific exceptions and logging
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
                            # TODO: Consider catching specific exceptions and logging
                            pass
                elif( isinstance( target, hdbfs.ImageFile ) ):
                    try:
                        w, h = target.get_dimensions()
                    except:
                        # TODO: Consider catching specific exceptions and logging
                        pass

                info['width'] = w
                info['height'] = h

                if( 'sizes' in items ):
                    info['sizes'] = target.get_thumb_sizes()

            if( 'exif' in items ):
                info['exif'] = target.get_exif()

        if( isinstance( target, hdbfs.File ) ):
            if( 'imports' in items ):
                imports = target.get_imports()
                info['imports'] = list( map( make_obj_tuple, imports ) )

        if( 'text' in items ):
            info['text'] = target.get_text()

        if( isinstance( target, hdbfs.File ) or isinstance( target, hdbfs.Album ) ):
            if( 'albums' in items ):
                albums = target.get_member_of()
                info['albums'] = list( map( make_obj_tuple, albums ) )

        if( isinstance( target, hdbfs.Album )
         or isinstance( target, hdbfs.Import )
         or isinstance( target, hdbfs.Tag ) ):
            if( 'short_files' in items ):
                files = target.get_items( limit = 10 )
                info['files'] = list( map( make_obj_tuple, files ) )
            if( 'files' in items ):
                files = target.get_items()
                info['files'] = list( map( make_obj_tuple, files ) )

        if( isinstance( target, hdbfs.File ) or isinstance( target, hdbfs.Album ) ):
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
                creation_ts = stream.get_add_time()
            else:
                creation_ts = target.get_add_time()
            if( creation_ts is not None ):
                info['creation_time'] = creation_ts.strftime( '%Y/%m/%d %H:%M:%S' )
            else:
                info['creation_time'] = None

        return info

    def __fetch_fields( self, fields: List[str], target: hdbfs.Obj ) -> Dict[str, Any]:
        """ Fetch custom metadata fields from an object.

        Args:
            fields: List of field names to fetch
            target: Object to fetch fields from

        Returns:
            Dictionary mapping field names to their values (None if not present)
        """

        def read_field( target: hdbfs.Obj, field: str ) -> Any:

            try:
                return target[field]
            except KeyError:
                return None

        return {
            f : read_field( target, f )
            for f in fields
        }

    def close( self ) -> None:
        """ Close the interface and release resources. """

        pass

    def execute( self, data: Dict[str, Any] ) -> JsonResponse:
        """ Execute a JSON command.

        Dispatches to cmd_* methods based on the 'action' field in data.
        Supports three calling conventions:
        1. Old style: cmd_method(data) - takes full data dict
        2. Strict: cmd_method(arg1, arg2) - explicit parameters
        3. Flexible: cmd_method(**kwargs) - accepts keyword arguments

        Args:
            data: Dictionary containing 'action' field and command parameters

        Returns:
            JSON response dictionary
        """

        if( self.__db is None or self.__session_id is None ):
            return json_err( 'nosession' )

        # TODO: Re-enable proper exception handling instead of letting exceptions
        # propagate to CherryPy. The finally: pass is present to disable the
        # commented exception handler below.
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
                        if arg not in data:
                            return json_err( 'value', f'{arg} not provided for {data["action"]}' )
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
                        if arg not in data:
                            return json_err( 'value', f'Missing arg {arg}' )
                    return fn( **data )
        finally:
            pass
        #except:
        #    return {
        #        'result' : 'error',
        #        'errmsg' : sys.exc_info()[0],
        #    }

    def cmd_version( self ) -> JsonResponse:
        """ Get version information.

        Returns:
            JSON response dictionary

        Example:
            {
                'result': 'ok',
                'json_ver': [0, 0],
                'higu_ver': [16, 0],
                'db_ver': [16, 0]
            }
        """

        return json_ok(
            json_ver = [ VERSION, REVISION ],
            higu_ver = [ hdbfs.VERSION, hdbfs.REVISION ],
            db_ver   = [ hdbfs.DB_VERSION, hdbfs.DB_REVISION ] )

    def cmd_info( self,
                target: Optional[int] = None,
                targets: Optional[List[int]] = None,
                items: Optional[List[str]] = None,
                fields: Optional[List[str]] = None
            ) -> JsonResponse:
        """ Get information about one or more objects.

        Args:
            target: Single object ID to fetch info for
            targets: List of object IDs to fetch info for
            items: List of info items to fetch
            fields: List of custom fields to fetch

        Returns:
            JSON response dictionary

        Example:
            {
                'result': 'ok',
                'info': {'object_id': 123, 'type': 'file:original', 'repr': 'image.jpg'},
                'fields': {'custom_field': 'value'}
            }
        """

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

    def cmd_stream_info( self,
                target: int,
                stream: Optional[int],
                items: List[str]
            ) -> JsonResponse:
        """ Get information about a stream.

        Args:
            target: Object ID
            stream: Stream ID (None for root stream)
            items: List of info items to fetch

        Returns:
            JSON response dictionary

        Example:
            {
                'result': 'ok',
                'info': {'object_id': 123, 'stream_id': 456, 'width': 1920, 'height': 1080}
            }
        """

        db = self.__db
        target = db.get_object_by_id( target )
        if( stream is not None ):
            stream = db.get_stream_by_id( stream )

        results = self.__fetch_info( items, target, stream = stream )
        return json_ok( info = results )

    def cmd_set_field( self, target: int, field: str, value: Any ) -> JsonResponse:
        """ Set a custom metadata field on an object.

        Args:
            target: Object ID
            field: Field name
            value: Field value

        Returns:
            JSON response dictionary
        """

        target = self.__db.get_object_by_id( target )
        target[field] = value

        return json_ok()

    def cmd_tag( self, targets: List[int], **args ) -> JsonResponse:
        """ Add or remove tags from objects.

        Args:
            targets: List of object IDs to tag
            **args: Can contain 'query' (tag string) or 'add_tags', 'sub_tags', 'new_tags'

        Returns:
            JSON response dictionary
        """

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

    def cmd_rename( self, target: int, name: str, saveold: bool = False ) -> JsonResponse:
        """ Rename an object.

        Args:
            target: Object ID
            name: New name
            saveold: Whether to save old name (currently unused)

        Returns:
            JSON response dictionary
        """

        db = self.__db

        target = db.get_object_by_id( target )
        target.set_name( name )

        return json_ok()

    def cmd_group_deorder( self, group: int ) -> JsonResponse:
        """ Remove explicit ordering from an ordered group.

        Args:
            group: Group object ID

        Returns:
            JSON response dictionary
        """

        db = self.__db

        group = db.get_object_by_id( group )
        assert( isinstance( group, hdbfs.objects.groups.OrderedGroup ) )

        group.clear_order()

        return json_ok()

    def cmd_group_reorder( self, group: int, items: List[int] ) -> JsonResponse:
        """ Set explicit order for items in an ordered group.

        Args:
            group: Group object ID
            items: List of object IDs in desired order

        Returns:
            JSON response dictionary
        """

        db = self.__db

        group = db.get_object_by_id( group )
        assert( isinstance( group, hdbfs.objects.groups.OrderedGroup ) )

        items = list( map( db.get_object_by_id, items ) )
        group.set_order( items )

        return json_ok()

    def cmd_album_partition( self, album: int, items: List[int] ) -> JsonResponse:
        """ Partition files from an album into a new album.

        Args:
            album: Album object ID
            items: List of file IDs to partition out

        Returns:
            JSON response dictionary
        """

        db = self.__db

        album = db.get_object_by_id( album )
        assert( isinstance( album, hdbfs.Album ) )

        items = list( map( db.get_object_by_id, items ) )
        db.albums.partition( album, items )

        return json_ok()

    def cmd_taglist( self ) -> JsonResponse:
        """ Get a list of all tags with usage counts.

        Returns:
            JSON response dictionary

        Example:
            {
                'result': 'ok',
                'tags': [['vacation', 123, 45], ['family', 124, 32]]
            }
        """

        db = self.__db

        tags = [
            ( k, v[0].get_id(), v[1] )
            for k, v in db.all_tags().items()
        ]

        return json_ok( tags = tags )

    def __exec_search( self, data: Dict[str, Any] ) -> Tuple[Any, Dict]:
        """ Execute a search query.

        Internal method that handles various search modes and returns
        results along with context information.

        Args:
            data: Search parameters

        Returns:
            Tuple of (result_iterator, context_dict)
        """

        db = self.__db

        if( 'mode' in data ):
            # Search by directive
            if( data['mode'] == 'all' ):
                return hdbfs.query.Query().execute( db ), {}
            elif( data['mode'] == 'untagged' ):
                return hdbfs.query.Query().set_untagged().execute( db ), {}
            elif( data['mode'] == 'object_items' ):
                obj = db.get_object_by_id( data['object'] )
                items = []
                if( isinstance( obj, hdbfs.Album )
                 or isinstance( obj, hdbfs.Import )
                 or isinstance( obj, hdbfs.Tag ) ):
                    items = list( map( lambda x: x.get_id(), obj.get_items() ) )
                return items, { 'parent' : data['object'] }

        else:
            if( 'query' in data ):
                query = hdbfs.query.Query().from_string( data['query'] )
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

                req = list( map( higu.query.create_constraint, req ) )
                add = list( map( higu.query.create_constraint, add ) )
                sub = list( map( higu.query.create_constraint, sub ) )

            return query.execute( db ), {}

    def cmd_search( self, data: Dict[str, Any] ) -> JsonResponse:
        """ Execute a search and return results.

        Args:
            data: Search parameters including query, index, count, info, fields, etc.

        Returns:
            JSON response dictionary

        Example:
            {
                'result': 'ok',
                'results': 150,
                'index': 0,
                'selection': 'abc123',
                'items': [...]
            }
        """

        try:
            rs, ctx = self.__exec_search( data )
        except ( KeyError, ValueError, ) as e:
            return json_err( e )

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

    def cmd_bulk( self, data: Dict[str, Any] ) -> JsonResponse:
        """ Execute a bulk operation on search results.

        Args:
            data: Contains search parameters and 'exec' string for bulk operation

        Returns:
            JSON response dictionary

        Example:
            {
                'result': 'ok',
                'affected': 42,
                'changes': [[123, 'Tagged'], [124, 'Tagged'], ...]
            }
        """

        try:
            rs, ctx = self.__exec_search( data )
        except ( KeyError, ValueError, ) as e:
            return json_err( e )

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

    def cmd_selection_fetch( self,
                selection: str,
                index: int,
                info: Optional[List[str]] = None,
                fields: Optional[List[str]] = None
            ) -> JsonResponse:
        """ Fetch an item from a saved selection.

        Args:
            selection: Selection ID
            index: Index of item to fetch
            info: Optional list of info items to fetch
            fields: Optional list of fields to fetch

        Returns:
            JSON response dictionary

        Example:
            {
                'result': 'ok',
                'object_id': 123,
                'info': {...},
                'fields': {...}
            }
        """

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

    def cmd_selection_close( self, selection: str ) -> JsonResponse:
        """ Close a saved selection.

        Args:
            selection: Selection ID to close

        Returns:
            JSON response dictionary
        """

        if( not isinstance( selection, str ) ):
            return json_err( 'argument', 'selection is not a valid selection id' )

        try:
            self.__cache.close_selection( self.__session_id, selection )
        except KeyError:
            pass

        return json_ok()

    def cmd_obj_delete( self, target: int ) -> JsonResponse:
        """ Delete an object from the database.

        Args:
            target: Object ID to delete

        Returns:
            JSON response dictionary
        """

        db = self.__db

        obj = db.get_object_by_id( target )
        assert(
                isinstance( obj, hdbfs.File )
            or isinstance( obj, hdbfs.Album )
            )

        db.delete_object( obj )

        return json_ok()

    def cmd_group_create( self,
                targets: Optional[List[int]] = None,
                from_import: Optional[int] = None
            ) -> JsonResponse:
        """ Create a new album group.

        Args:
            targets: List of object IDs to add to new album
            from_import: Import ID to create album from

        Returns:
            JSON response dictionary

        Example:
            {
                'result': 'ok',
                'group': [456, 'New Album', 'album:free']
            }
        """

        db = self.__db

        if( targets is not None ):
            targets = list( map( db.get_object_by_id, targets ) )

            group = db.create_album()
            assert( isinstance( group, hdbfs.Album ) )

            for target in targets:
                target.assign( group )

            return json_ok( group = make_obj_tuple( group ) )

        elif( from_import is not None ):
            imp = db.get_object_by_id( from_import )
            assert( isinstance( imp, hdbfs.Import ) )

            group = db.create_album( from_import = imp )
            assert( isinstance( group, hdbfs.Album ) )

            return json_ok( group = group.get_id() )

        else:
            return json_err( 'argument', 'must specify targets or from_import' )

    def cmd_group_append( self, group: int, targets: List[int] ) -> JsonResponse:
        """ Add items to an album.

        Args:
            group: Album object ID
            targets: List of object IDs to add

        Returns:
            JSON response dictionary
        """

        db = self.__db

        group = db.get_object_by_id( group )
        assert( isinstance( group, hdbfs.Album ) )

        for target in map( db.get_object_by_id, targets ):
            assert( isinstance( target, hdbfs.File )
                 or isinstance( target, hdbfs.Album ) )
            target.assign( group )

        return json_ok()

    def cmd_group_remove( self, group: int, targets: List[int] ) -> JsonResponse:
        """ Remove items from an album.

        Args:
            group: Album object ID
            targets: List of object IDs to remove

        Returns:
            JSON response dictionary
        """

        db = self.__db

        group = db.get_object_by_id( group )
        assert( isinstance( group, hdbfs.Album ) )

        for target in map( db.get_object_by_id, targets ):
            target.unassign( group )

        return json_ok()

    def cmd_gather_tags( self, target: int ) -> JsonResponse:
        """ Gather tags from album contents to the album itself.

        Args:
            target: Album object ID

        Returns:
            JSON response dictionary
        """

        db = self.__db

        obj = db.get_object_by_id( target )

        assert isinstance( obj, hdbfs.Album )
        obj.gather_tags()

        return json_ok()

    def cmd_tag_delete( self, tag: str ) -> JsonResponse:
        """ Delete a tag.

        Args:
            tag: Tag name or pattern to delete

        Returns:
            JSON response dictionary
        """

        db = self.__db

        db.delete_tag( tag )
        return json_ok()

    def cmd_tag_move( self, tag: str, target: str ) -> JsonResponse:
        """ Move/rename a tag.

        Args:
            tag: Current tag name
            target: New tag name

        Returns:
            JSON response dictionary
        """

        db = self.__db

        db.move_tag( tag, target )
        return json_ok()

    def cmd_tag_copy( self, tag: str, target: str ) -> JsonResponse:
        """ Copy a tag to a new name.

        Args:
            tag: Source tag name
            target: Destination tag name

        Returns:
            JSON response dictionary
        """

        db = self.__db

        db.copy_tag( tag, target )
        return json_ok()

    def cmd_link_files( self,
                original: int,
                variant: int,
                is_duplicate: bool = False
            ) -> JsonResponse:
        """ Link files as variants or duplicates.

        Args:
            original: Original file object ID
            variant: Variant file object ID
            is_duplicate: Whether to mark as duplicate

        Returns:
            JSON response dictionary
        """

        db = self.__db

        original = db.get_object_by_id( original )
        variant = db.get_object_by_id( variant )

        variant.assign( original, is_duplicate = is_duplicate )

        return json_ok()

    def cmd_unlink_files( self, original: int, variant: int ) -> JsonResponse:
        """ Unlink files.

        Args:
            original: Original file object ID
            variant: Variant file object ID

        Returns:
            JSON response dictionary
        """

        db = self.__db

        original = db.get_object_by_id( original )
        variant = db.get_object_by_id( variant )

        variant.unassign( original )

        return json_ok()

    def cmd_clear_variant( self, original: int, variant: int ) -> JsonResponse:
        """ Clear variant relationship between files.

        Args:
            original: Original file object ID
            variant: Variant file object ID

        Returns:
            JSON response dictionary
        """

        db = self.__db

        original = db.get_object_by_id( original )
        variant = db.get_object_by_id( variant )

        variant.clear_variant_of( original )

        return json_ok()

    def cmd_change_album( self, target: int, subtype: str ) -> JsonResponse:
        """ Change album type (free/formal/closed).

        Args:
            target: Album object ID
            subtype: New subtype ('free', 'formal', or 'closed')

        Returns:
            JSON response dictionary
        """

        db = self.__db

        target = db.get_object_by_id( target )
        assert isinstance( target, hdbfs.Album )

        if( subtype == 'free' ):
            target.make_free_album()
        elif( subtype == 'formal' ):
            if( target.get_type() == hdbfs.ObjectType.ALBUM_CLOSED ):
                target.open_album()
            else:
                target.make_formal_album()
        elif( subtype == 'closed' ):
            target.close_album()
        else:
            assert False

        return json_ok()

    def cmd_change_tag( self, target: int, subtype: str ) -> JsonResponse:
        """ Change tag ordering mode.

        Args:
            target: Tag object ID
            subtype: New ordering ('unordered', 'ordered', 'nameorder', 'dateorder')

        Returns:
            JSON response dictionary
        """

        db = self.__db

        target = db.get_object_by_id( target )
        assert isinstance( target, hdbfs.Tag )

        target.set_ordering( {
                'unordered' : hdbfs.Tag.Order.UNORDERED,
                'ordered'   : hdbfs.Tag.Order.EXPLICIT,
                'nameorder' : hdbfs.Tag.Order.NAME,
                'dateorder' : hdbfs.Tag.Order.DATE,
            }[subtype] )

        return json_ok()

    def cmd_set_root_stream( self, target: int, stream: int ) -> JsonResponse:
        """ Set the root stream for a file.

        Args:
            target: File object ID
            stream: Stream ID to set as root

        Returns:
            JSON response dictionary
        """

        db = self.__db

        target = db.get_object_by_id( target )
        stream = db.get_stream_by_id( stream )

        target.set_root_stream( stream )

        return json_ok()

    def cmd_auto_orientation( self, target: int ) -> JsonResponse:
        """ Apply auto-orientation based on EXIF data.

        Args:
            target: Image file object ID

        Returns:
            JSON response dictionary
        """

        db = self.__db

        target = db.get_object_by_id( target )
        target.auto_orientation()

        return json_ok()

    def cmd_rotate_cw( self, target: int ) -> JsonResponse:
        """ Rotate image clockwise.

        Args:
            target: Image file object ID

        Returns:
            JSON response dictionary
        """

        db = self.__db

        target = db.get_object_by_id( target )
        target.rotate_cw()

        return json_ok()

    def cmd_rotate_ccw( self, target: int ) -> JsonResponse:
        """ Rotate image counter-clockwise.

        Args:
            target: Image file object ID

        Returns:
            JSON response dictionary
        """

        db = self.__db

        target = db.get_object_by_id( target )
        target.rotate_ccw()

        return json_ok()

    def cmd_mirror( self, target: int ) -> JsonResponse:
        """ Mirror image horizontally.

        Args:
            target: Image file object ID

        Returns:
            JSON response dictionary
        """

        db = self.__db

        target = db.get_object_by_id( target )
        target.mirror()

        return json_ok()

init = hdbfs.init
