package ca._4haven.higu.hdbfs

import java.io.*
import java.nio.file.*

class TestUtils {

    companion object {
        val red = "red_sq.png"
        val yellow = "yellow_sq.png"
        val green = "green_sq.png"
        val cyan = "cyan_sq.png"
        val blue = "blue_sq.png"
        val magenta = "magenta_sq.png"
        val white = "white_sq.png"
        val grey = "grey_sq.png"
        val black = "black_sq.png"
        val cl_desc = "cl_sq_desc.txt"
        val bw_desc = "bw_sq_desc.txt"
    
        val red_hash = "92a5cf2c69d16d57c5dde8e0c0d4bdb9d76bc316"
        val yellow_hash = "ca90c86d1621d000f1de2071f766615417298537"
        val green_hash = "2cc964f5c885bde996b38a6f0fd8a3b907d038c9"
        val cyan_hash = "ef0495c17ef137143fb3ca403bef657e77d411ae"
        val blue_hash = "0ca527049c4e8f2b145e15afbf3d6393473e0178"
        val magenta_hash = "ab8d44c936e2ccfe1c73cde3d7ace31750530442"
        val white_hash = "f5a7cebc04fdd67e746b14b9492eb0cf56d815cf"
        val grey_hash = "5c75230de43a5617f7e85f32602ce3866a430e19"
        val black_hash = "c2d1060c9ea2949e327d412778ccda8d31cdb538"
    }

    lateinit var data_dir: Path
    lateinit var work_dir: Path
    lateinit var cfg_file_path: Path
    lateinit var db_path: Path
    lateinit var web_db: Path

    fun init_env( do_init: Boolean = true, web_init: Boolean = false ) {

        this.data_dir = Paths.get( "test/data" )
        this.work_dir = Files.createTempDirectory( "higuTest" )
        this.cfg_file_path = this.work_dir.resolve( "test.cfg" )
        this.db_path = this.work_dir.resolve( "test.db" )
        this.web_db = this.work_dir.resolve( "web.db" )

        val cfg_file = PrintWriter( this.cfg_file_path.toFile() )
        cfg_file.println( "[main]" )
        cfg_file.println( "library = ${this.db_path}" )
        cfg_file.println( "" )
        cfg_file.println( "[www]" )
        cfg_file.println( "host = localhost" )
        cfg_file.println( "port = 60080\n" )
        cfg_file.println()

        if( do_init ) this._init_hdbfs()

        /* TODO
        if( web_init ) higu.model.init( self.web_db )*/
    }

    fun uninit_env() {
        /* TODO
        hdbfs.dispose()
        higu.model.dispose()
        shutil.rmtree( this.work_dir )*/
    }

    fun _init_hdbfs() {
        Database( this.db_path.toString() )
    }

    /* TODO
    fun _data_path( self, fname ) {
        return os.path.join( self.data_dir, fname )
    }

    fun _load_data( self, fname, tname = None ) {

        src = self._data_path( fname )
        if( tname is None ):
            tgt = os.path.join( self.work_dir, fname )
        else:
            tgt = os.path.join( self.work_dir, tname )

        shutil.copy( src, tgt )

        return tgt
    }

    fun _diff_data( self, f, data ) {
        return self._diff( f, self._data_path( data ) )
    }

    fun _diff( self, f1, f2 ) {

        if( isinstance( f1, str ) ):
            if( not os.path.isfile( f1 ) ):
                return False

            f1 = open( f1, "rb" )

        if( isinstance( f2, str ) ):
            if( not os.path.isfile( f2 ) ):
                return False

            f2 = open( f2, "rb" )

        try:
            while True:
                d1 = f1.read( 4096 )
                d2 = f2.read( 4096 )

                if( d1 != d2 ):
                    return False

                if( len( d1 ) == 0 ):
                    return True
        finally:
            f1.close()
            f2.close()
    }*/
}