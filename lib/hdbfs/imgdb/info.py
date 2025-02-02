import calendar
import datetime
import sys

import hdbfs.ark

import hdbfs.basic_objs
import hdbfs.model as model
import hdbfs.imgdb.exif as exif

from hdbfs.defs import *

from typing import Optional

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
            return None, None

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

    def __init__( self, imgdb, obj: 'ImageFile' ):

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

    def __get_info( self, lazy: bool = False ) -> Optional[model.ImageInfo]:

        if( self.info is None ):
            self.info = self.obj.obj.info

        if( self.info is None and not lazy ):
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

    def is_available( self ):

        return self.__get_info( True ) is not None

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
            return None, None

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

        request = self.obj.obj.request
        if( request is not None ):
            self.obj.db.session.delete( request )

        self.obj.obj.request = None

    def get_avail_e( self ) -> int:

        info = self.__get_info()
        if( info is None ):
            return 0

        if( info.avail_e is None ):
            return False

        avail_e = info.avail_e

        if( self.get_use_root() ):
            avail_e = avail_e | (1 << self.get_max_e())

        return avail_e

    def is_avail_e( self, exp: int ) -> bool:
        '''Returns true if the given exp is available.'''

        return (self.get_avail_e() & (1 << exp))

    def mark_avail_e( self, exp: int ) -> None:
        '''Marks the thumb with the given exp as available.'''

        info = self.__get_info()
        if( info is None ):
            return

        base = info.avail_e if( info.avail_e is not None ) else 0
        info.avail_e = (base | (1 << exp))

        self.clear_requested_e( exp )

    def mark_requested_mask( self, mask: Optional[int], prio: model.ImageRequestPriority ) -> None:

        request = self.obj.obj.request

        if( request is None ):
            request = model.ImageRequest( self.obj.obj, prio.value, mask )
            self.obj.db.session.add( request )

        elif( mask is not None ):
            base = request.exp_mask if( request.exp_mask is not None ) else 0
            request.exp_mask = (base | mask)

            if( request.prio is None or prio.value > request.prio ):
                request.prio = prio.value

        self.obj.db.session.flush()

    def mark_requeted_e( self, exp: int, prio: model.ImageRequestPriority ) -> None:
        '''Marks the thumb with the given exp as requested.'''

        self.mark_requested_mask( (1 << exp), prio )

    def clear_requested_e( self, exp: int ) -> None:
        '''Clears a request for the thumb with the given exp.'''

        request = self.obj.obj.request

        if( request is None ):
            return

        if( request.exp_mask is not None ):
            exp_mask = (request.exp_mask & ~(1 << exp))
            if( exp_mask == 0 ):
                self.obj.db.session.delete( request )
            else:
                request.exp_mask = exp_mask

        self.obj.db.session.flush()

    def get_thumb( self, exp: int, lazy: bool = False ) -> 'ImageStream':

        # We need basic info for max_e and use_root.
        # If these aren't populated, abort if we're lazy
        if( self.__get_info( lazy ) is None ):
            return None

        max_e = self.get_max_e()
        use_root = self.get_use_root()

        if( exp >= max_e ):
            if( use_root == 1 ):
                self.clear_requested_e( exp )
                return self.get_root_stream()
            else:
                exp = max_e

        t_stream = self.obj.get_stream( f'tb:{exp}' )
        if( t_stream is not None ):
            if( not self.is_avail_e( exp ) ):
                self.mark_avail_e( exp )
            return t_stream

        return None
