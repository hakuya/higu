package ca._4haven.higu.hdbfs.model

import org.ktorm.schema.*
import org.ktorm.entity.Entity

object StreamMetadata : Table<Nothing>( "stream_metadata" ) {
    val stream_id = int( "stream_id" ).primaryKey()
    val key = varchar( "key" )
    val value = varchar( "value" )
    val numeric = int( "numeric" )
}

interface StreamMetadataEntry : Entity<StreamMetadataEntry> {
    val stream_id: Int
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