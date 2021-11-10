import datetime
import os
import re
import sys
import time

from hash import calculate_details

import ark
import imgdb
import model
import query

from basic_objs import *
from defs import *
from imgdb import ImageStream, ImageFile, Album
from hooks import *
from obj_factory import *

_LIBRARY = None

def check_tag_name( s ):

    if( re.match( '^[\w\-_:]+$', s ) is None ):
        raise ValueError, '"%s" is not a valid tag name' % ( s, )

def make_unicode( s ):

    if( not isinstance( s, unicode ) ):
        return unicode( s, 'utf-8' )
    else:
        return s

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
            raise type, value, trace

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

    def __del__( self ):

        if( self.session is not None ):
            self.session.close()

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

    def _get_object_by_id( self, object_id ):

        obj = self.session.query( model.Object ) \
                  .filter( model.Object.object_id == object_id ) \
                  .first()
        if( obj is None ):
            return None

        return model_obj_to_higu_obj( self, obj )

    def get_object_by_id( self, object_id ):

        with self._access():
            return self._get_object_by_id( object_id )

    def get_stream_by_id( self, stream_id ):

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

    def all_tags( self ):

        objs = self.session.query( model.Object ) \
                .filter( model.Object.object_type == TYPE_CLASSIFIER ) \
                .order_by( model.Object.name )

        return ModelObjToHiguObjIterator( self, objs )

    def get_tag( self, name ):

        obj = self.session.query( model.Object ) \
                .filter( model.Object.object_type == TYPE_CLASSIFIER ) \
                .filter( model.Object.name == name ).first()
        if( obj is None ):
            raise KeyError, 'No such tag "%s"' % ( name, )

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

        tag = self.get_tag( tag )
        self.delete_object( tag )

    def move_tag( self, tag, target ):

        from sqlalchemy import and_

        with self._access( write = True ):

            check_tag_name( target )
            c = self.get_tag( tag ).obj

            try:
                d = self.get_tag( target ).obj

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
                c.name = target

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
                album.obj.name = make_unicode( name )

            if( text is not None ):
                album.obj['text'] = make_unicode( text )

            for t in tags:
                album.assign( t, None )

            return album

    def __register_file( self, path, name_policy, name = None ):

        import mimetypes

        if( name is None ):
            name = os.path.split( path )[1].decode( sys.getfilesystemencoding() )

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
