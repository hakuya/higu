package ca._4haven.higu.hdbfs.model

import org.ktorm.schema.*
import org.ktorm.entity.Entity

object ObjectMetadata : Table<Nothing>( "object_metadata" ) {
    val object_id = int( "object_id" ).primaryKey()
    val key = varchar( "key" )
    val value = varchar( "value" )
    val numeric = int( "numeric" )
}

interface ObjectMetadataEntry : Entity<ObjectMetadataEntry> {
    val object_id: Int
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