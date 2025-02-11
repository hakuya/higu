import os
import re

from hdbfs.hash import calculate_details

from hdbfs.objects.album import Album
from hdbfs.objects.file import File
from hdbfs.objects.groups import Tag
from hdbfs.session import Session
from hdbfs.objects.factories import init_basic_factories

import hdbfs.imgdb as imgdb
import hdbfs.model as model
import hdbfs.query as query

from hdbfs.imgdb.objects import ThumbRequestPrio
from hdbfs.imgdb.dataconfig import ImageDbDataConfig

from hdbfs.objects.basic import *
from hdbfs.defs import *
from hdbfs.imgdb import ImageStream, ImageFile

import hdbfs.bulk as bulk

from hdbfs.model import ImageRequestPriority

from typing import Optional, NamedTuple, List

_LIBRARY = None

def check_tag_name( s ):

    if( re.match( '^[\w\-_:]+$', s ) is None ):
        raise ValueError( f'"{s}" is not a valid tag name' )

class ThumbRequest( NamedTuple ):
    prio: ImageRequestPriority
    exps: Optional[ List[int] ]
    file: ImageFile

class Database( Session ):

    def __init__( self ):
        global _LIBRARY

        super().__init__( ImageDbDataConfig( _LIBRARY ) )
        self.tbcache = imgdb.ThumbCache( self )

        imgdb.init_session( self, self.tbcache )
        init_basic_factories( self, self.tbcache )

    def _get_object_by_id( self, object_id: int ) -> Obj:

        obj = self.model.query( model.Object ) \
                  .filter( model.Object.object_id == object_id ) \
                  .first()
        if( obj is None ):
            return None

        return self._construct_session_object( obj )

    @Session._with_access()
    def get_object_by_id( self, object_id: int ) -> Obj:

        return self._get_object_by_id( object_id )

    @Session._with_access()
    def get_stream_by_id( self, stream_id: int ) -> Optional[Stream]:

        stream = self.model.query( model.Stream ) \
                        .filter( model.Stream.stream_id == stream_id ) \
                        .first()
        if( stream is None ):
            return None

        return self._construct_session_object( stream )

    def _lookup_streams_by_details( self, file_length = None,
                                          hash_crc32 = None,
                                          hash_md5 = None,
                                          hash_sha1 = None ):

        q = self.model.query( model.Stream )
        if( file_length is not None ):
            q = q.filter( model.Stream.stream_length == file_length )
        if( hash_crc32 is not None ):
            q = q.filter( model.Stream.hash_crc32 == hash_crc32 )
        if( hash_md5 is not None ):
            q = q.filter( model.Stream.hash_md5 == hash_md5 )
        if( hash_sha1 is not None ):
            q = q.filter( model.Stream.hash_sha1 == hash_sha1 )

        return [ self._construct_session_object( s ) for s in q ]

    def lookup_untagged_files( self ):

        return self.unowned_files()

    def _all_tags( self, scope: Optional[str] ) -> List[Tag]:

        from sqlalchemy import func, or_

        q = self.model.query( model.Object.name,
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
            result[name] = ( self._construct_session_object( obj ), count )

        return result

    @Session._with_access()
    def all_tags( self, scope: Optional[str] = None ) -> List[Tag]:

        return self._all_tags( scope )

    def _get_tag( self, name: str, fuzzy: bool = False ) -> Tag:
        obj = self.model.query( model.Object ) \
                .filter( model.Object.object_type == TYPE_CLASSIFIER ) \
                .filter( model.Object.name == name ).first()

        if( obj is None ):
            if( not fuzzy ):
                raise KeyError( f'No such tag "{name}"' )

            name_s = '%' \
                + name.replace( '%', '[%]' ) \
                        .replace( '*', '%' ) \
                + '%'

            q = self.model.query( model.Object ) \
                    .filter( model.Object.object_type == TYPE_CLASSIFIER ) \
                    .filter( model.Object.name.like( name_s ) )

            r = [r for r in q]
            if( len( r ) == 0 ):
                raise KeyError( f'No tags match "{name}"' )
            elif( len( r ) > 1 ):
                raise KeyError( f'Tag name "{name}" is ambiguous' )

            obj = r[0]

        return self._construct_session_object( obj )

    @Session._with_access()
    def get_tag( self, name: str, fuzzy: bool = False ) -> Tag:
        '''Gets the tag with the given name. If fuzzy is true, then a substring
        match will be performed, as long as only one tag matches.'''

        return self._get_tag( name, fuzzy )

    def _make_tag( self, name ):

        check_tag_name( name )
        try:
            return self._get_tag( name, False )
        except KeyError:
            obj = model.Object( TYPE_CLASSIFIER, name )
            self.model.add( obj )
            return self._construct_session_object( obj )

    @Session._with_access( write = True )
    def make_tag( self, name ):

        return self._make_tag( name )

    def delete_tag( self, tag ):

        tags = self.all_tags( tag )
        for tag, count in tags.values():
            self.delete_object( tag )

    @Session._with_access( write = True )
    def move_tag( self, tag, target ):

        from sqlalchemy import and_

        check_tag_name( target )
        tags = self._all_tags( tag, None )

        for t, count in tags.values():

            c = t.obj
            new_name = target + c.name[len( tag ):]

            try:
                d = self._get_tag( new_name, False ).obj

                # Remove tag where it would be a duplicate
                dups = self.model.query( model.Relation.child_id ) \
                    .filter( model.Relation.parent_id == d.object_id ) \
                    .subquery()
                self.model.query( model.Relation ) \
                    .filter( and_( model.Relation.parent_id == c.object_id,
                                    model.Relation.child_id.in_( dups ) ) ) \
                    .delete( synchronize_session = 'fetch' )
                self.model.flush()
                self.model.query( model.Relation ) \
                    .filter( model.Relation.parent_id == c.object_id ) \
                    .update( { 'parent_id' : d.object_id } )
                self.model.delete( c )

            except KeyError:
                c.name = new_name

    @Session._with_access( write = True )
    def copy_tag( self, tag, target ):

        check_tag_name( target )
        c = self._get_tag( tag, False ).obj

        try:
            d = self._get_tag( target, False ).obj
        except KeyError:
            d = model.Object( TYPE_CLASSIFIER, target )
            self.model.add( d )

        for rel in c.child_rel:
            rel_copy = model.Relation( rel.sort )
            rel_copy.parent_obj = d
            rel_copy.child_obj = rel.child_obj

    def __recover_file( self, path ):

        import mimetypes

        name = os.path.split( path )[1]

        details = calculate_details( path )
        streams = self._lookup_streams_by_details( *details )

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

    @Session._with_access( write = True )
    def recover_files( self, files ):

        for f in files:
            if( not self.__recover_file( f ) ):
                #log.warn( '%s was not found in the db and was ignored', f )
                pass

    @Session._with_access( write = True )
    def create_album( self, tags = [], name = None, text = None ) -> hdbfs.Album:

        album = model.Object( TYPE_ALBUM )
        self.model.add( album )
        album = self._construct_session_object( album )

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
        streams = self._lookup_streams_by_details( *details )
        new_stream = False

        if( len( streams ) == 0 ):
            obj = model.Object( TYPE_FILE )
            self.model.add( obj )
            stream = model.Stream( obj, '.', model.SP_NORMAL,
                                   None, ext, mime_type )
            stream.set_details( *details )
            self.model.add( stream )
            obj.root_stream = stream

            f = self._construct_session_object( obj )
            stream = self._construct_session_object( stream )
            new_stream = True

            self.model.flush()
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
        self.model.add( log )

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

    @Session._with_access( write = True )
    def register_file( self, path, name_policy = NAME_POLICY_SET_IF_UNDEF, name = None ):

        return self.__register_file( path, name_policy, name )[0]

    @Session._with_access( write = True )
    def register_file3( self, path, name_policy = NAME_POLICY_SET_IF_UNDEF, name = None ):

        return self.__register_file( path, name_policy, name )

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
        self.model.add( stream )

        log = model.StreamLog( stream, 'imgdb:' + name,
                               origin.stream, None )
        self.model.add( log )
        self.model.flush()

        self.imgdb.load_data( path, stream.stream_id,
                                    stream.priority,
                                    stream.extension )

        return self._construct_session_object( stream )

    @Session._with_access( write = True )
    def register_thumb( self, path, obj, origin, name ):

        return self.__register_thumb( path, obj, origin, name )

    def __get_next_thumb_request( self,
                min_prio: Optional[ImageRequestPriority],
            ) -> Optional[ThumbRequest]:

        q = self.model.query( model.ImageRequest )

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
                    self._construct_session_object( r.obj ) )

    @Session._with_access( write = True )
    def get_next_thumb_request( self,
                min_prio: Optional[ImageRequestPriority] = None,
            ) -> Optional[ThumbRequest]:
        '''Gets the highest priority thumb request. The returned request will
        be at least the provided min_prio priority.'''

        return self.__get_next_thumb_request( min_prio )

    @Session._with_access( write = True )
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

    @Session._with_access( write = True )
    def batch_add_files( self, files, tags = [], tags_new = [],
                         name_policy = NAME_POLICY_SET_IF_UNDEF,
                         create_album = False, album_name = None, album_text = None ):

        # Load tags
        taglist = []
        taglist += map( self._get_tag, tags )
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

    @Session._with_access( write = True )
    def delete_object( self, obj ):

        object_id = obj.obj.object_id

        if( isinstance( obj, File ) ):
            obj._drop_streams()
            self.obj_del_list.append( object_id )

        self.model.query( model.ObjectMetadata ) \
            .filter( model.ObjectMetadata.object_id == object_id ) \
            .delete()
        self.model.query( model.Relation ) \
            .filter( model.Relation.parent_id == object_id ) \
            .delete()
        self.model.query( model.Relation ) \
            .filter( model.Relation.child_id == object_id ) \
            .delete()
        self.model.query( model.Object ) \
            .filter( model.Object.object_id == object_id ) \
            .delete()

def compare_details( a, b ):

    return long( a[0] ) == long( b[0] ) \
       and str( a[1] ) == str( b[1] ) \
       and str( a[2] ) == str( b[2] ) \
       and str( a[3] ) == str( b[3] )

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

imgdb.init_module()