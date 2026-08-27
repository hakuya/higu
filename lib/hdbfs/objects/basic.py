import datetime

import hdbfs.ark
import hdbfs.model as model

from hdbfs.session import Session, SessionObject
from hdbfs.defs import *
from hdbfs.hash import calculate_details

from typing import Optional, List, Union, Dict, Any, BinaryIO

ObjectTypeSelect = Union[ ObjectType, ObjectClass, List[ObjectType], List[ObjectClass] ]

class Stream( SessionObject ):
    """ Represents a data stream in the database.

    A Stream contains the actual file data (bytes) for files in the database.
    Each File object has one or more streams - typically a root stream for the
    original data, and additional streams for thumbnails or transformed versions.

    Streams are content-addressable by their hash values. Multiple files can
    share the same stream if they have identical content (deduplication).

    Attributes:
        stream: The underlying model.Stream database object
    """

    def __init__( self, session: Session, stream: model.Stream ):

        super().__init__( session )
        self.stream = stream

    @SessionObject._with_access()
    def get_file( self ) -> 'hdbfs.File':
        """ Get the file object that owns this stream.

        Returns:
            The File object this stream belongs to
        """

        return self.session._construct_session_object( self.stream.obj )

    @SessionObject._with_access()
    def get_stream_id( self ) -> int:
        """ Get the unique stream identifier.

        Returns:
            The stream ID
        """

        return self.stream.stream_id

    @SessionObject._with_access()
    def get_name( self ) -> str:
        """ Get the stream name.

        Stream names identify the purpose/type of the stream, such as
        '.' for root stream, 'thumb.256' for thumbnails, etc.

        Returns:
            The stream name
        """

        return self.stream.name

    @SessionObject._with_access()
    def get_priority( self ) -> int:
        """ Get the stream priority level.

        Priority determines whether a stream can be automatically deleted
        to save space (e.g., thumbnails vs. original files).

        Returns:
            The priority value (StreamPriority enum value)
        """

        return self.stream.priority

    @SessionObject._with_access()
    def get_add_timestamp( self ) -> int:
        """ Get the Unix timestamp when this stream was added.

        Returns:
            Unix timestamp (seconds since epoch)
        """

        create_log = self.stream.log_entries \
                        .order_by( model.StreamLog.timestamp ).first()
        return create_log.timestamp

    def get_add_time( self ) -> datetime.datetime:
        """ Get the datetime when this stream was added (local time).

        Returns:
            Datetime object in local timezone
        """

        return datetime.datetime.fromtimestamp( self.get_add_timestamp() )

    def get_add_time_utc( self ) -> datetime.datetime:
        """ Get the datetime when this stream was added (UTC).

        Returns:
            Datetime object in UTC timezone
        """

        return datetime.datetime.fromtimestamp(
                    self.get_add_timestamp(),
                    datetime.timezone.utc )

    @SessionObject._with_access()
    def get_origin_stream( self ) -> Optional['Stream']:
        """ Get the stream this was derived from, if any.

        For transformed streams (thumbnails, conversions), returns the
        source stream. For root streams, returns None.

        Returns:
            The origin Stream object, or None
        """

        if( self.stream.origin_stream is not None ):
            return self.session._construct_session_object(
                        self.stream.origin_stream )
        else:
            return None

    @SessionObject._with_access()
    def get_origin_method( self ) -> Optional[str]:
        """ Get the method used to create this stream.

        Returns:
            Method name string (e.g., 'thumbnail', 'convert'), or None
        """

        create_log = self.stream.log_entries \
                        .order_by( model.StreamLog.timestamp ).first()
        return create_log.origin_method

    @SessionObject._with_access()
    def get_length( self ) -> int:
        """ Get the stream data size in bytes.

        Returns:
            Size in bytes
        """

        return self.stream.stream_length

    @SessionObject._with_access()
    def get_hash( self ) -> str:
        """ Get the SHA-1 hash of the stream data.

        Returns:
            SHA-1 hash as hex string
        """

        return self.stream.hash_sha1

    @SessionObject._with_access()
    def get_extension( self ) -> str:
        """ Get the file extension for this stream.

        Returns:
            File extension including leading dot (e.g., '.jpg')
        """

        return self.stream.extension

    @SessionObject._with_access()
    def get_mime( self ) -> str:
        """ Get the MIME type of the stream data.

        Returns:
            MIME type string (e.g., 'image/jpeg')
        """

        return self.stream.mime_type

    @SessionObject._with_access()
    def open( self ) -> BinaryIO:
        """ Open a file handle to read the stream data.

        Returns:
            Binary file-like object for reading stream contents
        """

        return self.session.imgdb.open(
                        self.stream.stream_id,
                        self.stream.priority,
                        self.stream.extension  )

    @SessionObject._with_access()
    def verify( self ) -> bool:
        """ Verify the stream data integrity using stored hashes.

        Reads the stream data and recalculates all hashes (CRC32, MD5, SHA-1)
        and length, comparing them against stored values.

        Returns:
            True if all checks pass, False if any mismatch or data unavailable
        """

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

    def _drop_data( self ) -> None:
        """ Delete the physical stream data from storage.

        Internal method - removes the actual file data while keeping
        the database record.
        """

        self.session.imgdb.delete(
                self.stream.stream_id,
                self.stream.priority,
                self.stream.extension  )

    def get_repr( self ) -> str:
        """ Get the string representation of this stream.

        Returns:
            String representation
        """

        return str( self )

    def __str__( self ) -> str:
        """ Get the string representation as 'file:stream_name'.

        Returns:
            String in format 'file:stream_name'
        """

        return f'{self.get_file()!s}:{self.get_name()}'

    def __repr__( self ) -> str:
        """ Get detailed string representation for debugging.

        Returns:
            String with stream name, ID, object ID, and MIME type
        """

        name = self.get_name()
        id = self.get_stream_id()
        obj = self.stream.object_id
        mime = self.stream.mime_type

        return f'Stream( {name}, {id=}, {obj=}, {mime=} )'

    @SessionObject._with_access()
    def __getitem__( self, key: str ) -> Any:
        """ Access stream database fields by key.

        Args:
            key: Database field name

        Returns:
            Field value
        """

        return self.stream[key]

    @SessionObject._with_access( write = True )
    def __setitem__( self, key: str, value: Any ) -> None:
        """ Set stream database fields by key.

        Args:
            key: Database field name
            value: Value to set
        """

        self.stream[key] = value

    def __eq__( self, o: Any ) -> bool:
        """ Check equality with another Stream object.

        Args:
            o: Object to compare with

        Returns:
            True if same session and stream record
        """

        if( o == None ):
            return False
        if( not isinstance( o, self.__class__ ) ):
            return False
        return self.session == o.session \
           and self.stream == o.stream

