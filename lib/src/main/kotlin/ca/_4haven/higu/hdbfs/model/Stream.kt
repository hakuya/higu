package ca._4haven.higu.hdbfs.model

import ca._4haven.higu.hdbfs.dbutils.Session
import org.ktorm.schema.*
import org.ktorm.entity.Entity
import org.ktorm.entity.sequenceOf

interface ModelStream : Entity<ModelStream> {

    companion object : Entity.Factory<ModelStream>()

    var stream_id: Id
    var object_id: Id
    var name: String
    var priority: Int
    var origin_stream_id: Id?
    var extension: String?
    var mime_type: String?
    var stream_length: Long?
    var hash_crc32: String?
    var hash_md5: String?
    var hash_sha1: String?
    /* TODO
    __tablename__ = 'streams'
    __table_args__ = (
        UniqueConstraint( 'object_id', 'name' ),
        Index( 'streams_object_id_name_index',
               'object_id', 'name', unique = True ),
    )

    stream_id = Column( Integer, primary_key = True )
    object_id = Column( Integer, ForeignKey( 'objects.object_id' ), nullable = False )
    name = Column( Text, nullable = False )
    priority = Column( Integer, nullable = False )
    origin_stream_id = Column( Integer, ForeignKey( 'streams.stream_id' ) )
    extension = Column( Text )
    mime_type = Column( Text )
    stream_length = Column( Integer )
    hash_crc32 = Column( Text )
    hash_md5 = Column( Text )
    hash_sha1 = Column( Text )

    obj = relation( 'Object', foreign_keys = [ object_id ],
                    backref = backref( 'streams', lazy = 'dynamic' ) )
    origin_stream = relation( 'Stream',
                        backref = 'derived_streams',
                            remote_side = [ stream_id ] )

    def __init__( self, obj, name, priority,
                  origin_stream, extension, mime_type ):

        self.obj = obj
        self.name = name
        self.priority = priority
        self.origin_stream = origin_stream
        self.extension = extension
        self.mime_type = mime_type

    def set_details( self, stream_length, hash_crc32, hash_md5, hash_sha1 ):

        self.stream_length = stream_length
        self.hash_crc32 = hash_crc32
        self.hash_md5 = hash_md5
        self.hash_sha1 = hash_sha1

    def __getitem__( self, key ):

        from sqlalchemy import and_

        row = self.metadata.filter( StreamMetadata.key == key ).first()

        if( row is None ):
            raise KeyError

        if( row.numeric is not None ):
            return row.numeric
        else:
            return row.value

    def __setitem__( self, key, value ):

        value_s = value
        value_i = value if( isinstance( value, numbers.Number ) ) else None

        row = self.metadata.filter( StreamMetadata.key == key ).first()

        if( row is not None ):
            row.value = value_s
            row.numeric = value_i
        else:
            row = StreamMetadata( key, value_s, value_i )
            self.metadata.append( row )

    def __delitem__( self, key ):

        row = self.metadata.filter( StreamMetadata.key == key ).first()
        if( row is None ):
            raise KeyError

        self.metadata.remove( row )

    def __repr__( self ):

        return 'Stream( %r, %r, %r, %r, %r, %r, %r, %r, %r, %r )' % (
                self.stream_id, self.object_id, self.name, self.priority,
                self.origin_stream_id, self.mime_type, self.stream_length,
                self.hash_crc32, self.hash_md5, self.hash_sha1 )*/
}

object Streams : Table<ModelStream>( "streams" ) {
    val stream_id = long( "stream_id" ).primaryKey().bindTo { it.stream_id }
    val object_id = long( "object_id" ).bindTo { it.object_id }
    val name = varchar( "name" ).bindTo { it.name }
    val priority = int( "priority" ).bindTo { it.priority }
    val origin_stream_id = long( "origin_stream_id" ).bindTo { it.origin_stream_id }
    val extension = varchar( "extension" ).bindTo { it.extension }
    val mime_type = varchar( "mime_type" ).bindTo { it.mime_type }
    val stream_length = long( "stream_length" ).bindTo { it.stream_length }
    val hash_crc32 = varchar( "hash_crc32" ).bindTo { it.hash_crc32 }
    val hash_md5 = varchar( "hash_md5" ).bindTo { it.hash_md5 }
    val hash_sha1 = varchar( "hash_sha1" ).bindTo { it.hash_sha1 }

    fun create( session: Session ) {
        session.useConnection { conn ->
            val sql = """
                CREATE TABLE IF NOT EXISTS streams (
                    stream_id           INTEGER PRIMARY KEY,
                    object_id           INTEGER NOT NULL,
                    name                TEXT NOT NULL,
                    priority            INTEGER NOT NULL,
                    origin_stream_id    INTEGER,
                    extension           TEXT,
                    mime_type           TEXT,
                    stream_length       INTEGER,
                    hash_crc32          TEXT,
                    hash_md5            TEXT,
                    hash_sha1           TEXT,
                    UNIQUE ( object_id, name ),
                    FOREIGN KEY ( object_id )
                        REFERENCES objects( object_id ),
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

val Session.streams get() = this.sequenceOf( Streams )