package ca._4haven.higu.hdbfs.ark

import ca._4haven.higu.hdbfs.imgdb.Config

class FileVolume( val data_config: Config, val vol_id: Int ) : Volume {

    private var to_commit = listOf<String>()
    private var state = "clean"
    private var rm_dir: String? = null

    /* TODO
    def __get_path( self, id, priority, extension ):

        path = self.data_config.get_file_vol_path( self.vol_id, priority )
        return os.path.join( path, '%016x.%s' % ( id, extension ) )*/

    override fun verify(): Boolean {
        return true
    }

    override fun read( id: Int, priority: Int, extension: String? ): Int {
        /* TODO
        p = self.__get_path( id, priority, extension )
        if( not os.path.isfile( p ) ):
            return None
        else:
            try:
                return open( p, 'rb' )
            except IndexError:
                return None
        */
        return 0
    }

    /* TODO
    def _debug_write( self, id, priority, extension ):

        p = self.__get_path( id, priority, extension )

        try:
            return open( p, 'wb' )
        except IndexError:
            return None*/

    override fun get_state(): String = this.state

    override fun reset_state() {
        /* TODO
        self.to_commit = []
        self.state = 'clean'

        rm_dir = self.rm_dir
        self.rm_dir = None
        self.to_commit = []

        if( rm_dir is not None ):
            shutil.rmtree( rm_dir )*/
    }

    override fun commit() {
        /* TODO
        completion = 0

        try:
            for t in self.to_commit:
                shutil.move( t[0], t[1] )
                completion += 1

        except:
            # Something went wrong, rollback
            for t in self.to_commit[:completion]:
                shutil.move( t[1], t[0] )

            # Sometimes move() seems to leave files behind
            for t in self.to_commit:
                try:
                    if( os.path.isfile( t[1] ) ):
                        os.remove( t[1] )
                except:
                    pass

            raise

        # Comitted
        self.state = 'committed'*/
    }

    override fun rollback() {
        /* TODO
        if( self.state == 'dirty' ):
            self.to_commit = []
            self.state = 'clean'

        elif( self.state == 'committed' ):
            for t in self.to_commit:
                shutil.move( t[1], t[0] )

            # Sometimes move() seems to leave files behind
            for t in self.to_commit:
                try:
                    if( os.path.isfile( t[1] ) ):
                        os.remove( t[1] )
                except:
                    pass

            self.state = 'dirty'*/
    }

    override fun load_data( path: String, id: Int, priority: Int, extension: String? ) {
        /* TODO
        if( self.state == 'committed' ):
            self.reset_state()

        self.state = 'dirty'

        new_path = self.data_config.get_file_vol_path( self.vol_id, priority )
        if( not os.path.isdir( new_path ) ):
            os.makedirs( new_path )

        tgt = os.path.join( new_path, '%016x.%s' % ( id, extension ) )
        self.to_commit.append( ( path, tgt, ) )*/
    }

    override fun delete( id: Int, priority: Int, extension: String? ) {
        /* TODO
        if( self.state == 'committed' ):
            self.reset_state()

        self.state = 'dirty'

        if( self.rm_dir is None ):
            self.rm_dir = tempfile.mkdtemp()

        src = self.__get_path( id, priority, extension )
        if( not os.path.isfile( src ) ):
            return

        name = os.path.split( src )[-1]
        tgt = os.path.join( self.rm_dir, name )
        self.to_commit.append( ( src, tgt, ) )*/
    }
}