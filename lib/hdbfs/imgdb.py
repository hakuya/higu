import calendar
import datetime
import os
import sys
import tempfile

import model

from defs import *
from basic_objs import *
from hooks import *
from obj_factory import add_obj_factory

IMGDB_DATA_PATH = 'imgdat'
IMGDB_THUMB_PATH = 'tbdat'

MIN_THUMB_EXP = 7

METADATA_VERSION = 2

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

        self.w = None
        self.h = None
        self.orientation = None
        self.img = None
        self.origin_time = None

    def get_img( self ):

        from PIL import Image

        if( self.img is None ):
            f = self.stream.read()
            if( f is None ):
                return None

            try:
                self.img = Image.open( f )
            except IOError:
                LOG.warning(
                        'Failed opening image for "%s": %s',
                        self.stream.get_repr(), str( sys.exc_info()[1] ) )

        return self.img

    def get_orientation( self ):

        if( self.orientation is None ):
            try:
                self.orientation = self.stream['orientation']
            except:
                pass

        if( self.orientation is None ):
            try:
                rot = self.stream['rotation']
                if( rot == 0 ):
                    self.orientation = 1
                elif( rot == 1 ):
                    self.orientation = 6
                elif( rot == 2 ):
                    self.orientation = 3
                elif( rot == 3 ):
                    self.orientation = 8
                del self.stream['rotation']
            except:
                pass

        if( self.orientation is None ):
            self.get_img()
            if( self.img is not None and 'exif' in self.img.info ):
                ORIENTATION = 274

                exif = self.img._getexif()
                if( ORIENTATION in exif \
                and exif[ORIENTATION] != '' ):

                    self.orientation = int( exif[ORIENTATION] )
                    if( self.orientation < 1 or self.orientation > 8 ):
                        self.orientation = 1

            if( self.orientation is None ):
                self.orientation = 1
            self.stream['orientation'] = self.orientation

        return self.orientation

    def get_dims( self ):

        if( self.w is None or self.h is None ):
            try:
                self.w = self.stream['width']
            except:
                pass

            try:
                self.h = self.stream['height']
            except:
                pass

        # Image info is not present, we need to read it from the file
        if( self.w is None or self.h is None ):
            try:
                self.get_img()
                if( self.img is None ):
                    return None, None

                self.w, self.h = self.img.size
            except IOError:
                return None, None

            self.stream['width'] = self.w
            self.stream['height'] = self.h

        return self.w, self.h

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

                exif = self.img._getexif()
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
                        dt = datetime.datetime.strptime(
                                    original_date,
                                    '%Y:%m:%d %H:%M:%S' )
                        self.origin_time = calendar.timegm( dt.timetuple() )
                    except:
                        raise ValueError, 'Bad date <%r>: %r' % ( original_date, sys.exc_info()[1] )
                    break

            if( self.origin_time is not None ):
                self.stream['origin_time'] = self.origin_time

        return self.origin_time

class ImageInfo:

    def __init__( self, imgdb, obj ):

        self.imgdb = imgdb
        self.obj = obj
        self.root_si = None

        self.tb_gen = None
        self.max_e = None
        self.use_root = None

        self.obj_w = None
        self.obj_h = None

        self.origin_time = None

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

        if( self.obj_w is None or self.obj_h is None ):

            try:
                self.obj_w = self.obj['width']
            except:
                pass

            try:
                self.obj_h = self.obj['height']
            except:
                pass

        if( verify or self.obj_w is None or self.obj_h is None ):

            w, h = self.get_dims()
            orientation = self.get_orientation()

            if( orientation > 4 ):
                w, h = h, w

            if( self.obj_w != w or self.obj_h != h ):
                self.obj_w = w
                self.obj_h = h

                self.obj['width'] = w
                self.obj['height'] = h

        return self.obj_w, self.obj_h

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
            orientation = self.get_orientation()

            if( self.tb_gen is not None ):
                self.tb_gen += 1
            else:
                self.tb_gen = 0

            self.max_e = 0
            if( orientation == 1 ):
                self.use_root = 1
            else:
                self.use_root = 0

            while( 2**self.max_e < w or 2**self.max_e < h ):
                self.max_e += 1

            tb_info = [ self.tb_gen, self.max_e, self.use_root ]
            self.obj['.tbinfo'] = ':'.join( map( str, tb_info ) )

        return self.tb_gen, self.max_e, self.use_root

