package ca._4haven.higu.hdbfs.basic_objects

import ca._4haven.higu.hdbfs.*
import ca._4haven.higu.hdbfs.model.*

object Factories {
    init {
        ObjectFactory.add_stream_factory( { db, stream ->
            Stream( db, stream )
        } )
        ObjectFactory.add_obj_factory( { db, obj ->
            when {
                obj.object_type == TYPE_FILE -> File( db, obj )
                obj.object_type == TYPE_ALBUM -> Group( db, obj )
                obj.object_type == TYPE_CLASSIFIER -> Tag( db, obj )
                else -> null
            }
        } )
    }
}