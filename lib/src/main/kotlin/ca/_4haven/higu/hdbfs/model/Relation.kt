package ca._4haven.higu.hdbfs.model

import org.ktorm.schema.*
import org.ktorm.entity.Entity

object Relations : Table<Nothing>( "relations" ) {
    val child_id = int( "child_id" ).primaryKey()
    val parent_id = int( "parent_id" ).primaryKey()
    val sort = int( "sort" )
}

interface Relation : Entity<Relation> {
    val child_id: Int
    val parent_id: Int
    var sort: Int?
    /* TODO
    __tablename__ = 'relations'
    __table_args__ = (
        PrimaryKeyConstraint( 'child_id', 'parent_id' ),
    )

    child_id = Column( Integer, ForeignKey( 'objects.object_id' ), primary_key = True )
    parent_id = Column( Integer, ForeignKey( 'objects.object_id' ), primary_key = True )
    sort = Column( Integer )

    def __init__( self, sort = None ):

        self.sort = sort

    def __repr__( self ):

        return 'Relation( %r, %r, %r )' % (
                self.child_id, self.parent_id, self.sort )*/
}