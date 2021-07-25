package ca._4haven.higu.hdbfs.model

import ca._4haven.higu.hdbfs.dbutils.Session
import org.ktorm.schema.*
import org.ktorm.entity.Entity
import org.ktorm.entity.sequenceOf

interface StreamLogEntry : Entity<StreamLogEntry> {

    companion object : Entity.Factory<StreamLogEntry>()

    var log_id: Id
    var stream_id: Id
    var timestamp: Long
    var origin_method: String
    var origin_stream_id: Id?
    var origin_name: String?
    /* TODO
    __tablename__ = 'stream_log'
    __table_args__ = (
        Index( 'stream_log_stream_id_index', 'stream_id' ),
    )

    log_id = Column( Integer, primary_key = True )
    stream_id = Column( Integer, ForeignKey( 'streams.stream_id' ), nullable = False )
    timestamp = Column( Integer, nullable = False )
    origin_method = Column( Text, nullable = False )
    origin_stream_id = Column( Integer, ForeignKey( 'streams.stream_id' ) )
    origin_name = Column( Text )

    stream = relation( 'Stream', foreign_keys = [ stream_id ],
                        backref = backref( 'log_entries', lazy = 'dynamic' ) )
    origin_stream = relation( 'Stream', foreign_keys = [ origin_stream_id ] )

    def __init__( self, stream, origin_method,
                  origin_stream, origin_name ):

        self.stream = stream
        self.timestamp = calendar.timegm(time.gmtime())
        self.origin_method = origin_method
        self.origin_stream = origin_stream
        self.origin_name = origin_name

    def __repr__( self ):

        return 'StreamLog( %r, %r, %r, %r, %r )' % (
                self.stream_id, self.timestamp, self.origin_method,
                self.origin_stream_id, self.origin_name )*/
}

object StreamLog : Table<StreamLogEntry>( "stream_log" ) {
    val log_id = long( "log_id" ).primaryKey().bindTo { it.log_id }
    val stream_id = long( "stream_id" ).bindTo { it.stream_id }
    val timestamp = long( "timestamp" ).bindTo { it.timestamp }
    val origin_method = varchar( "origin_method" ).bindTo { it.origin_method }
    val origin_stream_id = long( "origin_stream_id" ).bindTo { it.origin_stream_id }
    val origin_name = varchar( "origin_name" ).bindTo { it.origin_name }

    fun create( session: Session ) {
        session.useConnection { conn ->
            val sql = """
                CREATE TABLE IF NOT EXISTS stream_log (
                    log_id            INTEGER PRIMARY KEY,
                    stream_id         INTEGER NOT NULL,
                    timestamp         INTEGER NOT NULL,
                    origin_method     TEXT NOT NULL,
                    origin_stream_id  INTEGER,
                    origin_name       TEXT,
                    FOREIGN KEY ( stream_id )
                        REFERENCES streams( stream_id ),
                    FOREIGN KEY ( origin_stream_id )
                        REFERENCES streams( stream_id )
                )
            """.trimIndent()

            conn.prepareStatement(sql).use { stmt ->
                stmt.execute()
            }
        }
    }
}

val Session.stream_log get() = this.sequenceOf( StreamLog )