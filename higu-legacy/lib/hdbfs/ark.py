import os
import shutil
import tempfile
import zipfile

class ZipVolume:

    def __init__( self, path ):

        self.zf = zipfile.ZipFile( path, 'r' )
        self.ls = {}

        self.__load_ls()

    def __load_ls( self ):

        ils = self.zf.infolist()

        for i in ils:
            try:
                ids, e = i.filename.split( '.' )
                id = int( ids, 16 )
                self.ls[id] = i
            except:
                print 'WARNING: %s not loaded from zip' % ( i.filename, )
                pass

    def verify( self ):

        return self.zf.testzip() is None

    def read( self, id, extension ):

        try:
            info = self.ls[id]
            return self.zf.open( info, 'r' )
        except KeyError:
            return None

    def _debug_write( self, id, extension ):

        assert False

    def get_state( self ):

        return 'clean'

    def reset_state( self ):

        pass

class FileVolume:

    def __init__( self, data_config, vol_id ):

        self.data_config = data_config
        self.vol_id = vol_id
        self.to_commit = []
        self.state = 'clean'
        self.rm_dir = None

    def __get_path( self, id, priority, extension ):

        path = self.data_config.get_file_vol_path( self.vol_id, priority )
        return os.path.join( path, '%016x.%s' % ( id, extension ) )

    def verify( self ):

        return True

    def read( self, id, priority, extension ):

        p = self.__get_path( id, priority, extension )
        if( not os.path.isfile( p ) ):
            return None
        else:
            try:
                return open( p, 'rb' )
            except IndexError:
                return None

    def _debug_write( self, id, priority, extension ):

        p = self.__get_path( id, priority, extension )

        try:
            return open( p, 'wb' )
        except IndexError:
            return None

    def get_state( self ):

        return self.state

    def reset_state( self ):

        self.to_commit = []
        self.state = 'clean'

        rm_dir = self.rm_dir
        self.rm_dir = None
        self.to_commit = []

        if( rm_dir is not None ):
            shutil.rmtree( rm_dir )

    def commit( self ):

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

    def rollback( self ):

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

    def load_data( self, path, id, priority, extension ):

        if( self.state == 'committed' ):
            self.reset_state()

        self.state = 'dirty'

        new_path = self.data_config.get_file_vol_path( self.vol_id, priority )
        if( not os.path.isdir( new_path ) ):
            os.makedirs( new_path )

        tgt = os.path.join( new_path, '%016x.%s' % ( id, extension ) )
        self.to_commit.append( ( path, tgt, ) )

    def delete( self, id, priority, extension ):

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

    def __init__( self, data_config ):

        self.volumes = {}
        self.data_config = data_config
        self.state = 'clean'

    def __get_volume( self, vol_id ):

        if( self.volumes.has_key( vol_id ) ):
            return self.volumes[vol_id]

        vol = FileVolume( self.data_config, vol_id )
        self.volumes[vol_id] = vol

        return vol

    def __get_vol_for_id( self, id ):

        return self.__get_volume( id >> 12 )

    def get_state( self ):

        return self.state

    def reset_state( self ):

        for vol in self.volumes.values():
            vol.reset_state()

        self.state = 'clean'

    def prepare_commit( self ):

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

    def unprepare_commit( self ):

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

    def complete_commit( self ):

        if( self.state == 'clean' ):
            return

        assert self.state == 'prepared'

        vols = self.volumes.values()
        for vol in vols:
            if( vol.get_state() == 'committed' ):
                vol.reset_state()

        self.state = 'clean'

    def commit( self ):

        self.prepare_commit()
        self.complete_commit()

    def rollback( self ):

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

    def load_data( self, path, id, priority, extension ):

        if( self.state == 'committed' ):
            # Clean things up before we begin. We need to do this so that
            # We can determine the volumes that changes as part of this
            # commit
            self.reset_state()

        self.state = 'dirty'

        v = self.__get_vol_for_id( id )
        v.load_data( path, id, priority, extension )

    def delete( self, id, priority, extension ):

        if( self.state == 'committed' ):
            # Clean things up before we begin. We need to do this so that
            # We can determine the volumes that changes as part of this
            # commit
            self.reset_state()

        self.state = 'dirty'

        v = self.__get_vol_for_id( id )
        v.delete( id, priority, extension )

    def read( self, id, priority, extension ):

        v = self.__get_vol_for_id( id )
        return v.read( id, priority, extension )

    def _debug_write( self, id, priority, extension ):

        v = self.__get_vol_for_id( id )
        return v._debug_write( id, priority, extension )

