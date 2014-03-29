import os
import shutil
import tempfile
import zipfile
import mimetypes

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

    def get_ext( self, id ):

        try:
            info = self.ls[id]
            fname = info.filename
            return fname[fname.rindex( '.' )+1:]
        except ( KeyError, ValueError ):
            return None

    def get_mime( self, id ):

        try:
            info = self.ls[id]
            fname = info.filename
            return mimetypes.guess_type( fname )[0]
        except ( KeyError, ValueError ):
            return None

    def read( self, id ):

        try:
            info = self.ls[id]
            return self.zf.open( info, 'r' )
        except KeyError:
            return None

    def _debug_write( self, id ):

        assert False

    def get_state( self ):

        return 'clean'

    def reset_state( self ):

        pass

class FileVolume:

    def __init__( self, path ):

        self.path = path
        self.to_commit = []
        self.state = 'clean'
        self.rm_dir = None

    def __get_path( self, id ):

        try:
            ls = os.listdir( self.path )
            ids = '%016x.' % ( id )
        except OSError:
            return None

        for f in ls:
            try:
                if( f.index( ids ) == 0 ):
                    return os.path.join( self.path, f )
            except ValueError:
                pass

        return None

    def verify( self ):

        return True

    def get_ext( self, id ):

        p = self.__get_path( id )
        if( p is None ):
            return None
        else:
            try:
                return p[p.rindex( '.' )+1:]
            except IndexError:
                return None

    def get_mime( self, id ):

        p = self.__get_path( id )
        if( p is None ):
            return None
        else:
            return mimetypes.guess_type( p )[0]

    def read( self, id ):

        p = self.__get_path( id )
        if( p is None ):
            return None
        else:
            try:
                return open( p, 'rb' )
            except IndexError:
                return None

    def _debug_write( self, id ):

        p = self.__get_path( id )
        if( p is None ):
            return None
        else:
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

    def load_data( self, path, id ):

        if( self.state == 'committed' ):
            self.reset_state()

        self.state = 'dirty'

        if( not os.path.isdir( self.path ) ):
            os.makedirs( self.path )

        name = os.path.split( path )[-1]
        try:
            ext = name[name.rindex( '.' ):]
        except ValueError:
            ext = '.dat'

        tgt = os.path.join( self.path, '%016x%s' % ( id, ext ) )
        self.to_commit.append( ( path, tgt, ) )

    def delete( self, id ):

        if( self.state == 'committed' ):
            self.reset_state()

        self.state = 'dirty'

        if( self.rm_dir is None ):
            self.rm_dir = tempfile.mkdtemp()

        src = self.__get_path( id )

        name = os.path.split( src )[-1]
        tgt = os.path.join( self.rm_dir, name )
        self.to_commit.append( ( src, tgt, ) )

