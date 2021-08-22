package ca._4haven.higu.hdbfs.basic_objects

import ca._4haven.higu.hdbfs.*
import ca._4haven.higu.hdbfs.model.*
import org.ktorm.dsl.*
import org.ktorm.entity.*

open class Group( db: Database, obj: ModelObject ) : Obj( db, obj ) {

    open fun is_ordered(): Boolean {
        return false
    }

    fun _get_files(): List<File> {
        return this._get_children( TYPE_FILE ).map { it as File }
    }

    fun get_files(): List<File> {
        return this.db._access().with { this._get_files() }
    }
}

open class OrderedGroup( db: Database, obj: ModelObject ) : Group( db, obj ) {

    override fun is_ordered(): Boolean {
        return true
    }

    fun clear_order() {
        this.db._access().with {
            this.get_files().forEach { child ->
                child.reorder( this )
            }
        }
    }

    fun set_order( children: List<Obj> ) {
        this.db._access( write = true ).with {
            val all_objs = this._get_files().toMutableList()
            
            children.forEachIndexed { i, v ->
                if( v !in all_objs ) {
                    throw IllegalArgumentException( "${v} is not a child of ${this}" )
                }

                all_objs.remove( v )
                v._reorder( this, i )
            }

            val offset = children.size

            all_objs.forEachIndexed { i, v ->
                v._reorder( this, offset + i )
            }
        }
    }
}

class Tag( db: Database, obj: ModelObject) : Group( db, obj ) {

    fun _get_objs(): List<Obj> {
        /* TODO
        objs = [ obj for obj in self.obj.children
                             if obj.object_type == TYPE_FILE ]
        return map( lambda x: model_obj_to_higu_obj( self.db, x ), objs )*/
        return listOf<File>();
    }

    fun get_objs(): List<Obj> {
        return this.db._access().with { this._get_objs() }
    }
}