package ca._4haven.higu.hdbfs.imgdb

class StreamInfo( stream: ImageStream ) {

    private var w: Int? = null
    private var h: Int? = null

    private var orientation: Int? = null
    private var img: Int? = null
    private var origin_time: Int? = null

    /* TODO
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

                try:
                    exif = self.img._getexif()
                except:
                    exif = []
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
                        raise ValueError, 'Bad date <%r>: %r' % ( original_date, sys.exc_info()[1] )
                    break

            if( self.origin_time is not None ):
                self.stream['origin_time'] = self.origin_time

        return self.origin_time*/
}