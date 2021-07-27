package ca._4haven.higu.hdbfs.model

import ca._4haven.higu.hdbfs.dbutils.Session
import org.ktorm.schema.*
import org.ktorm.entity.Entity
import org.ktorm.entity.sequenceOf

interface ObjectMetadataEntry : Entity<ObjectMetadataEntry> {

    companion object : Entity.Factory<ObjectMetadataEntry>()

    var object_id: Id
    var key: String
    var value: String?
    var numeric: Int?

    /* TODO
class ObjectMetadata( Base ):
    __tablename__ = 'object_metadata'
    __table_args__ = (
        PrimaryKeyConstraint( 'object_id', 'key' ),
        Index( 'object_metadata_object_id_key_index',
               'object_id', 'key', unique = True ),
    )

    object_id = Column( Integer, ForeignKey( 'objects.object_id' ),
                        nullable = False )
    key = Column( Text, nullable = False )
    value = Column( Text )
    numeric = Column( Integer )

    obj = relation( 'Object',
                    backref = backref( 'metadata',
                                       lazy = 'dynamic',
                                       cascade = 'all, delete-orphan' ) )

    def __init__( self, key, value, numeric ):

        self.key = key
        self.value = value
        self.numeric = numeric

    def __repr__( self ):

        return 'ObjectMetadata( %r, %r, %r, %r )' % (
                self.object_id, self.key, self.value, self.numeric )*/
}

object ObjectMetadata : Table<ObjectMetadataEntry>( "object_metadata" ) {
    val object_id = long( "object_id" ).primaryKey().bindTo { it.object_id }
    val key = varchar( "key" ).primaryKey().bindTo { it.key }
    val value = varchar( "value" ).bindTo { it.value }
    val numeric = int( "numeric" ).bindTo { it.numeric }

    fun create( session: Session ) {
        session.useConnection { conn ->
            val sql = """
                CREATE TABLE IF NOT EXISTS object_metadata (
                    object_id         INTEGER NOT NULL,
                    key               TEXT NOT NULL,
                    value             TEXT,
                    numeric           INTEGER,
                    PRIMARY KEY ( object_id, key ),
                    FOREIGN KEY ( object_id )
                        REFERENCES objects( object_id )
                )
            """.trimIndent()

            conn.prepareStatement(sql).use { stmt ->
                stmt.execute()
            }
        }
    }
}

val Session.object_metadata get() = this.sequenceOf( ObjectMetadata )