import datetime

import hdbfs.ark
import hdbfs.model as model

from hdbfs.defs import *
from hdbfs.hash import calculate_details
from hdbfs.obj_factory import *

from typing import Optional

class Stream:

    def __init__( self, db, stream: model.Stream ):

        self.db = db
        self.stream = stream

    def get_file( self ):

        with self.db._access():
            return model_obj_to_higu_obj( self.db, self.stream.obj )

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
            return datetime.datetime.fromtimestamp(
                            create_log.timestamp,
                             datetime.timezone.utc )

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

    def open( self ):

        with self.db._access():
            return self.db.imgdb.open( self.stream.stream_id,
                                       self.stream.priority,
                                       self.stream.extension  )

    def verify( self ):

        with self.db._access():
            try:
                with self.open() as fd:
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
            except hdbfs.ark.FileUnavailableError:
                return False

    def _drop_data( self ):

        self.db.imgdb.delete( self.stream.stream_id,
                              self.stream.priority,
                              self.stream.extension  )

    def get_repr( self ):

        return str( self )

    def __str__( self ):

        return f'{self.get_file()!s}:{self.get_name()}'

    def __repr__( self ):

        name = self.get_name()
        id = self.get_stream_id()
        obj = self.stream.object_id
        mime = self.stream.mime_type

        return f'Stream( {name}, {id=}, {obj=}, {mime=} )'

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

    def __init__( self, db, obj: model.Object ):

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

    def get_parents( self, obj_type, limit = None ):

        obj_type = [ obj_type ] if( not isinstance( obj_type, list ) ) else obj_type

        with self.db._access():
            objs = [ obj for obj in self.obj.parents if obj.object_type in obj_type ]
            if( limit is not None and len( objs ) > limit ):
                objs = objs[:limit]
            return list( map( lambda x: model_obj_to_higu_obj( self.db, x ), objs ) )

    def get_children( self, obj_type, limit = None ):

        obj_type = [ obj_type ] if( not isinstance( obj_type, list ) ) else obj_type

        with self.db._access():
            objs = [ obj for obj in self.obj.children if obj.object_type in obj_type ]
            if( limit is not None and len( objs ) > limit ):
                objs = objs[:limit]
            return list( map( lambda x: model_obj_to_higu_obj( self.db, x ), objs ) )

    def get_creation_time( self ):

        with self.db._access():
            return datetime.datetime.fromtimestamp( self.obj.create_ts )

    def get_creation_time_utc( self ):

        with self.db._access():
            return datetime.datetime.fromtimestamp(
                        self.obj.create_ts,
                         datetime.timezone.utc )

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
            return list( map( lambda x: Tag( self.db, x ), tag_objs ) )

    def has_tag( self, tag ):

        tags = self.get_tags()

        if( tag in tags ):
            return True

        for t in tags:
            if( tag == t.obj.name ):
                return True
        else:
            return False

    def __assign_duplicate( self, parent, rel ):

        from sqlalchemy import or_
        from sqlalchemy.orm import aliased

        # If our parent was a duplicate, we are now promoting it:
        # duplicates do not stack
        if( parent.obj.object_type == model.TYPE_DUPLICATE ):
            parent.obj.object_type = model.TYPE_FILE

        self.obj.object_type = model.TYPE_DUPLICATE

        # Duplicates do not have relations with most other objects
        # so we need to move the relations to the parent now

        # Move relationships which do not conflict
        #---------------------------------------------------------------
        r_i = aliased( model.Relation )

        q = self.db.session.query( model.Relation )
        # For relations where we are the parent
        q = q.filter( model.Relation.parent_id == self.obj.object_id )
        # And, for which a child is not also a child of our parent
        q = q.filter( ~self.db.session.query( r_i )
                          .filter( r_i.parent_id == parent.obj.object_id )
                          .filter( r_i.child_id == model.Relation.child_id )
                          .exists() )
        # Move the parent to our parent
        q.update( { 'parent_id' : parent.obj.object_id }, synchronize_session = 'fetch' )

        q = self.db.session.query( model.Relation )
        # For relations where we are the child
        q = q.filter( model.Relation.child_id == self.obj.object_id )
        # And which isn't the relation with our parent
        q = q.filter( model.Relation.parent_id != parent.obj.object_id )
        # And which isn't a relation with a PUBLISHED album
        q = q.filter( ~model.Relation.parent_id.in_(
                        self.db.session.query( model.Object.object_id )
                            .filter( model.Object.object_type == model.TYPE_PUBLISHED ) ) )
        # And, for which the parent is not also a parent of our parent
        q = q.filter( ~self.db.session.query( r_i )
                          .filter( r_i.parent_id == model.Relation.parent_id )
                          .filter( r_i.child_id == parent.obj.object_id )
                          .exists() )
        # Move it to a parent of our parent
        q.update( { 'child_id' : parent.obj.object_id }, synchronize_session = 'fetch' )

        # Drop remaining relationships
        #---------------------------------------------------------------
        q = self.db.session.query( model.Relation )
        # For relations where we are either the parent or the child
        q = q.filter( or_( model.Relation.parent_id == self.obj.object_id,
                           model.Relation.child_id == self.obj.object_id ) )
        # And which isn't the relation with our parent
        q = q.filter( model.Relation.parent_id != parent.obj.object_id )
        # And which isn't a relation with a PUBLISHED album
        q = q.filter( ~model.Relation.parent_id.in_(
                        self.db.session.query( model.Object.object_id )
                            .filter( model.Object.object_type == model.TYPE_PUBLISHED ) ) )
        # Delete these
        q.delete( synchronize_session = 'fetch' )

    def __assign( self, parent, order, name, is_duplicate, force ):

        # Sanity checks
        if( self.obj.object_type == model.TYPE_ALBUM ):

            assert parent.obj.object_type in [
                        model.TYPE_CLASSIFIER,
                        model.TYPE_ALBUM,
                    ]

        elif( self.obj.object_type == model.TYPE_PUBLISHED ):

            if( force ):
                assert parent.obj.object_type in [
                            model.TYPE_CLASSIFIER,
                            model.TYPE_ALBUM,
                            model.TYPE_PUBLISHED,
                        ]
            else:
                assert parent.obj.object_type in [
                            model.TYPE_CLASSIFIER,
                            model.TYPE_ALBUM,
                        ]

        elif( self.obj.object_type == model.TYPE_FILE ):

            if( force ):
                assert parent.obj.object_type in [
                            model.TYPE_CLASSIFIER,
                            model.TYPE_ALBUM,
                            model.TYPE_PUBLISHED,
                            model.TYPE_FILE
                        ]
            else:
                assert parent.obj.object_type in [
                            model.TYPE_CLASSIFIER,
                            model.TYPE_ALBUM,
                            model.TYPE_FILE
                        ]

        elif( self.obj.object_type == model.TYPE_DUPLICATE ):

            if( force ):
                assert parent.obj.object_type == model.TYPE_PUBLISHED
            else:
                return self.get_original_file().__assign(
                            parent, order, name,
                            is_duplicate, force )

        else:
            assert False

        # Orders and names are allowed only for albums
        if( order is not None or name is not None ):
            assert parent.obj.object_type in model.ALBUM_TYPES

        # Fetch an existing relation
        rel = self.db.session.query( model.Relation ) \
                .filter( model.Relation.parent_id == parent.obj.object_id ) \
                .filter( model.Relation.child_id == self.obj.object_id ).first()

        # Loops aren't permitted, so reverse a relation if we get into that case
        if( rel is None ):
            rel = self.db.session.query( model.Relation ) \
                    .filter( model.Relation.child_id == parent.obj.object_id ) \
                    .filter( model.Relation.parent_id == self.obj.object_id ).first()

            if( rel is not None ):
                rel.parent_obj = parent.obj
                rel.child_obj = self.obj

        if( is_duplicate is not None ):
            # Duplicates are allowed only on files
            assert parent.obj.object_type == model.TYPE_FILE

            if( is_duplicate ):
                self.__assign_duplicate( parent, rel )

        if( rel is None ):
            rel = model.Relation()
            rel.parent_obj = parent.obj
            rel.child_obj = self.obj

        if( order is not None ):
            rel.sort = order
        if( name is not None ):
            rel.child_name = name

    def assign( self, parent,
                order = None,
                name = None,
                is_duplicate = None,
                force = None ):

        with self.db._access( write = True ):
            self.__assign( parent, order, name, is_duplicate, force )
            parent._on_children_changed()

    def __unassign( self, parent, force ):

        if( not force ):
            assert parent.obj.object_type != model.TYPE_PUBLISHED

        rel = self.db.session.query( model.Relation ) \
                .filter( model.Relation.parent_id == parent.obj.object_id ) \
                .filter( model.Relation.child_id == self.obj.object_id ).first()

        if( rel is not None ):
            self.db.session.delete( rel )

            if( self.obj.object_type == model.TYPE_DUPLICATE
            and parent.obj.object_type == model.TYPE_FILE ):

                # We're no longer a duplicate
                self.obj.object_type = model.TYPE_FILE

    def unassign( self, parent, force = None  ):

        with self.db._access( write = True ):
            self.__unassign( parent, force )
            parent._on_children_changed()

    def reorder( self, group, order = None ):

        with self.db._access( write = True ):

            assert group.obj.object_type == model.TYPE_ALBUM

            rel = self.db.session.query( model.Relation ) \
                    .filter( model.Relation.parent_id == group.obj.object_id ) \
                    .filter( model.Relation.child_id == self.obj.object_id ) \
                    .first()
            if( rel is None ):
                raise ValueError( f'{self!s} is not in {group!s}' )
            rel.sort = order

    def get_order( self, group ):

        with self.db._access():
            rel = self.db.session.query( model.Relation ) \
                    .filter( model.Relation.parent_id == group.obj.object_id ) \
                    .filter( model.Relation.child_id == self.obj.object_id ).first()
            if( rel is None ):
                raise ValueError( f'{self!s} is not in {group!s}' )
            return rel.sort

    def get_name( self, group = None ):

        with self.db._access():
            if( group is not None ):
                rel = self.db.session.query( model.Relation ) \
                        .filter( model.Relation.parent_id == group.obj.object_id ) \
                        .filter( model.Relation.child_id == self.obj.object_id ).first()
                if( rel is not None and rel.child_name is not None ):
                    return rel.child_name

            return self.obj.name

    def set_name( self, name, group = None ):

        with self.db._access( write = True ):
            if( group is not None ):
                rel = self.db.session.query( model.Relation ) \
                        .filter( model.Relation.parent_id == group.obj.object_id ) \
                        .filter( model.Relation.child_id == self.obj.object_id ).first()
                if( rel is None ):
                    raise ValueError( f'{self!s} is not in {group!s}' )
                else:
                    rel.child_name = name
            else:
                self.obj.name = name

    def get_repr( self, group = None ):

        name = self.get_name( group )
        if( name is not None ):
            return name
        else:
            return '%016x' % ( self.get_id() )

    def __str__( self ):

        name = self.get_name()
        if( name is not None ):
            return name
        else:
            return '%016x' % ( self.get_id() )

    def __repr__( self ):

        id = self.obj.object_id
        name = self.get_name()

        if( name is None ):
            return f'Object( {id=} )'
        else:
            return f'Object( "{name}", {id=} )'

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

    def __init__( self, db, obj: model.Object ):

        Obj.__init__( self, db, obj )

    def is_ordered( self ):

        return False

    def get_items( self, limit = None ):

        return self.get_children( [
                    model.TYPE_ALBUM,
                    model.TYPE_PUBLISHED,
                    model.TYPE_FILE,
                    model.TYPE_DUPLICATE
                ], limit )

    def get_albums( self, limit = None ):

        return self.get_children( [
                    model.TYPE_ALBUM,
                    model.TYPE_PUBLISHED
                ], limit )

    def get_files( self, limit = None ):

        return self.get_children( [
                    model.TYPE_FILE,
                    model.TYPE_DUPLICATE
                ], limit )

