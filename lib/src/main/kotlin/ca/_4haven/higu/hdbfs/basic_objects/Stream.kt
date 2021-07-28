package ca._4haven.higu.hdbfs.basic_objects

import ca._4haven.higu.hdbfs.*
import ca._4haven.higu.hdbfs.model.*
import java.io.InputStream
import org.ktorm.dsl.*
import org.ktorm.entity.*

open class Stream( val db: Database, val stream: ModelStream ) {

    fun _get_file(): File {
        return this.db.session.objects.find {
            Objects.object_id eq this.stream.object_id
        }.let {
            ObjectFactory.model_obj_to_higu_obj( this.db, it!! )
        } as File
    }

    fun get_file(): File {
        return this.db._access().with { this.get_file() }
    }

    fun get_stream_id(): Id {
        return this.db._access().with { this.stream.stream_id }
    }

    fun get_name(): String {
        return this.db._access().with { this.stream.name }
    }

    fun get_priority(): Int {
        return this.db._access().with { this.stream.priority }
    }

    fun get_creation_time() {
        /* TODO
        this.db._access().with {
            create_log = this.stream.log_entries \
                            .order_by( model.StreamLog.timestamp ).first()
            return datetime.datetime.fromtimestamp( create_log.timestamp )
        }*/
    }

    fun get_creation_time_utc() {
        /* TODO
        this.db._access().with {
            create_log = this.stream.log_entries \
                            .order_by( model.StreamLog.timestamp ).first()
            return datetime.datetime.utcfromtimestamp( create_log.timestamp )
        }*/
    }

    fun get_origin_stream(): Stream? {
        /* TODO
        return this.db._access().with {
            if( this.stream.origin_stream != null )
                model_stream_to_higu_stream( this.db, this.stream.origin_stream )
            else
                null
        }*/
        return null
    }

    fun get_origin_method(): String? {
        /* TODO
        this.db._access().with {
            create_log = this.stream.log_entries \
                            .order_by( model.StreamLog.timestamp ).first()
            return create_log.origin_method
        }*/
        return null
    }

    fun get_length(): Long? {
        return this.db._access().with { this.stream.stream_length }
    }

    fun get_hash(): String? {
        return this.db._access().with { this.stream.hash_sha1 }
    }

    fun get_extension(): String? {
        return this.db._access().with { this.stream.extension }
    }

    fun get_mime(): String? {
        return this.db._access().with { this.stream.mime_type }
    }

    fun _read(): InputStream? {
        return this.db.imgdb.read( this.stream.stream_id,
                                   this.stream.priority,
                                   this.stream.extension  )
    }

    fun read(): InputStream? {
        return this.db._access().with { this._read() }
    }

    fun _verify(): Boolean {
        val istm = this._read() ?: return false

        val details = Details.calculate( istm )

        if( details.length != this.stream.stream_length ) return false
        if( details.crc32  != this.stream.hash_crc32 )    return false
        if( details.md5    != this.stream.hash_md5 )      return false
        if( details.sha1   != this.stream.hash_sha1 )     return false

        return true
    }

    fun verify() {
        return this.db._access().with { this._verify() }
    }

    fun _drop_data() {
        this.db.imgdb.delete( this.stream.stream_id,
                              this.stream.priority,
                              this.stream.extension )
    }

    fun get_repr(): String {
        return "s%016x.%s".format( this.get_stream_id(),
                                   this.get_extension() )
    }

    fun getItem( key: String ): Any? {
        return this.db._access().with {
            val entry = this.db.session.stream_metadata.find {
                (StreamMetadata.stream_id eq this.stream.stream_id) and
                (StreamMetadata.key eq key)
            }
            entry?.numeric ?: entry?.value
        }
    }

    fun setItem( key: String, value: Any? ) {
        if( value == null ) return delItem( key )

        this.db._access( write = true ).with {
            val entry = StreamMetadataEntry {
                this.stream_id = this@Stream.stream.stream_id
                this.key = key
                this.value = value.toString()
                this.numeric = value as? Int
            }

            if( this.db.session.stream_metadata.update( entry ) < 1 ) {
                this.db.session.stream_metadata.add( entry )
            }
        }
    }

    fun delItem( key: String ) {
        this.db._access( write = true ).with {
            this.db.session.stream_metadata.removeIf {
                (StreamMetadata.stream_id eq this.stream.stream_id) and
                (StreamMetadata.key eq key)
            }
        }
    }

    override fun equals( o: Any? ): Boolean {
        if( o == null ) return false
        if( o !is Stream ) return false
        return this.db == o.db && this.stream == o.stream
    }
}
