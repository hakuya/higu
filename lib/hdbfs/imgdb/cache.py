import calendar
import datetime
import os
import tempfile

from hdbfs.imgdb.defs import *
from hdbfs.imgdb.info import StreamInfo, ImageInfo
from hdbfs.imgdb.objects import ImageFile, Album

MIN_THUMB_EXP = 7

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

    def get_thumb_sizes( self, obj ):

        with ImageInfo( self.imgdb, obj ) as imginfo:

            w, h = imginfo.get_obj_dims()

            maxdim = w if( w > h ) else h
            sizes = [ 1 << MIN_THUMB_EXP ]
            exps = [ MIN_THUMB_EXP ]

            while( sizes[-1] < maxdim ):
                sizes.append( sizes[-1] * 2 )
                exps.append( exps[-1] + 1 )

            sizes[-1] = maxdim

            tb_names = list( map( lambda e: f'tb:{e}', exps ) )
            tb_names[-1] = '.'

            ls = obj.list_streams()

            if( w > h ):
                return list( map( lambda x, e, n: ( e, x, x * h // w, n in ls ), sizes, exps, tb_names ) )
            else:
                return list( map( lambda y, e, n: ( e, y * w // h, y, n in ls ), sizes, exps, tb_names ) )
