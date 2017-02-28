import datetime
import os
import re
import sys
import time

from hash import calculate_details

import ark
import model
import query

VERSION = 1
REVISION = 0

DB_VERSION  = model.VERSION
DB_REVISION = model.REVISION

DEFAULT_LIBRARY = os.path.join( os.environ['HOME'], '.higu' )
HIGURASHI_DB_NAME = 'hfdb.dat'

TYPE_FILE       = model.TYPE_FILE
TYPE_GROUP      = model.TYPE_GROUP
TYPE_ALBUM      = model.TYPE_ALBUM
TYPE_CLASSIFIER = model.TYPE_CLASSIFIER

_LIBRARY = None

def check_tag_name( s ):

    if( re.match( '^[\w\-_:]+$', s ) is None ):
        raise ValueError, '"%s" is not a valid tag name' % ( s, )

def make_unicode( s ):

    if( not isinstance( s, unicode ) ):
        return unicode( s, 'utf-8' )
    else:
        return s

def model_obj_to_higu_obj( db, obj ):

    if( obj.object_type == TYPE_FILE ):
        return File( db, obj )
    elif( obj.object_type == TYPE_ALBUM ):
        return Album( db, obj )
    elif( obj.object_type == TYPE_CLASSIFIER ):
        return Tag( db, obj )
    else:
        assert False

class Stream:

    def __init__( self, db, stream ):

        self.db = db
        self.stream = stream

    def _get_file( self ):

        return File( self.db, self.stream.obj )

    def get_file( self ):

        with self.db._access():
            return self.get_file()

    def get_stream_id( self ):

        with self.db._access():
            return self.stream.stream_id

    def get_name( self ):

        with self.db._access():
            return self.stream.name

    def get_priority( self ):

        with self.db._access():
            return self.stream.priority

    def get_creation_time( self ):

        with self.db._access():
            return datetime.datetime.fromtimestamp( self.stream.create_ts )

    def get_creation_time_utc( self ):

        with self.db._access():
            return datetime.datetime.utcfromtimestamp( self.stream.create_ts )

    def get_origin_stream( self ):

        with self.db._access():
            if( self.stream.origin_stream is not None ):
                return Stream( self.db, self.stream.origin_stream )
            else:
                return None

    def get_origin_method( self ):

        with self.db._access():
            return self.stream.origin_method

    def get_length( self ):

        with self.db._access():
            return self.stream.stream_length

    def get_hash( self ):

        with self.db._access():
            return self.stream.hash_sha1

    def get_extension( self ):

        with self.db._access():
            return self.stream.extension

    def get_mime( self ):

        with self.db._access():
            return self.stream.mime_type

    def _read( self ):

        return self.db.imgdb.read( self.stream.stream_id,
                                   self.stream.priority,
                                   self.stream.extension  )

    def read( self ):

        with self.db._access():
            return self._read()

    def _verify( self ):

        fd = self._read()

        if( fd is None ):
            return False

        details = calculate_details( fd )

        if( details[0] != self.stream.stream_length ):
            return False
        if( details[1] != self.stream.hash_crc32 ):
            return False
        if( details[2] != self.stream.hash_md5 ):
            return False
        if( details[3] != self.stream.hash_sha1 ):
            return False

        return True

    def verify( self ):

        with self._access():
            return self._verify()

    def _drop_data( self ):

        self.db.imgdb.delete( self.stream.stream_id,
                              self.stream.priority,
                              self.stream.extension  )

    def __getitem__( self, key ):

        with self.db._access():
            return self.stream[key]

    def __setitem__( self, key, value ):

        with self.db._access( write = True ):
            self.stream[key] = value

    def __eq__( self, o ):

        if( o == None ):
            return False
        if( not isinstance( o, self.__class__ ) ):
            return False
        return self.db == o.db and self.stream == o.stream

