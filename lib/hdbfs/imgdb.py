import calendar
import datetime
import os
import sys
import tempfile

import hdbfs.ark
import hdbfs.exif as exif
import hdbfs.model as model

from hdbfs.defs import *
from hdbfs.basic_objs import *
from hdbfs.hooks import *
from hdbfs.obj_factory import add_obj_factory

from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

IMGDB_DATA_PATH = 'imgdat'
IMGDB_THUMB_PATH = 'tbdat'

MIN_THUMB_EXP = 7

METADATA_VERSION = 3

_METADATA_INIT_REQUIRED = []
def _require_metadata_init( obj, stream ):
    global _METADATA_INIT_REQUIRED

    _METADATA_INIT_REQUIRED.append( ( obj, stream ) )

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

class StreamInfo:

    def __init__( self, imgdb, stream ):

        self.imgdb = imgdb
        self.stream = stream
        self.info = None

        self.fd = None
        self.img = None
        self.origin_time = None

    def __enter__( self ):

        return self

    def __exit__( self, type, value, tb ):

        self.close()

    def __get_info( self ):

        if( self.info is None ):
            self.info = self.stream.stream.info

        if( self.info is None ):
            try:
                self.get_img()
                if( self.img is None ):
                    return None

                self.info = model.StreamInfo( self.stream.stream,
                                self.img.size[0], self.img.size[1] )
                self.stream.db.session.add( self.info )
            except IOError:
                return None

        return self.info

    def close( self ):

        if( self.fd is not None ):
            self.fd.close()
            self.fd = None
            self.img = None

    def get_img( self ):

        from PIL import Image

        if( self.img is None ):
            try:
                self.fd = self.stream.open()
                self.img = Image.open( self.fd )
            except hdbfs.ark.FileUnavailableError:
                return None
            except:
                LOG.warning(
                        'Failed opening image for "%s": %s',
                        self.stream.get_repr(), str( sys.exc_info()[1] ) )

        return self.img

    def get_exif( self ):

        # Ensure the image is loaded
        self.get_img()

        if( self.img is not None ):
            return exif.read_exif( self. img )

        return None

    def get_orientation( self ):

        info = self.__get_info()
        if( info is None ):
            return None

        if( info.orientation is None ):
            self.get_img()
            if( self.img is not None and 'exif' in self.img.info ):
                ORIENTATION = 274

                try:
                    exif = self.img._getexif()
                except:
                    exif = []
                if( ORIENTATION in exif \
                and exif[ORIENTATION] != '' ):

                    orientation = int( exif[ORIENTATION] )
                    if( orientation < 1 or orientation > 8 ):
                        orientation = 1

                    info.orientation = orientation

            if( info.orientation is None ):
                info.orientation = 1

        return info.orientation

    def set_orientation( self, orientation ):

        info = self.__get_info()
        if( info is None ):
            return

        info.orientation = orientation

    def get_dims( self ):

        info = self.__get_info()
        if( info is None ):
            return None

        return info.width, info.height

    def get_origin_time( self ):

        if( self.origin_time is None ):
            try:
                self.origin_time = self.stream['origin_time']
            except:
                pass

        if( self.origin_time is None ):
            self.get_img()
            if( self.img is not None and 'exif' in self.img.info ):
                ORIGINAL_DATE = 36867
                DATE_TIME     = 306

                TAGS = [ ORIGINAL_DATE, DATE_TIME, ]

                try:
                    exif = self.img._getexif()
                except:
                    exif = []
                for tag in TAGS:
                    if( tag not in exif
                     or exif[tag] == '' ):

                        continue

                    original_date = str( exif[tag] )
                    original_date = original_date.replace( '\x00', '' )
                    original_date = original_date.strip()

                    if( original_date == ''
                     or original_date == '0000:00:00 00:00:00'
                     or original_date == ':  :     :  :' ):
                        continue

                    try:
                        try:
                            dt = datetime.datetime.strptime(
                                        original_date,
                                        '%Y:%m:%d %H:%M:%S' )
                        except:
                            dt = datetime.datetime.strptime(
                                        original_date,
                                        '%Y:%m:%dT%H:%M:%S' )
                        self.origin_time = calendar.timegm( dt.timetuple() )
                    except:
                        pass
                        #raise ValueError, 'Bad date <%r>: %r' % ( original_date, sys.exc_info()[1] )
                    break

            if( self.origin_time is not None ):
                self.stream['origin_time'] = self.origin_time

        return self.origin_time

