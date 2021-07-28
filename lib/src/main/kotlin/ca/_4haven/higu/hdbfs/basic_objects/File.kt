package ca._4haven.higu.hdbfs.basic_objects

import ca._4haven.higu.hdbfs.*
import ca._4haven.higu.hdbfs.model.*
import org.ktorm.dsl.*
import org.ktorm.entity.*

open class File( db: Database, obj: ModelObject ) : Obj( db, obj ) {

    fun _get_albums() = this._get_parents( TYPE_ALBUM )
    fun get_albums() = this.get_parents( TYPE_ALBUM )
    fun _get_variants_of() = this._get_parents( TYPE_FILE )
    fun get_variants_of() = this.get_parents( TYPE_FILE )
    fun _get_variants() = this._get_children( TYPE_FILE )
    fun get_variants() = this.get_children( TYPE_FILE )

    fun _set_variant_of( parent: File ) {
        if( parent.obj == this.obj ) throw RuntimeException()

        this._assign( parent, null )
    }

    fun set_variant_of( parent: File ) {
        this.db._access( write = true ).with {
            this._set_variant_of( parent )
        }
    }

    fun _clear_variant_of( parent: File ) {
        this._unassign( parent )
    }

    fun clear_variant_of( parent: File ) {
        this.unassign( parent )
    }

    fun _get_duplicate_streams(): List<Stream> {
        /* TODO
        from sqlalchemy import and_

        return [ model_stream_to_higu_stream( self.db, s ) for s in
            self.db.session.query( model.Stream )
                        .filter( and_( model.Stream.object_id == self.obj.object_id,
                                        model.Stream.name.like( 'dup:%' ) ) )
                        .order_by( model.Stream.stream_id ) ]*/
        return listOf<Stream>()
    }

    fun get_duplicate_streams(): List<Stream> {
        return this.db._access().with { this._get_duplicate_streams() }
    }

    fun _set_root_stream( stream: Stream ) {
        /* TODO
        if( stream.stream.object_id != this.obj.object_id ) throw RuntimeException()
        if( !stream.stream.name.startsWith( "dup:" ) ) throw RuntimeException()
        this.obj.root_stream.name = 'dup:' + this.obj.root_stream.hash_sha1
        this.db.session.flush()
        stream.stream.name = '.'
        this.obj.root_stream = stream.stream
        this.db.session.flush()*/
    }

    fun set_root_stream( stream: Stream ) {
        this.db._access( write = true ).with { this._set_root_stream( stream ) }
    }

    fun get_origin_names( all_streams: Boolean = false ): List<String> {
        /* TODO
        from sqlalchemy import and_

        with self.db._access():
            if( all_streams ):
                return [ log.origin_name for log in
                    self.db.session.query( model.StreamLog.origin_name )
                        .join( model.Stream,
                            model.Stream.stream_id == model.StreamLog.stream_id )
                        .filter( and_( model.Stream.object_id == self.obj.object_id,
                                    model.StreamLog.origin_name != None ) )
                        .distinct() ]
            else:
                return [ log.origin_name for log in
                    self.db.session.query( model.StreamLog.origin_name )
                        .filter( and_( model.StreamLog.stream_id == self.obj.root_stream.stream_id,
                                    model.StreamLog.origin_name != None ) )
                        .distinct() ]*/
        return listOf<String>()
    }

    override fun get_repr(): String {
        return this.get_name() ?: this.db._access().with {
            var obj_id = this.obj.object_id
            /*stream_id = this.obj.root_stream.stream_id
            priority = this.obj.root_stream.priority
            extension = this.obj.root_stream.extension*/
            var extension: String? = null

            return@with if( extension == null )
                "%016x".format( obj_id )
            else
                "%016x.%s".format( obj_id, extension )
        }
    }

    fun _get_stream( name: String ): Stream? {
        return this.db.session.streams.find {
                    (Streams.object_id eq this.obj.object_id) and
                    (Streams.name eq name)
                }?.let {
                    ObjectFactory.model_stream_to_higu_stream( this.db, it )
                }
    }

    fun get_stream( name: String ): Stream? {
        return this.db._access().with { this._get_stream( name ) }
    }

    fun _get_streams(): List<Stream> {
        return this.db.session.streams.filter {
            Streams.object_id eq this.obj.object_id
        }.sortedBy {
            Streams.stream_id
        }.map {
            ObjectFactory.model_stream_to_higu_stream( this.db, it )
        }
    }

    fun get_streams(): List<Stream> {
        return this.db._access().with { this._get_streams() }
    }

    fun _drop_streams() {
        this._get_streams().forEach { s ->
            s._drop_data()

            this.db.session.stream_metadata.removeIf { StreamMetadata.stream_id eq s.stream.stream_id }
            this.db.session.stream_log.removeIf { StreamLog.stream_id eq s.stream.stream_id }
        }

        this.db.session.streams.removeIf { Streams.object_id eq this.obj.object_id }
    }

    fun _drop_expendable_streams() {
        this.db.session.streams.filter {
            (Streams.object_id eq this.obj.object_id) and
            (Streams.priority less SP_NORMAL)
        }.forEach { s ->
            val stream = ObjectFactory.model_stream_to_higu_stream( this.db, s )
            stream._drop_data()

            this.db.session.stream_metadata.removeIf { StreamMetadata.stream_id eq s.stream_id }
            this.db.session.stream_log.removeIf { StreamLog.stream_id eq s.stream_id }
        }

        this.db.session.streams.removeIf {
            (Streams.object_id eq this.obj.object_id) and
            (Streams.priority less SP_NORMAL)
        }
    }

    fun drop_expendable_streams() {
        this.db._access().with { this._drop_expendable_streams() }
    }

    fun _get_root_stream(): Stream? {
        val stream_id = this.obj.root_stream_id ?: return null
        return this.db.session.streams.find {
                    Streams.stream_id eq stream_id
                }?.let {
                    ObjectFactory.model_stream_to_higu_stream( this.db, it )
                }
    }

    fun get_root_stream(): Stream? {
        return this.db._access().with { this._get_root_stream() }
    }

    fun _verify() {
        this._get_streams().forEach { s ->
            s._verify()
        }
    }
}