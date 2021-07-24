package ca._4haven.higu.hdbfs.basic_objects

import ca._4haven.higu.hdbfs.*
import ca._4haven.higu.hdbfs.model.*

open class Group( db: Database, obj: ModelObject ) : Obj( db, obj ) {

    open fun is_ordered(): Boolean {
        return false
    }

    fun _get_files(): List<File> {
        /* TODO
        objs = [ obj for obj in self.obj.children
                             if obj.object_type == TYPE_FILE ]
        return map( lambda x: model_obj_to_higu_obj( self.db, x ), objs )*/
        return listOf<File>();
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

    fun set_order( children: Obj ) {
        this.db._access( write = true ).with {
            /* TODO
            all_objs = self._get_files()
            
            for child in enumerate( children ):
                assert( child[1] in all_objs )
                all_objs.remove( child[1] )
                
                child[1]._reorder( self, child[0] )

            offset = len( children )

            for child in enumerate( all_objs ):
                child[1]._reorder( self, offset + child[0] )*/
        }
    }
}

class Tag( db: Database, obj: ModelObject) : Obj( db, obj ) {

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