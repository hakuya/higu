package ca._4haven.higu.hdbfs.imgdb

import ca._4haven.higu.hdbfs.ark.*
import com.sksamuel.scrimage.ImmutableImage
import java.io.IOException

class StreamInfo( val imgdb: StreamDatabase, val stream: ImageStream ) {

    private var dims: Dimensions? = null

    private var orientation: Orientation? = null
    private var img: ImmutableImage? = null
    private var origin_time: Int? = null

    fun get_img(): ImmutableImage? {

        if( this.img == null ) {
            val i_stm = this.stream.read() ?: return null

            try {
                this.img = ImmutableImage.loader().apply {
                    detectOrientation( false )
                 }.fromStream( i_stm )
            } catch( ex: IOException ) {
                Log.warning( "Failed opening image for \"${this.stream.get_repr()}\": ${ex}" )
            }
        }

        return this.img
    }

    fun get_orientation(): Orientation {

        if( this.orientation == null ) {
            try {
                this.orientation = (this.stream.getItem( "orientation" ) as? Int)
                                        ?.let { Orientation.fromInt( it ) }
            } catch( ex: Exception ) {
            }
        }

        if( this.orientation == null ) {
            try {
                this.orientation = (this.stream.getItem( "rotation" ) as? Int)
                                        ?.let {
                                            when {
                                                it == 0 -> Orientation.NORMAL
                                                it == 1 -> Orientation.R90
                                                it == 2 -> Orientation.R180
                                                it == 3 -> Orientation.R270
                                                else -> null
                                            }
                                        }
            } catch( ex: Exception ) {
            }
            this.stream.db._access( write = true ). with {
                this.orientation?.let {
                    this.stream.setItem( "orientation", it.value )
                }
                this.stream.delItem( "rotation" )
            }
        }

        if( this.orientation == null ) {
            try {
                this.orientation = this.get_img()?.metadata?.orientation?.get()
                                    ?.ordinal?.let { Orientation.fromInt( it ) }

            } catch( ex: Exception ) {
            }
            this.orientation?.let {
                this.stream.setItem( "orientation", it.value )
            }
        }

        if( this.orientation == null ) {
            this.orientation = Orientation.NORMAL
            this.orientation?.let {
                this.stream.setItem( "orientation", it.value )
            }
        }

        return this.orientation!!
    }

    fun get_dims(): Dimensions? {

        if( this.dims == null ) {
            try {
                val w = this.stream.getItem( "width" ) as? Int
                val h = this.stream.getItem( "height" ) as? Int

                if( w != null && h != null ) {
                    dims = Dimensions( w, h )
                }
            } catch( ex: Exception ) {
            }
        }

        // Image info is not present, we need to read it from the file
        if( this.dims == null ) {
            try {
                val img = this.get_img() ?: return null
                this.dims = Dimensions( img.width, img.height )
            } catch( ex: IOException ) {
                return null
            }

            this.stream.db._access( write = true ).with {
                this.stream.setItem( "width", this.dims!!.width )
                this.stream.setItem( "height", this.dims!!.height )
            }
        }

        return this.dims
    }

    /* TODO
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
