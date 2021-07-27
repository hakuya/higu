package ca._4haven.higu.hdbfs.model

import ca._4haven.higu.hdbfs.dbutils.Session
import org.ktorm.schema.*
import org.ktorm.entity.Entity
import org.ktorm.entity.sequenceOf

interface StreamMetadataEntry : Entity<StreamMetadataEntry> {

    companion object : Entity.Factory<StreamMetadataEntry>()

    var stream_id: Id
    var key: String
    var value: String?
    var numeric: Int?

    /* TODO
    __tablename__ = 'stream_metadata'
    __table_args__ = (
        PrimaryKeyConstraint( 'stream_id', 'key' ),
        Index( 'stream_metadata_stream_id_key_index',
               'stream_id', 'key', unique = True ),
    )

    stream_id = Column( Integer, ForeignKey( 'streams.stream_id' ),
                        nullable = False )
    key = Column( Text, nullable = False )
    value = Column( Text )
    numeric = Column( Integer )

    stream = relation( 'Stream',
                       backref = backref( 'metadata',
                                          lazy = 'dynamic',
                                          cascade = 'all, delete-orphan' ) )

    def __init__( self, key, value, numeric ):

        self.key = key
        self.value = value
        self.numeric = numeric

    def __repr__( self ):

        return 'StreamMetadata( %r, %r, %r, %r )' % (
                self.object_id, self.key, self.value, self.numeric )*/
}

object StreamMetadata : Table<StreamMetadataEntry>( "stream_metadata" ) {
    val stream_id = long( "stream_id" ).primaryKey().bindTo { it.stream_id }
    val key = varchar( "key" ).primaryKey().bindTo { it.key }
    val value = varchar( "value" ).bindTo { it.value }
    val numeric = int( "numeric" ).bindTo { it.numeric }

    fun create( session: Session ) {
        // TODO this definition is wrong in v10!
        session.useConnection { conn ->
            val sql = """
                CREATE TABLE stream_metadata (
                    stream_id         INTEGER NOT NULL,
                    key               TEXT NOT NULL,
                    value             TEXT,
                    numeric           INTEGER,
                    PRIMARY KEY ( stream_id, key ),
                    FOREIGN KEY ( stream_id )
                        REFERENCES streams( stream_id )
                )
            """.trimIndent()

            conn.prepareStatement(sql).use { stmt ->
                stmt.execute()
            }
        }
    }
}

val Session.stream_metadata get() = this.sequenceOf( StreamMetadata )