class ImageInfo:

    def __init__( self, imgdb, obj ):

        self.imgdb = imgdb
        self.obj = obj
        self.root_si = None
        self.info = None

        self.origin_time = None

    def __enter__( self ):

        return self

    def __exit__( self, type, value, tb ):

        self.close()

    def __compute_dims( self ):

        root_si = self.get_root_stream_info()
        if( root_si is None ):
            return None, None

        w, h = self.get_dims()
        orientation = self.get_orientation()

        if( w is None or h is None ):
            return None, None

        if( orientation is not None and orientation > 4 ):
            w, h = h, w

        return w, h

    def __get_info( self ):

        if( self.info is None ):
            self.info = self.obj.obj.info

        if( self.info is None ):
            w, h = self.__compute_dims()
            if( w is None or h is None ):
                return None

            self.info = model.ImageInfo( self.obj.obj, w, h )
            self.obj.db.session.add( self.info )

        return self.info

    def close( self ):

        if( self.root_si is not None ):
            self.root_si.close()
            self.root_si = None

    def get_root_stream_info( self ):

        if( self.root_si is None ):
            root_s = self.obj.get_root_stream()
            if( root_s is not None ):
                self.root_si = StreamInfo( self.imgdb, root_s )

        return self.root_si

    def get_root_stream( self ):

        root_si = self.get_root_stream_info()
        if( root_si is not None ):
            return root_si.stream
        else:
            return None

    def get_img( self ):

        root_si = self.get_root_stream_info()
        if( root_si is not None ):
            return root_si.get_img()
        else:
            return None

    def get_orientation( self ):

        root_si = self.get_root_stream_info()
        if( root_si is not None ):
            return root_si.get_orientation()
        else:
            return 1

    def get_dims( self ):

        root_si = self.get_root_stream_info()
        if( root_si is not None ):
            return root_si.get_dims()
        else:
            return None, None

    def get_origin_time( self ):

        if( self.origin_time is None ):
            try:
                self.origin_time = self.obj['origin_time']
            except:
                pass

        if( self.origin_time is None ):
            root_si = self.get_root_stream_info()
            if( root_si is not None ):
                self.origin_time = root_si.get_origin_time()

            if( self.origin_time is not None ):
                self.obj['origin_time'] = self.origin_time

        return self.origin_time

    def get_obj_dims( self, verify = False ):

        info = self.__get_info()
        if( info is None ):
            return None

        if( verify ):
            w, h = self.__compute_dims()

            if( w is not None and h is not None ):
                if( w != info.width or h != info.height ):
                    info.width = w
                    info.height = h

        return info.width, info.height

    def get_max_e( self ):

        info = self.__get_info()
        if( info is None ):
            return None

        if( info.max_e is None ):
            max_e = 0

            while( 2**max_e < info.width or 2**max_e < info.height ):
                max_e += 1

            info.max_e = max_e

        return info.max_e

    def get_use_root( self ):

        info = self.__get_info()
        if( info is None ):
            return None

        if( info.use_root is None ):
            orientation = self.get_orientation()

            if( orientation == 1 ):
                info.use_root = 1
            else:
                info.use_root = 0

        return info.use_root

    def reorient( self, orientation = None, remap = None ):

        # We need to purge our info
        self.obj.obj.info = None

        root_si = self.get_root_stream_info()

        if( remap is not None ):
            orientation = root_si.get_orientation()
            orientation = remap[orientation-1]

        root_si.set_orientation( orientation )

        # And regen now
        self.__get_info()

    def get_gen( self ):

        info = self.__get_info()
        if( info is None ):
            return 0

        return info.gen

    def regen( self ):

        info = self.__get_info()
        if( info is None ):
            return

        info.gen += 1
        info.avail_e = None

    def mark_avail_e( self, exp ):

        info = self.__get_info()
        if( info is None ):
            return

        base = info.avail_e if( info.avail_e is not None ) else 0
        info.avail_e = (base | (1 << exp))

