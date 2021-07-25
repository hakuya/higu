package ca._4haven.higu.hdbfs.imgdb

import ca._4haven.higu.hdbfs.*
import ca._4haven.higu.hdbfs.model.*
import java.nio.file.*

val IMGDB_DATA_PATH = "imgdat"
val IMGDB_THUMB_PATH = "tbdat"

class Config( val imgdb_path: String ) {

    fun get_file_vol_path( vol_id: Id, priority: Int ): Path {

        val path = when {
            priority > SP_EXPENDABLE -> Paths.get( this.imgdb_path, IMGDB_DATA_PATH )
            else -> Paths.get( this.imgdb_path, IMGDB_THUMB_PATH )
        }

        var lv2 = vol_id and 0xfff
        var lv3 = (vol_id shr 12) and 0xfff
        var lv4 = (vol_id shr 24) and 0xfff

        if( lv4 != 0.toLong() ) throw RuntimeException()

        return path.resolve( "%03x".format( lv3 ) )
                   .resolve( "%03x".format( lv2 ) )
    }
}
