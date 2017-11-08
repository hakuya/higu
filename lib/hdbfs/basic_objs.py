import datetime

import model

from defs import *
from hash import calculate_details
from obj_factory import *

class Stream:

    def __init__( self, db, stream ):

        self.db = db
        self.stream = stream

    def _get_file( self ):

        return model_obj_to_higu_obj( self.db, self.stream.obj )

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
            create_log = self.stream.log_entries \
                            .order_by( model.StreamLog.timestamp ).first()
            return datetime.datetime.fromtimestamp( create_log.timestamp )

    def get_creation_time_utc( self ):

        with self.db._access():
            create_log = self.stream.log_entries \
                            .order_by( model.StreamLog.timestamp ).first()
            return datetime.datetime.utcfromtimestamp( create_log.timestamp )

    def get_origin_stream( self ):

        with self.db._access():
            if( self.stream.origin_stream is not None ):
                return model_stream_to_higu_stream( self.db, self.stream.origin_stream )
            else:
                return None

    def get_origin_method( self ):

        with self.db._access():
            create_log = self.stream.log_entries \
                            .order_by( model.StreamLog.timestamp ).first()
            return create_log.origin_method

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

    def get_repr( self ):

        return 's%016x.%s' % ( self.get_stream_id(),
                               self.get_extension() )

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

    def _on_created( self, stream ):

        pass

    def _on_children_changed( self ):

        pass

    def get_id( self ):

        with self.db._access():
            return self.obj.object_id

    def get_type( self ):

        with self.db._access():
            return self.obj.object_type

    def _get_parents( self, obj_type ):

        objs = [ obj for obj in self.obj.parents if obj.object_type == obj_type ]
        return map( lambda x: model_obj_to_higu_obj( self.db, x ), objs )

    def get_parents( self, obj_type ):

        with self.db._access():
            return self._get_parents( obj_type )

    def _get_children( self, obj_type ):

        objs = [ obj for obj in self.obj.children if obj.object_type == obj_type ]
        return map( lambda x: model_obj_to_higu_obj( self.db, x ), objs )

    def get_children( self, obj_type ):

        with self.db._access():
            return self._get_children( obj_type )

    def get_creation_time( self ):

        with self.db._access():
            return datetime.datetime.fromtimestamp( self.obj.create_ts )

    def get_creation_time_utc( self ):

        with self.db._access():
            return datetime.datetime.utcfromtimestamp( self.obj.create_ts )

    def get_tags( self ):

        from sqlalchemy import and_

        with self.db._access():
            tag_objs = [
                obj for obj in
                self.db.session.query( model.Object )
                    .filter(
                        and_( model.Object.object_type == TYPE_CLASSIFIER,
                              model.Object.children.contains( self.obj ) ) )
                             .order_by( model.Object.name ) ]
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

        group._on_children_changed()

    def assign( self, group, order = None ):

        with self.db._access( write = True ):
            self._assign( group, order )

    def _unassign( self, group ):

        rel = self.db.session.query( model.Relation ) \
                .filter( model.Relation.parent_id == group.obj.object_id ) \
                .filter( model.Relation.child_id == self.obj.object_id ).first()

        if( rel is not None ):
            self.db.session.delete( rel )

        group._on_children_changed()

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

    def set_name( self, name ):

        with self.db._access( write = True ):
            self.obj.name = name

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
        return map( lambda x: model_obj_to_higu_obj( self.db, x ), objs )

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

