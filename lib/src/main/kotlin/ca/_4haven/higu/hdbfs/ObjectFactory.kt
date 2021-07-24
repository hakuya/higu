package ca._4haven.higu.hdbfs

import ca._4haven.higu.hdbfs.basic_objects.*
import ca._4haven.higu.hdbfs.model.*

typealias BasicStreamFactory = ( db: Database, model_obj: ModelStream ) -> Stream?
typealias BasicObjectFactory = ( db: Database, model_obj: ModelObject ) -> Obj?

object ObjectFactory {

    /* TODO
    class Iterator( val db: Database, it: Iterable ) {

        /*def __iter__( self ):

            return ModelObjToHiguObjIterator( self.db, self.it )*/

        fun next() {
            return model_obj_to_higu_obj( this.db, this.it.next() )
        }
    }*/

    val _STM_FACTORIES = mutableListOf<BasicStreamFactory>()
    val _OBJ_FACTORIES = mutableListOf<BasicObjectFactory>()

    fun add_stream_factory( f: BasicStreamFactory ) {
        this._STM_FACTORIES.add( f )
    }

    fun add_obj_factory( f: BasicObjectFactory ) {
        this._OBJ_FACTORIES.add( f )
    }

    fun model_stream_to_higu_stream( db: Database, stream: ModelStream ): Stream {
        _STM_FACTORIES.forEach { f ->
            var result = f( db, stream )
            if( result != null ) {
                return result
            }
        }

        throw RuntimeException()
    }

    fun model_obj_to_higu_obj( db: Database, obj: ModelObject ): Obj {
        _OBJ_FACTORIES.forEach { f ->
            var result = f( db, obj )
            if( result != null ) {
                return result
            }
        }

        throw RuntimeException()
    }
}