class Obj:

    def __init__( self, db, obj ):

        self.db = db
        self.obj = obj

    def get_id( self ):

        with self.db._access():
            return self.obj.object_id

    def get_type( self ):

        with self.db._access():
            return self.obj.object_type

    def get_creation_time( self ):

        with self.db._access():
            return datetime.datetime.fromtimestamp( self.obj.create_ts )

    def get_creation_time_utc( self ):

        with self.db._access():
            return datetime.datetime.utcfromtimestamp( self.obj.create_ts )

    def get_tags( self ):

        with self.db._access():
            tag_objs = [ obj for obj in self.obj.parents
                                     if obj.object_type == TYPE_CLASSIFIER ]
            return map( lambda x: Tag( self.db, x ), tag_objs )

    def _assign( self, group, order ):
    
        rel = self.db.session.query( model.Relation ) \
                .filter( model.Relation.parent_id == group.obj.object_id ) \
                .filter( model.Relation.child_id == self.obj.object_id ).first()
        if( rel is not None ):
            rel.sort = order
            return
        rel = model.Relation( order )
        rel.parent_obj = group.obj
        rel.child_obj = self.obj

    def assign( self, group, order = None ):

        with self.db._access( write = True ):
            self._assign( group, order )

    def _unassign( self, group ):

        rel = self.db.session.query( model.Relation ) \
                .filter( model.Relation.parent_id == group.obj.object_id ) \
                .filter( model.Relation.child_id == self.obj.object_id ).first()

        if( rel is not None ):
            self.db.session.delete( rel )

    def unassign( self, group ):

        with self.db._access( write = True ):
            self._unassign( group )

    def _reorder( self, group, order ):

        rel = self.db.session.query( model.Relation ) \
                .filter( model.Relation.parent_id == group.obj.object_id ) \
                .filter( model.Relation.child_id == self.obj.object_id ) \
                .first()
        if( rel is None ):
            raise ValueError, str( self ) + ' is not in ' + str( group )
        rel.sort = order

    def reorder( self, group, order = None ):

        with self.db._access( write = True ):
            self._reorder( group, order )

    def get_order( self, group ):

        with self.db._access():
            rel = self.db.session.query( model.Relation ) \
                    .filter( model.Relation.parent_id == group.obj.id ) \
                    .filter( model.Relation.child_id == self.obj.id ).first()
            if( rel is None ):
                raise ValueError, str( self ) + ' is not in ' + str( group )
            return rel.sort
        
    def get_name( self ):

        with self.db._access():
            return self.obj.name

    def _clear_names( self ):

        self.obj.name = None
        del self.obj.root_stream['names']

    def _set_names( self, names ):

        if( len( names ) == 0 ):
            self._clear_names()

        self.obj.name = names[0]
        self.obj.root_stream['names'] = ':'.join( names )

    def _set_name( self, name ):

        try:
            names = self.obj.root_stream['names'].split( ':' )
            try:
                names.remove( name )
            except ValueError:
                pass
        except:
            names = []

        names.insert( name, 0 )

        self._set_names( names )

    def _add_name( self, name ):

        try:
            names = self.obj.root_stream['names'].split( ':' )
            if( name in names ):
                return
            names.append( name )
        except:
            names = [ name ]

        self._set_names( names )

    def set_name( self, name, saveold = False ):

        with self.db._access( write = True ):
            self._set_name( name, saveold )

    def add_name( self, name ):

        with self.db._access( write = True ):
            self._add_name( name )

    def get_names( self ):

        try:
            return self.get_root_stream()['names'].split( ':' )
        except KeyError:
            return None

    def set_text( self, text ):

        self['text'] = text

    def get_text( self ):

        try:
            return self['text']
        except KeyError:
            return None

    def get_repr( self ):

        name = self.get_name()
        if( name is not None ):
            return name
        else:
            return '%016x' % ( self.get_id() )

    def __getitem__( self, key ):

        with self.db._access():
            return self.obj[key]

    def __setitem__( self, key, value ):

        with self.db._access( write = True ):
            self.obj[key] = value

    def __hash__( self ):

        return self.get_id()

    def __eq__( self, o ):

        if( o == None ):
            return False
        if( not isinstance( o, self.__class__ ) ):
            return False
        return self.db == o.db and self.obj == o.obj

class Group( Obj ):

    def __init__( self, db, obj ):

        Obj.__init__( self, db, obj )

    def is_ordered( self ):

        return False

    def _get_files( self ):

        objs = [ obj for obj in self.obj.children
                             if obj.object_type == TYPE_FILE ]
        return map( lambda x: File( self.db, x ), objs )

    def get_files( self ):

        with self.db._access():
            return self._get_files()

