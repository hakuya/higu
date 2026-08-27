""" Album management interface for the database.

This module provides the Albums_interface class which handles creation,
querying, and management of albums in the database. Albums are containers
for organizing files and can be in different states (FREE, FORMAL, CLOSED).

Album states:
- FREE: Can contain files, auto-deduplicates
- FORMAL: Can contain files and explicitly store duplicates
- CLOSED: Immutable, cannot be modified

The interface is typically accessed through Database.albums.
"""

from hdbfs.session import \
        Session, \
        SessionObject

from hdbfs.objects.album import Album
from hdbfs.objects.importobj import Import
from hdbfs.objects.file import File

import hdbfs.model as model

from hdbfs.model import ObjectType

from typing import List, Optional

class Albums_interface( SessionObject ):
    """ Interface for managing albums in the database.

    Provides methods for creating, querying, and managing albums. Albums are
    containers for organizing files with different organizational models
    (FREE for flexible collections, FORMAL for explicit ordering, CLOSED
    for immutable archives).

    This interface is typically accessed via Database.albums rather than
    being instantiated directly.

    Attributes:
        session: The database session this interface operates on
    """

    def __init__( self, session: Session ):
        """ Initialize the albums interface.

        Args:
            session: Database session to use for album operations
        """

        self.session = session

    @SessionObject._with_access( write = True )
    def create( self,
                tags: List = [],
                name: Optional[str] = None,
                text: Optional[str] = None
            ) -> Album:
        """ Create a new FREE album.

        Creates an empty FREE album with the specified metadata. FREE albums
        automatically deduplicate files - each file can only appear once.

        Args:
            tags: List of tags to assign to the album
            name: Optional name for the album
            text: Optional description text for the album

        Returns:
            The newly created Album object

        Example:
            >>> album = db.albums.create(
            ...     tags=[vacation_tag],
            ...     name='Summer Trip',
            ...     text='Photos from our vacation'
            ... )
        """

        model_album = model.Object( model.ObjectType.ALBUM_FREE )
        self.session.model.add( model_album )

        album = self.session._construct_session_object( model_album )
        assert isinstance( album, Album )

        if( name is not None ):
            album.obj.name = name

        if( text is not None ):
            album.obj['text'] = text

        for t in tags:
            album.assign( t, None )

        return album

    @SessionObject._with_access( write = True )
    def create_from_files( self,
                from_files: List[File],
                tags: List = [],
                name: Optional[str] = None,
                text: Optional[str] = None,
                alb_type: ObjectType = ObjectType.ALBUM_FREE
            ) -> Album:
        """ Create an album from a list of files.

        Creates an album and adds the specified files to it. Can create
        FREE (auto-deduplicating), FORMAL (allows duplicate file references),
        or CLOSED (immutable) albums.

        Args:
            from_files: List of File objects to include in the album
            tags: List of tags to assign to the album
            name: Optional name for the album
            text: Optional description text for the album
            alb_type: Album type (FREE, FORMAL, or CLOSED)

        Returns:
            The newly created Album object with files added

        Raises:
            AssertionError: If alb_type is not a valid album type

        Example:
            >>> files = [db.get_object_by_id(123), db.get_object_by_id(456)]
            >>> album = db.albums.create_from_files(
            ...     files,
            ...     name='Selection',
            ...     alb_type=ObjectType.ALBUM_CLOSED
            ... )
        """

        assert alb_type in [
                ObjectType.ALBUM_FREE,
                ObjectType.ALBUM_FORMAL,
                ObjectType.ALBUM_CLOSED
            ]

        album = self.create( tags, name, text )

        if( alb_type in [ ObjectType.ALBUM_FORMAL, ObjectType.ALBUM_CLOSED ] ):
            album.make_formal_album()
        for it, f in enumerate( from_files ):
            f.assign( album, it, f.get_name() )
        if( alb_type == ObjectType.ALBUM_CLOSED ):
            album.close_album()

        return album

    @SessionObject._with_access( write = True )
    def create_from_import( self,
                from_import: Import,
                tags: List = [],
                name: Optional[str] = None,
                text: Optional[str] = None,
            ) -> Album:
        """ Create a CLOSED album from an import session.

        Converts an import into a closed album containing all the imported
        files. The import must be in CLOSED state. This is the typical way
        to finalize a batch import into an album.

        Args:
            from_import: The Import object to convert to an album
            tags: List of tags to assign to the album
            name: Optional name for the album (defaults to import name)
            text: Optional description text for the album

        Returns:
            The newly created CLOSED Album object

        Raises:
            AssertionError: If import is not in CLOSED state

        Example:
            >>> imp = db.start_import(name='New Photos')
            >>> # ... add files to import ...
            >>> imp.close_import()
            >>> album = db.albums.create_from_import(
            ...     imp,
            ...     tags=[vacation_tag],
            ...     name='Beach Photos'
            ... )
        """

        if( name is None ):
            name = from_import.get_name()
        if( text is None ):
            text = from_import['text']

        album = self.create( tags, name, text )

        album.make_formal_album()
        for it, f in enumerate( from_import.get_files() ):
            f.assign( album, it, f.get_name( from_import, it ) )
        album.close_album()

        return album

    @SessionObject._with_access( write = True )
    def partition( self,
                album: Album,
                files: List[File]
            ) -> Album:
        """ Create a partition from files in an album.

        Extracts a subset of files from an album into a new album (partition).
        The files are removed from the original album and placed in the new
        partition, which is then added to the original album as a sub-album.
        This preserves the hierarchical structure.

        The partition inherits the album type (FREE or FORMAL) from the
        original album.

        Args:
            album: The source album (must not be CLOSED)
            files: List of files to extract into the partition (must all
                be in the source album)

        Returns:
            The newly created partition Album

        Raises:
            AssertionError: If album is CLOSED, or if any file is not in album

        Example:
            >>> album = db.get_object_by_id(123)
            >>> files_to_group = [album.get_files()[0], album.get_files()[1]]
            >>> partition = db.albums.partition(album, files_to_group)
            # Creates sub-album within album containing those files
        """

        album_files = album.get_files()
        album_type = album.get_type()
        order = None

        assert album_type != ObjectType.ALBUM_CLOSED

        # All the files in the partition must be in the album
        for f in files:
            assert f in album_files

            f_order = f.get_order( album )
            if( order is None
                or (f_order is not None and f_order < order) ):

                order = f_order

        part = self.create()

        if( album_type == ObjectType.ALBUM_FORMAL ):
            part.make_formal_album()

        # Assign to the partition, preserving the local name
        for it, f in enumerate( files ):
            f.assign( part, it, f.get_name( album, it ) )

        # Now remove the files from the album
        for f in files:
            f.unassign( album )

        # And add the partition in
        part.assign( album, order = order )

        return part

