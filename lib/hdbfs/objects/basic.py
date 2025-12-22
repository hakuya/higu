import datetime

import hdbfs.ark
import hdbfs.model as model

from hdbfs.session import Session, SessionObject
from hdbfs.defs import *
from hdbfs.hash import calculate_details

from typing import Optional, List, Union, Dict

ObjectTypeSelect = Union[ ObjectType, ObjectClass, List[ObjectType], List[ObjectClass] ]

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
    def get_add_timestamp( self ) -> int:
        '''Gets the numeric timestamp this stream was added to the database'''

        create_log = self.stream.log_entries \
                        .order_by( model.StreamLog.timestamp ).first()
        return create_log.timestamp

    def get_add_time( self ) -> datetime.datetime:
        '''Gets the time this stream was added to the database'''

        return datetime.datetime.fromtimestamp( self.get_add_timestamp() )

    def get_add_time_utc( self ):
        '''Gets the time this stream was added to the database in UTC'''

        return datetime.datetime.fromtimestamp(
                    self.get_add_timestamp(),
                    datetime.timezone.utc )

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
    def get_type( self ) -> ObjectType:

        return self.obj.get_type()

    def __build_obj_type_values( self, obj_type: ObjectTypeSelect ) -> List[int]:

        if( isinstance( obj_type, list ) ):
            obj_type_ls = obj_type
        else:
            obj_type_ls = [ obj_type ]

        obj_type_values = []
        for ty in obj_type_ls:
            if( isinstance( ty, model.ObjectClass ) ):
                obj_type_values.extend( ty.all_type_values() )
            else:
                obj_type_values.append( ty.value )

        return obj_type_values

    @SessionObject._with_access()
    def get_parents( self,
                obj_type: ObjectTypeSelect,
                limit: Optional[int] = None
            ) -> List['Obj']:

        obj_type_values = self.__build_obj_type_values( obj_type )

        objs = list( set( [ obj for obj in self.obj.parents if obj.object_type in obj_type_values ] ) )
        if( limit is not None and len( objs ) > limit ):
            objs = objs[:limit]
        return list( map( lambda x: self.session._construct_session_object( x ), objs ) )

    @SessionObject._with_access()
    def get_children( self,
                obj_type: ObjectTypeSelect,
                limit: Optional[int] = None
            ) -> List['Obj']:

        obj_type_values = self.__build_obj_type_values( obj_type )

        objs = [ obj for obj in self.obj.children if obj.object_type in obj_type_values ]
        if( limit is not None and len( objs ) > limit ):
            objs = objs[:limit]
        return list( map( lambda x: self.session._construct_session_object( x ), objs ) )

    @SessionObject._with_access()
    def get_add_timestamp( self, group: Optional['Obj'] = None ) -> int:
        '''Gets the numeric timestamp when this object was added to the database
        '''

        if( group is not None ):
            rel = self.session.model.query( model.Relation ) \
                    .filter( model.Relation.parent_id == group.obj.object_id ) \
                    .filter( model.Relation.child_id == self.obj.object_id ).first()
            assert rel is not None
            return rel.add_ts

        return self.obj.add_ts

    def get_add_time( self, group: Optional['Obj'] = None ) -> datetime.datetime:
        '''Gets the time when this object was added to the database'''

        return datetime.datetime.fromtimestamp( self.get_add_timestamp( group ) )

    def get_add_time_utc( self, group: Optional['Obj'] = None ) -> datetime.datetime:
        '''Gets the time when this object was added to the database in UTC'''

        return datetime.datetime.fromtimestamp(
                    self.get_add_timestamp( group ),
                    datetime.timezone.utc )

    def get_member_of( self ) -> List['hdbfs.Album']:

        return self.get_parents( model.ObjectClass.ALBUM )

    @SessionObject._with_access()
    def get_tags( self ) -> List['hdbfs.Tag']:

        from sqlalchemy import and_

        tag_objs = [
            obj for obj in
            self.session.model.query( model.Object )
                .filter(
                    and_( model.Object.object_type.in_( model.ObjectClass.CLASSIFIER.all_type_values() ),
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

    def __assign_duplicate( self, parent: 'Obj', rel ):

        from sqlalchemy import or_
        from sqlalchemy.orm import aliased

        # If our parent was a duplicate, we are now promoting it:
        # duplicates do not stack
        if( parent.obj.get_type() == model.ObjectType.DUPLICATE ):
            parent.obj.set_type( model.ObjectType.FILE )

        self.obj.set_type( model.ObjectType.DUPLICATE )

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
        # And which isn't a relation with a FORMAL or PUBLISHED album
        q = q.filter( ~model.Relation.parent_id.in_(
                        self.session.model.query( model.Object.object_id )
                            .filter( or_(
                                model.Object.object_type == model.ObjectType.ALBUM_FORMAL.value,
                                model.Object.object_type == model.ObjectType.ALBUM_CLOSED.value,
                                model.Object.object_type == model.ObjectType.IMPORT_OPEN.value,
                                model.Object.object_type == model.ObjectType.IMPORT_CLOSED.value
                            ) ) ) )
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
        # And which isn't a relation with a FORMAL or PUBLISHED album
        q = q.filter( ~model.Relation.parent_id.in_(
                        self.session.model.query( model.Object.object_id )
                            .filter( or_(
                                model.Object.object_type == model.ObjectType.ALBUM_FORMAL.value,
                                model.Object.object_type == model.ObjectType.ALBUM_CLOSED.value,
                                model.Object.object_type == model.ObjectType.IMPORT_OPEN.value,
                                model.Object.object_type == model.ObjectType.IMPORT_CLOSED.value
                            ) ) ) )
        # Delete these
        q.delete( synchronize_session = 'fetch' )

    def __assign( self, parent: 'Obj', order, name, is_duplicate ):

        # Sanity checks
        if( self.obj.get_type() == model.ObjectType.ALBUM_FREE ):

            assert parent.obj.get_type() == model.ObjectType.ALBUM_FREE \
                or parent.obj.get_type().get_class() == model.ObjectClass.CLASSIFIER

        elif( self.obj.get_type() in [
                model.ObjectType.ALBUM_FORMAL,
                model.ObjectType.ALBUM_CLOSED
            ] ):

                assert parent.obj.get_type() in [
                            model.ObjectType.ALBUM_FREE,
                            model.ObjectType.ALBUM_FORMAL,
                        ] \
                    or parent.obj.get_type().get_class() == model.ObjectClass.CLASSIFIER

        elif( self.obj.get_type().get_class() == model.ObjectClass.FILE ):

            assert parent.obj.get_type() in [
                        model.ObjectType.ALBUM_FREE,
                        model.ObjectType.ALBUM_FORMAL,
                        model.ObjectType.FILE,
                        model.ObjectType.IMPORT_OPEN
                    ] \
                or parent.obj.get_type().get_class() == model.ObjectClass.CLASSIFIER

            # We can add duplicates to formal albums and imports
            if( self.obj.get_type() == model.ObjectType.DUPLICATE
             and parent.obj.get_type() not in [
                    model.ObjectType.ALBUM_FORMAL,
                    model.ObjectType.IMPORT_OPEN
                ] ):

                # Otherwise, we need to assign the original file
                return self.get_original_file().__assign(
                            parent, order, name,
                            is_duplicate )

        else:
            assert False

        # Orders and names are allowed only for albums and imports
        if( order is not None ):
            assert parent.obj.get_type().get_class() in [
                    model.ObjectClass.ALBUM,
                    model.ObjectClass.IMPORT
                ] or parent.obj.get_type() in [
                    model.ObjectType.CLASSIFIER_ORDERED
                ]

        # Names are allowed only for albums and imports
        if( name is not None ):
            assert parent.obj.get_type().get_class() in [
                    model.ObjectClass.ALBUM,
                    model.ObjectClass.IMPORT
                ]

        # Fetch an existing relation
        rels = [r for r in self.session.model.query( model.Relation ) \
                .filter( model.Relation.parent_id == parent.obj.object_id ) \
                .filter( model.Relation.child_id == self.obj.object_id )]

        # Loops aren't permitted, so reverse a relation if we get into that case
        rrels = [r for r in self.session.model.query( model.Relation ) \
                .filter( model.Relation.child_id == parent.obj.object_id ) \
                .filter( model.Relation.parent_id == self.obj.object_id )]

        assert rels == [] or rrels == []
        rel = None

        if( rrels != [] ):
            # Need to reverse the relationship
            assert len( rrels ) == 1
            rel = rrels[0]

            rel.parent_obj = parent.obj
            rel.child_obj = self.obj

        elif( rels != [] ):

            if( parent.obj.get_type() in [
                        model.ObjectType.ALBUM_FORMAL,
                        model.ObjectType.IMPORT_OPEN,
                    ] ):

                # Poly linking allowed, though see if we're being sloted to
                # an existing position
                for r in rels:
                    if( r.sort == order ):
                        rel = r
                        break

                # Otherwise leave null to add another instance

            else:
                # Poly linking not allowed
                assert len( rels ) == 1
                rel = rels[0]

        if( is_duplicate is not None ):
            # Duplicates are allowed only on files
            assert parent.obj.get_type() == model.ObjectType.FILE

            if( is_duplicate ):
                self.__assign_duplicate( parent, rel )

        if( rel is None ):
            # Make sure we have a unique instance number for poly linking
            instance = 0
            for r in rels:
                instance = max( instance, r.instance + 1 )

            rel = model.Relation()
            rel.parent_obj = parent.obj
            rel.child_obj = self.obj
            rel.instance = instance
            self.session.model.add( rel )

        if( order is not None ):
            rel.sort = order
        if( name is not None ):
            rel.child_name = name

    @SessionObject._with_access( write = True )
    def assign( self, parent,
                order = None,
                name = None,
                is_duplicate = None ):

        self.__assign( parent, order, name, is_duplicate )
        parent._on_children_changed()

    def __unassign( self, parent: 'Obj' ):

        assert parent.obj.get_type() != model.ObjectType.ALBUM_CLOSED

        rel = self.session.model.query( model.Relation ) \
                .filter( model.Relation.parent_id == parent.obj.object_id ) \
                .filter( model.Relation.child_id == self.obj.object_id ).first()

        if( rel is not None ):
            self.session.model.delete( rel )

            if( self.obj.get_type() == model.ObjectType.DUPLICATE
            and parent.obj.get_type() == model.ObjectType.FILE ):

                # We're no longer a duplicate
                self.obj.set_type( model.ObjectType.FILE )

    @SessionObject._with_access( write = True )
    def unassign( self, parent ):

        self.__unassign( parent )
        parent._on_children_changed()

    @SessionObject._with_access( write = True )
    def reorder( self, group: 'hdbfs.OrderedGroup', order = None ):

        assert group.obj.get_type() in [
                model.ObjectType.ALBUM_FREE,
                model.ObjectType.ALBUM_FORMAL,
                model.ObjectType.CLASSIFIER_ORDERED
            ]

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
    def get_name( self, group = None, index = None ) -> Optional[str]:

        if( group is not None ):
            q = self.session.model.query( model.Relation ) \
                    .filter( model.Relation.parent_id == group.obj.object_id ) \
                    .filter( model.Relation.child_id == self.obj.object_id )
            if( index is not None ):
                q = q.filter( model.Relation.sort == index )
            rel = q.first()
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
    def get_metadata( self ) -> Dict[ str, Union[ str, int ] ]:

        return dict( self.obj.metadata_items() )

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