class File( Obj ):

    def __init__( self, db, obj ):

        Obj.__init__( self, db, obj )

    def _get_albums( self ):

        return self._get_parents( TYPE_ALBUM )

    def get_albums( self ):

        return self.get_parents( TYPE_ALBUM )

    def _get_variants_of( self ):

        return self._get_parents( TYPE_FILE )

    def get_variants_of( self ):

        return self.get_parents( TYPE_FILE )

    def _get_variants( self ):

        return self._get_children( TYPE_FILE )

    def get_variants( self ):

        return self.get_children( TYPE_FILE )

    def _set_variant_of( self, parent ):

        assert( isinstance( parent, File ) )
        assert( parent.obj != self.obj )

        self._assign( parent, None )

    def set_variant_of( self, parent ):

        with self.db._access( write = True ):
            self._set_variant_of( parent )

    def _clear_variant_of( self, parent ):

        assert( isinstance( parent, File ) )
        self._unassign( parent )

    def clear_variant_of( self, parent ):

        with self.db._access( write = True ):
            self._clear_variant_of( parent )

    def _get_duplicate_streams( self ):

        from sqlalchemy import and_

        return [ model_stream_to_higu_stream( self.db, s ) for s in
            self.db.session.query( model.Stream )
                           .filter( and_( model.Stream.object_id == self.obj.object_id,
                                          model.Stream.name.like( 'dup:%' ) ) )
                           .order_by( model.Stream.stream_id ) ]

    def get_duplicate_streams( self ):

        with self.db._access():
            return self._get_duplicate_streams()

    def _set_root_stream( self, stream ):

        assert stream.stream.object_id == self.obj.object_id
        assert stream.stream.name.startswith( 'dup:' )
        self.obj.root_stream.name = 'dup:' + self.obj.root_stream.hash_sha1
        self.db.session.flush()
        stream.stream.name = '.'
        self.obj.root_stream = stream.stream
        self.db.session.flush()

    def set_root_stream( self, stream ):

        with self.db._access( write = True ):
            self._set_root_stream( stream )

    def get_origin_names( self, all_streams = False ):

        from sqlalchemy import and_

        with self.db._access():
            if( all_streams ):
                return [ log.origin_name for log in
                    self.db.session.query( model.StreamLog.origin_name )
                        .join( model.Stream,
                               model.Stream.stream_id == model.StreamLog.stream_id )
                        .filter( and_( model.Stream.object_id == self.obj.object_id,
                                       model.StreamLog.origin_name != None ) )
                        .distinct() ]
            else:
                return [ log.origin_name for log in
                    self.db.session.query( model.StreamLog.origin_name )
                        .filter( and_( model.StreamLog.stream_id == self.obj.root_stream.stream_id,
                                       model.StreamLog.origin_name != None ) )
                        .distinct() ]

    def get_repr( self ):

        name = self.get_name()
        if( name is not None ):
            return name
        else:
            with self.db._access():
                obj_id = self.obj.object_id
                stream_id = self.obj.root_stream.stream_id
                priority = self.obj.root_stream.priority
                extension = self.obj.root_stream.extension

            if( extension == None ):
                return '%016x' % ( obj_id, )
            else:
                return '%016x.%s' % ( obj_id, extension, )

    def _get_stream( self, name ):

        s = self.obj.streams \
                .filter( model.Stream.name == name ) \
                .first()

        if( s is not None ):
            return model_stream_to_higu_stream( self.db, s )
        else:
            return None

    def get_stream( self, name ):

        with self.db._access():
            return self._get_stream( name )
    
    def _get_streams( self ):

        return [ model_stream_to_higu_stream( self.db, s ) for s in
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
                .filter( model.StreamMetadata.stream_id == s.stream.stream_id ) \
                .delete()

            self.db.session.query( model.StreamLog ) \
                .filter( model.StreamLog.stream_id == s.stream.stream_id ) \
                .delete()

        self.db.session.query( model.Stream ) \
            .filter( model.Stream.object_id == self.obj.object_id ) \
            .delete()

    def _drop_expendable_streams( self ):

        for s in self.db.session.query( model.Stream ) \
                     .filter( model.Stream.object_id == self.obj.object_id ) \
                     .filter( model.Stream.priority < model.SP_NORMAL ):

            stream = model_stream_to_higu_stream( self.db, s )
            stream._drop_data()

            self.db.session.query( model.StreamMetadata ) \
                .filter( model.StreamMetadata.stream_id == s.stream_id ) \
                .delete()

            self.db.session.query( model.StreamLog ) \
                .filter( model.StreamLog.stream_id == s.stream_id ) \
                .delete()

        self.db.session.query( model.Stream ) \
            .filter( model.Stream.object_id == self.obj.object_id ) \
            .filter( model.Stream.priority < model.SP_NORMAL ) \
            .delete()

    def drop_expendable_streams( self ):

        with self.db._access( write = True ):
            self._drop_expendable_streams()

    def _get_root_stream( self ):

        return model_stream_to_higu_stream( self.db, self.obj.root_stream )

    def get_root_stream( self ):

        with self.db._access():
            return self._get_root_stream()

    def _verify( self ):

        for s in self._get_streams():
            s._verify()

def _basic_stream_factory( db, stream ):

    return Stream( db, stream )

def _basic_obj_factory( db, obj ):

    if( obj.object_type == TYPE_FILE ):
        return File( db, obj )
    elif( obj.object_type == TYPE_ALBUM ):
        return Group( db, obj )
    elif( obj.object_type == TYPE_CLASSIFIER ):
        return Tag( db, obj )
    else:
        return None

add_stream_factory( _basic_stream_factory )
add_obj_factory( _basic_obj_factory )
