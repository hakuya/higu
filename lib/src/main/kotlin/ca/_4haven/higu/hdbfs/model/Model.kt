package ca._4haven.higu.hdbfs.model

import ca._4haven.higu.hdbfs.dbutils.DatabaseFile
import ca._4haven.higu.hdbfs.dbutils.Session

class Model {
    //Base = declarative_base()

    lateinit var session: Session

    fun init( database_file: String, imgdb_path: String ) {

        val migrators = mapOf(
            "hdbfs" to HDBFSMigrator()
            //"imgdb" to legacy.ImgDBMigrator( imgdb_path ),
        )

        val dbfile = DatabaseFile( database_file, migrators )
        dbfile.init()

        dbfile.init_schema( "hdbfs", HDBFS_VERSION )
        // TODO dbfile.init_schema( "imgdb", IMGDB_VERSION, IMGDB_REVISION )

        this.session = dbfile.get_session()
    }

    fun dispose() {
        /* TODO
        global dbfile
        global Session

        if( dbfile is not None ):
            Session = None
            dbfile.dispose()
            dbfile = None*/
    }
}