class ImageStream( Stream ):

    def __init__( self, db, stream ):

        Stream.__init__( self, db, stream )

    def get_exif( self ):

        with StreamInfo( self.db, self ) as sinfo:
            return sinfo.get_exif()

    def get_dimensions( self ):

        with StreamInfo( self.db, self ) as sinfo:
            return sinfo.get_dims()

    def get_origin_time( self ):

        with StreamInfo( self.db, self ) as sinfo:
            origin_ts = sinfo.get_origin_time()
            if( origin_ts is None ):
                return None

            return datetime.datetime\
                    .utcfromtimestamp( origin_ts )

    def check_metadata( self ):

        try:
            ver = self['.metaver']
            if( ver == METADATA_VERSION ):
                return
        except:
            pass
        
        self.db.tbcache.init_stream_metadata( self )

class ImageFile( File ):

    def __init__( self, db, obj ):

        File.__init__( self, db, obj )

    def _on_created( self, stream ):

        _require_metadata_init( self, stream )

    def get_exif( self ):

        with self.db._access():
            return self.get_root_stream().get_exif()

    def get_dimensions( self ):

        return self.db.tbcache.get_dimensions( self )

    def get_origin_time( self ):

        return self.db.tbcache.get_origin_time( self )

    def set_text( self, text ):

        self['text'] = text

    def get_text( self ):

        try:
            return self['text']
        except KeyError:
            return None

    def __drop_info( self ):

        this.obj.info = None

    def rotate_cw( self ):

        CW_REMAP = [ 6, 5, 8, 7, 4, 3, 2, 1 ]
        self.db.tbcache.reorient_image( self, remap = CW_REMAP )

    def rotate_ccw( self ):

        CCW_REMAP = [ 8, 7, 6, 5, 2, 1, 4, 3 ]
        self.db.tbcache.reorient_image( self, remap = CCW_REMAP )

    def mirror( self ):

        MIRROR_REMAP = [ 2, 1, 4, 3, 8, 7, 6, 5 ]
        self.db.tbcache.reorient_image( self, remap = MIRROR_REMAP )

    def auto_orientation( self ):

        self.db.tbcache.reorient_image( self )

    def get_orientation( self ):

        return self.db.tbcache.get_orientation( self )

    def get_generation( self ):

        return self.db.tbcache.get_generation( self )

    def get_thumb_stream( self, exp ):

        if( self.obj.object_type == model.TYPE_FILE ):
            return self.db.tbcache.make_thumb( self, exp )
        else:
            return self.get_root_stream()

    def check_metadata( self ):

        try:
            ver = self['.metaver']
            if( ver == METADATA_VERSION ):
                return
        except:
            pass
        
        self.db.tbcache.init_object_metadata( self )

    def assign( self, parent,
                order = None,
                name = None,
                is_duplicate = None,
                force = None ):

        File.assign( self, parent, order, name, is_duplicate, force )
        if( self.obj.object_type == model.TYPE_DUPLICATE ):
            self.db.tbcache.purge_thumbs( self )

    def __getitem__( self, key ):

        if( key == 'width' ):
            return self.get_dimensions()[0]
        elif( key == 'height' ):
            return self.get_dimensions()[1]
        else:
            return Obj.__getitem__( self, key )

    def __setitem__( self, key, value ):

        assert key not in [ 'width', 'height' ]
        return Obj.__setitem__( self, key, value )

