package ca._4haven.higu.hdbfs

val VERSION = 2
val REVISION = 0

val HIGURASHI_DB_NAME = "hfdb.dat"

val TYPE_NILL       = 0
val TYPE_FILE       = 1000
val TYPE_GROUP      = 2000
val TYPE_ALBUM      = 2001
val TYPE_CLASSIFIER = 2002

val SP_EXPENDABLE = 1000
val SP_NORMAL     = 2000
val SP_PRIORITY   = 3000

val NAME_POLICY_DONT_REGISTER   = 0
val NAME_POLICY_DONT_SET        = 1
val NAME_POLICY_SET_IF_UNDEF    = 2
val NAME_POLICY_SET_ALWAYS      = 3

typealias NamePolicy = Int
