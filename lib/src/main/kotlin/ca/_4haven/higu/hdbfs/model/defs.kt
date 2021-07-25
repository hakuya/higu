package ca._4haven.higu.hdbfs.model

import ca._4haven.higu.hdbfs.dbutils.Schema

typealias Id = Long
typealias ObjType = Int

val HDBFS_VERSION = Schema.Version( 10, 0 )
val IMGDB_VERSION = Schema.Version( 1, 0 )