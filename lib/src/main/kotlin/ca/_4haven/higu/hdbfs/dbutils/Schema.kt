package ca._4haven.higu.hdbfs.dbutils

import org.ktorm.schema.*
import org.ktorm.entity.Entity
import org.ktorm.entity.sequenceOf

interface SchemaEntry : Entity<SchemaEntry> {

    companion object : Entity.Factory<SchemaEntry>()

    var uuid: String
    var schema_name: String
    var ver: Int
    var rev: Int
    /* TODO
    __tablename__ = 'db_schema'

    uuid = Column( Text, primary_key = True )
    schema = Column( Text, nullable = False )
    ver = Column( Integer, nullable = False )
    rev = Column( Integer, nullable = False )

    def __init__( self, schema, ver, rev, _uuid = None ):

        if( _uuid is None ):
            self.uuid = str( uuid.uuid1() )
        else:
            self.uuid = _uuid

        self.schema = schema
        self.ver = ver
        self.rev = rev

    def __repr__( self ):

        return 'Schema( %r, %r, %r, %r )' % ( self.uuid, self.schema, self.ver, self.rev )*/
}

object Schema : Table<SchemaEntry>( "db_schema" ) {
    data class Version( val major: Int, val rev: Int )

    var uuid = varchar( "uuid" ).primaryKey().bindTo { it.uuid }
    var schema_name = varchar( "schema" ).bindTo{ it.schema_name }
    var ver = int( "ver" ).bindTo{ it.ver }
    var rev = int( "rev" ).bindTo{ it.rev }

    fun create( session: Session ) {
        session.useConnection { conn ->
            val sql = """
                CREATE TABLE IF NOT EXISTS db_schema (
                    uuid   TEXT PRIMARY KEY,
                    schema TEXT NOT NULL,
                    ver    INTEGER NOT NULL,
                    rev    INTEGER NOT NULL
                )
            """.trimIndent()

            conn.prepareStatement(sql).use { stmt ->
                stmt.execute()
            }
        }
    }
}

val Session.schema_ get() = this.sequenceOf( Schema )