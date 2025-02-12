import datetime
import os
import re
import sys
import time

from hdbfs.hash import calculate_details

import hdbfs.ark as ark
import hdbfs.imgdb as imgdb
import hdbfs.model as model
import hdbfs.query as query
import hdbfs.bulk as bulk

from hdbfs.imgdb.objects import ThumbRequestPrio

from hdbfs.basic_objs import *
from hdbfs.defs import *
from hdbfs.imgdb import ImageStream, ImageFile, Album
from hdbfs.hooks import *
from hdbfs.obj_factory import *

from hdbfs.model import ImageRequestPriority

from typing import Optional, NamedTuple, List

_LIBRARY = None

def check_tag_name( s ):

    if( re.match( r'^[\w\-_:]+$', s ) is None ):
        raise ValueError( f'"{s}" is not a valid tag name' )

class _AccessContext:

    def __init__( self, manager,
                  write = False,
                  transaction = False ):

        self.__manager = manager
        self.__write = write
        self.__transaction = transaction
        self.__active = False

    def __enter__( self ):

        self.__manager._begin_access( self )
        self.__active = True

        return self

    def __exit__( self, type, value, trace ):

        self.__active = False
        self.__manager._end_access( self, type is not None )

        if( type is not None ):
            raise type.with_traceback( value, trace )

    def is_transaction( self ):
        return self.__transaction

    def is_write( self ):
        return self.__write

    def commit( self ):
        self.__manager._commit( self )

    def rollback( self ):
        self.__manager._rollback( self )

class AccessManager:

    def __init__( self, db ):

        self.__db = db
        self.__write_permitted = False

        self.__accesses = []
        self.__locked = False
        self.__failed = False

    def _begin_access( self, dba ):

        assert not dba.is_write() or self.__write_permitted, 'Read-Only Access'

        if( dba.is_transaction() ):
            assert len( self.__accesses ) == 0

        self.__accesses.append( dba )

        if( dba.is_write() and not self.__locked ):
            self.__db._begin()
            self.__locked = True

    def _end_access( self, dba, is_except ):

        # Don't pop yet! we may be within the pre-commit hook!
        assert dba == self.__accesses[-1]

        if( len( self.__accesses ) == 1 ):
            if( self.__locked ):
                committed = False

                if( not is_except ):
                    try:
                        self.__db._commit()
                        committed = True

                    except:
                        pass

                if( not committed ):
                    self.__db._rollback()

            self.__locked = False

        assert dba == self.__accesses.pop()

    def _commit( self, dba ):

        assert self.__locked, 'Can only commit with write access'
        assert self.__accesses[0] == dba, 'Only transaction may commit'

        self.__db._commit()
        if( self.__locked ):
            self.__db._begin()

    def _rollback( self, dba ):

        assert self.__locked, 'Can only rollback with write access'
        assert self.__accesses[0] == dba, 'Only transaction may rollback'

        self.__db._rollback()
        if( self.__locked ):
            self.__db._begin()

    def enable_writes( self ):

        self.__write_permitted = True

    def __call__( self, **kwargs ):

        return _AccessContext( self, **kwargs )

class ThumbRequest( NamedTuple ):
    prio: ImageRequestPriority
    exps: Optional[ List[int] ]
    file: ImageFile

