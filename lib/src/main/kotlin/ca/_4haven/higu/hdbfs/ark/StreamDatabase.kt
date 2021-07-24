package ca._4haven.higu.hdbfs.ark

import ca._4haven.higu.hdbfs.imgdb.Config

class StreamDatabase( val data_config: Config ) {

    private val volumes = mutableMapOf<Int,Volume>()
    private var state = "clean"

    private fun __get_volume( vol_id: Int ): Volume {

        if( this.volumes.containsKey( vol_id ) ) {
            return this.volumes[vol_id]!!
        }

        val vol = FileVolume( this.data_config, vol_id )
        this.volumes[vol_id] = vol

        return vol
    }

    private fun __get_vol_for_id( id: Int ): Volume {
        return this.__get_volume( id shr 12 )
    }

    fun get_state(): String = this.state

    fun reset_state() {
        this.volumes.values.forEach { vol ->
            vol.reset_state()
        }

        this.state = "clean"
    }


    fun prepare_commit() {
        /* TODO
        if( self.state == 'clean' ):
            return

        assert self.state != 'prepared'

        vols = self.volumes.values()
        # Clean things up before we begin. We need to do this so that
        # We can determine the volumes that changes as part of this
        # commit
        for vol in vols:
            assert vol.get_state() != 'committed'

        try:
            # Try to commit all the dirty volumes
            for vol in vols:
                if( vol.get_state() == 'dirty' ):
                    vol.commit()
        except:
            # Something went wrong, rollback
            for vol in vols:
                if( vol.get_state() == 'committed' ):
                    vol.rollback()

            raise

        # Comitted
        self.state = 'prepared'*/
    }

    fun unprepare_commit() {
        /* TODO
        if( self.state == 'clean' ):
            return

        assert self.state == 'prepared'

        vols = self.volumes.values()
        for vol in vols:
            assert vol.get_state() != 'dirty'
            if( vol.get_state() == 'committed' ):
                vol.rollback()

        for vol in vols:
            assert vol.get_state() != 'committed'

        self.state = 'dirty'*/
    }

    fun complete_commit() {
        /* TODO
        if( self.state == 'clean' ):
            return

        assert self.state == 'prepared'

        vols = self.volumes.values()
        for vol in vols:
            if( vol.get_state() == 'committed' ):
                vol.reset_state()

        self.state = 'clean'*/
    }

    fun commit() {
        this.prepare_commit()
        this.complete_commit()
    }

    fun rollback() {
        /* TODO
        vols = self.volumes.values()

        if( self.state == 'clean' ):
            for vol in vols:
                assert vol.get_state() == 'clean'
            return

        if( self.state == 'prepared' ):
            self.unprepare_commit()

        if( self.state == 'dirty' ):
            for vol in vols:
                assert vol.get_state() != 'committed'
                if( vol.get_state() == 'dirty' ):
                    vol.rollback()

            for vol in vols:
                assert vol.get_state() == 'clean'

            self.state = 'clean'*/
    }

    fun load_data( path: String, id: Int, priority: Int, extension: String? ) {

        /* TODO
        if( self.state == 'committed' ):
            # Clean things up before we begin. We need to do this so that
            # We can determine the volumes that changes as part of this
            # commit
            self.reset_state()

        self.state = 'dirty'

        v = self.__get_vol_for_id( id )
        v.load_data( path, id, priority, extension )*/
    }

    fun delete( id: Int, priority: Int, extension: String? ) {

        if( this.state == "committed" ) {
            // Clean things up before we begin. We need to do this so that
            // We can determine the volumes that changes as part of this
            // commit
            this.reset_state()
        }

        this.state = "dirty"

        val v = this.__get_vol_for_id( id )
        v.delete( id, priority, extension )
    }

    fun read( id: Int, priority: Int, extension: String? ): Int {
        return this.__get_vol_for_id( id )
                   .read( id, priority, extension )
    }

    /* TODO
    def _debug_write( self, id, priority, extension ):

        v = self.__get_vol_for_id( id )
        return v._debug_write( id, priority, extension )
    */
}