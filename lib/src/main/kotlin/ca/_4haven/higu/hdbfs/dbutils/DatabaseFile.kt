package ca._4haven.higu.hdbfs.dbutils

import org.ktorm.database.*
import org.ktorm.dsl.*
import org.ktorm.entity.add
import org.ktorm.entity.find
import java.util.UUID

/* TODO
def _do_sqlite_connect( dbapi_conn, conn_record ):
    # Disable python's auto BEGIN/COMMIT
    dbapi_conn.isolation_level = None
    dbapi_conn.execute( 'PRAGMA busy_timeout = 10000' )*/

typealias Session = org.ktorm.database.Database

class DatabaseFile( val __file: String, private val __migrators: Map<String,Migrator>) {

    private var session: Session? = null

    fun get_schema_version( schema: String ): Schema.Version? {
        try { 
            var result = Schema.createEntity( this.get_session()
                .from( Schema )
                .select()
                .where { Schema.schema_name eq schema }
                .iterator().next() )
            return Schema.Version( result.ver, result.rev )
        } catch( ex: NoSuchElementException ) {
            return null
        }
    }

    fun set_schema_version( schema: String, version: Schema.Version ) {

        val session = this.get_session()

        session.useTransaction {
            var c = session.update( Schema ) {
                set( it.ver, version.major )
                set( it.rev, version.rev )
            }
            if( c == 0 ) {
                // No updated rows, must insert
                val entry = SchemaEntry {
                    uuid = UUID.randomUUID().toString()
                    schema_name = schema
                    ver = version.major
                    rev = version.rev
                }
                c = this.get_session().schema_.add( entry )
            }
            if( c == 0 ) throw RuntimeException()
        }
    }

    fun backup() {
        /* TODO
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
    }

    fun init() {
        val session = Database.connect( "jdbc:sqlite:" + this.__file )
        /* TODO
        event.listen( self.__engine, 'connect', _do_sqlite_connect )*/

        session.useTransaction {
            Schema.create( session )
        }

        this.session = session
    }

    fun init_schema( schema: String, target_ver: Schema.Version ) {

        val session = this.get_session()
        val migrator = this.__migrators[schema] ?: throw RuntimeException()

        val version = this.get_schema_version( schema )

        if( version == null ) {
            migrator.init_schema( session, target_ver )
            this.set_schema_version( schema, target_ver )
        } else if( version.major > target_ver.major ) {
            throw RuntimeException( "Unsupported schema version" )
        } else if( version.major != target_ver.major
                || version.rev != target_ver.rev )
        {
            this.backup()

            session.useTransaction( TransactionIsolation.SERIALIZABLE ) {
                var _version: Schema.Version = version
                while( _version.major != target_ver.major
                    || _version.rev != target_ver.rev )
                {
                    var new_version = migrator.upgrade_schema( session, _version )
                    if( new_version.major < _version.major
                     || (new_version.major == _version.major && new_version.rev <= _version.rev) )
                    {
                        throw RuntimeException()
                    }
                    _version = new_version
                }

                val info = session.schema_.find { Schema.schema_name eq schema }!!
                info.ver = _version.major
                info.rev = _version.rev
                info.flushChanges()
            }
        }
    }

    /* TODO
    def dispose( self ):

        self.__Session = None
        self.__engine.dispose()
        self.__engine = None

    def get_engine( self ):

        return self.__engine*/

    fun get_session(): Session {
        if( this.session != null ) {
            return this.session!!
        }
        throw RuntimeException()
    }
}
