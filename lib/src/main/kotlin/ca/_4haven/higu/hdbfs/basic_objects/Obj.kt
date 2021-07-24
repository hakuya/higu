package ca._4haven.higu.hdbfs.basic_objects

import ca._4haven.higu.hdbfs.*
import ca._4haven.higu.hdbfs.model.*

open class Obj( val db: Database, val obj: ModelObject ) {

    open fun _on_created( stream: Stream ) {
    }

    open fun _on_children_changed() {
    }

    fun get_id(): Int {
        return this.db._access().with { this.obj.object_id }
    }

    fun get_type(): ObjType {
        return this.db._access().with { this.obj.object_type }
    }

    fun _get_parents( obj_type: ObjType ): List<Obj> {
        /* TODO
        objs = [ obj for obj in self.obj.parents if obj.object_type == obj_type ]
        return map( lambda x: model_obj_to_higu_obj( self.db, x ), objs )*/
        return listOf<Obj>()
    }

    fun get_parents( obj_type: ObjType ): List<Obj> {
        return this.db._access().with { this._get_parents( obj_type ) }
    }

    fun _get_children( obj_type: ObjType ): List<Obj> {
        /* TODO
        objs = [ obj for obj in self.obj.children if obj.object_type == obj_type ]
        return map( lambda x: model_obj_to_higu_obj( self.db, x ), objs )*/
        return listOf<Obj>()
    }

    fun get_children( obj_type: ObjType ): List<Obj> {
        return this.db._access().with { this._get_children( obj_type ) }
    }

    fun get_creation_time() {
        /* TODO
        this.db._access().with {
            return datetime.datetime.fromtimestamp( this.obj.create_ts )
        }*/
    }

    fun get_creation_time_utc() {
        /* TODO
        this.db._access().with {
            return datetime.datetime.utcfromtimestamp( this.obj.create_ts )
        }*/
    }

    fun get_tags(): List<Tag> {
        /* TODO
        from sqlalchemy import and_

        this.db._access().with {
            tag_objs = [
                obj for obj in
                self.db.session.query( model.Object )
                    .filter(
                        and_( model.Object.object_type == TYPE_CLASSIFIER,
                              model.Object.children.contains( self.obj ) ) )
                             .order_by( model.Object.name ) ]
            return map( lambda x: Tag( self.db, x ), tag_objs )
        }*/
        return listOf<Tag>()
    }

    fun _assign( group: Obj, order: Int? ) {
        /* TODO
        rel = self.db.session.query( model.Relation ) \
                .filter( model.Relation.parent_id == group.obj.object_id ) \
                .filter( model.Relation.child_id == self.obj.object_id ).first()
        if( rel is not None ):
            rel.sort = order
            return
        rel = model.Relation( order )
        rel.parent_obj = group.obj
        rel.child_obj = self.obj

        group._on_children_changed()*/
    }

    fun assign( group: Obj, order: Int? = null ) {
        this.db._access( write = true ).with {
            this._assign( group, order )
        }
    }

    fun _unassign( group: Obj ) {
        /* TODO
        rel = self.db.session.query( model.Relation ) \
                .filter( model.Relation.parent_id == group.obj.object_id ) \
                .filter( model.Relation.child_id == self.obj.object_id ).first()

        if( rel is not None ):
            self.db.session.delete( rel )

        group._on_children_changed()*/
    }

    fun unassign( group: Obj ) {
        this.db._access( write = true ).with {
            this._unassign( group )
        }
    }

    fun _reorder( group: Group, order: Int? ) {
        /* TODO
        rel = self.db.session.query( model.Relation ) \
                .filter( model.Relation.parent_id == group.obj.object_id ) \
                .filter( model.Relation.child_id == self.obj.object_id ) \
                .first()
        if( rel is None ):
            raise ValueError, str( self ) + ' is not in ' + str( group )
        rel.sort = order*/
    }

    fun reorder( group: OrderedGroup, order: Int? = null ) {
        this.db._access( write = true ).with {
            this._reorder( group, order )
        }
    }

    fun get_order( group: OrderedGroup ) {
        /* TODO
        this.db._access().with {
            rel = self.db.session.query( model.Relation ) \
                    .filter( model.Relation.parent_id == group.obj.id ) \
                    .filter( model.Relation.child_id == self.obj.id ).first()
            if( rel is None ):
                raise ValueError, str( self ) + ' is not in ' + str( group )
            return rel.sort
        }*/
    }
        
    fun get_name(): String? {
        return this.db._access().with { this.obj.name }
    }

    fun set_name( name: String? ) {
        this.db._access( write = true ).with {
            this.obj.name = name
        }
    }

    open fun get_repr(): String {
        return this.get_name() ?: "%016x".format( this.get_id() )
    }

    fun getItem( key: String ): Any? {
        /* TODO
        return this.db._access().with {
            self.obj.getItem( key )
        }*/
        return null
    }

    fun setItem( key: String, value: Any? ) {
        /* TODO
        this.db._access( write = true ).with {
            this.obj.setItem( key, value )
        }*/
    }

    override fun equals( o: Any? ): Boolean {
        if( o == null ) return false
        if( o !is Obj ) return false
        return this.db == o.db && this.obj == o.obj
    }
}