class Database:

    def __init__( self ):
        global _LIBRARY

        self.session = model.Session()

        imgdat_config = imgdb.ImageDbDataConfig( _LIBRARY )
        self.imgdb = ark.StreamDatabase( imgdat_config )
        self.tbcache = imgdb.ThumbCache( self, self.imgdb )

        self._access = AccessManager( self )
        self._trans_write = False

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
        self.session.execute( 'BEGIN EXCLUSIVE' )
        self._trans_write = True

    def _commit( self ):

        if( not self._trans_write ):
            return

        self.imgdb.prepare_commit()

        try:
            trigger_pre_commit_hooks( self, False )
            self.session.commit()
            self.imgdb.complete_commit()
        except:
            self.imgdb.unprepare_commit()
            raise

        self.obj_del_list = []
        self._trans_write = False

        trigger_post_commit_hooks( self, False )

    def _rollback( self ):

        if( not self._trans_write ):
            return

        trigger_pre_commit_hooks( self, True )

        self.imgdb.rollback()
        self.session.rollback()
        self._trans_write = False

        trigger_post_commit_hooks( self, True )

    def close( self ):

        self.session.close()
        self.session = None

    def enable_write_access( self ):

        self._access.enable_writes()

    def transaction( self ):

        return self._access()

    def _get_object_by_id( self, object_id: int ) -> Obj:

        obj = self.session.query( model.Object ) \
                  .filter( model.Object.object_id == object_id ) \
                  .first()
        if( obj is None ):
            return None

        return model_obj_to_higu_obj( self, obj )

    def get_object_by_id( self, object_id: int ) -> Obj:

        with self._access():
            return self._get_object_by_id( object_id )

    def get_stream_by_id( self, stream_id: int ) -> Optional[Stream]:

        with self._access():
            stream = self.session.query( model.Stream ) \
                         .filter( model.Stream.stream_id == stream_id ) \
                         .first()
            if( stream is None ):
                return None

            return model_stream_to_higu_stream( self, stream )

    def lookup_streams_by_details( self, file_length = None,
                                         hash_crc32 = None,
                                         hash_md5 = None,
                                         hash_sha1 = None ):

        q = self.session.query( model.Stream )
        if( file_length is not None ):
            q = q.filter( model.Stream.stream_length == file_length )
        if( hash_crc32 is not None ):
            q = q.filter( model.Stream.hash_crc32 == hash_crc32 )
        if( hash_md5 is not None ):
            q = q.filter( model.Stream.hash_md5 == hash_md5 )
        if( hash_sha1 is not None ):
            q = q.filter( model.Stream.hash_sha1 == hash_sha1 )

        return [ model_stream_to_higu_stream( self, s ) for s in q ]

    def lookup_untagged_files( self ):

        return self.unowned_files()

    def all_tags( self, scope = None ):

        from sqlalchemy import func, or_

        q = self.session.query( model.Object.name,
                                model.Object,
                                func.count( model.Relation.child_id ) ) \
                .join( model.Relation, model.Object.object_id == model.Relation.parent_id ) \
                .filter( model.Object.object_type == TYPE_CLASSIFIER )

        if( scope is not None ):
            q = q.filter( or_( model.Object.name == scope,
                               model.Object.name.like( scope + ':%' ) ) )

        q = q.group_by( model.Relation.parent_id ) \
             .order_by( model.Object.name )

        result = {}
        for name, obj, count in q.all():
            result[name] = ( model_obj_to_higu_obj( self, obj ), count )

        return result

    def get_tag( self, name: str, fuzzy: bool = False ) -> Tag:
        '''Gets the tag with the given name. If fuzzy is true, then a substring
        match will be performed, as long as only one tag matches.'''

        obj = self.session.query( model.Object ) \
                .filter( model.Object.object_type == TYPE_CLASSIFIER ) \
                .filter( model.Object.name == name ).first()

        if( obj is None ):
            if( not fuzzy ):
                raise KeyError( f'No such tag "{name}"' )

            name_s = '%' \
                + name.replace( '%', '[%]' ) \
                        .replace( '*', '%' ) \
                + '%'

            q = self.session.query( model.Object ) \
                    .filter( model.Object.object_type == TYPE_CLASSIFIER ) \
                    .filter( model.Object.name.like( name_s ) )

            r = [r for r in q]
            if( len( r ) == 0 ):
                raise KeyError( f'No tags match "{name}"' )
            elif( len( r ) > 1 ):
                raise KeyError( f'Tag name "{name}" is ambiguous' )

            obj = r[0]

        return model_obj_to_higu_obj( self, obj )

    def _make_tag( self, name ):

        check_tag_name( name )
        try:
            return self.get_tag( name )
        except KeyError:
            obj = model.Object( TYPE_CLASSIFIER, name )
            self.session.add( obj )
            return model_obj_to_higu_obj( self, obj )

    def make_tag( self, name ):

        with self._access( write = True ):
            return self._make_tag( name )

    def delete_tag( self, tag ):

        tags = self.all_tags( tag )
        for tag, count in tags.values():
            self.delete_object( tag )

    def move_tag( self, tag, target ):

        from sqlalchemy import and_

        with self._access( write = True ):

            check_tag_name( target )
            tags = self.all_tags( tag )

            for t, count in tags.values():

                c = t.obj
                new_name = target + c.name[len( tag ):]

                try:
                    d = self.get_tag( new_name ).obj

                    # Remove tag where it would be a duplicate
                    dups = self.session.query( model.Relation.child_id ) \
                        .filter( model.Relation.parent_id == d.object_id ) \
                        .subquery()
                    self.session.query( model.Relation ) \
                        .filter( and_( model.Relation.parent_id == c.object_id,
                                       model.Relation.child_id.in_( dups ) ) ) \
                        .delete( synchronize_session = 'fetch' )
                    self.session.flush()
                    self.session.query( model.Relation ) \
                        .filter( model.Relation.parent_id == c.object_id ) \
                        .update( { 'parent_id' : d.object_id } )
                    self.session.delete( c )

                except KeyError:
                    c.name = new_name

    def copy_tag( self, tag, target ):

        with self._access( write = True ):

            check_tag_name( target )
            c = self.get_tag( tag ).obj

            try:
                d = self.get_tag( target ).obj
            except KeyError:
                d = model.Object( TYPE_CLASSIFIER, target )
                self.session.add( d )

            for rel in c.child_rel:
                rel_copy = model.Relation( rel.sort )
                rel_copy.parent_obj = d
                rel_copy.child_obj = rel.child_obj

    def __recover_file( self, path ):

        import mimetypes

        name = os.path.split( path )[1]

        details = calculate_details( path )
        streams = self.lookup_streams_by_details( *details )

        if( len( streams ) == 0 ):
            return False

        if( not streams[0].verify() ):
            self.imgdb.load_data( path, streams[0].stream.stream_id,
                                        streams[0].stream.priority,
                                        streams[0].stream.extension )

            ext = os.path.splitext( path )[1]
            assert ext[0] == '.'
            streams[0].stream.extension = ext[1:]
            streams[0].stream.mime_type = mimetypes.guess_type( path, strict=False )[0]
        return True

    def recover_files( self, files ):

        with self._access( write = True ):
            for f in files:
                if( not self.__recover_file( f ) ):
                    #log.warn( '%s was not found in the db and was ignored', f )
                    pass

    def create_album( self, tags = [], name = None, text = None ):

        with self._access( write = True ):
            album = model.Object( TYPE_ALBUM )
            self.session.add( album )
            album = model_obj_to_higu_obj( self, album )

            if( name is not None ):
                album.obj.name = name

            if( text is not None ):
                album.obj['text'] = text

            for t in tags:
                album.assign( t, None )

            return album

    def __register_file( self, path, name_policy, name = None ):

        import mimetypes

        if( name is None ):
            name = os.path.split( path )[1]

        ext = os.path.splitext( name )[1]
        assert ext[0] == '.'
        ext = ext[1:]

        details = calculate_details( path )

        mime_type = mimetypes.guess_type( path, strict=False )[0]
        streams = self.lookup_streams_by_details( *details )
        new_stream = False

        if( len( streams ) == 0 ):
            obj = model.Object( TYPE_FILE )
            self.session.add( obj )
            stream = model.Stream( obj, '.', model.SP_NORMAL,
                                   None, ext, mime_type )
            stream.set_details( *details )
            self.session.add( stream )
            obj.root_stream = stream

            f = model_obj_to_higu_obj( self, obj )
            stream = model_stream_to_higu_stream( self, stream )
            new_stream = True

            self.session.flush()
            f._on_created( stream )
        else:
            stream = streams[0]
            if( stream.stream.mime_type is None ):
                stream.stream.mime_type = mime_type

            f = stream.get_file()

        if( name_policy == NAME_POLICY_DONT_REGISTER ):
            log = model.StreamLog( stream.stream, 'hdbfs:register',
                                   None, None )
        else:
            log = model.StreamLog( stream.stream, 'hdbfs:register',
                                   None, name )
        self.session.add( log )

        if( name_policy == NAME_POLICY_SET_ALWAYS
         or (name_policy == NAME_POLICY_SET_IF_UNDEF
         and f.obj.name is None) ):

            f.obj.name = name

        if( not stream.verify() ):
            self.imgdb.load_data( path, stream.stream.stream_id,
                                        stream.stream.priority,
                                        stream.stream.extension )

        # Request thumbnails be generated
        if( isinstance( f, ImageFile ) ):
            f.request_thumbs()

        return f, stream, new_stream

    def register_file( self, path, name_policy = NAME_POLICY_SET_IF_UNDEF, name = None ):

        with self._access( write = True ):
            f, stream, is_new = self.__register_file( path, name_policy, name )

        return f

    def register_file3( self, path, name_policy = NAME_POLICY_SET_IF_UNDEF, name = None ):

        with self._access( write = True ):
            f, stream, is_new = self.__register_file( path, name_policy, name )

        return f, stream, is_new

    def __register_thumb( self, path, obj, origin, name ):

        import mimetypes

        ext = os.path.splitext( path )[1]
        assert ext[0] == '.'
        ext = ext[1:]

        details = calculate_details( path )
        mime_type = mimetypes.guess_type( path, strict=False )[0]

        stream = model.Stream( obj.obj, name, model.SP_EXPENDABLE,
                               origin.stream, ext, mime_type )
        stream.set_details( *details )
        self.session.add( stream )

        log = model.StreamLog( stream, 'imgdb:' + name,
                               origin.stream, None )
        self.session.add( log )
        self.session.flush()

        self.imgdb.load_data( path, stream.stream_id,
                                    stream.priority,
                                    stream.extension )

        return model_stream_to_higu_stream( self, stream )

    def register_thumb( self, path, obj, origin, name ):

        with self._access( write = True ):
            return self.__register_thumb( path, obj, origin, name )

    @_with_access( write = True )
    def __get_next_thumb_request( self,
                min_prio: Optional[ImageRequestPriority],
            ) -> Optional[ThumbRequest]:

        q = self.session.query( model.ImageRequest )

        if( min_prio is not None ):
                q.filter( model.ImageRequest.prio >= min_prio.value )

        r = q.order_by( model.ImageRequest.prio.desc() ) \
             .limit( 1 ).first()

        if( r is None ):
            return None

        if( r.exp_mask is not None ):
            req_e = []
            req_shift = r.exp_mask
            exp = 0

            while( req_shift != 0 ):
                if( (req_shift & 1) != 0 ):
                    req_e.append( exp )

                exp += 1
                req_shift >>= 1
        else:
            req_e = None

        return ThumbRequest(
                    ImageRequestPriority( r.prio ),
                    req_e,
                    model_obj_to_higu_obj( self, r.obj ) )

    @_with_access( write = True )
    def get_next_thumb_request( self,
                min_prio: Optional[ImageRequestPriority] = None,
            ) -> Optional[ThumbRequest]:
        '''Gets the highest priority thumb request. The returned request will
        be at least the provided min_prio priority.'''

        return self.__get_next_thumb_request( min_prio )

    @_with_access( write = True )
    def process_next_thumb_request( self,
                min_prio: Optional[ImageRequestPriority] = None,
            ) -> Optional[ImageFile]:
        '''Processes thumbs for the next request.'''

        req = self.__get_next_thumb_request( min_prio )
        if( req is None ):
            return None

        if( req.exps is None ):
            # The image doesn't have the ImageInfo initialized.
            # Initialize it now and change us to a normal thumb
            # request.
            req.file.get_thumb_sizes()
            req.file.request_thumbs( req.prio )
        else:
            for exp in req.exps:
                req.file.get_thumb_stream( exp, ThumbRequestPrio.IMMEDIATE )

        return req.file

    def process_thumb_requests( self,
                min_prio: Optional[ThumbRequestPrio] = None,
            ) -> bool:
        '''Processes all thumb requests above the provided priority. If no
        priority is provided, processes all.'''

        processed_one = False

        while( self.process_next_thumb_request( min_prio ) is not None ):
            processed_one = True

        return processed_one

    def batch_add_files( self, files, tags = [], tags_new = [],
                         name_policy = NAME_POLICY_SET_IF_UNDEF,
                         create_album = False, album_name = None, album_text = None ):

        with self._access( write = True ):

            # Load tags
            taglist = []
            taglist += map( self.get_tag, tags )
            taglist += map( self._make_tag, tags_new )

            if( create_album ):
                album = self.create_album( taglist, album_name, album_text )
            else:
                album = None

            for f in files:
                x, stream, is_new = self.__register_file( f, name_policy )

                if( album is not None ):
                    x.assign( album, None )
                else:
                    for t in taglist:
                        x.assign( t, None )

    def delete_object( self, obj ):

        with self._access( write = True ):

            object_id = obj.obj.object_id

            if( isinstance( obj, File ) ):
                obj._drop_streams()
                self.obj_del_list.append( object_id )

            self.session.query( model.ObjectMetadata ) \
                .filter( model.ObjectMetadata.object_id == object_id ) \
                .delete()
            self.session.query( model.Relation ) \
                .filter( model.Relation.parent_id == object_id ) \
                .delete()
            self.session.query( model.Relation ) \
                .filter( model.Relation.child_id == object_id ) \
                .delete()
            self.session.query( model.Object ) \
                .filter( model.Object.object_id == object_id ) \
                .delete()

def init( library_path = None ):
    global _LIBRARY

    if( library_path is not None ):
        _LIBRARY = library_path
    else:
        _LIBRARY = DEFAULT_LIBRARY

    if( not os.path.isdir( _LIBRARY ) ):
        os.makedirs( _LIBRARY )

    model.init( os.path.join( _LIBRARY, HIGURASHI_DB_NAME ),
                _LIBRARY )

def dispose():
    global _LIBRARY

    model.dispose()
    _LIBRARY = None

def compare_details( a, b ):

    return long( a[0] ) == long( b[0] ) \
       and str( a[1] ) == str( b[1] ) \
       and str( a[2] ) == str( b[2] ) \
       and str( a[3] ) == str( b[3] )

imgdb.init_module()

# vim:sts=4:sw=4:et
