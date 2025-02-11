import datetime

import hdbfs.ark
import hdbfs.model as model

from hdbfs.session import Session, SessionObject
from hdbfs.defs import *
from hdbfs.hash import calculate_details

from typing import Optional, List

class Stream( SessionObject ):

    def __init__( self, session: Session, stream: model.Stream ):

        super().__init__( session )
        self.stream = stream

    @SessionObject._with_access()
    def get_file( self ):

        return self.session._construct_session_object( self.stream.obj )

    @SessionObject._with_access()
    def get_stream_id( self ):

        return self.stream.stream_id

    @SessionObject._with_access()
    def get_name( self ):

        return self.stream.name

    @SessionObject._with_access()
    def get_priority( self ):

        return self.stream.priority

    @SessionObject._with_access()
    def get_creation_time( self ):

        create_log = self.stream.log_entries \
                        .order_by( model.StreamLog.timestamp ).first()
        return datetime.datetime.fromtimestamp( create_log.timestamp )

    @SessionObject._with_access()
    def get_creation_time_utc( self ):

        create_log = self.stream.log_entries \
                        .order_by( model.StreamLog.timestamp ).first()
        return datetime.datetime.utcfromtimestamp( create_log.timestamp )

    @SessionObject._with_access()
    def get_origin_stream( self ):

        if( self.stream.origin_stream is not None ):
            return self.session._construct_session_object(
                        self.stream.origin_stream )
        else:
            return None

    @SessionObject._with_access()
    def get_origin_method( self ):

        create_log = self.stream.log_entries \
                        .order_by( model.StreamLog.timestamp ).first()
        return create_log.origin_method

    @SessionObject._with_access()
    def get_length( self ):

        return self.stream.stream_length

    @SessionObject._with_access()
    def get_hash( self ):

        return self.stream.hash_sha1

    @SessionObject._with_access()
    def get_extension( self ):

        return self.stream.extension

    @SessionObject._with_access()
    def get_mime( self ):

        return self.stream.mime_type

    @SessionObject._with_access()
    def open( self ):

        return self.session.imgdb.open(
                        self.stream.stream_id,
                        self.stream.priority,
                        self.stream.extension  )

    @SessionObject._with_access()
    def verify( self ):

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

        self.session.imgdb.delete(
                self.stream.stream_id,
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

    @SessionObject._with_access()
    def __getitem__( self, key ):

        return self.stream[key]

    @SessionObject._with_access( write = True )
    def __setitem__( self, key, value ):

        self.stream[key] = value

    def __eq__( self, o ):

        if( o == None ):
            return False
        if( not isinstance( o, self.__class__ ) ):
            return False
        return self.session == o.session \
           and self.stream == o.stream

class Obj( SessionObject ):

    def __init__( self, session: Session, obj: model.Object ):

        super().__init__( session )
        self.obj = obj

    def _on_created( self, stream ):

        pass

    def _on_children_changed( self ):

        pass

    @SessionObject._with_access()
    def get_id( self ):

        return self.obj.object_id

    @SessionObject._with_access()
    def get_type( self ):

        return self.obj.object_type

    @SessionObject._with_access()
    def get_parents( self, obj_type, limit = None ):

        obj_type = [ obj_type ] if( not isinstance( obj_type, list ) ) else obj_type

        objs = [ obj for obj in self.obj.parents if obj.object_type in obj_type ]
        if( limit is not None and len( objs ) > limit ):
            objs = objs[:limit]
        return list( map( lambda x: self.session._construct_session_object( x ), objs ) )

    @SessionObject._with_access()
    def get_children( self, obj_type, limit = None ):

        obj_type = [ obj_type ] if( not isinstance( obj_type, list ) ) else obj_type

        objs = [ obj for obj in self.obj.children if obj.object_type in obj_type ]
        if( limit is not None and len( objs ) > limit ):
            objs = objs[:limit]
        return list( map( lambda x: self.session._construct_session_object( x ), objs ) )

    @SessionObject._with_access()
    def get_creation_time( self ):

        return datetime.datetime.fromtimestamp( self.obj.create_ts )

    @SessionObject._with_access()
    def get_creation_time_utc( self ):

        return datetime.datetime.utcfromtimestamp( self.obj.create_ts )

    def get_member_of( self ):

        return self.get_parents( [ model.TYPE_ALBUM, model.TYPE_PUBLISHED ] )

    @SessionObject._with_access()
    def get_tags( self ) -> List['hdbfs.Tag']:

        from sqlalchemy import and_

        tag_objs = [
            obj for obj in
            self.session.model.query( model.Object )
                .filter(
                    and_( model.Object.object_type == TYPE_CLASSIFIER,
                            model.Object.children.contains( self.obj ) ) )
                            .order_by( model.Object.name ) ]
        return list( map( lambda x: self.session._construct_session_object( x ), tag_objs ) )

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

        q = self.session.model.query( model.Relation )
        # For relations where we are the parent
        q = q.filter( model.Relation.parent_id == self.obj.object_id )
        # And, for which a child is not also a child of our parent
        q = q.filter( ~self.session.model.query( r_i )
                          .filter( r_i.parent_id == parent.obj.object_id )
                          .filter( r_i.child_id == model.Relation.child_id )
                          .exists() )
        # Move the parent to our parent
        q.update( { 'parent_id' : parent.obj.object_id }, synchronize_session = 'fetch' )

        q = self.session.model.query( model.Relation )
        # For relations where we are the child
        q = q.filter( model.Relation.child_id == self.obj.object_id )
        # And which isn't the relation with our parent
        q = q.filter( model.Relation.parent_id != parent.obj.object_id )
        # And which isn't a relation with a PUBLISHED album
        q = q.filter( ~model.Relation.parent_id.in_(
                        self.session.model.query( model.Object.object_id )
                            .filter( model.Object.object_type == model.TYPE_PUBLISHED ) ) )
        # And, for which the parent is not also a parent of our parent
        q = q.filter( ~self.session.model.query( r_i )
                          .filter( r_i.parent_id == model.Relation.parent_id )
                          .filter( r_i.child_id == parent.obj.object_id )
                          .exists() )
        # Move it to a parent of our parent
        q.update( { 'child_id' : parent.obj.object_id }, synchronize_session = 'fetch' )

        # Drop remaining relationships
        #---------------------------------------------------------------
        q = self.session.model.query( model.Relation )
        # For relations where we are either the parent or the child
        q = q.filter( or_( model.Relation.parent_id == self.obj.object_id,
                           model.Relation.child_id == self.obj.object_id ) )
        # And which isn't the relation with our parent
        q = q.filter( model.Relation.parent_id != parent.obj.object_id )
        # And which isn't a relation with a PUBLISHED album
        q = q.filter( ~model.Relation.parent_id.in_(
                        self.session.model.query( model.Object.object_id )
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
        rel = self.session.model.query( model.Relation ) \
                .filter( model.Relation.parent_id == parent.obj.object_id ) \
                .filter( model.Relation.child_id == self.obj.object_id ).first()

        # Loops aren't permitted, so reverse a relation if we get into that case
        if( rel is None ):
            rel = self.session.model.query( model.Relation ) \
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

    @SessionObject._with_access( write = True )
    def assign( self, parent,
                order = None,
                name = None,
                is_duplicate = None,
                force = None ):

        self.__assign( parent, order, name, is_duplicate, force )
        parent._on_children_changed()

    def __unassign( self, parent, force ):

        if( not force ):
            assert parent.obj.object_type != model.TYPE_PUBLISHED

        rel = self.session.model.query( model.Relation ) \
                .filter( model.Relation.parent_id == parent.obj.object_id ) \
                .filter( model.Relation.child_id == self.obj.object_id ).first()

        if( rel is not None ):
            self.session.model.delete( rel )

            if( self.obj.object_type == model.TYPE_DUPLICATE
            and parent.obj.object_type == model.TYPE_FILE ):

                # We're no longer a duplicate
                self.obj.object_type = model.TYPE_FILE

    @SessionObject._with_access( write = True )
    def unassign( self, parent, force = None  ):

        self.__unassign( parent, force )
        parent._on_children_changed()

    @SessionObject._with_access( write = True )
    def reorder( self, group, order = None ):

        assert group.obj.object_type == model.TYPE_ALBUM

        rel = self.session.model.query( model.Relation ) \
                .filter( model.Relation.parent_id == group.obj.object_id ) \
                .filter( model.Relation.child_id == self.obj.object_id ) \
                .first()
        if( rel is None ):
            raise ValueError( f'{self!s} is not in {group!s}' )
        rel.sort = order

    @SessionObject._with_access()
    def get_order( self, group ):

        rel = self.session.model.query( model.Relation ) \
                .filter( model.Relation.parent_id == group.obj.object_id ) \
                .filter( model.Relation.child_id == self.obj.object_id ).first()
        if( rel is None ):
            raise ValueError( f'{self!s} is not in {group!s}' )
        return rel.sort

    @SessionObject._with_access()
    def get_name( self, group = None ) -> Optional[str]:

        if( group is not None ):
            rel = self.session.model.query( model.Relation ) \
                    .filter( model.Relation.parent_id == group.obj.object_id ) \
                    .filter( model.Relation.child_id == self.obj.object_id ).first()
            if( rel is not None and rel.child_name is not None ):
                return rel.child_name

        return self.obj.name

    @SessionObject._with_access( write = True )
    def set_name( self, name, group = None ):

        if( group is not None ):
            rel = self.session.model.query( model.Relation ) \
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

    @SessionObject._with_access()
    def __getitem__( self, key ):

        return self.obj[key]

    @SessionObject._with_access( write = True )
    def __setitem__( self, key, value ):

        self.obj[key] = value

    def __hash__( self ):

        return self.get_id()

    def __eq__( self, o ):

        if( o == None ):
            return False
        if( not isinstance( o, self.__class__ ) ):
            return False
        return self.session == o.session and self.obj == o.obj
