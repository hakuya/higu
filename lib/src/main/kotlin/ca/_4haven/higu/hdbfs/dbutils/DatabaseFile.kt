package ca._4haven.higu.hdbfs.dbutils

import org.ktorm.database.*
import org.ktorm.dsl.*
import java.util.UUID

/* TODO
def _do_sqlite_connect( dbapi_conn, conn_record ):
    # Disable python's auto BEGIN/COMMIT
    dbapi_conn.isolation_level = None
    dbapi_conn.execute( 'PRAGMA busy_timeout = 10000' )*/

typealias Session = org.ktorm.database.Database

class DatabaseFile( val __file: String, private val __migrators: List<Migrator>) {

    private var session: Session? = null

    fun get_schema_version( schema: String ): Pair<Int,Int>? {
        try { 
            var result = Schema.createEntity( this.get_session()
                .from( Schema )
                .select()
                .where { Schema.schema_name eq schema }
                .iterator().next() )
            return Pair( result.ver, result.rev )
        } catch( ex: NoSuchElementException ) {
            return null
        }
    }

    fun set_schema_version( schema: String, ver: Int, rev: Int ) {
        this.get_session().useTransaction {
            var c = this.get_session().update( Schema ) {
                set( it.ver, ver )
                set( it.rev, rev )
            }
            if( c == 0 ) {
                // No updated rows, must insert
                c = this.get_session().insert( Schema ) {
                    set( it.uuid, UUID.randomUUID() )
                    set( it.schema_name, schema )
                    set( it.ver, ver )
                    set( it.rev, rev )
                }
            }
            if( c == 0 ) throw RuntimeException()
        }
    }

    /* TODO
    def backup( self ):

        with file( self.__file, 'rb' ) as f:
            n = 0
            while( 1 ):
                if( not os.path.isfile( self.__file + '.bak' + str( n ) ) ):
                    break
                n += 1
            with file( self.__file + '.bak' + str( n ), 'wb' ) as g:
                while( 1 ):
                    buff = f.read( 1024 )
                    if( len( buff ) == 0 ):
                        f.close()
                        g.close()
                        break
                    g.write( buff )*/

    fun init() {
        val session = Database.connect( "jdbc:sqlite:" + this.__file )
        /* TODO
        event.listen( self.__engine, 'connect', _do_sqlite_connect )*/

        session.useTransaction {
            Schema.create( session )
        }

        this.session = session
    }

    /* TODO
    def init_schema( self, schema, target_ver, target_rev ):

        ver, rev = self.get_schema_version( schema )

        if( ver is None ):
            self.__migrators[schema].init_schema( self.__engine, target_ver, target_rev )
            self.set_schema_version( schema, target_ver, target_rev )
        elif( ver > target_ver ):
            assert False, 'Unsupported schema version'
        elif( ver != target_ver or rev != target_rev ):
            self.backup()

            s = self.get_session()
            try:
                m = self.__migrators[schema]
                s.execute( 'BEGIN EXCLUSIVE' )

                while( ver != target_ver or rev != target_rev ):
                    new_ver, new_rev = m.upgrade_schema( s, ver, rev )
                    assert new_ver > ver or (new_ver == ver and new_rev > rev)
                    ver, rev = new_ver, new_rev

                info = s.query( Schema ).filter( Schema.schema == schema ).first()
                info.ver = ver
                info.rev = rev

                s.commit()
            finally:
                s.close()

    def dispose( self ):

        self.__Session = None
        self.__engine.dispose()
        self.__engine = None

    def get_engine( self ):

        return self.__engine*/

    fun get_session(): Session {
        if( session != null ) {
            return this.session!!
        }
        throw RuntimeException()
    }
}
