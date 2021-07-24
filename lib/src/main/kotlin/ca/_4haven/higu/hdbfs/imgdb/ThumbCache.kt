package ca._4haven.higu.hdbfs.imgdb

import ca._4haven.higu.hdbfs.*
import ca._4haven.higu.hdbfs.ark.*
import ca._4haven.higu.hdbfs.basic_objects.*
import ca._4haven.higu.hdbfs.model.*

val MIN_THUMB_EXP = 7
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

    /* TODO
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
        ImageInfo( self.imgdb, obj ).get_tb_info( True )*/
}