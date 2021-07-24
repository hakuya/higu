package ca._4haven.higu.hdbfs.ark

interface Volume {
    fun verify(): Boolean
    fun read( id: Int, priority: Int, extension: String? ): Int
    fun get_state(): String
    fun reset_state()
    fun commit()
    fun rollback()
    fun load_data( path: String, id: Int, priority: Int, extension: String? )
    fun delete( id: Int, priority: Int, extension: String? )
}