package ca._4haven.higu.hdbfs.model

import ca._4haven.higu.hdbfs.dbutils.Session
import org.ktorm.schema.*
import org.ktorm.entity.Entity
import org.ktorm.entity.sequenceOf

interface Relation : Entity<Relation> {

    companion object : Entity.Factory<Relation>()

    var child_id: Id
    var parent_id: Id
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

object Relations : Table<Relation>( "relations" ) {
    val child_id = long( "child_id" ).primaryKey().bindTo { it.child_id }
    val parent_id = long( "parent_id" ).primaryKey().bindTo { it.parent_id }
    val sort = int( "sort" ).bindTo { it.sort }

    fun create( session: Session ) {
        session.useConnection { conn ->
            val sql = """
                CREATE TABLE IF NOT EXISTS relations (
                    child_id          INTEGER NOT NULL,
                    parent_id         INTEGER NOT NULL,
                    sort              INTEGER,
                    PRIMARY KEY ( child_id, parent_id ),
                    FOREIGN KEY ( child_id )
                      REFERENCES objects( object_id ),
                    FOREIGN KEY ( parent_id )
                      REFERENCES objects( object_id )
                )
            """.trimIndent()

            conn.prepareStatement(sql).use { stmt ->
                stmt.execute()
            }
        }
    }
}

val Session.relations get() = this.sequenceOf( Relations )