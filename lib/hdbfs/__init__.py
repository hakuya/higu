""" Core HDBFS database interface.

This module provides the main Database class for interacting with Higurashi's
content-addressable file storage system. The database manages:

- Content-addressable file storage with automatic deduplication
- Hierarchical tagging system
- Album organization (free, formal, and closed albums)
- Import tracking and metadata
- Transactional access control
- Thumbnail generation coordination

Key classes:
    Database: Primary interface for all database operations
    ThumbRequest: Thumbnail generation request descriptor

Key functions:
    check_tag_name: Validate tag name format
    compare_details: Compare two file detail tuples
    init: Initialize database from configuration
    dispose: Clean up database resources
"""

import os
import re

from hdbfs.hash import calculate_details

from hdbfs.objects.album import Album
from hdbfs.objects.importobj import Import
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

from hdbfs.albums import Albums_interface

from typing import \
        Optional, \
        NamedTuple, \
        List, \
        Dict, \
        Tuple

_LIBRARY = None

def check_tag_name( s: str ) -> None:
    """ Validates that a string is a valid tag name.

    Tag names must consist only of word characters (alphanumeric and underscore),
    hyphens, and colons. Colons are typically used for hierarchical tags like
    "category:subcategory".

    Args:
        s: The string to validate as a tag name

    Raises:
        ValueError: If the string contains invalid characters
    """

    if( re.match( r'^[\w\-_:]+$', s ) is None ):
        raise ValueError( f'"{s}" is not a valid tag name' )

class ThumbRequest( NamedTuple ):
    """ Represents a thumbnail generation request.

    Used by the thumbnail generation system to track which thumbnails need to
    be generated for which images. Contains the priority, specific thumbnail
    sizes requested, and the target image file.

    Attributes:
        prio: Priority level (ImageRequestPriority enum)
        exps: List of exponent values for thumbnail sizes (e.g., [8, 9, 10]
            for sizes 256, 512, 1024), or None if metadata needs initialization
        file: The ImageFile that needs thumbnails
    """
    prio: ImageRequestPriority
    exps: Optional[ List[int] ]
    file: ImageFile