class ImageStream( Stream ):

    def __init__( self, db, stream ):

        Stream.__init__( self, db, stream )

    def get_dimensions( self ):

        sinfo = StreamInfo( self.db, self )
        return sinfo.get_dims()

    def get_origin_time( self ):

        sinfo = StreamInfo( self.db, self )
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

    def set_root_stream( self, stream ):

        File.set_root_stream( self, stream )
        self.db.tbcache.purge_thumbs( self )
        self.db.tbcache.init_object_metadata( self )

        # Trigger a metadata update on the albums
        for album in self.get_albums():
            album._on_children_changed()

    def _on_created( self, stream ):

        _require_metadata_init( self, stream )

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

    def __reorient( self, remap ):

        with self.db._access( write = True ):
            if( self.obj.root_stream is None ):
                return

            try:
                orientation = self.obj.root_stream['orientation']
            except:
                orientation = 1

            orientation = remap[orientation-1]
            self.obj.root_stream['orientation'] = orientation

            # We need to purge the size
            try:
                del self.obj['width']
            except KeyError:
                pass

            try:
                del self.obj['height']
            except KeyError:
                pass

        self.db.tbcache.purge_thumbs( self )

    def rotate_cw( self ):

        CW_REMAP = [ 6, 5, 8, 7, 4, 3, 2, 1 ]
        self.__reorient( CW_REMAP )

    def rotate_ccw( self ):

        CCW_REMAP = [ 8, 7, 6, 5, 2, 1, 4, 3 ]
        self.__reorient( CCW_REMAP )

    def mirror( self ):

        MIRROR_REMAP = [ 2, 1, 4, 3, 8, 7, 6, 5 ]
        self.__reorient( MIRROR_REMAP )

    def auto_orientation( self ):

        with self.db._access( write = True ):
            try:
                del self.obj.root_stream['orientation']
            except KeyError:
                pass

            try:
                del self.obj['width']
            except KeyError:
                pass

            try:
                del self.obj['height']
            except KeyError:
                pass

        self.db.tbcache.purge_thumbs( self )

    def get_thumb_stream( self, exp ):

        return self.db.tbcache.make_thumb( self, exp )

    def check_metadata( self ):

        try:
            ver = self['.metaver']
            if( ver == METADATA_VERSION ):
                return
        except:
            pass
        
        self.db.tbcache.init_object_metadata( self )

class Album( OrderedGroup ):

    def __init__( self, db, obj ):

        OrderedGroup.__init__( self, db, obj )

    def _on_created( self, stream ):

        _require_metadata_init( self, None )

    def _on_children_changed( self ):

        _require_metadata_init( self, None )

    def get_origin_time( self ):

        print 'GO1'
        self.check_metadata()
        print 'GO2'
        try:
            print 'GO3'
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

        imginfo = ImageInfo( self.imgdb, obj )
        return imginfo.get_obj_dims()

    def get_origin_time( self, obj ):

        imginfo = ImageInfo( self.imgdb, obj )

        origin_ts = imginfo.get_origin_time()
        if( origin_ts is None ):
            return None

        return datetime.datetime\
                .utcfromtimestamp( origin_ts )

    def init_stream_metadata( self, stream ):

        try:
            del stream['creation_time']
        except:
            pass

        streaminfo = StreamInfo( self.imgdb, stream )
        streaminfo.get_origin_time()
        streaminfo.get_dims()
        streaminfo.get_orientation()

        stream['.metaver'] = METADATA_VERSION

    def init_object_metadata( self, obj ):

        try:
            del stream['creation_time']
        except:
            pass

        self.init_stream_metadata( obj.get_root_stream() )

        imginfo = ImageInfo( self.imgdb, obj )
        imginfo.get_origin_time()
        imginfo.get_dims()

        obj['.metaver'] = METADATA_VERSION

    def init_album_metadata( self, obj ):

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

        if( isinstance( obj, ImageFile ) ):
            if( stream == None ):
                stream = obj.get_root_stream()

            self.init_stream_metadata( stream )
            self.init_object_metadata( obj )
        elif( isinstance( obj, Album ) ):
            self.init_album_metadata( obj )

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

def _img_stream_factory( db, stream ):

    #TODO pick only image mime types?
    return ImageStream( db, stream )

def _img_obj_factory( db, obj ):

    if( obj.object_type == TYPE_FILE ):
        return ImageFile( db, obj )
    elif( obj.object_type == TYPE_ALBUM ):
        return Album( db, obj )
    else:
        return None

def _post_commit_hook( db, is_rollback ):
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
                LOG.warning( 'Failed loading metadata for "%s:%s": %s',
                             obj.get_repr(), str( sys.exc_info()[1] ) )

def init_module():

    add_stream_factory( _img_stream_factory )
    add_obj_factory( _img_obj_factory )
    add_post_commit_hook( _post_commit_hook )
