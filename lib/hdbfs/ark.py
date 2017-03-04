import os
import shutil
import tempfile
import zipfile
import mimetypes
import model

IMGDB_DATA_PATH = 'imgdat'
IMGDB_THUMB_PATH = 'tbdat'

MIN_THUMB_EXP = 7

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

class ImageDbDataConfig:

    def __init__( self, imgdb_path ):

        self.imgdb_path = imgdb_path

    def get_file_vol_path( self, vol_id, priority ):

        if( priority > model.SP_EXPENDABLE ):
            path = os.path.join( self.imgdb_path, IMGDB_DATA_PATH )
        else:
            path = os.path.join( self.imgdb_path, IMGDB_THUMB_PATH )

        lv2 = vol_id & 0xfff
        lv3 = (vol_id >> 12) & 0xfff
        lv4 = (vol_id >> 24) & 0xfff

        assert lv4 == 0

        path = os.path.join( path, '%03x' % ( lv3 ),
                                   '%03x' % ( lv2 ) )

        return path

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

class ImageInfo:

    def __init__( self, imgdb, obj ):

        self.imgdb = imgdb
        self.obj = obj
        self.root_stream = None

        self.tb_gen = None
        self.max_e = None
        self.use_root = None
        self.w = None
        self.h = None
        self.rot = None
        self.img = None

    def get_root_stream( self ):

        if( self.root_stream is None ):
            self.root_stream = self.obj.get_root_stream()

        return self.root_stream

    def get_img( self ):

        from PIL import Image

        if( self.img is None ):
            root_stream = self.get_root_stream()
            if( root_stream is None ):
                return None

            f = root_stream.read()
            if( f is None ):
                return None

            self.img = Image.open( f )

        return self.img

    def get_rot( self ):

        if( self.rot is None ):
            try:
                self.rot = self.root_stream['rotation']
            except:
                self.rot = 0

        return self.rot

    def get_dims( self ):

        if( self.w is None or self.h is None ):
            root_stream = self.get_root_stream()

            try:
                self.w = root_stream['width']
            except:
                pass

            try:
                self.h = root_stream['height']
            except:
                pass

        # Image info is not present, we need to read it from the file
        if( self.w is None or self.h is None ):
            root_stream = self.get_root_stream()

            try:
                self.img = self.get_img()
                if( self.img is None ):
                    return None, None

                self.w, self.h = self.img.size
            except IOError:
                return None, None

            root_stream['width'] = self.w
            root_stream['height'] = self.h

        return self.w, self.h

    def get_tb_info( self, bump_gen = False ):

        if( self.tb_gen is None
         or self.max_e is None
         or self.use_root is None ):

            try:
                tb_info = map( int, self.obj['.tbinfo'].split( ':' ) )

                self.tb_gen = tb_info[0]
                self.max_e = tb_info[1]
                self.use_root = tb_info[2]

            except:
                pass

        if( bump_gen
         or self.tb_gen is None
         or self.max_e is None
         or self.use_root is None ):

            w, h = self.get_dims()
            rot = self.get_rot()

            if( self.tb_gen is not None ):
                self.tb_gen += 1
            else:
                self.tb_gen = 0

            self.max_e = 0
            if( rot == 0 ):
                self.use_root = 1
            else:
                self.use_root = 0

            while( 2**self.max_e < w or 2**self.max_e < h ):
                self.max_e += 1

            tb_info = [ self.tb_gen, self.max_e, self.use_root ]
            self.obj['.tbinfo'] = ':'.join( map( str, tb_info ) )

        return self.tb_gen, self.max_e, self.use_root

class ThumbCache:

    def __init__( self, fsdb, imgdb ):

        self.fsdb = fsdb
        self.imgdb = imgdb

    def make_thumb( self, obj, exp ):

        from PIL import Image

        imginfo = ImageInfo( self.imgdb, obj )

        gen, max_e, use_root = imginfo.get_tb_info()

        if( exp < MIN_THUMB_EXP ):
            exp = MIN_THUMB_EXP

        if( exp >= max_e ):
            if( use_root == 1 ):
                return imginfo.get_root_stream()
            else:
                exp = max_e

        t_stream = obj.get_stream( 'tb:%d' % ( exp, ) )
        if( t_stream is not None ):
            return t_stream

        s = 2**exp

        # If we're here, we need to produce a thumb
        t = tempfile.mkstemp( '.jpg' )
        os.close( t[0] )

        # At this point, we need to create a thumb, open the file
        try:
            img = imginfo.get_img()
            if( img is None ):
                return None

            w, h = imginfo.get_dims()
            rot = imginfo.get_rot()

            if( rot == 1 or rot == 3 ):
                w, h = h, w

            try:
                update_size = obj['width'] != w or obj['height'] != h
            except:
                update_size = True

            if( update_size ):
                obj['width'] = w
                obj['height'] = h

            # Always operate in RGB
            img = img.convert( 'RGB' )

            # Do the rotate
            if( rot == 1 ):
                img = img.transpose( Image.ROTATE_270 )
            elif( rot == 2 ):
                img = img.transpose( Image.ROTATE_180 )
            elif( rot == 3 ):
                img = img.transpose( Image.ROTATE_90 )

            # Do the resize
            if( w > s or h > s ):
                if( w > h ):
                    tw = s
                    th = h * s / w
                else:
                    tw = w * s / h
                    th = s

                img = img.resize( ( tw, th, ), Image.ANTIALIAS )

            # Save the image
            img.save( t[1] )

            # Now load the thumb into the database
            return obj.db.register_thumb( t[1], obj,
                                          imginfo.get_root_stream(),
                                          'tb:%d' % ( exp, ) )

        except IOError:
            return None

    def purge_thumbs( self, obj ):

        obj.drop_expendable_streams()
        ImageInfo( self.imgdb, obj ).get_tb_info( True )