class Database( Session ):
    """ Primary interface for interacting with the Higurashi database.

    The Database class provides all high-level operations for managing files,
    tags, albums, and queries. It handles content-addressable storage with
    automatic deduplication based on file hashes.

    The database uses a session-based access control system. Most operations
    require calling enable_write_access() first for write operations.

    Example:
        db = hdbfs.Database()
        db.enable_write_access()

        # Register a file
        f = db.register_file('/path/to/image.jpg')

        # Tag it
        tag = db.make_tag('vacation')
        f.assign(tag)

        # Commit changes
        db.close()

    Attributes:
        albums: Albums_interface for album operations
        tbcache: Thumbnail cache manager
    """

    def __init__( self ):
        """ Initialize a new database session.

        Connects to the library initialized by hdbfs.init() and sets up
        the session, thumbnail cache, and object factories.
        """
        global _LIBRARY

        super().__init__( ImageDbDataConfig( _LIBRARY ) )
        self.tbcache = imgdb.ThumbCache( self )

        imgdb.init_session( self, self.tbcache )
        init_basic_factories( self, self.tbcache )

        self.albums = Albums_interface( self )

    def _get_object_by_id( self, object_id: int ) -> Obj:

        obj = self.model.query( model.Object ) \
                  .filter( model.Object.object_id == object_id ) \
                  .first()
        if( obj is None ):
            return None

        return self._construct_session_object( obj )

    @Session._with_access()
    def get_object_by_id( self, object_id: int ) -> Obj:
        """ Get an object by its unique ID.

        Retrieves any object from the database by its object_id. The returned
        object will be the appropriate subclass (File, ImageFile, Album, Tag,
        Import, etc.) based on the object's type.

        Args:
            object_id: The unique object identifier

        Returns:
            The object, or None if not found
        """

        return self._get_object_by_id( object_id )

    @Session._with_access()
    def get_stream_by_id( self, stream_id: int ) -> Optional[Stream]:
        """ Get a stream by its unique ID.

        Retrieves a data stream (file contents) by its stream_id. Streams
        represent the actual data for files and thumbnails.

        Args:
            stream_id: The unique stream identifier

        Returns:
            The stream object, or None if not found
        """

        stream = self.model.query( model.Stream ) \
                        .filter( model.Stream.stream_id == stream_id ) \
                        .first()
        if( stream is None ):
            return None

        return self._construct_session_object( stream )

    def _lookup_streams_by_details( self,
                file_length: Optional[int] = None,
                hash_crc32: Optional[str] = None,
                hash_md5: Optional[str] = None,
                hash_sha1: Optional[str] = None
            ) -> List[Stream]:

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

    @Session._with_access()
    def get_stream_by_sha1( self, stream_sha1: str ) -> Optional[Stream]:
        """ Get a stream by its SHA-1 hash.

        Looks up a stream using its SHA-1 hash. Since SHA-1 should be unique,
        this will return at most one stream. This is useful for deduplication
        and finding existing files.

        Args:
            stream_sha1: The SHA-1 hash as a hexadecimal string

        Returns:
            The stream object, or None if not found

        Raises:
            AssertionError: If multiple streams with the same SHA-1 are found
                (indicates database corruption)
        """

        streams = self._lookup_streams_by_details( hash_sha1 = stream_sha1 )
        assert( len( streams ) < 2 )

        return streams[0] if( len( streams ) > 0 ) else None

    def get_object_by_sha1( self, stream_sha1: str ) -> Optional[Obj]:
        """ Get a file object by the SHA-1 hash of its stream.

        Convenience method that looks up a stream by SHA-1 hash and returns
        the file object that owns it. This is useful for finding if a file
        already exists in the database before importing.

        Args:
            stream_sha1: The SHA-1 hash as a hexadecimal string

        Returns:
            The file object, or None if not found
        """

        stream = self.get_stream_by_sha1( stream_sha1 )
        return stream.get_file() if( stream is not None ) else None

    def lookup_untagged_files( self ) -> List[File]:
        """ Find all files that have no tags assigned.

        Returns files that are not assigned to any tags (classifiers). This is
        useful for finding newly imported files that need to be organized.

        Returns:
            List of untagged file objects
        """

        return self.unowned_files()

    def _all_tags( self, scope: Optional[str] ) -> List[Tag]:

        from sqlalchemy import func, or_

        q = self.model.query( model.Object.name,
                              model.Object,
                              func.count( model.Relation.child_id ) ) \
                .join( model.Relation, model.Object.object_id == model.Relation.parent_id ) \
                .filter( model.Object.object_type.in_( model.ObjectClass.CLASSIFIER.all_type_values() ) )

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
    def all_tags( self, scope: Optional[str] = None ) -> Dict[ str, Tuple[Tag,int] ]:
        """ Get all tags with their usage counts.

        Returns a dictionary of all tags (classifiers) in the database, along
        with the count of how many objects are tagged with each tag. Optionally
        filters to a specific scope or namespace.

        Args:
            scope: Optional scope prefix to filter tags. For example, 'person'
                will return tags like 'person', 'person:alice', 'person:bob'.
                If None, returns all tags.

        Returns:
            Dictionary mapping tag name to tuple of (Tag object, usage count)

        Example:
            >>> tags = db.all_tags('category')
            >>> for name, (tag, count) in tags.items():
            ...     print(f"{name}: {count} items")
        """

        return self._all_tags( scope )

    def _get_tag( self, name: str, fuzzy: bool = False ) -> Tag:

        if( not fuzzy ):
            obj = self.model.query( model.Object ) \
                    .filter( model.Object.object_type.in_( model.ObjectClass.CLASSIFIER.all_type_values() ) ) \
                    .filter( model.Object.name == name ).first()

        else:
            obj = None

            patterns = [
                name,
                '*' + ':' + name,
                '*' + ':' + name + '*',
                '*' + name,
                '*' + name + '*'
            ]

            for name_s in patterns:

                name_sql = name_s.replace( '%', '[%]' ).replace( '*', '%' )

                q = self.model.query( model.Object ) \
                        .filter( model.Object.object_type.in_( model.ObjectClass.CLASSIFIER.all_type_values() ) ) \
                        .filter( model.Object.name.like( name_sql ) )
                r = [r for r in q]

                if( len( r ) == 1 ):
                    obj = r[0]
                    break;
                elif( len( r ) > 1 ):
                    raise KeyError( f'Tag name "{name}" is ambiguous' )

        if( obj is None ):
            raise KeyError( f'No such tag "{name}"' )

        return self._construct_session_object( obj )

    @Session._with_access()
    def get_tag( self, name: str, fuzzy: bool = False ) -> Tag:
        """ Get a tag by name with optional fuzzy matching.

        Retrieves a tag (classifier) by its exact name, or performs fuzzy
        substring matching if requested. Fuzzy matching will try several patterns
        in order of specificity until it finds exactly one match.

        Args:
            name: The tag name to search for
            fuzzy: If True, performs substring matching with patterns like:
                - Exact match first
                - "*:name" (as a suffix in a namespace)
                - "*:name*" (anywhere in a namespace)
                - "*name" (as a suffix)
                - "*name*" (anywhere)

        Returns:
            The Tag object

        Raises:
            KeyError: If no tag is found, or if fuzzy matching finds multiple
                matches (ambiguous)

        Example:
            >>> tag = db.get_tag('category:vacation')  # Exact match
            >>> tag = db.get_tag('vacation', fuzzy=True)  # Will find category:vacation
        """

        return self._get_tag( name, fuzzy )

    def _make_tag( self, name: str ) -> Tag:

        check_tag_name( name )
        try:
            return self._get_tag( name, False )
        except KeyError:
            obj = model.Object( model.ObjectType.CLASSIFIER_UNORDERED, name )
            self.model.add( obj )
            return self._construct_session_object( obj )

    @Session._with_access( write = True )
    def make_tag( self, name: str ) -> Tag:
        """ Create a new tag or return existing one.

        Creates a new unordered tag with the given name, or returns the existing
        tag if one with that name already exists. Tag names must be valid
        according to check_tag_name().

        Args:
            name: The tag name (must match pattern: [\\w\\-_:]+)

        Returns:
            The Tag object (newly created or existing)

        Raises:
            ValueError: If the tag name contains invalid characters

        Example:
            >>> tag = db.make_tag('person:alice')
            >>> file.assign(tag)
        """

        return self._make_tag( name )

    def delete_tag( self, tag: str ) -> None:
        """ Delete a tag and all tags in its scope.

        Deletes the specified tag and all tags that begin with the tag name
        followed by a colon (i.e., all tags in that namespace). The tag will
        be unassigned from all objects before deletion.

        Args:
            tag: Tag name or scope to delete (e.g., 'person' deletes 'person',
                'person:alice', 'person:bob', etc.)

        Example:
            >>> db.delete_tag('temp')  # Delete temporary tag
            >>> db.delete_tag('category')  # Delete all category:* tags
        """

        tags = self.all_tags( tag )
        for tag, count in tags.values():
            self.delete_object( tag )

    @Session._with_access( write = True )
    def move_tag( self, tag: str, target: str ) -> None:
        """ Move or rename a tag and all tags in its scope.

        Renames a tag by changing its name prefix. All tags that begin with
        the source tag name will have that prefix replaced with the target name.
        If a target tag already exists, the tags will be merged (duplicate
        assignments are removed, remaining assignments are moved).

        Args:
            tag: Source tag name or scope prefix
            target: Target tag name (must be valid tag name)

        Raises:
            ValueError: If target contains invalid characters

        Example:
            >>> db.move_tag('temp:vacation', 'trip:summer')
            # Changes 'temp:vacation' to 'trip:summer'
            >>> db.move_tag('old_category', 'category')
            # Changes all 'old_category:*' to 'category:*'
        """

        from sqlalchemy import and_

        check_tag_name( target )
        tags = self._all_tags( tag )

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
    def copy_tag( self, tag: str, target: str ) -> None:
        """ Copy a tag and all its assignments to a new name.

        Creates a new tag with all the same assignments as the source tag.
        The source tag remains unchanged. This is useful for creating tag
        aliases or reorganizing tag hierarchies.

        Args:
            tag: Source tag name
            target: Target tag name (must be valid tag name)

        Raises:
            ValueError: If target contains invalid characters
            KeyError: If source tag doesn't exist

        Example:
            >>> db.copy_tag('favorites', 'starred')
            # Creates 'starred' tag with same items as 'favorites'
        """

        check_tag_name( target )
        c = self._get_tag( tag, False ).obj

        try:
            d = self._get_tag( target, False ).obj
        except KeyError:
            d = model.Object( model.ObjectType.CLASSIFIER_UNORDERED, target )
            self.model.add( d )

        for rel in c.child_rel:
            rel_copy = model.Relation( rel.sort )
            rel_copy.parent_obj = d
            rel_copy.child_obj = rel.child_obj
            self.model.add( rel_copy )

    def __recover_file( self, path: str ) -> bool:

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
    def recover_files( self, files: List[str] ) -> None:
        """ Recover file data from filesystem paths.

        Attempts to restore file data for streams that exist in the database
        but have missing or corrupted data files. This is useful for disaster
        recovery when the streams directory was damaged but the database
        remained intact.

        Args:
            files: List of filesystem paths to recover

        Note:
            Files are matched by hash. If a file's hash doesn't match any
            stream in the database, it is silently ignored.

        Example:
            >>> db.recover_files(['/backup/image1.jpg', '/backup/image2.jpg'])
        """

        for f in files:
            if( not self.__recover_file( f ) ):
                #log.warn( '%s was not found in the db and was ignored', f )
                pass

    # ***Deprecated*** use albums.create directly
    def create_album( self,
                tags = [],
                name = None,
                text = None,
                from_import : Optional[hdbfs.Import] = None
            ) -> hdbfs.Album:
        """ Create a new album. DEPRECATED: Use db.albums.create() instead.

        Creates a new album, optionally from an import. This method is
        deprecated in favor of using the albums interface directly.

        Args:
            tags: List of tags to assign to the album
            name: Optional album name
            text: Optional album description
            from_import: If provided, creates album from import

        Returns:
            The newly created Album object

        Deprecated:
            Use db.albums.create() or db.albums.create_from_import() instead
        """

        if( from_import is not None ):
            return self.albums.create_from_import( from_import, tags, name, text )
        else:
            return self.albums.create( tags, name, text )

    @Session._with_access( write = True )
    def start_import( self, name = None, text = None ) -> hdbfs.Import:
        """ Start a new import session.

        Creates a new import object for tracking a batch of files being added
        to the library. Imports can be used to group related files and later
        convert them into albums.

        Args:
            name: Optional name for the import
            text: Optional description text

        Returns:
            A new Import object in open state

        Example:
            >>> imp = db.start_import(name='Summer Photos')
            >>> # ... register files and assign to imp ...
            >>> imp.close_import()
        """

        model_import = model.Object( model.ObjectType.IMPORT_OPEN )
        self.model.add( model_import )
        importobj = self._construct_session_object( model_import )

        if( name is not None ):
            importobj.obj.name = name

        if( text is not None ):
            importobj.obj['text'] = text

        return importobj

    @Session._with_access( write = True )
    def album_to_import( self, album: hdbfs.Album, duplicate = False ) -> hdbfs.Import:
        """ Convert a closed album to an import.

        Converts a closed album into an import object. If duplicate is True,
        creates a copy of the album structure before conversion; otherwise
        replaces the album with an import.

        Args:
            album: A closed album to convert
            duplicate: If True, creates a copy; if False, replaces the album

        Returns:
            The resulting Import object

        Raises:
            AssertionError: If album is not closed, or contains non-file items

        Example:
            >>> imp = db.album_to_import(album, duplicate=True)
            # Original album remains, creates import copy
        """

        assert album.get_type() == model.ObjectType.ALBUM_CLOSED

        import_obj = album.obj
        album_obj = model.Object( model.ObjectType.ALBUM_CLOSED, import_obj.name ) \
                        if( duplicate ) else None

        for c in import_obj.children:
            assert c.get_type().get_class() == model.ObjectClass.FILE

        if( album_obj is not None ):
            album_obj.add_ts = import_obj.add_ts
            self.model.add( album_obj )
            self.model.flush()

            assert album_obj.object_id is not None

            self.model.query( model.Relation ) \
                .filter( model.Relation.child_id == import_obj.object_id ) \
                .update( { 'child_id' : album_obj.object_id } )

            q = self.model.query( model.Relation ) \
                .filter( model.Relation.parent_id == import_obj.object_id )
            rs = [r for r in q]

            # Duplicate children
            for r in rs:
                dup = model.Relation()
                dup.parent_id = album_obj.object_id
                dup.child_id = r.child_id
                dup.child_name = r.child_name
                dup.sort = r.sort

                self.model.add( dup )

            q = self.model.query( model.ObjectMetadata ) \
                .filter( model.ObjectMetadata.object_id == import_obj.object_id )
            rs = [r for r in q]

            # Duplicate metadata
            for r in rs:
                meta = model.ObjectMetadata( r.key, r.value, r.numeric )
                meta.object_id = album_obj.object_id

                self.model.add( meta )

        else:
            self.model.query( model.Relation ) \
                .filter( model.Relation.child_id == import_obj.object_id ) \
                .delete()

        import_obj.set_type( model.ObjectType.IMPORT_CLOSED )
        self.model.flush()

        return self._construct_session_object( import_obj )

    def __register_file( self,
                path: str,
                name_policy: int,
                name: Optional[str] = None
            ) -> Tuple[File, Stream, bool]:

        import mimetypes

        if( name is None ):
            name = os.path.split( path )[1]

        ext = os.path.splitext( name )[1]
        assert len( ext ) > 0 and ext[0] == '.'
        ext = ext[1:]

        details = calculate_details( path )

        mime_type = mimetypes.guess_type( path, strict=False )[0]
        streams = self._lookup_streams_by_details( *details )
        new_stream = False

        if( len( streams ) == 0 ):
            obj = model.Object( model.ObjectType.FILE )
            self.model.add( obj )
            stream = model.Stream( obj, '.', model.StreamPriority.NORMAL.value,
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
    def register_file( self,
                path: str,
                name_policy: int = NAME_POLICY_SET_IF_UNDEF,
                name: Optional[str] = None
            ) -> File:
        """ Register a file from the filesystem into the database.

        Imports a file into the database. If a file with the same hash already
        exists, returns the existing file instead of creating a duplicate.
        Creates necessary streams and optionally sets the file name based on
        the name_policy.

        Args:
            path: Filesystem path to the file
            name_policy: How to handle the filename:
                NAME_POLICY_DONT_REGISTER - Don't log origin name
                NAME_POLICY_DONT_SET - Log name but don't set as object name
                NAME_POLICY_SET_IF_UNDEF - Set name if object has no name (default)
                NAME_POLICY_SET_ALWAYS - Always set/overwrite object name
            name: Optional name to use (defaults to filename from path)

        Returns:
            The File object (newly created or existing)

        Example:
            >>> f = db.register_file('/photos/sunset.jpg')
            >>> f = db.register_file('/photos/img.jpg', name='Beautiful Sunset')
        """

        return self.__register_file( path, name_policy, name )[0]

    @Session._with_access( write = True )
    def register_file3( self,
                path: str,
                name_policy: int = NAME_POLICY_SET_IF_UNDEF,
                name: Optional[str] = None
            ) -> Tuple[File, Stream, bool]:
        """ Register a file and return detailed information.

        Like register_file(), but returns a tuple with additional information
        about whether a new file was created.

        Args:
            path: Filesystem path to the file
            name_policy: How to handle the filename (see register_file)
            name: Optional name to use

        Returns:
            Tuple of (file, stream, is_new) where:
                file: The File object
                stream: The root Stream object
                is_new: True if a new file was created, False if existing

        Example:
            >>> f, stream, is_new = db.register_file3('/photos/image.jpg')
            >>> if is_new:
            ...     print("New file imported")
        """

        return self.__register_file( path, name_policy, name )

    def __register_thumb( self,
                path: str,
                obj: ImageFile,
                origin: Stream,
                name: str
            ) -> Stream:

        import mimetypes

        ext = os.path.splitext( path )[1]
        assert ext[0] == '.'
        ext = ext[1:]

        details = calculate_details( path )
        mime_type = mimetypes.guess_type( path, strict=False )[0]

        stream = model.Stream( obj.obj, name, model.StreamPriority.EXPENDABLE.value,
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
    def register_thumb( self,
                path: str,
                obj: ImageFile,
                origin: Stream,
                name: str
            ) -> Stream:
        """ Register a thumbnail stream for an image.

        Creates a new thumbnail stream for an image file. This is typically
        called internally by the thumbnail generation system, but can be used
        manually for custom thumbnail creation.

        Args:
            path: Filesystem path to the thumbnail file
            obj: The file object this thumbnail belongs to
            origin: The original stream this thumbnail is derived from
            name: Stream name (e.g., 'thumb.256')

        Returns:
            The new Stream object for the thumbnail

        Note:
            This is a low-level method. Most users should use the automatic
            thumbnail generation via request_thumbs() on ImageFile objects.
        """

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
        """ Get the highest priority thumbnail request.

        Retrieves the next thumbnail generation request from the queue. Returns
        the highest priority request that is at or above min_prio. Used by the
        thumbnail generation system to process pending requests.

        Args:
            min_prio: Minimum priority threshold (BACKGROUND, PREFETCH,
                INTERACTIVE, or IMMEDIATE). If None, returns any priority.

        Returns:
            ThumbRequest with (prio, exps, file), or None if no requests

        Example:
            >>> req = db.get_next_thumb_request(ImageRequestPriority.INTERACTIVE)
            >>> if req:
            ...     print(f"Processing thumbs for {req.file}")
        """

        return self.__get_next_thumb_request( min_prio )

    @Session._with_access( write = True )
    def process_next_thumb_request( self,
                min_prio: Optional[ImageRequestPriority] = None,
            ) -> Optional[ImageFile]:
        """ Process the next thumbnail generation request.

        Gets and processes the highest priority thumbnail request. Generates
        the requested thumbnails for the image file. If the image doesn't have
        metadata initialized, initializes it first.

        Args:
            min_prio: Minimum priority threshold. If None, processes any priority.

        Returns:
            The ImageFile that was processed, or None if no requests

        Example:
            >>> while db.process_next_thumb_request():
            ...     print("Processed one thumbnail request")
        """

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
        """ Process all thumbnail requests above a priority threshold.

        Processes all pending thumbnail generation requests that meet the
        priority threshold. Continues until no more requests remain at or
        above the specified priority.

        Args:
            min_prio: Minimum priority threshold. If None, processes all requests.

        Returns:
            True if at least one request was processed, False otherwise

        Example:
            >>> # Process all interactive and immediate requests
            >>> if db.process_thumb_requests(ThumbRequestPrio.IMMEDIATE):
            ...     print("Generated some thumbnails")
        """

        processed_one = False

        while( self.process_next_thumb_request( min_prio ) is not None ):
            processed_one = True

        return processed_one

    @Session._with_access( write = True )
    def batch_add_files( self,
                files: List[str],
                tags: List[str] = [],
                tags_new: List[str] = [],
                name_policy: int = NAME_POLICY_SET_IF_UNDEF,
                create_album: bool = False,
                album_name: Optional[str] = None,
                album_text: Optional[str] = None
            ) -> None:
        """ Add multiple files to the database in a single operation.

        Efficiently imports multiple files, optionally creating tags, albums,
        and an import session. This is the preferred method for bulk imports.

        Args:
            files: List of filesystem paths to import
            tags: List of existing tag names to assign to all files
            tags_new: List of tag names to create and assign (if they don't exist)
            name_policy: How to handle filenames (see register_file)
            create_album: If True, creates an album containing all files
            album_name: Name for the created album (if create_album=True)
            album_text: Description for the created album (if create_album=True)

        Raises:
            KeyError: If a tag in 'tags' doesn't exist

        Example:
            >>> db.batch_add_files(
            ...     ['/photos/img1.jpg', '/photos/img2.jpg'],
            ...     tags_new=['vacation', 'beach'],
            ...     create_album=True,
            ...     album_name='Summer Trip'
            ... )
        """

        # Load tags
        taglist = []
        taglist += map( self._get_tag, tags )
        taglist += map( self._make_tag, tags_new )

        imp = self.start_import()

        if( create_album ):
            album = self.create_album( taglist, album_name, album_text )
        else:
            album = None

        for idx, f in enumerate( files ):
            x, stream, is_new = self.__register_file( f, name_policy )
            x.assign( imp, idx )

            if( album is not None ):
                x.assign( album, idx )
            else:
                for t in taglist:
                    x.assign( t, None )

        imp.close_import()

    @Session._with_access( write = True )
    def delete_object( self, obj: Obj ) -> None:
        """ Delete an object from the database.

        Removes an object and all its relationships from the database. For File
        objects, also deletes all associated streams (file data). This operation
        cannot be undone.

        Args:
            obj: The object to delete (File, Album, Tag, Import, etc.)

        Warning:
            For files, this deletes the actual file data. For tags, consider
            using delete_tag() which handles scopes properly.

        Example:
            >>> temp_file = db.get_object_by_id(12345)
            >>> db.delete_object(temp_file)
        """

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

def compare_details( a: Tuple, b: Tuple ) -> bool:
    """ Compare two file hash details tuples for equality.

    Args:
        a: First details tuple (file_length, crc32, md5, sha1)
        b: Second details tuple (file_length, crc32, md5, sha1)

    Returns:
        True if all hash components match, False otherwise
    """

    return long( a[0] ) == long( b[0] ) \
       and str( a[1] ) == str( b[1] ) \
       and str( a[2] ) == str( b[2] ) \
       and str( a[3] ) == str( b[3] )

def init( library_path: Optional[str] = None ) -> None:
    """ Initialize the hdbfs library with a database path.

    Sets up the global library path and initializes the database model.
    This must be called before creating any Database instances.

    Args:
        library_path: Path to the library directory. If None, uses the
            default path from DEFAULT_LIBRARY (~/.higu)

    Example:
        >>> import hdbfs
        >>> hdbfs.init('/path/to/library')
        >>> db = hdbfs.Database()
    """
    global _LIBRARY

    if( library_path is not None ):
        _LIBRARY = library_path
    else:
        _LIBRARY = DEFAULT_LIBRARY

    if( not os.path.isdir( _LIBRARY ) ):
        os.makedirs( _LIBRARY )

    model.init( os.path.join( _LIBRARY, HIGURASHI_DB_NAME ),
                _LIBRARY )

def dispose() -> None:
    """ Clean up and dispose of the hdbfs library resources.

    Closes the database model and clears the global library path.  Should be
    called when shutting down the application.
    """
    global _LIBRARY

    model.dispose()
    _LIBRARY = None

imgdb.init_module()
