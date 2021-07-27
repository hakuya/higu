package ca._4haven.higu.hdbfs.imgdb

import ca._4haven.higu.hdbfs.*
import ca._4haven.higu.hdbfs.basic_objects.*
import ca._4haven.higu.hdbfs.model.*

class ImageStream( db: Database, stream: ModelStream ) : Stream( db, stream ) {

    fun get_dimensions(): Dimensions? {
        /* TODO
        return StreamInfo( this ).get_dims()*/
        return null
    }

    fun get_origin_time() {
        /* TODO

        val origin_ts = StreamInfo( this ).get_origin_time()
        if( origin_ts == null ) return*/

        /* TODO
        return datetime.datetime\
                .utcfromtimestamp( origin_ts )*/
    }

    fun check_metadata() {
        try {
            val ver = this.getItem( ".metaver" )
            if( ver == METADATA_VERSION ) return
        } catch( ex: Exception ) {}
        
        this.db.tbcache.init_stream_metadata( this )
    }
}