package ca._4haven.higu.hdbfs.imgdb

import ca._4haven.higu.hdbfs.*
import ca._4haven.higu.hdbfs.model.*

object Factories {
    init {
        ObjectFactory.add_stream_factory( { db, stream ->
            // TODO pick only image mime types?
            ImageStream( db, stream )
        } )
        ObjectFactory.add_obj_factory( { db, obj ->
            when {
                obj.object_type == TYPE_FILE -> ImageFile( db, obj )
                obj.object_type == TYPE_ALBUM -> Album( db, obj )
                else -> null
            }
        } )
    }
}