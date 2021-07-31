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
        return this.db._access().with {
            if( all_streams ) {
                this.db.session
                    .from( StreamLog )
                    .innerJoin( Streams, Streams.stream_id eq StreamLog.stream_id )
                    .selectDistinct( StreamLog.origin_name )
                    .where {
                        (Streams.object_id eq this.obj.object_id) and
                        (StreamLog.origin_name.isNotNull())
                    }.map { it[StreamLog.origin_name]!! }
            } else {
                this.obj.root_stream_id?.let { root_stream_id ->
                    this@File.db.session.stream_log.filter {
                        (StreamLog.stream_id eq root_stream_id) and
                        (StreamLog.origin_name.isNotNull())
                    }.mapColumnsNotNull( isDistinct = true ) { it.origin_name }
                } ?: listOf()
            }
        }
    }

    override fun get_repr(): String {
        return this.get_name()
            ?: this.get_root_stream()?.let {
                    it.stream.extension
                }?.let { "%016x.%s".format( this.obj.object_id, it ) }
            ?: "%016x".format( this.obj.object_id )
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