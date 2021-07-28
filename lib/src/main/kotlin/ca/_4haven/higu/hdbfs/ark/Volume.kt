package ca._4haven.higu.hdbfs.ark

import ca._4haven.higu.hdbfs.model.Id
import java.io.*

interface Volume {
    enum class State {
        CLEAN,
        COMITTED,
        DIRTY,
    }

    fun verify(): Boolean
    fun read( id: Id, priority: Int, extension: String? ): InputStream?
    fun get_state(): State
    fun reset_state()
    fun commit()
    fun rollback()
    fun load_data( path: String, id: Id, priority: Int, extension: String? )
    fun delete( id: Id, priority: Int, extension: String? )

    fun _debug_write( id: Id, priority: Int, extension: String? ): OutputStream?
}