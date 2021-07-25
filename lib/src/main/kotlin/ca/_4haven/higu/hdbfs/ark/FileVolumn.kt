package ca._4haven.higu.hdbfs.ark

import ca._4haven.higu.hdbfs.imgdb.Config
import ca._4haven.higu.hdbfs.model.Id
import java.io.IOException
import java.io.InputStream
import java.nio.file.*

class FileVolume( val data_config: Config, val vol_id: Id ) : Volume {
    private var to_commit = mutableListOf< Pair<Path,Path> >()
    private var state = Volume.State.CLEAN
    private var rm_dir: Path? = null

    private fun __get_path( id: Id, priority: Int, extension: String? ): Path {
        val path = this.data_config.get_file_vol_path( this.vol_id, priority )
        return path.resolve( "%016x.%s".format( id, extension ) )
    }

    override fun verify(): Boolean {
        return true
    }

    override fun read( id: Id, priority: Int, extension: String? ): InputStream? {
        val p = this.__get_path( id, priority, extension )
        return if( !p.toFile().isFile() ) {
            null
        } else {
            p.toFile().inputStream()
        }
    }

    /* TODO
    def _debug_write( self, id, priority, extension ):

        p = self.__get_path( id, priority, extension )

        try:
            return open( p, 'wb' )
        except IndexError:
            return None*/

    override fun get_state(): Volume.State = this.state

    override fun reset_state() {
        this.state = Volume.State.CLEAN

        val rm_dir = this.rm_dir
        this.rm_dir = null
        this.to_commit = mutableListOf()

        rm_dir?.toFile()?.deleteRecursively()
    }

    override fun commit() {
        val moved = mutableListOf< Pair<Path,Path> >()

        try {
            this.to_commit.forEach {
                Files.move( it.first, it.second )
                moved.add( it )
            }
        } catch( ex: Exception ) {
            // Something went wrong, rollback
            moved.forEach {
                Files.move( it.second, it.first )
            }

            // Sometimes move() seems to leave files behind
            moved.forEach {
                try {
                    if( it.second.toFile().isFile() ) {
                        it.second.toFile().delete()
                    }
                } catch( ex: IOException ) {
                }
            }

            throw ex
        }

        // Comitted
        this.state = Volume.State.COMITTED
    }

    override fun rollback() {
        if( this.state == Volume.State.DIRTY ) {
            this.to_commit = mutableListOf()
            this.state = Volume.State.CLEAN
        } else if( this.state == Volume.State.COMITTED ) {
            this.to_commit.forEach {
                Files.move( it.second, it.first )
            }

            // Sometimes move() seems to leave files behind
            this.to_commit.forEach {
                try {
                    if( it.second.toFile().isFile() ) {
                        it.second.toFile().delete()
                    }
                } catch( ex: IOException ) {
                }
            }

            this.state = Volume.State.DIRTY
        }
    }

    override fun load_data( path: String, id: Id, priority: Int, extension: String? ) {
        if( this.state == Volume.State.COMITTED ) {
            this.reset_state()
        }

        this.state = Volume.State.DIRTY

        val new_path = this.data_config.get_file_vol_path( this.vol_id, priority )
        if( !new_path.toFile().isDirectory() ) {
            new_path.toFile().mkdirs()
        }

        val tgt = new_path.resolve( "%016x.%s".format( id, extension ) )
        this.to_commit.add( Pair( Paths.get( path ), tgt ) )
    }

    override fun delete( id: Id, priority: Int, extension: String? ) {
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