class ImageDatabase:

    def __init__( self, path ):

        self.volumes = {}
        self.data_path = path
        self.state = 'clean'

    def __get_volume( self, vol_id ):

        if( self.volumes.has_key( vol_id ) ):
            return self.volumes[vol_id]

        lv2 = vol_id & 0xfff
        lv3 = (vol_id >> 12) & 0xfff
        lv4 = (vol_id >> 24) & 0xfff

        assert lv4 == 0

        path = os.path.join( self.data_path, '%03x' % ( lv3 ),
                                             '%03x' % ( lv2 ) )

        vol = FileVolume( path )
        self.volumes[vol_id] = vol

        return vol

    def __get_vol_for_id( self, id ):

        return self.__get_volume( id >> 12 )

    def __get_fname_base( self, id ):

        fname = '%016x' % ( id, )
        return os.path.join( self.__get_dir_for_id( id ), fname )

    def get_state( self ):

        return self.state

    def reset_state( self ):

        for vol in self.volumes.values():
            vol.reset_state()

        self.state = 'clean'

    def commit( self ):

        vols = self.volumes.values()
        # Clean things up before we begin. We need to do this so that
        # We can determine the volumes that changes as part of this
        # commit
        for vol in vols:
            if( vol.get_state() == 'committed' ):
                vol.reset_state()

        if( self.state == 'clean' or self.state == 'committed' ):
            return

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
        self.state = 'committed'

    def rollback( self ):

        vols = self.volumes.values()

        if( self.state == 'clean' ):
            for vol in vols:
                if( vol.get_state() != 'clean' ):
                    assert False

        elif( self.state == 'dirty' ):
            for vol in vols:
                if( vol.get_state() == 'dirty' ):
                    vol.rollback()
                elif( vol.get_state() == 'committed' ):
                    assert False

            for vol in vols:
                if( vol.get_state() != 'clean' ):
                    assert False

            self.state = 'clean'

        elif( self.state == 'committed' ):
            for vol in vols:
                if( vol.get_state() == 'committed' ):
                    vol.rollback()
                elif( vol.get_state() == 'dirty' ):
                    assert False

            for vol in vols:
                if( vol.get_state() == 'committed' ):
                    assert False

            self.state = 'dirty'

    def load_data( self, path, id ):

        if( self.state == 'committed' ):
            # Clean things up before we begin. We need to do this so that
            # We can determine the volumes that changes as part of this
            # commit
            self.reset_state()

        self.state = 'dirty'

        v = self.__get_vol_for_id( id )
        v.load_data( path, id )

    def delete( self, id ):

        if( self.state == 'committed' ):
            # Clean things up before we begin. We need to do this so that
            # We can determine the volumes that changes as part of this
            # commit
            self.reset_state()

        self.state = 'dirty'

        v = self.__get_vol_for_id( id )
        v.delete( id )

    def get_ext( self, id ):

        v = self.__get_vol_for_id( id )
        return v.get_ext( id )

    def get_mime( self, id ):

        v = self.__get_vol_for_id( id )
        return v.get_mime( id )

    def read( self, id ):

        v = self.__get_vol_for_id( id )
        return v.read( id )

    def _debug_write( self, id ):

        v = self.__get_vol_for_id( id )
        return v._debug_write( id )

class ThumbCache:

    def __init__( self, imgdb, path ):

        self.imgdb = imgdb
        self.data_path = path

    def __get_dir_for_id( self, id ):

        lv2 = (id >> 12) % 0xfff
        lv3 = (id >> 24) % 0xfff
        lv4 = id >> 36

        assert lv4 == 0

        return os.path.join( self.data_path, '%03x' % ( lv3 ),
                                             '%03x' % ( lv2 ) )

    def __get_fname_base( self, id ):

        fname = '%016x' % ( id, )
        return os.path.join( self.__get_dir_for_id( id ), fname )

    def __get_path( self, id ):

        try:
            d = self.__get_dir_for_id( id )
            ls = os.listdir( d )
            ids = '%016x.' % ( id )
        except OSError:
            return None

        for f in ls:
            try:
                if( f.index( ids ) == 0 ):
                    return os.path.join( d, f )
            except ValueError:
                pass

        return None

    def read_thumb( self, id, exp ):

        from PIL import Image

        t = self.__get_fname_base( id ) + '_%02d.jpg' % ( exp, )
        if( os.path.isfile( t ) ):
            return open( t, 'rb' )

        f = self.imgdb.read( id )
        if( f is None ):
            return None

        i = Image.open( f )
        s = 2**exp
        w, h = i.size

        if( w < s and h < s ):
            return self.imgdb.read( id )

        if( w > h ):
            tw = s
            th = h * s / w
        else:
            tw = w * s / h
            th = s

        i = i.convert( 'RGB' )
        r = i.resize( ( tw, th, ), Image.ANTIALIAS )
        r.save( t )

        return open( t, 'rb' )

    def make_thumb( self, id, exp ):

        from PIL import Image

        i = Image.open( self.imgdb.read( id ) )
        s = 2**exp
        w, h = i.size

        if( w < s and h < s ):
            return

        if( w > h ):
            tw = s
            ht = h * s / w
        else:
            tw = w * s / h
            th = s

        r = i.resize( ( tw, th, ), Image.ANTIALIAS )
        
        t = self.__get_fname_base( id ) + '_%02d.jpg' % ( exp, )
        if( os.path.isfile( t ) ):
            os.remove( t )
        r.save( t )

    def purge_thumbs( self, id ):

        from glob import glob
    
        fs = glob( self.__get_fname_base( id ) + '_*.jpg' )
        for f in fs:
            os.remove( f )