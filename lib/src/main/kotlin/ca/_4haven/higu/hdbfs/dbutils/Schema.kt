package ca._4haven.higu.hdbfs.dbutils

import org.ktorm.schema.*
import org.ktorm.entity.Entity

interface SchemaEntry : Entity<SchemaEntry> {
    val uuid: String
    val schema: String
    val ver: Int
    val rev: Int
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
    val uuid = varchar( "uuid" ).primaryKey()
    val schema_name = varchar( "schema" )
    val ver = int( "ver" )
    val rev = int( "rev" )

    fun create( session: Session ) {
        session.useConnection { conn ->
            val sql = """
                CREATE TABLE IF NOT EXISTS db_schema(
                    uuid   TEXT PRIMARY KEY,
                    schema TEXT NOT NULL,
                    ver    INTEGER NOT NULL,
                    rev    INTEGER NOT NULL
                )
            """

            conn.prepareStatement(sql).use { stmt ->
                stmt.execute()
            }
        }
    }
}