class Album( OrderedGroup ):

    def __init__( self, db, obj ):

        OrderedGroup.__init__( self, db, obj )

    def _on_created( self, stream ):

        _require_metadata_init( self, None )

    def _on_children_changed( self ):

        _require_metadata_init( self, None )

    def publish( self ):

        with self.db._access( write = True ):
            if( self.obj.object_type == model.TYPE_ALBUM ):
                # Ensure all children are published
                for alb in self.get_albums():
                    assert alb.obj.object_type == model.TYPE_PUBLISHED

                self.obj.object_type = model.TYPE_PUBLISHED
            elif( self.obj.object_type == model.TYPE_PUBLISHED ):
                pass
            else:
                assert False

    def unpublish( self ):

        with self.db._access( write = True ):
            if( self.obj.object_type == model.TYPE_ALBUM ):
                pass
            elif( self.obj.object_type == model.TYPE_PUBLISHED ):
                # There can't be any duplicates in an unpublished album
                assert len( [f for f in self.get_files()
                        if f.obj.object_type == model.TYPE_DUPLICATE] ) == 0
                self.obj.object_type = model.TYPE_ALBUM
            else:
                assert False

    def get_origin_time( self ):

        self.check_metadata()
        try:
            return datetime.datetime\
                    .utcfromtimestamp( self['origin_time'] )
        except:
            return None

    def set_text( self, text ):

        self['text'] = text

    def get_text( self ):

        try:
            return self['text']
        except KeyError:
            return None

    def check_metadata( self ):

        try:
            ver = self['.metaver']
            if( ver == METADATA_VERSION ):
                return
        except:
            pass
        
        self.db.tbcache.init_album_metadata( self )