class OrderedGroup( Group ):

    def __init__( self, db, obj: model.Object ):

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

            all_objs = self.get_files()

            for child in enumerate( children ):
                assert( child[1] in all_objs )
                all_objs.remove( child[1] )

                child[1].reorder( self, child[0] )

            offset = len( children )

            for child in enumerate( all_objs ):
                child[1].reorder( self, offset + child[0] )

class Tag( Group ):

    def __init__( self, db, obj: model.Object ):

        Group.__init__( self, db, obj )

class File( Obj ):

    def __init__( self, db, obj: model.Object ):

        Obj.__init__( self, db, obj )

    def get_albums( self ):

        return self.get_parents( [ model.TYPE_ALBUM, model.TYPE_PUBLISHED ] )

    def get_variants_of( self ):

        if( self.obj.object_type == model.TYPE_FILE ):
            return self.get_parents( model.TYPE_FILE )
        else:
            return []

    def get_variants( self ):

        return self.get_children( model.TYPE_FILE )

    def get_original_file( self ):

        if( self.obj.object_type == model.TYPE_DUPLICATE ):
            # Only one duplicate parent is permitted
            return self.get_parents( model.TYPE_FILE )[0]
        else:
            return None

    def get_duplicates( self ):

        return self.get_children( model.TYPE_DUPLICATE )

    def get_origin_names( self ):

        from sqlalchemy import and_

        with self.db._access():
            return [ log.origin_name for log in
                self.db.session.query( model.StreamLog.origin_name )
                    .filter( and_( model.StreamLog.stream_id == self.obj.root_stream.stream_id,
                                   model.StreamLog.origin_name != None ) )
                    .distinct() ]

    def get_repr( self, group = None ):

        name = self.get_name( group )
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

    def _list_streams( self ):

        return [ rs[0] for rs in
            self.db.session.query( model.Stream.name )
                .filter( model.Stream.object_id == self.obj.object_id )
                .order_by( model.Stream.stream_id ) ]

    def list_streams( self ):

        with self.db._access():
            return self._list_streams()

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

    def get_root_stream( self ) -> Stream:

        with self.db._access():
            return model_stream_to_higu_stream( self.db, self.obj.root_stream )

    def verify( self ):

        with self.db._access():
            for s in self.get_streams():
                s.verify()

def _basic_stream_factory( db, stream ):

    return Stream( db, stream )

def _basic_obj_factory( db, obj ):

    if( obj.object_type == model.TYPE_FILE
     or obj.object_type == model.TYPE_DUPLICATE ):
        return File( db, obj )
    elif( obj.object_type == model.TYPE_ALBUM
       or obj.object_type == model.TYPE_PUBLISHED ):
        return Group( db, obj )
    elif( obj.object_type == TYPE_CLASSIFIER ):
        return Tag( db, obj )
    else:
        return None

add_stream_factory( _basic_stream_factory )
add_obj_factory( _basic_obj_factory )
