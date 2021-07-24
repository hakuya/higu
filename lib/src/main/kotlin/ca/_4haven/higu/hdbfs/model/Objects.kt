package ca._4haven.higu.hdbfs.model

import org.ktorm.schema.*
import org.ktorm.entity.Entity

object Objects : Table<Nothing>( "objects" ) {
    val object_id = int( "object_id" ).primaryKey()
    val object_type = int( "object_type" )
    val create_ts = int( "create_ts" )
    val name = varchar( "name" )
}

interface ModelObject : Entity<ModelObject> {
    val object_id: Int
    val object_type: Int
    val create_ts: Int
    var name: String?
    /* TODO
    __tablename__ = 'objects'

    object_id = Column( Integer, primary_key = True )
    object_type = Column( Integer, nullable = False )
    create_ts = Column( Integer, nullable = False )
    name = Column( Text )

    # use_alter is required here to avoid circular dependency
    root_stream_id = Column( Integer,
                             ForeignKey( 'streams.stream_id',
                                         name = 'objects_root_stream_id_constraint',
                                         use_alter = True ) )

    child_rel = relation(
        'Relation',
        primaryjoin = 'Object.object_id==Relation.parent_id',
        backref = backref( 'parent_obj', uselist = False ),
        order_by = 'Relation.sort' )
    parent_rel = relation(
        'Relation',
        primaryjoin = 'Object.object_id==Relation.child_id',
        backref = backref( 'child_obj', uselist = False ) )

    parents = association_proxy( 'parent_rel', 'parent_obj' )
    children = association_proxy( 'child_rel', 'child_obj' )

    # We need post update here to avoid the circular dependency. Only update
    # root_stream after both the object and stream have been created
    root_stream = relation( 'Stream', foreign_keys = [ root_stream_id ],
                            backref = backref( 'objects', uselist = False ),
                            post_update = True )

    def __init__( self, object_type, name = None ):

        self.object_type = object_type
        self.name = name
        self.create_ts = calendar.timegm(time.gmtime())

    def __getitem__( self, key ):

        row = self.metadata.filter( ObjectMetadata.key == key ).first()

        if( row is None ):
            raise KeyError

        if( row.numeric is not None ):
            return row.numeric
        else:
            return row.value

    def __setitem__( self, key, value ):

        value_s = value
        value_i = value if( isinstance( value, numbers.Number ) ) else None

        row = self.metadata.filter( ObjectMetadata.key == key ).first()

        if( row is not None ):
            row.value = value_s
            row.numeric = value_i
        else:
            row = ObjectMetadata( key, value_s, value_i )
            self.metadata.append( row )

    def __delitem__( self, key ):

        row = self.metadata.filter( ObjectMetadata.key == key ).first()
        if( row is None ):
            raise KeyError

        self.metadata.filter( ObjectMetadata.key == key ).delete()

    def __repr__( self ):

        return 'Object( %r, %r, %r )' % ( self.id, self.type, time.gmtime( self.create_ts ), self.name )
    */
}