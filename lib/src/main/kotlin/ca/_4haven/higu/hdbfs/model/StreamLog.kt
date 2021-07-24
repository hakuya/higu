package ca._4haven.higu.hdbfs.model

import org.ktorm.schema.*
import org.ktorm.entity.Entity

object StreamLog : Table<Nothing>( "stream_log" ) {
    val log_id = int( "log_id" ).primaryKey()
    val stream_id = int( "stream_id" )
    val timestamp = int( "timestamp" )
    val origin_method = varchar( "origin_method" )
    val origin_stream_id = int( "origin_stream_id" )
    val origin_name = varchar( "origin_name" )
}

interface StreamLogEntry : Entity<StreamLogEntry> {
    val log_id: Int
    var stream_id: Int
    var timestamp: Int
    var origin_method: String
    var origin_stream_id: Int?
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