package ca._4haven.higu.hdbfs.basic_objects

import ca._4haven.higu.hdbfs.*
import ca._4haven.higu.hdbfs.model.*
import org.ktorm.dsl.*
import org.ktorm.entity.*

open class Obj( val db: Database, val obj: ModelObject ) {

    open fun _on_created( stream: Stream ) {
    }

    open fun _on_children_changed() {
    }

    fun get_id(): Id {
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

    fun get_creation_time(): Long {
        /* TODO
        this.db._access().with {
            return datetime.datetime.fromtimestamp( this.obj.create_ts )
        }*/
        return 0
    }

    fun get_creation_time_utc(): Long {
        return this.obj.create_ts
    }

    fun get_tags(): List<Tag> {
        return this.db._access().with {
            this.db.session.objects.filter {
                (Objects.object_id inList this.db.session.from( Relations )
                                            .select( Relations.parent_id )
                                            .where {
                                                Relations.child_id eq this.obj.object_id
                                            }) and
                (Objects.object_type eq TYPE_CLASSIFIER)
            }.map {
                ObjectFactory.model_obj_to_higu_obj( this.db, it ) as Tag
            }
        }
    }

    fun _assign( group: Obj, order: Int? ) {
        var rel = this.db.session.relations.find {
                (Relations.parent_id eq group.obj.object_id) and
                (Relations.child_id eq this.obj.object_id)
        }
        if( rel != null ) {
            rel.sort = order
            rel.flushChanges()
        } else {
            rel = Relation {
                this.parent_id = group.obj.object_id
                this.child_id = this@Obj.obj.object_id
                this.sort = order
            }
            this.db.session.relations.add( rel )
        }

        group._on_children_changed()
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
        val rel = this.db.session.relations.find {
            (Relations.parent_id eq group.obj.object_id) and
            (Relations.child_id eq this.obj.object_id)
        } ?: throw IllegalArgumentException( "${this.get_repr()} is not in ${group.get_repr()}" )
        rel.sort = order
        rel.flushChanges()
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
        return this.db._access().with {
            val entry = this.db.session.object_metadata.find {
                (ObjectMetadata.object_id eq this.obj.object_id) and
                (ObjectMetadata.key eq key)
            }
            entry?.numeric ?: entry?.value
        }
    }

    fun setItem( key: String, value: Any? ) {
        if( value == null ) return delItem( key )

        this.db._access( write = true ).with {
            val entry = ObjectMetadataEntry {
                this.object_id = this@Obj.obj.object_id
                this.key = key
                this.value = value.toString()
                this.numeric = value as? Int
            }

            if( this.db.session.object_metadata.update( entry ) < 1 ) {
                this.db.session.object_metadata.add( entry )
            }
        }
    }

    fun delItem( key: String ) {
        this.db._access( write = true ).with {
            this.db.session.object_metadata.removeIf {
                (ObjectMetadata.object_id eq this.obj.object_id) and
                (ObjectMetadata.key eq key)
            }
        }
    }

    override fun equals( o: Any? ): Boolean {
        if( o == null ) return false
        if( o !is Obj ) return false
        return this.db == o.db && this.obj.object_id == o.obj.object_id
    }
}