class OrderedGroup( Group ):

    def __init__( self, db, obj ):

        Group.__init__( self, db, obj )

    def is_ordered( self ):

        #TODO: check if ordered
        return True

    def clear_order( self ):

        all_objs = self.get_files()

        for child in all_objs:
            child.reorder( self )

    def set_order( self, children ):

        with self.db._access( write = True ):

            all_objs = self._get_files()
            
            for child in enumerate( children ):
                assert( child[1] in all_objs )
                all_objs.remove( child[1] )
                
                child[1]._reorder( self, child[0] )

            offset = len( children )

            for child in enumerate( all_objs ):
                child[1]._reorder( self, offset + child[0] )

class Tag( Group ):

    def __init__( self, db, obj ):

        Group.__init__( self, db, obj )

class Album( OrderedGroup ):

    def __init__( self, db, obj ):

        OrderedGroup.__init__( self, db, obj )

class File( Obj ):

    def __init__( self, db, obj ):

        Obj.__init__( self, db, obj )

    def _get_albums( self ):

        objs = [ obj for obj in self.obj.parents if obj.object_type == TYPE_ALBUM ]
        return map( lambda x: Album( self.db, x ), objs )

    def get_albums( self ):

        with self.db._access():
            return self._get_albums()

    def _get_variant_of( self ):

        objs = [ obj for obj in self.obj.parents if obj.object_type == TYPE_FILE ]
        return map( lambda x: File( self.db, x ), objs )

    def get_variant_of( self ):

        with self.db._access():
            return self._get_variant_of()

    def _get_duplicates( self ):

        from sqlalchemy import and_

        return [ Stream( self.db, s ) for s in
            self.db.session.query( model.Stream )
                           .filter( and_( model.Stream.object_id == self.obj.object_id,
                                          model.Stream.name.like( 'dup:%' ) ) )
                           .order_by( model.Stream.stream_id ) ]

    def get_duplicates( self ):

        with self.db._access():
            return self._get_duplicates()

    def _get_variants( self ):

        return [ File( self.db, o ) for o in self.obj.children ]

    def get_variants( self ):

        with self.db._access():
            return self._get_variants()

    def _set_variant_of( self, parent ):

        assert( isinstance( parent, File ) )
        assert( parent.obj != self.obj )

        self._assign( parent, None )

    def set_variant_of( self, parent ):

        with self.db._access( write = True ):
            self._set_variant_of( parent )

    def _clear_duplication( self ):

        self.obj.type = TYPE_FILE
        self.obj.similar_to = None

    def clear_duplication( self ):

        with self.db._access( write = True ):
            self._clear_duplication()

    def get_repr( self ):

        name = self.get_name()
        if( name is not None ):
            return name
        else:
            with self.db._access():
                obj_id = self.obj.object_id
                stream_id = self.obj.stream.stream_id
                priority = self.obj.stream.priority
                extension = self.obj.stream.extension

            if( extension == None ):
                return '%016x' % ( obj_id, )
            else:
                return '%016x.%s' % ( obj_id, extension, )

    def _get_stream( self, name ):

        s = self.obj.streams \
                .filter( model.Stream.name == name ) \
                .first()

        if( s is not None ):
            return Stream( self.db, s )
        else:
            return None

    def get_stream( self, name ):

        with self.db._access():
            return self._get_stream( name )
    
    def _get_streams( self ):

        return [ Stream( self.db, s ) for s in
            self.db.session.query( model.Stream )
                .filter( model.Stream.object_id == self.obj.object_id )
                .order_by( model.Stream.stream_id ) ]

    def get_streams( self ):

        with self.db._access():
            return self._get_streams()

    def _drop_streams( self ):

        for s in self._get_streams():
            s._drop_data()

            self.db.session.query( model.StreamMetadata ) \
                .filter( model.StreamMetadata.stream_id != s.stream.stream_id ) \
                .delete()

        self.db.session.query( model.Stream ) \
            .filter( model.Stream.object_id == self.obj.object_id ) \
            .delete()

    def _drop_expendable_streams( self ):

        for s in self.db.session.query( model.Stream ) \
                     .filter( model.Stream.priority < model.SP_NORMAL ):

            stream = Stream( self.db, s )
            stream._drop_data()

            self.db.session.query( model.StreamMetadata ) \
                .filter( model.StreamMetadata.stream_id != s.stream_id ) \
                .delete()

        self.db.session.query( model.Stream ) \
            .filter( model.Stream.priority < model.SP_NORMAL ) \
            .delete()

    def drop_expendable_streams( self ):

        with self.db._access( write = True ):
            self._drop_expendable_streams()

    def _get_root_stream( self ):

        return Stream( self.db, self.obj.root_stream )

    def get_root_stream( self ):

        with self.db._access():
            return self._get_root_stream()

    def rotate( self, rot ):

        with self.db._access( write = True ):
            if( self.obj.root_stream is None ):
                return

            try:
                rotation = self.obj.root_stream['rotation']
            except:
                rotation = 0

            rotation += int( rot )
            rotation %= 4

            if( rotation < 0 ):
                rotation += 4

            self.obj.root_stream['rotation'] = rotation

        self.db.tbcache.purge_thumbs( self )

    def get_thumb_stream( self, exp ):

        return self.db.tbcache.make_thumb( self, exp )

    def _verify( self ):

        for s in self._get_streams():
            s._verify()

