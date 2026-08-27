""" File storage backend for stream data (ark system).

This module provides the storage layer for stream data, supporting both
file-based storage (FileVolume) and zip-based archives (ZipVolume).

The ark system manages:
- Stream data storage across multiple volumes
- Transaction support (commit/rollback)
- File availability tracking
- Volume-based organization (high 12 bits of stream ID = volume ID)
"""

import os
import shutil
import tempfile
import zipfile

from typing import BinaryIO, Dict, List, Tuple, Optional

class FileUnavailableError( Exception ):
    """ Exception raised when requested file data is not available.

    This can occur when:
    - File has been deleted
    - File is in an archive that's not mounted
    - File path is invalid or inaccessible
    """

    def __init__( self, msg: str ):
        Exception.__init__( self, msg )

class ZipVolume:
    """ Read-only zip archive storage for stream data.

    Provides access to stream data stored in a zip file. Used for archived
    or read-only data that doesn't need to be modified. Files in the zip
    are indexed by stream ID.

    Attributes:
        zf: ZipFile object for the archive
        ls: Dictionary mapping stream IDs to ZipInfo objects
    """

    def __init__( self, path: str ):

        self.zf = zipfile.ZipFile( path, 'r' )
        self.ls: Dict[int, zipfile.ZipInfo] = {}

        self.__load_ls()

    def __load_ls( self ) -> None:
        """ Load the directory of files in the zip archive.

        Parses filenames (expected format: XXXXXXXXXXXXXXXX.ext) to build
        an index of stream IDs to ZipInfo objects.
        """

        ils = self.zf.infolist()

        for i in ils:
            try:
                ids, e = i.filename.split( '.' )
                id = int( ids, 16 )
                self.ls[id] = i
            except:
                print( f'WARNING: {i.filename} not loaded from zip' )
                pass

    def verify( self ) -> bool:
        """ Verify the integrity of the zip archive.

        Returns:
            True if archive is valid, False otherwise
        """

        return self.zf.testzip() is None

    def open( self, id: int, extension: str ) -> BinaryIO:
        """ Open a file from the zip archive.

        Args:
            id: Stream ID
            extension: File extension (not used for lookup, kept for compatibility)

        Returns:
            Binary file-like object for reading

        Raises:
            FileUnavailableError: If file with given ID is not in archive
        """

        try:
            info = self.ls[id]
            return self.zf.open( info, 'r' )
        except KeyError:
            raise FileUnavailableError( f'File with id={id} is not available' )

    def _debug_write( self, id: int, extension: str ) -> None:
        """ Debug method for writing (not supported for zip volumes).

        Args:
            id: Stream ID
            extension: File extension

        Raises:
            AssertionError: Always, as zip volumes are read-only
        """

        assert False

    def get_state( self ) -> str:
        """ Get the state of this volume.

        Returns:
            Always returns 'clean' (zip volumes have no dirty state)
        """

        return 'clean'

    def reset_state( self ) -> None:
        """ Reset the volume state (no-op for zip volumes). """

        pass

