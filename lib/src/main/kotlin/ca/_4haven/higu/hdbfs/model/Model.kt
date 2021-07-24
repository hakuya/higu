package ca._4haven.higu.hdbfs.model

import ca._4haven.higu.hdbfs.dbutils.DatabaseFile

class Model {
    //Base = declarative_base()

    lateinit var dbfile: DatabaseFile
    //var Session = None

    /* TODO
    fun _init_schema( engine, ver, rev ) {
        global dbfile

        Base.metadata.create_all( engine )
    }*/

    fun init( database_file: String, imgdb_path: String ) {

        /* TODO
        migrators = {
            'hdbfs' : legacy.HDBFSMigrator( _init_schema ),
            'imgdb' : legacy.ImgDBMigrator( imgdb_path ),
        }*/

        dbfile = DatabaseFile( database_file, listOf() )
        dbfile.init()

        /* TODO
        dbfile.init_schema( 'hdbfs', VERSION, REVISION )
        dbfile.init_schema( 'imgdb', IMGDB_VERSION, IMGDB_REVISION )

        Session = dbfile.get_session*/
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