class ModelObjToHiguObjIterator:

    def __init__( self, db, iterable ):

        self.db = db
        self.it = iterable.__iter__()

    def __iter__( self ):

        return ModelObjToHiguObjIterator( self.db, self.it )

    def next( self ):

        return model_obj_to_higu_obj( self.db, self.it.next() )

class _AccessContext:

    def __init__( self, db, manager, write = False, auto_commit = True ):

        self.__db = db
        self.__manager = manager
        self.__write = write
        self.__auto_commit = auto_commit
        self.__active = False

    def __enter__( self ):

        self.__db._begin( self.__write )
        self.__manager._begin_access( self.__write )
        self.__active = True
        return self

    def __exit__( self, type, value, trace ):

        self.__active = False

        if( self.__write ):
            committed = False

            if( type is None
            and self.__auto_commit ):

                try:
                    self.__db._commit()
                    committed = True

                except:
                    type, value, trace = sys.exc_info()

            if( not committed ):
                self.__db._rollback()

        self.__manager._end_access()
        if( type is not None ):
            raise type, value, trace

    def commit( self ):

        assert self.__write, 'Can only commit with write access'
        self.__db._commit()
        self.__db._begin( self.__write )

    def rollback( self ):

        self.__db._rollback()
        self.__db._begin( self.__write )

class AccessManager:

    def __init__( self, db ):

        self.__db = db
        self.__write_permitted = False

    def _begin_access( self, write ):

        assert not write or self.__write_permitted, 'Read-Only Access'

    def _end_access( self ):

        pass

    def enable_writes( self ):

        self.__write_permitted = True

    def __call__( self, **kwargs ):

        return _AccessContext( self.__db, self, **kwargs )