class ThumbCache:

    def __init__( self, fsdb, imgdb ):

        self.fsdb = fsdb
        self.imgdb = imgdb

    def get_dimensions( self, obj ):

        with ImageInfo( self.imgdb, obj ) as imginfo:
            return imginfo.get_obj_dims()

    def get_origin_time( self, obj ):

        with ImageInfo( self.imgdb, obj ) as imginfo:

            origin_ts = imginfo.get_origin_time()
            if( origin_ts is None ):
                return None

            return datetime.datetime\
                    .utcfromtimestamp( origin_ts )

    def reorient_image( self, obj, orientation = None, remap = None ):

        with ImageInfo( self.imgdb, obj ) as imginfo:
            imginfo.reorient( orientation, remap )
            self.purge_thumbs( obj )

    def get_orientation( self, obj ):

        with ImageInfo( self.imgdb, obj ) as imginfo:
            return imginfo.get_orientation()

    def get_generation( self, obj ):

        with ImageInfo( self.imgdb, obj ) as imginfo:
            return imginfo.get_gen()

    def init_stream_metadata( self, stream ):

        with stream.db._access( write = True ):
            try:
                del stream['creation_time']
            except:
                pass

            with StreamInfo( self.imgdb, stream ) as sinfo:
                sinfo.get_origin_time()
                sinfo.get_dims()
                sinfo.get_orientation()

            stream['.metaver'] = METADATA_VERSION

    def init_object_metadata( self, obj ):

        with obj.db._access( write = True ):
            try:
                del stream['creation_time']
            except:
                pass

            self.init_stream_metadata( obj.get_root_stream() )

            with ImageInfo( self.imgdb, obj ) as imginfo:
                imginfo.get_origin_time()
                imginfo.get_dims()

            obj['.metaver'] = METADATA_VERSION

    def init_album_metadata( self, obj ):

        with obj.db._access( write = True ):
            try:
                del obj['creation_time']
            except:
                pass

            files = obj.get_files()
            min_ts = None

            for f in files:
                f.check_metadata()
                f_ts = f.get_origin_time()
                f_ts = calendar.timegm( f_ts.timetuple() ) if( f_ts is not None ) else None
                if( f_ts is not None
                and (min_ts is None or f_ts < min_ts) ):
                    min_ts = f_ts

            if( min_ts is not None ):
                obj['origin_time'] = min_ts

            obj['.metaver'] = METADATA_VERSION

    def init_metadata( self, obj, stream ):

        with obj.db._access():
            if( isinstance( obj, ImageFile ) ):
                if( stream == None ):
                    stream = obj.get_root_stream()

                self.init_stream_metadata( stream )
                self.init_object_metadata( obj )
            elif( isinstance( obj, Album ) ):
                self.init_album_metadata( obj )

    def make_thumb( self, obj, exp ):

        from PIL import Image

        with ImageInfo( self.imgdb, obj ) as imginfo:

            max_e = imginfo.get_max_e()
            use_root = imginfo.get_use_root()

            if( exp < MIN_THUMB_EXP ):
                exp = MIN_THUMB_EXP

            if( exp >= max_e ):
                if( use_root == 1 ):
                    return imginfo.get_root_stream()
                else:
                    exp = max_e

            t_stream = obj.get_stream( f'tb:{exp}' )
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

                w, h = imginfo.get_obj_dims( verify = True )
                orientation = imginfo.get_orientation()

                # Always operate in RGB
                img = img.convert( 'RGB' )

                # Do the rotate
                if( orientation == 2 ):
                    img = img.transpose( Image.FLIP_LEFT_RIGHT )
                elif( orientation == 3 ):
                    img = img.transpose( Image.ROTATE_180 )
                elif( orientation == 4 ):
                    img = img.transpose( Image.FLIP_TOP_BOTTOM )
                elif( orientation == 5 ):
                    img = img.transpose( Image.FLIP_LEFT_RIGHT )
                    img = img.transpose( Image.ROTATE_270 )
                elif( orientation == 6 ):
                    img = img.transpose( Image.ROTATE_270 )
                elif( orientation == 7 ):
                    img = img.transpose( Image.FLIP_LEFT_RIGHT )
                    img = img.transpose( Image.ROTATE_90 )
                elif( orientation == 8 ):
                    img = img.transpose( Image.ROTATE_90 )

                # Do the resize
                if( w > s or h > s ):
                    if( w > h ):
                        tw = s
                        th = int( round( h * s / w ) )
                    else:
                        tw = int( round( w * s / h ) )
                        th = s

                    img = img.resize( ( tw, th, ), Image.ANTIALIAS )

                # Save the image
                img.save( t[1] )

                imginfo.mark_avail_e( exp )

                # Now load the thumb into the database
                return obj.db.register_thumb( t[1], obj,
                                              imginfo.get_root_stream(),
                                              f'tb:{exp}' )

            except IOError:
                return None

    def purge_thumbs( self, obj ):

        obj.drop_expendable_streams()

        with ImageInfo( self.imgdb, obj ) as imginfo:
            imginfo.regen()

def _img_stream_factory( db, stream ):

    #TODO pick only image mime types?
    return ImageStream( db, stream )

def _img_obj_factory( db, obj ):

    if( obj.object_type == model.TYPE_FILE
     or obj.object_type == model.TYPE_DUPLICATE ):
        return ImageFile( db, obj )
    elif( obj.object_type == model.TYPE_ALBUM
       or obj.object_type == model.TYPE_PUBLISHED ):
        return Album( db, obj )
    else:
        return None

def _commit_hook( db, is_rollback ):
    global _METADATA_INIT_REQUIRED

    # This hook can cause a write, which will trigger this hook again.
    # Make sure to clear the list before triggering a commit
    flist = _METADATA_INIT_REQUIRED
    _METADATA_INIT_REQUIRED = []

    if( not is_rollback ):
        for obj, stream in flist:
            try:
                db.tbcache.init_metadata( obj, stream )
            except:
                LOG.warning( 'Failed loading metadata for "%s": %s',
                             obj.get_repr(), str( sys.exc_info()[1] ) )

def init_module():

    add_stream_factory( _img_stream_factory )
    add_obj_factory( _img_obj_factory )
    add_pre_commit_hook( _commit_hook )