class FileVolume:
    """ File-based storage volume for stream data with transaction support.

    Manages stream files on disk for a single volume, supporting transactional
    operations (commit/rollback). Changes are staged in a temporary location
    and moved atomically on commit.

    States:
    - 'clean': No pending changes
    - 'dirty': Changes staged but not committed
    - 'committed': Changes committed but not yet finalized

    Attributes:
        data_config: Configuration object with volume path information
        vol_id: Volume identifier
        to_commit: List of (source, target) file moves to perform on commit
        state: Current transaction state
        rm_dir: Temporary directory for files being deleted
    """

    def __init__( self, data_config: 'ImageDbDataConfig', vol_id: int ):

        self.data_config = data_config
        self.vol_id = vol_id
        self.to_commit: List[Tuple[str, str]] = []
        self.state = 'clean'
        self.rm_dir: Optional[str] = None

    def __get_path( self, id: int, priority: int, extension: str ) -> str:
        """ Get the file path for a stream.

        Args:
            id: Stream ID
            priority: Stream priority level
            extension: File extension

        Returns:
            Full path to the file
        """

        path = self.data_config.get_file_vol_path( self.vol_id, priority )
        return os.path.join( path, '%016x.%s' % ( id, extension ) )

    def verify( self ) -> bool:
        """ Verify the integrity of this volume.

        Returns:
            Always True for file volumes (integrity checking not implemented)
        """

        return True

    def open( self, id: int, priority: int, extension: str ) -> BinaryIO:
        """ Open a file from this volume for reading.

        If there are uncommitted changes, checks the staged location first.

        Args:
            id: Stream ID
            priority: Stream priority level
            extension: File extension

        Returns:
            Binary file-like object for reading

        Raises:
            FileUnavailableError: If file is not available
        """

        p = self.__get_path( id, priority, extension )

        # If we have items to commit, it may have not yet been comitted
        if( self.state == 'dirty' ):
            tcp = [it[0] for it in self.to_commit if it[1] == p]
            if( len( tcp ) > 0 ):
                p = tcp[0]

        if( not os.path.isfile( p ) ):
            raise FileUnavailableError( f'File at {p} is not available' )
        else:
            try:
                return open( p, 'rb' )
            except IndexError:
                raise FileUnavailableError()

    def _debug_write( self, id: int, priority: int, extension: str ) -> BinaryIO:
        """ Open a file for writing (debug/testing only).

        Args:
            id: Stream ID
            priority: Stream priority level
            extension: File extension

        Returns:
            Binary file-like object for writing

        Raises:
            FileUnavailableError: If file cannot be opened
        """

        p = self.__get_path( id, priority, extension )

        try:
            return open( p, 'wb' )
        except IndexError:
            raise FileUnavailableError( f'File at {p} is not available' )

    def get_state( self ) -> str:
        """ Get the current transaction state.

        Returns:
            State string: 'clean', 'dirty', or 'committed'
        """

        return self.state

    def reset_state( self ) -> None:
        """ Reset to clean state and clean up temporary files.

        Clears the commit queue and deletes the temporary removal directory
        if it exists.
        """

        self.to_commit = []
        self.state = 'clean'

        rm_dir = self.rm_dir
        self.rm_dir = None
        self.to_commit = []

        if( rm_dir is not None ):
            shutil.rmtree( rm_dir )

    def commit( self ) -> None:
        """ Commit staged changes by moving files to their final locations.

        Atomically moves all staged files. If any move fails, attempts to
        rollback all completed moves.

        Raises:
            Exception: If file moves fail (after attempting rollback)
        """

        completion = 0

        try:
            for t in self.to_commit:
                shutil.move( t[0], t[1] )
                completion += 1

        except:
            # Something went wrong, rollback
            for t in self.to_commit[:completion]:
                shutil.move( t[1], t[0] )

            # Sometimes move() seems to leave files behind
            for t in self.to_commit:
                try:
                    if( os.path.isfile( t[1] ) ):
                        os.remove( t[1] )
                except:
                    pass

            raise

        # Comitted
        self.state = 'committed'

    def rollback( self ) -> None:
        """ Rollback changes to previous state.

        If dirty: clears staged changes
        If committed: moves files back to their original locations
        """

        if( self.state == 'dirty' ):
            self.to_commit = []
            self.state = 'clean'

        elif( self.state == 'committed' ):
            for t in self.to_commit:
                shutil.move( t[1], t[0] )

            # Sometimes move() seems to leave files behind
            for t in self.to_commit:
                try:
                    if( os.path.isfile( t[1] ) ):
                        os.remove( t[1] )
                except:
                    pass

            self.state = 'dirty'

    def load_data( self, path: str, id: int, priority: int, extension: str ) -> None:
        """ Stage a file to be added to this volume.

        The file will be moved to its final location on commit.

        Args:
            path: Current path of the file to add
            id: Stream ID
            priority: Stream priority level
            extension: File extension
        """

        if( self.state == 'committed' ):
            self.reset_state()

        self.state = 'dirty'

        new_path = self.data_config.get_file_vol_path( self.vol_id, priority )
        if( not os.path.isdir( new_path ) ):
            os.makedirs( new_path )

        tgt = os.path.join( new_path, '%016x.%s' % ( id, extension ) )
        self.to_commit.append( ( path, tgt, ) )

    def delete( self, id: int, priority: int, extension: str ) -> None:
        """ Stage a file to be deleted from this volume.

        The file will be moved to a temporary directory on commit, then
        deleted on reset_state.

        Args:
            id: Stream ID
            priority: Stream priority level
            extension: File extension
        """

        if( self.state == 'committed' ):
            self.reset_state()

        self.state = 'dirty'

        if( self.rm_dir is None ):
            self.rm_dir = tempfile.mkdtemp()

        src = self.__get_path( id, priority, extension )
        if( not os.path.isfile( src ) ):
            return

        name = os.path.split( src )[-1]
        tgt = os.path.join( self.rm_dir, name )
        self.to_commit.append( ( src, tgt, ) )

