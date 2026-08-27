from hdbfs.objects.basic import Obj, Stream
from hdbfs.session import Session, SessionObject

import hdbfs.model as model

from typing import List, Optional

class File( Obj ):
    """ Represents a file object in the database.

    File objects contain one or more Streams (data blobs). Each file has a
    root stream containing the original file data, and may have additional
    streams for thumbnails or other derived versions.

    Files can be related to each other as:
    - Variants: Different versions of the same file (edits, conversions)
    - Duplicates: Identical files that are deduplicated by hash
    - Original: The original file that duplicates reference

    Files belong to:
    - Albums: User-organized collections
    - Imports: Batch import operations
    - Tags: Classification/categorization

    Attributes:
        obj: The underlying model.Object database record
    """

    def __init__( self, session: Session, obj: model.Object ):

        super().__init__( session, obj )

    def get_imports( self ) -> List['Import']:
        """ Get all import batches this file belongs to.

        Returns:
            List of Import objects
        """

        return self.get_parents( model.ObjectClass.IMPORT )

    def get_variants_of( self ) -> List['File']:
        """ Get files that this file is a variant of.

        Variants are related versions (e.g., edited, converted, resized).
        Only regular FILE type objects can be variants; duplicates cannot.

        Returns:
            List of parent File objects, or empty list if this is a duplicate
        """

        if( self.obj.get_type() == model.ObjectType.FILE ):
            return self.get_parents( model.ObjectType.FILE )
        else:
            return []

    def get_variants( self ) -> List['File']:
        """ Get all variant files derived from this file.

        Returns:
            List of child File objects that are variants
        """

        return self.get_children( model.ObjectType.FILE )

    def get_original_file( self ) -> Optional['File']:
        """ Get the original file if this is a duplicate.

        Returns:
            The original File object if this is a duplicate, None otherwise
        """

        if( self.obj.get_type() == model.ObjectType.DUPLICATE ):
            # Only one duplicate parent is permitted
            return self.get_parents( model.ObjectType.FILE )[0]
        else:
            return None

    def get_duplicates( self ) -> List['File']:
        """ Get all duplicate files that reference this original.

        Returns:
            List of File objects marked as duplicates of this file
        """

        return self.get_children( model.ObjectType.DUPLICATE )

    @SessionObject._with_access()
    def get_origin_names( self ) -> List[str]:
        """ Get all original filenames from when this file was imported.

        A file may have been imported multiple times with different names.
        This returns all distinct origin names from the import history.

        Returns:
            List of original filename strings
        """

        from sqlalchemy import and_

        return [ log.origin_name for log in
            self.session.model.query( model.StreamLog.origin_name )
                .filter( and_( model.StreamLog.stream_id == self.obj.root_stream.stream_id,
                                model.StreamLog.origin_name != None ) )
                .distinct() ]

    def get_repr( self, group: Optional['Obj'] = None ) -> str:
        """ Get string representation of this file.

        Returns the file's name if it has one, otherwise returns a hex
        identifier based on object ID and file extension.

        Args:
            group: If provided, get the relationship-specific name

        Returns:
            Name string or hex ID (with extension if available)
        """

        name = self.get_name( group )
        if( name is not None ):
            return name
        else:
            with self.session._access():
                obj_id = self.obj.object_id
                stream_id = self.obj.root_stream.stream_id
                priority = self.obj.root_stream.priority
                extension = self.obj.root_stream.extension

            if( extension == None ):
                return '%016x' % ( obj_id, )
            else:
                return '%016x.%s' % ( obj_id, extension, )

    def _get_stream( self, name: str ) -> Optional[Stream]:
        """ Get a stream by name (internal, no access check).

        Args:
            name: Stream name (e.g., '.', 'thumb.256')

        Returns:
            Stream object if found, None otherwise
        """

        s = self.obj.streams \
                .filter( model.Stream.name == name ) \
                .first()

        if( s is not None ):
            return self.session._construct_session_object( s )
        else:
            return None

    @SessionObject._with_access()
    def get_stream( self, name: str ) -> Optional[Stream]:
        """ Get a stream by name.

        Args:
            name: Stream name (e.g., '.', 'thumb.256')

        Returns:
            Stream object if found, None otherwise
        """

        return self._get_stream( name )

    def _list_streams( self ) -> List[str]:
        """ List all stream names for this file (internal, no access check).

        Returns:
            List of stream name strings, ordered by stream ID
        """

        return [ rs[0] for rs in
            self.session.model.query( model.Stream.name )
                .filter( model.Stream.object_id == self.obj.object_id )
                .order_by( model.Stream.stream_id ) ]

    @SessionObject._with_access()
    def list_streams( self ) -> List[str]:
        """ List all stream names for this file.

        Returns:
            List of stream name strings, ordered by stream ID
        """

        return self._list_streams()

    def _get_streams( self ) -> List[Stream]:
        """ Get all streams for this file (internal, no access check).

        Returns:
            List of Stream objects, ordered by stream ID
        """

        return [ self.session._construct_session_object( s ) for s in
            self.session.model.query( model.Stream )
                .filter( model.Stream.object_id == self.obj.object_id )
                .order_by( model.Stream.stream_id ) ]

    @SessionObject._with_access()
    def get_streams( self ) -> List[Stream]:
        """ Get all streams for this file.

        Returns:
            List of Stream objects, ordered by stream ID
        """

        return self._get_streams()

    def _drop_streams( self ) -> None:
        """ Delete all streams and their data for this file (internal).

        Removes the physical file data and all database records for streams,
        stream metadata, and stream logs. This is a destructive operation.
        """

        for s in self._get_streams():
            s._drop_data()

            self.session.model.query( model.StreamMetadata ) \
                .filter( model.StreamMetadata.stream_id == s.stream.stream_id ) \
                .delete()

            self.session.model.query( model.StreamLog ) \
                .filter( model.StreamLog.stream_id == s.stream.stream_id ) \
                .delete()

        self.session.model.query( model.Stream ) \
            .filter( model.Stream.object_id == self.obj.object_id ) \
            .delete()

    def _drop_expendable_streams( self ) -> None:
        """ Delete low-priority streams to save space (internal).

        Removes streams with priority below NORMAL (e.g., thumbnails, cached
        conversions). The root stream and other important data are preserved.
        This is used for cleanup and space management.
        """

        for s in self.session.model.query( model.Stream ) \
                     .filter( model.Stream.object_id == self.obj.object_id ) \
                     .filter( model.Stream.priority < model.StreamPriority.NORMAL.value ):

            stream = self.session._construct_session_object( s )
            stream._drop_data()

            self.session.model.query( model.StreamMetadata ) \
                .filter( model.StreamMetadata.stream_id == s.stream_id ) \
                .delete()

            self.session.model.query( model.StreamLog ) \
                .filter( model.StreamLog.stream_id == s.stream_id ) \
                .delete()

        self.session.model.query( model.Stream ) \
            .filter( model.Stream.object_id == self.obj.object_id ) \
            .filter( model.Stream.priority < model.StreamPriority.NORMAL.value ) \
            .delete()

    @SessionObject._with_access( write = True )
    def drop_expendable_streams( self ) -> None:
        """ Delete low-priority streams to save space.

        Public method to remove expendable streams (thumbnails, cached data).
        Requires write access.
        """

        self._drop_expendable_streams()

    @SessionObject._with_access()
    def get_root_stream( self ) -> Stream:
        """ Get the root stream containing the original file data.

        Every file has exactly one root stream (named '.') which contains
        the original imported file data.

        Returns:
            The root Stream object
        """

        return self.session._construct_session_object( self.obj.root_stream )

    @SessionObject._with_access()
    def verify( self ) -> None:
        """ Verify integrity of all streams for this file.

        Checks that each stream's data matches its stored hashes and length.
        Useful for detecting data corruption or storage issues.

        Raises:
            May raise exceptions if stream data is corrupted or unavailable
        """

        for s in self._get_streams():
            s.verify()
