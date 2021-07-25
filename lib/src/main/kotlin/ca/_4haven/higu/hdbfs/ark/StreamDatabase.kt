package ca._4haven.higu.hdbfs.ark

import ca._4haven.higu.hdbfs.imgdb.Config
import ca._4haven.higu.hdbfs.model.Id
import java.io.InputStream

class StreamDatabase( val data_config: Config ) {
    enum class State {
        CLEAN,
        COMITTED,
        DIRTY,
        PREPARED,
    }

    private val volumes = mutableMapOf<Id,Volume>()
    private var state = State.CLEAN

    private fun __get_volume( vol_id: Id ): Volume {

        if( this.volumes.containsKey( vol_id ) ) {
            return this.volumes[vol_id]!!
        }

        val vol = FileVolume( this.data_config, vol_id )
        this.volumes[vol_id] = vol

        return vol
    }

    private fun __get_vol_for_id( id: Id ): Volume {
        return this.__get_volume( id shr 12 )
    }

    fun get_state(): State = this.state

    fun reset_state() {
        this.volumes.values.forEach { vol ->
            vol.reset_state()
        }

        this.state = State.CLEAN
    }


    fun prepare_commit() {
        if( this.state == State.CLEAN ) return
        if( this.state == State.PREPARED ) throw IllegalStateException()

        val vols = this.volumes.values
        // Clean things up before we begin. We need to do this so that
        // We can determine the volumes that changes as part of this
        // commit
        vols.forEach {
            assert( it.get_state() != Volume.State.COMITTED )
        }

        try {
            // Try to commit all the dirty volumes
            vols.forEach {
                if( it.get_state() == Volume.State.DIRTY ) {
                    it.commit()
                }
            }
        } catch( ex: Exception ) {
            // Something went wrong, rollback
            vols.forEach {
                if( it.get_state() == Volume.State.COMITTED ) {
                    it.rollback()
                }
            }

            throw ex
        }

        // Comitted
        this.state = State.PREPARED
    }

    fun unprepare_commit() {
        if( this.state != State.PREPARED ) throw IllegalStateException()

        val vols = this.volumes.values
        vols.forEach {
            assert( it.get_state() != Volume.State.DIRTY )
            if( it.get_state() == Volume.State.COMITTED ) {
                it.rollback()
            }
        }

        vols.forEach {
            assert( it.get_state() != Volume.State.COMITTED )
        }

        this.state = State.DIRTY
    }

    fun complete_commit() {
        if( this.state != State.PREPARED ) throw IllegalStateException()

        this.volumes.values.forEach {
            if( it.get_state() == Volume.State.COMITTED ) {
                it.reset_state()
            }
        }

        this.state = State.CLEAN
    }

    fun commit() {
        this.prepare_commit()
        this.complete_commit()
    }

    fun rollback() {
        val vols = this.volumes.values

        if( this.state == State.CLEAN ) {
            vols.forEach {
                assert( it.get_state() == Volume.State.CLEAN )
            }
            return
        }

        if( this.state == State.PREPARED ) {
            this.unprepare_commit()
        }

        if( this.state == State.DIRTY ) {
            vols.forEach {
                assert( it.get_state() != Volume.State.COMITTED )
                if( it.get_state() == Volume.State.DIRTY ) {
                    it.rollback()
                }
            }

            vols.forEach {
                assert( it.get_state() == Volume.State.CLEAN )
            }

            this.state = State.CLEAN
        }
    }

    fun load_data( path: String, id: Id, priority: Int, extension: String? ) {

        if( this.state == State.COMITTED ) {
            // Clean things up before we begin. We need to do this so that
            // We can determine the volumes that changes as part of this
            // commit
            this.reset_state()
        }

        this.state = State.DIRTY

        this.__get_vol_for_id( id )
            .load_data( path, id, priority, extension )
    }

    fun delete( id: Id, priority: Int, extension: String? ) {

        if( this.state == State.COMITTED ) {
            // Clean things up before we begin. We need to do this so that
            // We can determine the volumes that changes as part of this
            // commit
            this.reset_state()
        }

        this.state = State.DIRTY

        val v = this.__get_vol_for_id( id )
        v.delete( id, priority, extension )
    }

    fun read( id: Id, priority: Int, extension: String? ): InputStream? {
        return this.__get_vol_for_id( id )
                   .read( id, priority, extension )
    }

    /* TODO
    def _debug_write( self, id, priority, extension ):

        v = self.__get_vol_for_id( id )
        return v._debug_write( id, priority, extension )
    */
}