class StreamDatabase:
    """ Multi-volume transactional storage system for stream data.

    Manages multiple file volumes with coordinated transaction support.
    Changes across all volumes can be committed or rolled back atomically.

    Transaction lifecycle:
    1. 'clean': No pending changes
    2. 'dirty': Changes staged in one or more volumes
    3. 'prepared': All volume changes committed to volumes (2-phase commit)
    4. Back to 'clean': Changes finalized across all volumes

    Attributes:
        volumes: Dictionary mapping volume IDs to FileVolume instances
        data_config: Configuration object with volume path information
        state: Current transaction state
    """

    def __init__( self, data_config: 'ImageDbDataConfig' ):

        self.volumes: Dict[int, FileVolume] = {}
        self.data_config = data_config
        self.state = 'clean'

    def __get_volume( self, vol_id: int ) -> FileVolume:
        """ Get or create a volume by ID.

        Args:
            vol_id: Volume identifier

        Returns:
            FileVolume instance for the given ID
        """

        if( vol_id in self.volumes ):
            return self.volumes[vol_id]

        vol = FileVolume( self.data_config, vol_id )
        self.volumes[vol_id] = vol

        return vol

    def __get_vol_for_id( self, id: int ) -> FileVolume:
        """ Get the volume that contains a given stream ID.

        Stream IDs encode their volume in the upper bits (id >> 12).

        Args:
            id: Stream ID

        Returns:
            FileVolume instance containing the stream
        """

        return self.__get_volume( id >> 12 )

    def get_state( self ) -> str:
        """ Get the current transaction state.

        Returns:
            State string: 'clean', 'dirty', or 'prepared'
        """

        return self.state

    def reset_state( self ) -> None:
        """ Reset all volumes to clean state and clear all changes.

        This is typically called after complete_commit() to finalize.
        """

        for vol in self.volumes.values():
            vol.reset_state()

        self.state = 'clean'

    def prepare_commit( self ) -> None:
        """ Phase 1 of two-phase commit: commit changes in all volumes.

        Attempts to commit all dirty volumes. If any commit fails, rolls back
        all volumes that were successfully committed.

        Raises:
            AssertionError: If state is already 'prepared'
            Exception: If volume commit fails (after attempting rollback)
        """

        if( self.state == 'clean' ):
            return

        assert self.state != 'prepared'

        vols = self.volumes.values()
        # Clean things up before we begin. We need to do this so that
        # We can determine the volumes that changes as part of this
        # commit
        for vol in vols:
            assert vol.get_state() != 'committed'

        try:
            # Try to commit all the dirty volumes
            for vol in vols:
                if( vol.get_state() == 'dirty' ):
                    vol.commit()
        except:
            # Something went wrong, rollback
            for vol in vols:
                if( vol.get_state() == 'committed' ):
                    vol.rollback()

            raise

        # Comitted
        self.state = 'prepared'

    def unprepare_commit( self ) -> None:
        """ Reverse phase 1 of two-phase commit: undo volume commits.

        Rolls back all volumes from 'committed' to 'dirty' state. Used when
        a later part of the transaction fails.

        Raises:
            AssertionError: If state is not 'prepared'
        """

        if( self.state == 'clean' ):
            return

        assert self.state == 'prepared'

        vols = self.volumes.values()
        for vol in vols:
            assert vol.get_state() != 'dirty'
            if( vol.get_state() == 'committed' ):
                vol.rollback()

        for vol in vols:
            assert vol.get_state() != 'committed'

        self.state = 'dirty'

    def complete_commit( self ) -> None:
        """ Phase 2 of two-phase commit: finalize all volume changes.

        Resets all volumes to clean state, making changes permanent. Should
        be called after prepare_commit() succeeds and any database updates
        are complete.

        Raises:
            AssertionError: If state is not 'prepared'
        """

        if( self.state == 'clean' ):
            return

        assert self.state == 'prepared'

        vols = self.volumes.values()
        for vol in vols:
            if( vol.get_state() == 'committed' ):
                vol.reset_state()

        self.state = 'clean'

    def commit( self ) -> None:
        """ Commit all changes in a single operation.

        Convenience method that performs both phases of the commit:
        prepare_commit() followed by complete_commit().
        """

        self.prepare_commit()
        self.complete_commit()

    def rollback( self ) -> None:
        """ Rollback all changes to clean state.

        If prepared: unprepares, then rolls back volumes
        If dirty: rolls back all dirty volumes
        If clean: validates state and returns

        Raises:
            AssertionError: If state is inconsistent
        """

        vols = self.volumes.values()

        if( self.state == 'clean' ):
            for vol in vols:
                assert vol.get_state() == 'clean'
            return

        if( self.state == 'prepared' ):
            self.unprepare_commit()

        if( self.state == 'dirty' ):
            for vol in vols:
                assert vol.get_state() != 'committed'
                if( vol.get_state() == 'dirty' ):
                    vol.rollback()

            for vol in vols:
                assert vol.get_state() == 'clean'

            self.state = 'clean'

    def load_data( self, path: str, id: int, priority: int, extension: str ) -> None:
        """ Stage a file to be added to the database.

        The file will be moved to its final location on commit. Automatically
        routes to the correct volume based on the stream ID.

        Args:
            path: Current path of the file to add
            id: Stream ID
            priority: Stream priority level
            extension: File extension
        """

        if( self.state == 'committed' ):
            # Clean things up before we begin. We need to do this so that
            # We can determine the volumes that changes as part of this
            # commit
            self.reset_state()

        self.state = 'dirty'

        v = self.__get_vol_for_id( id )
        v.load_data( path, id, priority, extension )

    def delete( self, id: int, priority: int, extension: str ) -> None:
        """ Stage a file to be deleted from the database.

        The file will be moved to a temporary directory on commit. Automatically
        routes to the correct volume based on the stream ID.

        Args:
            id: Stream ID
            priority: Stream priority level
            extension: File extension
        """

        if( self.state == 'committed' ):
            # Clean things up before we begin. We need to do this so that
            # We can determine the volumes that changes as part of this
            # commit
            self.reset_state()

        self.state = 'dirty'

        v = self.__get_vol_for_id( id )
        v.delete( id, priority, extension )

    def open( self, id: int, priority: int, extension: str ) -> BinaryIO:
        """ Open a file from the database for reading.

        Automatically routes to the correct volume based on the stream ID.

        Args:
            id: Stream ID
            priority: Stream priority level
            extension: File extension

        Returns:
            Binary file-like object for reading

        Raises:
            FileUnavailableError: If file is not available
        """

        v = self.__get_vol_for_id( id )
        return v.open( id, priority, extension )

    def _debug_write( self, id: int, priority: int, extension: str ) -> BinaryIO:
        """ Open a file for writing (debug/testing only).

        Automatically routes to the correct volume based on the stream ID.

        Args:
            id: Stream ID
            priority: Stream priority level
            extension: File extension

        Returns:
            Binary file-like object for writing

        Raises:
            FileUnavailableError: If file cannot be opened
        """

        v = self.__get_vol_for_id( id )
        return v._debug_write( id, priority, extension )