class Obj( SessionObject ):
    """ Represents a database object (file, album, tag, import, etc).

    Obj is the base class for most entities in the database. Objects are
    organized in a hierarchical graph structure through parent-child
    relationships. The object type (ObjectType enum) determines what kind
    of entity it represents and what relationships are valid.

    Common object types:
    - FILE: Regular files and DUPLICATE (deduplicated files)
    - ALBUM_FREE, ALBUM_FORMAL, ALBUM_CLOSED: Different album types
    - CLASSIFIER_*: Tags and other classifiers
    - IMPORT_*: Import batches

    Objects can have:
    - Parent-child relationships (e.g., files in albums, albums in albums)
    - Names (either intrinsic or per-relationship)
    - Metadata key-value pairs
    - Order within ordered parents (albums, imports)

    Attributes:
        obj: The underlying model.Object database object
    """

    def __init__( self, session: Session, obj: model.Object ):

        super().__init__( session )
        self.obj = obj

    def _on_created( self, stream: Stream ) -> None:
        """ Hook called when a new stream is created for this object.

        Override in subclasses to perform actions when streams are added.

        Args:
            stream: The newly created Stream object
        """

        pass

    def _on_children_changed( self ) -> None:
        """ Hook called when child relationships change.

        Override in subclasses to perform actions when children are
        added or removed.
        """

        pass

    @SessionObject._with_access()
    def get_id( self ) -> int:
        """ Get the unique object identifier.

        Returns:
            The object ID
        """

        return self.obj.object_id

    @SessionObject._with_access()
    def get_type( self ) -> ObjectType:
        """ Get the object type.

        Returns:
            ObjectType enum value (FILE, ALBUM_FREE, etc.)
        """

        return self.obj.get_type()

    def __build_obj_type_values( self, obj_type: ObjectTypeSelect ) -> List[int]:
        """ Convert ObjectType/ObjectClass to list of type values.

        Internal helper that handles both single types and lists, and
        expands ObjectClass to all its member ObjectType values.

        Args:
            obj_type: Single or list of ObjectType/ObjectClass

        Returns:
            List of ObjectType integer values
        """

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
        """ Get parent objects of specified type(s).

        Args:
            obj_type: ObjectType, ObjectClass, or list of either
            limit: Maximum number of parents to return

        Returns:
            List of parent Obj objects matching the type filter
        """

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
        """ Get child objects of specified type(s).

        Args:
            obj_type: ObjectType, ObjectClass, or list of either
            limit: Maximum number of children to return

        Returns:
            List of child Obj objects matching the type filter
        """

        obj_type_values = self.__build_obj_type_values( obj_type )

        objs = [ obj for obj in self.obj.children if obj.object_type in obj_type_values ]
        if( limit is not None and len( objs ) > limit ):
            objs = objs[:limit]
        return list( map( lambda x: self.session._construct_session_object( x ), objs ) )

    @SessionObject._with_access()
    def get_add_timestamp( self, group: Optional['Obj'] = None ) -> int:
        """ Get the Unix timestamp when this object was added.

        Args:
            group: If provided, get timestamp for when added to this group

        Returns:
            Unix timestamp (seconds since epoch)
        """

        if( group is not None ):
            rel = self.session.model.query( model.Relation ) \
                    .filter( model.Relation.parent_id == group.obj.object_id ) \
                    .filter( model.Relation.child_id == self.obj.object_id ).first()
            assert rel is not None
            return rel.add_ts

        return self.obj.add_ts

    def get_add_time( self, group: Optional['Obj'] = None ) -> datetime.datetime:
        """ Get the datetime when this object was added (local time).

        Args:
            group: If provided, get time for when added to this group

        Returns:
            Datetime object in local timezone
        """

        return datetime.datetime.fromtimestamp( self.get_add_timestamp( group ) )

    def get_add_time_utc( self, group: Optional['Obj'] = None ) -> datetime.datetime:
        """ Get the datetime when this object was added (UTC).

        Args:
            group: If provided, get time for when added to this group

        Returns:
            Datetime object in UTC timezone
        """

        return datetime.datetime.fromtimestamp(
                    self.get_add_timestamp( group ),
                    datetime.timezone.utc )

    def get_member_of( self ) -> List['hdbfs.Album']:
        """ Get all albums this object belongs to.

        Returns:
            List of Album objects
        """

        return self.get_parents( model.ObjectClass.ALBUM )

    @SessionObject._with_access()
    def get_tags( self ) -> List['hdbfs.Tag']:
        """ Get all tags (classifiers) applied to this object.

        Returns:
            List of Tag objects, sorted by name
        """

        from sqlalchemy import and_

        tag_objs = [
            obj for obj in
            self.session.model.query( model.Object )
                .filter(
                    and_( model.Object.object_type.in_( model.ObjectClass.CLASSIFIER.all_type_values() ),
                            model.Object.children.contains( self.obj ) ) )
                            .order_by( model.Object.name ) ]
        return list( map( lambda x: self.session._construct_session_object( x ), tag_objs ) )

    def has_tag( self, tag: Union['hdbfs.Tag', str] ) -> bool:
        """ Check if this object has a specific tag.

        Args:
            tag: Tag object or tag name string

        Returns:
            True if the tag is applied to this object
        """

        tags = self.get_tags()

        if( tag in tags ):
            return True

        for t in tags:
            if( tag == t.obj.name ):
                return True
        else:
            return False

    def __assign_duplicate( self, parent: 'Obj', rel: Optional[model.Relation] ) -> None:
        """ Mark this object as a duplicate of parent and migrate relationships.

        Internal method that handles the complex logic of converting a file
        to a duplicate. Moves non-conflicting relationships to the parent
        file and drops relationships that conflict or are with formal albums.

        Args:
            parent: The original file this is a duplicate of
            rel: Existing relation object, if any
        """

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

    def __assign( self, parent: 'Obj', order: Optional[int], name: Optional[str], is_duplicate: Optional[bool] ) -> None:
        """ Create or update parent-child relationship.

        Internal method handling the complex logic of assigning this object
        to a parent. Validates type compatibility, handles ordering, naming,
        poly-linking, relation reversal, and duplicate marking.

        Args:
            parent: The parent object to assign to
            order: Sort order within parent (for ordered relations)
            name: Override name within this relationship
            is_duplicate: If True and parent is FILE, mark as duplicate
        """

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
        is_ordered_relation = model.is_relation_ordered( parent.get_type(), self.get_type() )
        assert order is None or is_ordered_relation

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
            rel.sort = None

        elif( rels != [] ):

            if( model.is_poly_linking_permitted( parent.get_type(), self.get_type() ) ):
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

        if( (rel is None or rel.sort is None)
                and order is None and is_ordered_relation ):
            # Make sure we have a unique order if we're ordered
            from sqlalchemy import func

            order = self.session.model.query( func.max( model.Relation.sort ) ) \
                        .filter( model.Relation.parent_id == parent.obj.object_id ) \
                        .scalar()
            if( order is not None ):
                order += 1
            else:
                order = 0

        if( rel is not None ):
            # We have an existing relationship

            if( order is not None ):
                # Update the order if requested
                rel.sort = order

        else:
            # Make sure we have a unique instance number for poly linking
            instance = 0
            for r in rels:
                instance = max( instance, r.instance + 1 )

            rel = model.Relation()
            rel.parent_obj = parent.obj
            rel.child_obj = self.obj
            rel.instance = instance
            if( order is not None ):
                rel.sort = order
            self.session.model.add( rel )

        if( name is not None ):
            rel.child_name = name

    @SessionObject._with_access( write = True )
    def assign( self,
                parent: 'Obj',
                order: Optional[int] = None,
                name: Optional[str] = None,
                is_duplicate: Optional[bool] = None
            ) -> None:
        """ Assign this object as a child of parent.

        Creates or updates the parent-child relationship. The relationship
        semantics depend on the object types involved.

        Args:
            parent: Parent object to assign to (album, file, tag, etc.)
            order: Sort order for ordered relationships (albums, imports)
            name: Override name within this specific relationship
            is_duplicate: Mark as duplicate if parent is a FILE

        Example relationships:
        - File -> Album: Add file to album
        - Album -> Album: Nest album within album
        - File -> File: Mark first as duplicate of second (if is_duplicate=True)
        - File/Album -> Tag: Apply tag to file/album
        """

        self.__assign( parent, order, name, is_duplicate )
        parent._on_children_changed()

    def __unassign( self, parent: 'Obj' ) -> None:
        """ Remove parent-child relationship.

        Internal method that removes the relation and handles duplicate
        status changes.

        Args:
            parent: Parent object to unassign from
        """

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
    def unassign( self, parent: 'Obj' ) -> None:
        """ Remove this object from parent.

        Removes the parent-child relationship. If this was a duplicate
        file assigned to its original, it is promoted back to regular FILE.

        Args:
            parent: Parent object to remove from

        Raises:
            AssertionError: If parent is a closed album (cannot modify)
        """

        self.__unassign( parent )
        parent._on_children_changed()

    @SessionObject._with_access( write = True )
    def reorder( self, group: 'hdbfs.OrderedGroup', order: Optional[int] = None ) -> None:
        """ Change the sort order of this object within an ordered group.

        Args:
            group: The ordered group (album or ordered classifier)
            order: New sort order, or None to unset

        Raises:
            ValueError: If this object is not in the group
            AssertionError: If group type doesn't support ordering
        """

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
    def get_order( self, group: 'Obj' ) -> Optional[int]:
        """ Get the sort order of this object within a group.

        Args:
            group: The ordered group to check

        Returns:
            The sort order value, or None if unordered

        Raises:
            ValueError: If this object is not in the group
        """

        rel = self.session.model.query( model.Relation ) \
                .filter( model.Relation.parent_id == group.obj.object_id ) \
                .filter( model.Relation.child_id == self.obj.object_id ).first()
        if( rel is None ):
            raise ValueError( f'{self!s} is not in {group!s}' )
        return rel.sort

    @SessionObject._with_access()
    def get_name( self, group: Optional['Obj'] = None, index: Optional[int] = None ) -> Optional[str]:
        """ Get the object's name.

        Names can be intrinsic to the object or overridden within specific
        parent relationships (albums, imports).

        Args:
            group: If provided, get the relationship-specific name
            index: For poly-linked objects, which instance to get name for

        Returns:
            The name string, or None if unnamed
        """

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
    def set_name( self, name: str, group: Optional['Obj'] = None ) -> None:
        """ Set the object's name.

        Can set either the intrinsic name or the relationship-specific name
        within a group.

        Args:
            name: New name string
            group: If provided, set name only within this relationship

        Raises:
            AssertionError: If classifier name conflicts with existing tag
            ValueError: If group provided but object not in that group
        """

        from sqlalchemy import and_

        if( self.get_type().get_class() == model.ObjectClass.CLASSIFIER ):
            # Tags are not permitted to have duplicate names
            assert self.session.model.query( model.Object.object_id ) \
                .filter( and_(
                    model.Object.name == name,
                    model.Object.object_type.in_( model.ObjectClass.CLASSIFIER.all_type_values() )
                ) ).first() is None

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

    def set_text( self, text: str ) -> None:
        """ Set the 'text' metadata field.

        Args:
            text: Text content to store
        """

        self['text'] = text

    def get_text( self ) -> Optional[str]:
        """ Get the 'text' metadata field.

        Returns:
            Text content, or None if not set
        """

        try:
            return self['text']
        except KeyError:
            return None

    def get_repr( self, group: Optional['Obj'] = None ) -> str:
        """ Get a string representation (name or hex ID).

        Args:
            group: If provided, use relationship-specific name

        Returns:
            Name if available, otherwise hex object ID
        """

        name = self.get_name( group )
        if( name is not None ):
            return name
        else:
            return '%016x' % ( self.get_id() )

    def __str__( self ) -> str:
        """ Get string representation (name or hex ID).

        Returns:
            Name if available, otherwise hex object ID
        """

        name = self.get_name()
        if( name is not None ):
            return name
        else:
            return '%016x' % ( self.get_id() )

    def __repr__( self ) -> str:
        """ Get detailed string representation for debugging.

        Returns:
            String with object ID and name (if available)
        """

        id = self.obj.object_id
        name = self.get_name()

        if( name is None ):
            return f'Object( {id=} )'
        else:
            return f'Object( "{name}", {id=} )'

    @SessionObject._with_access()
    def get_metadata( self ) -> Dict[ str, Union[ str, int ] ]:
        """ Get all metadata key-value pairs.

        Returns:
            Dictionary of metadata entries
        """

        return dict( self.obj.metadata_items() )

    @SessionObject._with_access()
    def __getitem__( self, key: str ) -> Any:
        """ Access metadata by key.

        Args:
            key: Metadata field name

        Returns:
            Field value

        Raises:
            KeyError: If key doesn't exist
        """

        return self.obj[key]

    @SessionObject._with_access( write = True )
    def __setitem__( self, key: str, value: Any ) -> None:
        """ Set metadata by key.

        Args:
            key: Metadata field name
            value: Value to set
        """

        self.obj[key] = value

    def __hash__( self ) -> int:
        """ Get hash value (uses object ID).

        Returns:
            Object ID as hash
        """

        return self.get_id()

    def __eq__( self, o: Any ) -> bool:
        """ Check equality with another Obj object.

        Args:
            o: Object to compare with

        Returns:
            True if same session and database object
        """

        if( o == None ):
            return False
        if( not isinstance( o, self.__class__ ) ):
            return False
        return self.session == o.session and self.obj == o.obj