class Database:

    def __init__( self ):
        global _LIBRARY

        self.session = model.Session()

        imgdat_config = ark.ImageDbDataConfig( _LIBRARY )
        self.imgdb = ark.StreamDatabase( imgdat_config )
        self.tbcache = ark.ThumbCache( self, self.imgdb )

        self._access = AccessManager( self )
        self._trans_write = False

        self.obj_del_list = []

    def __del__( self ):

        if( self.session is not None ):
            self.session.close()

    def _begin( self, write ):

        if( write ):
            self.session.execute( 'BEGIN EXCLUSIVE' )
            self._trans_write = True

    def _commit( self ):

        if( not self._trans_write ):
            return

        self.imgdb.prepare_commit()
        try:
            self.session.commit()
            self.imgdb.complete_commit()
        except:
            self.imgdb.unprepare_commit()
            raise

        self.obj_del_list = []
        self._trans_write = False

    def _rollback( self ):

        if( not self._trans_write ):
            return

        self.imgdb.rollback()
        self.session.rollback()
        self._trans_write = False

    def close( self ):

        self.session.close()
        self.session = None

    def enable_write_access( self ):

        self._access.enable_writes()

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

    def all_albums_or_free_files( self ):

        files = self.session.query( model.Object.object_id ) \
                .filter( model.Object.object_type == TYPE_FILE )
        albums = self.session.query( model.Object.object_id ) \
                .filter( model.Object.object_type == TYPE_ALBUM )
        all_children = self.session.query( model.Relation.child_id ) \
                .filter( model.Relation.parent_id.in_( albums ) )
        free_files = files.filter( ~model.Object.object_id.in_( all_children ) )

        select_ids = free_files.union( albums )

        return ModelObjToHiguObjIterator( self, 
                self.session.query( model.Object )
                    .filter( model.Object.object_id.in_( select_ids ) )
                    .order_by( 'RANDOM()' ) )

    def unowned_files( self ):

        from sqlalchemy import or_

        all_children = self.session.query( model.Relation.child_id )
        return ModelObjToHiguObjIterator( self,
                self.session.query( model.Object )
                    .filter( model.Object.object_type.in_( [ TYPE_FILE, TYPE_ALBUM ] ) )
                    .filter( ~model.Object.object_id.in_( all_children ) )
                    .order_by( 'RANDOM()' ) )

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

        return [ Stream( self, s ) for s in q ]

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

        with self._access( write = True ):

            check_tag_name( target )
            c = self.get_tag( tag ).obj

            try:
                d = self.get_tag( target ).obj
                self.session.query( model.Relation ) \
                    .filter( model.Relation.parent_id == c.id ) \
                    .update( { 'parent' : d.id } )
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

        if( not streams[0]._verify() ):
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

    def __create_album( self, tags = [], name = None, text = None ):

        album = model.Object( TYPE_ALBUM )
        self.session.add( album )
        album = model_obj_to_higu_obj( self, album )

        if( name is not None ):
            album.obj.name = make_unicode( name )

        if( text is not None ):
            album.obj['text'] = make_unicode( text )

        for t in tags:
            album._assign( t, None )

        return album

    def create_album( self, tags = [], name = None, text = None ):

        with self._access( write = True ):
            return self.__create_album( tags, name, text )

    def __register_file( self, path, add_name ):

        import mimetypes

        name = os.path.split( path )[1].decode( sys.getfilesystemencoding() )
        ext = os.path.splitext( name )[1]
        assert ext[0] == '.'
        ext = ext[1:]

        details = calculate_details( path )

        mime_type = mimetypes.guess_type( path, strict=False )[0]
        streams = self.lookup_streams_by_details( *details )

        if( len( streams ) == 0 ):
            obj = model.Object( TYPE_FILE )
            self.session.add( obj )
            stream = model.Stream( obj, '.', model.SP_NORMAL,
                                   None, 'hdbfs:register',
                                   ext, mime_type )
            stream.set_details( *details )
            self.session.add( stream )
            obj.root_stream = stream

            f = File( self, obj )
            stream = Stream( self, stream )

            self.session.flush()
        else:
            stream = streams[0]
            if( stream.stream.mime_type is None ):
                stream.stream.mime_type = mime_type

            f = stream._get_file()

        if( add_name ):
            f._add_name( name )

        if( not stream._verify() ):
            self.imgdb.load_data( path, stream.stream.stream_id,
                                        stream.stream.priority,
                                        stream.stream.extension )

        return f

    def register_file( self, path, add_name = True ):

        with self._access( write = True ):
            return self.__register_file( path, add_name )

    def __register_thumb( self, path, obj, origin, name ):

        import mimetypes

        ext = os.path.splitext( path )[1]
        assert ext[0] == '.'
        ext = ext[1:]

        details = calculate_details( path )
        mime_type = mimetypes.guess_type( path, strict=False )[0]

        stream = model.Stream( obj.obj, name, model.SP_EXPENDABLE,
                               origin.stream, 'imgdb:thumb',
                               ext, mime_type )
        stream.set_details( *details )
        self.session.add( stream )
        self.session.flush()

        self.imgdb.load_data( path, stream.stream_id,
                                    stream.priority,
                                    stream.extension )

        return Stream( self, stream )

    def register_thumb( self, path, obj, origin, name ):

        with self._access( write = True ):
            return self.__register_thumb( path, obj, origin, name )

    def batch_add_files( self, files, tags = [], tags_new = [], save_name = False,
                         create_album = False, album_name = None, album_text = None ):

        with self._access( write = True ):

            # Load tags
            taglist = []
            taglist += map( self.get_tag, tags )
            taglist += map( self._make_tag, tags_new )

            if( create_album ):
                album = self.__create_album( taglist, album_name, album_text )
            else:
                album = None

            for f in files:
                x = self.__register_file( f, save_name )

                if( album is not None ):
                    x._assign( album, None )
                else:
                    for t in taglist:
                        x._assign( t, None )

    def _merge_objects( self, primary_obj, merge_obj ):

        from sqlalchemy import and_, or_
        from sqlalchemy.orm import aliased

        assert isinstance( primary_obj, File ), 'Expected File got %r' % ( merge_obj )
        assert isinstance( merge_obj, File ), 'Expected File got %r' % ( merge_obj )

        obj_p = primary_obj.obj
        obj_m = merge_obj.obj

        assert obj_p != obj_m

        merge_obj._drop_expendable_streams()

        # Rename the root stream of the object to be merged so that it
        # appears as a duplicate stream
        stream = obj_m.root_stream
        stream.name = 'dup:' + stream.hash_sha1

        # Move all streams from the object to be merged to the 
        self.session.query( model.Stream ) \
            .filter( model.Stream.object_id == obj_m.object_id ) \
            .update( { 'object_id' : obj_p.object_id } )

        # Delete the metadata on the object to be merged, it will not be
        # persisted
        self.session.query( model.ObjectMetadata ) \
            .filter( model.ObjectMetadata.object_id == obj_m.object_id ) \
            .delete()

        # Drop relationships with duplicate
        self.session.query( model.Relation ) \
            .filter( and_( model.Relation.parent_id == obj_p.object_id,
                           model.Relation.child_id == obj_m.object_id ) ) \
            .delete()
        self.session.query( model.Relation ) \
            .filter( and_( model.Relation.parent_id == obj_m.object_id,
                           model.Relation.child_id == obj_p.object_id ) ) \
            .delete()

        # Move relationships which do not conflict
        r_i = aliased( model.Relation )

        self.session.query( model.Relation ) \
            .filter( and_( model.Relation.parent_id == obj_m.object_id,
                           ~self.session.query( r_i )
                                .filter( and_( r_i.parent_id == obj_p.object_id,
                                               r_i.child_id == model.Relation.child_id ) )
                               .exists() ) ) \
            .update( { 'parent_id' : obj_p.object_id },
                     synchronize_session = 'fetch' )
        self.session.query( model.Relation ) \
            .filter( and_( model.Relation.child_id == obj_m.object_id,
                           ~self.session.query( r_i )
                                .filter( and_( r_i.parent_id == model.Relation.parent_id,
                                               r_i.child_id == obj_p.object_id ) )
                               .exists() ) ) \
            .update( { 'child_id' : obj_p.object_id },
                     synchronize_session = 'fetch' )

        # Copy sort from relationships that conflict
        for r_m in self.session.query( model.Relation ) \
                       .filter( model.Relation.parent_id == obj_m.object_id ):

            r_p = self.session.query( model.Relation ) \
                      .filter( and_( model.Relation.parent_id == obj_p.object_id,
                                     model.Relation.child_id == r_m.child_id ) ) \
                      .first()

            if( r_p.sort is None ):
                r_p.sort = r_m.sort

        for r_m in self.session.query( model.Relation ) \
                       .filter( model.Relation.child_id == obj_m.object_id ):

            r_p = self.session.query( model.Relation ) \
                      .filter( and_( model.Relation.child_id == obj_p.object_id,
                                     model.Relation.parent_id == r_m.parent_id ) ) \
                      .first()

            if( r_p.sort is None ):
                r_p.sort = r_m.sort

        self.session.query( model.Relation ) \
            .filter( and_( model.Relation.parent_id == obj_m.object_id,
                           self.session.query( r_i )
                               .filter( and_( r_i.parent_id == model.Relation.parent_id,
                                              r_i.child_id == model.Relation.child_id ) )
                               .exists() ) ) \
            .update( { 'sort' : obj_p.object_id },
                     synchronize_session = 'fetch' )

        # Drop remaining relationships
        self.session.query( model.Relation ) \
                    .filter( or_( model.Relation.parent_id == obj_m.object_id,
                                  model.Relation.child_id == obj_m.object_id ) ) \
                    .delete()

        merge_obj.obj = primary_obj.obj
        self.session.query( model.Object ) \
            .filter( model.Object.object_id == obj_m.object_id ) \
            .delete()

    def merge_objects( self, primary_obj, merge_obj ):

        with self._access( write = True ):
            self._merge_objects( primary_obj, merge_obj )

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

# vim:sts=4:sw=4:et
