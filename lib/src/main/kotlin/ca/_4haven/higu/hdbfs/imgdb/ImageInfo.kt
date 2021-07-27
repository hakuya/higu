package ca._4haven.higu.hdbfs.imgdb

import ca._4haven.higu.hdbfs.ark.*
import com.sksamuel.scrimage.ImmutableImage

class ImageInfo( val imgdb: StreamDatabase, val obj: ImageFile ) {

    data class ThumbInfo( val gen: Int, val max_e: Int, val use_root: Boolean )

    private var root_si: StreamInfo? = null

    private var tbinfo: ThumbInfo? = null

    private var dims: Dimensions? = null

    private var origin_time: Int? = null

    fun get_root_stream_info(): StreamInfo? {

        if( this.root_si == null ) {
            val root_s = this.obj.get_root_stream() as? ImageStream
            if( root_s != null ) {
                this.root_si = StreamInfo( this.imgdb, root_s )
            }
        }

        return this.root_si
    }

    fun get_root_stream(): ImageStream? {
        return this.get_root_stream_info()?.stream
    }

    fun get_img(): ImmutableImage? {
        return this.get_root_stream_info()?.get_img()
    }

    fun get_orientation(): Orientation {
        return this.get_root_stream_info()?.get_orientation()
                    ?: Orientation.NORMAL
    }

    fun get_dims(): Dimensions? {
        return this.get_root_stream_info()?.get_dims()
    }

    /* TODO
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

        return self.origin_time*/

    fun get_obj_dims( verify: Boolean = false ): Dimensions? {

        if( !verify && this.dims == null ) {

            try {
                val obj_w = this.obj.getItem( "width" ) as? Int
                val obj_h = this.obj.getItem( "height" ) as? Int

                if( obj_w != null && obj_h != null ) {
                    this.dims = Dimensions( obj_w, obj_h )
                }
            } catch( ex: Exception ) {
            }
        }

        if( verify || this.dims == null ) {

            var dims = this.get_dims() ?: return null
            val orientation = this.get_orientation()

            if( orientation.value > 4 ) {
                dims = Dimensions( dims.height, dims.width )
            }

            if( this.dims == null || !dims.equals( dims ) ) {
                this.dims = dims

                this.obj.setItem( "width", dims.width )
                this.obj.setItem( "height", dims.height )
            }
        }

        return this.dims
    }

    fun get_tb_info( bump_gen: Boolean = false ): ThumbInfo? {

        if( this.tbinfo == null ) {
            try {
                val tbinfo = this.obj.getItem( ".tbinfo" )
                                ?.let { it.toString() }?.split( ":" )
                                ?.map { it.toInt() }

                this.tbinfo = tbinfo?.let { ThumbInfo( it[0], it[1], it[2] != 0 ) }
            } catch( ex: Exception ) {
            }
        }

        if( bump_gen || this.tbinfo == null ) {

            var tb_gen = this.tbinfo?.gen?.let { it + 1 } ?: 0

            var max_e = this.tbinfo?.max_e
                            ?: this.get_dims()?.let { dims ->
                                var result = 0

                                while( (1 shl result) < dims.width
                                    || (1 shl result) < dims.height )
                                {
                                    result += 1
                                }
                                result
                            }

            var use_root = this.tbinfo?.use_root
                            ?: this.get_orientation().let { it ->
                                it == Orientation.NORMAL
                            }

            if( max_e != null ) {
                this.tbinfo = ThumbInfo( tb_gen, max_e, use_root )
                this.obj.setItem( ".tbinfo", "${tb_gen}:${max_e}:${(if( use_root ) 1 else 0)}" )
            }
        }

        return this.tbinfo
    }
}
