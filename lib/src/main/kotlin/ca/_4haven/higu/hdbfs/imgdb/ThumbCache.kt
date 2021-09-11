package ca._4haven.higu.hdbfs.imgdb

import ca._4haven.higu.hdbfs.*
import ca._4haven.higu.hdbfs.ark.*
import ca._4haven.higu.hdbfs.basic_objects.*
import ca._4haven.higu.hdbfs.model.*
import com.sksamuel.scrimage.*
import com.sksamuel.scrimage.nio.JpegWriter
import java.io.IOException
import java.nio.file.Files
import kotlin.io.createTempFile

val METADATA_VERSION = 2

class ThumbCache( val fsdb: Database, val imgdb: StreamDatabase ) {

    var _METADATA_INIT_REQUIRED = mutableListOf< Pair<ImageFile,ImageStream> >()

    init {
        this.fsdb.hooks.add_pre_commit_hook( { db, is_rollback ->
            // This hook can cause a write, which will trigger this hook again.
            // Make sure to clear the list before triggering a commit
            val flist = _METADATA_INIT_REQUIRED
            _METADATA_INIT_REQUIRED = mutableListOf()

            if( !is_rollback ) {
                flist.forEach{  pair ->
                    try {
                        db.tbcache.init_metadata( pair.first, pair.second )
                    } catch( ex: Exception ) {
                        Log.warning( "Failed loading metadata for \"${pair.first.get_repr()}:${pair.second.get_repr()}\": ${ex}" )
                    }
                }
            }
        } )
    }

    fun _require_metadata_init( obj: ImageFile, stream: ImageStream ) {
        this._METADATA_INIT_REQUIRED.add( Pair( obj, stream ) )
    }

    fun get_dimensions( obj: ImageFile ) {
        /* TODO
        return ImageInfo( this.imgdb, obj ).get_obj_dims()*/
    }
    /* TODO
    def get_origin_time( self, obj ):

        imginfo = ImageInfo( self.imgdb, obj )

        origin_ts = imginfo.get_origin_time()
        if( origin_ts is None ):
            return None

        return datetime.datetime\
                .utcfromtimestamp( origin_ts )*/

    fun init_stream_metadata( stream: ImageStream ) {
        /* TODO
        with stream.db._access( write = True ):
            try:
                del stream['creation_time']
            except:
                pass

            streaminfo = StreamInfo( self.imgdb, stream )
            streaminfo.get_origin_time()
            streaminfo.get_dims()
            streaminfo.get_orientation()

            stream['.metaver'] = METADATA_VERSION*/
    }

    fun init_object_metadata( obj: ImageFile ) {
        /* TODO
        with obj.db._access( write = True ):
            try:
                del stream['creation_time']
            except:
                pass

            self.init_stream_metadata( obj.get_root_stream() )

            imginfo = ImageInfo( self.imgdb, obj )
            imginfo.get_origin_time()
            imginfo.get_dims()

            obj['.metaver'] = METADATA_VERSION*/
    }

    fun init_album_metadata( obj: Album ) {
        /* TODO
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

            obj['.metaver'] = METADATA_VERSION*/
    }

    fun init_metadata( obj: Obj, stream: Stream? ) {
        obj.db._access().with {
            when {
                obj is ImageFile -> {
                    this.init_object_metadata( obj )
                    (( stream ?: obj.get_root_stream() ) as? ImageStream)?.let {
                        this.init_stream_metadata( it )
                    }
                }
                obj is Album -> this.init_album_metadata( obj )
                else -> {}
            }   
        }
    }

    fun make_thumb( obj: ImageFile, exp: Int ): ImageStream? {

        val imginfo = ImageInfo( this.imgdb, obj )

        val tbi = imginfo.get_tb_info() ?: return null
        //gen, max_e, use_root = imginfo.get_tb_info()

        val _exp = when {
            exp < ThumbCache.minThumbExp -> ThumbCache.minThumbExp
            exp > tbi.max_e -> tbi.max_e
            else -> exp
        }

        if( _exp == tbi.max_e && tbi.use_root ) {
            return imginfo.get_root_stream()
        }

        val t_stream = obj.get_stream( "tb:${_exp}" ) as? ImageStream
        if( t_stream != null ) return t_stream

        val target_sz = (1 shl _exp)

        // If we're here, we need to produce a thumb
        val work_file = Files.createTempFile( "higu", ".tb" )

        // At this point, we need to create a thumb, open the file
        try {
            val dims = imginfo.get_obj_dims( verify = true ) ?: return null
            val orientation = imginfo.get_orientation()

            var img = imginfo.get_img() ?: return null

            // Always operate in RGB
            // img = img.convert( 'RGB' )

            // Do the rotate
            img = when {
                orientation == Orientation.MIRROR      -> img.flipX()
                orientation == Orientation.R180        -> img.flipX().flipY()
                orientation == Orientation.R180_MIRROR -> img.flipY()
                orientation == Orientation.R90_MIRROR  -> img.flipX().rotateRight()
                orientation == Orientation.R90         -> img.rotateRight()
                orientation == Orientation.R270_MIRROR -> img.flipX().rotateLeft()
                orientation == Orientation.R270        -> img.rotateLeft()
                else -> img
            }

            // Do the resize
            if( dims.width > target_sz || dims.height > target_sz ) {
                val target_dims = if( dims.width > dims.height ) {
                                        Dimensions( target_sz, dims.height * target_sz / dims.width )
                                    } else {
                                        Dimensions( dims.width * target_sz / dims.height, target_sz )
                                    }

                img = img.scaleTo( target_dims.width, target_dims.height, ScaleMethod.Lanczos3 )
            }

            // Save the image
            val writer = JpegWriter().withCompression( 90 )
            img.output( writer, work_file )

            // Now load the thumb into the database
            return obj.db.register_thumb( work_file.toString(), obj,
                                          imginfo.get_root_stream()!!,
                                          "tb:${exp}" ) as? ImageStream
        } catch( ex: IOException ) {
            return null
        }
    }

    fun purge_thumbs( obj: ImageFile ) {
        obj.drop_expendable_streams()
        ImageInfo( this.imgdb, obj ).get_tb_info( true )
    }

    companion object {
        var minThumbExp = 7
    }
}