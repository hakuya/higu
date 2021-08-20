package ca._4haven.higu.hdbfs

import ca._4haven.higu.hdbfs.ark.*
import ca._4haven.higu.hdbfs.basic_objects.*
import ca._4haven.higu.hdbfs.imgdb.*
import ca._4haven.higu.hdbfs.model.*
import ca._4haven.higu.hdbfs.dbutils.Session
import java.nio.file.*
import java.time.Instant
import kotlin.io.path.isDirectory
import org.ktorm.entity.*
import org.ktorm.database.*
import org.ktorm.dsl.*

class Database( library_path: String? = null ) {

    class _AccessContext( val manager: AccessManager,
                          val write: Boolean = false,
                          val transaction: Boolean = false )
    {
        private var active = false

        init {
            this.manager._begin_access( this )
            this.active = true
        }

        private fun closeFinally( ex: Exception? ) {
            this.active = false
            this.manager._end_access( this, ex != null )
        }

        fun < R > with( block: (_AccessContext) -> R ): R {
            var except: Exception? = null;

            try {
                return block( this );
            } catch( ex: Exception ) {
                except = ex;
                throw ex
            } finally {
                this.closeFinally( except )
            }
        }

        fun commit() = this.manager._commit( this )
        fun rollback() = this.manager._rollback( this )
    }

    class AccessManager( val __db: Database ) {

        var write_permitted = false

        private val __accesses = mutableListOf<_AccessContext>();
        private var __locked = false
        private var __failed = false

        private fun check( condition: Boolean, msg: String? = null ) {
            if( condition ) return
            throw RuntimeException( msg )
        }

        fun _begin_access( dba: _AccessContext ) {

            check( !dba.write or this.write_permitted, "Read-Only Access" )

            if( dba.transaction ) {
                assert( this.__accesses.size == 0 )
            }

            this.__accesses.add( dba )

            if( dba.write && !this.__locked ) {
                this.__db._begin()
                this.__locked = true
            }
        }

        fun _end_access( dba: _AccessContext, is_except: Boolean ) {

            // Don't pop yet! we may be within the pre-commit hook!
            check( dba == this.__accesses.last() )

            if( this.__accesses.size == 1 ) {
                if( this.__locked ) {
                    var committed = false
                    var except: Exception? = null

                    if( !is_except ) {
                        try {
                            this.__db._commit()
                            committed = true
                        } catch( ex: Exception ) {
                            except = ex
                        }
                    }

                    if( !committed ) {
                        this.__db._rollback()
                    }
                    except?.let { throw except }
                }

                this.__locked = false
            }

            assert( dba == this.__accesses.removeLast() )
        }

        fun _commit( dba: _AccessContext ) {

            check( this.__locked, "Can only commit with write access" )
            check( this.__accesses[0] == dba, "Only transaction may commit" )

            this.__db._commit()
            if( this.__locked ) {
                this.__db._begin()
            }
        }

        fun _rollback( dba: _AccessContext ) {

            check( this.__locked, "Can only rollback with write access" )
            check( this.__accesses.first() == dba, "Only transaction may rollback" )

            this.__db._rollback()
            if( this.__locked ) {
                this.__db._begin()
            }
        }

        operator fun invoke( write: Boolean = false, transaction: Boolean = false ): _AccessContext {
            return _AccessContext( this, write, transaction )
        }
    }

    var library: Path
    val model = Model()
    val session: Session

    val hooks = Hooks( this )
    val imgdb: StreamDatabase
    val tbcache: ThumbCache

    val _access = AccessManager( this )
    var transaction: Transaction? = null

    var obj_del_list = mutableListOf<Id>()

    init {
        this.library = library_path?.let { Paths.get( it ) }
                            ?: Database.defaultLibrary

        if( !this.library.toFile().isDirectory() ) {
            this.library.toFile().mkdirs()
        }

        this.model.init( this.library.resolve( HIGURASHI_DB_NAME ).toString(),
                         this.library.toString() )
        this.session = this.model.session

        val imgdat_config = Config( this.library.toString() )
        this.imgdb = StreamDatabase( imgdat_config )
        this.tbcache = ThumbCache( this, this.imgdb )
    }

    /*def __del__( self ):

        if( self.session is not None ):
            self.session.close()*/

    fun _begin() {
        Log.debug( "Starting transaction" )
        if( this.transaction != null ) throw IllegalStateException()
        this.transaction = this.session.transactionManager
                               .newTransaction( TransactionIsolation.SERIALIZABLE )
    }

    fun _commit() {
        Log.debug( "Comitting transaction" )
        val transaction = this.transaction ?: throw IllegalStateException()

        this.imgdb.prepare_commit()

        try {
            this.hooks.trigger_pre_commit_hooks( false )
            transaction.commit()
            this.imgdb.complete_commit()
        } catch( ex: Exception ) {
            Log.warning( "Exception ${ex} occurred during commit, rolling back..." )
            this.imgdb.unprepare_commit()
            throw ex
        }

        this.obj_del_list = mutableListOf()
        transaction.close()
        this.transaction = null

        this.hooks.trigger_post_commit_hooks( false )
    }

    fun _rollback() {
        Log.debug( "Rolling back transaction" )
        val transaction = this.transaction ?: throw RuntimeException()

        this.hooks.trigger_pre_commit_hooks( true )

        this.imgdb.rollback()
        transaction.rollback()
        transaction.close()
        this.transaction = null

        this.hooks.trigger_post_commit_hooks( true )
    }

    /* TODO
    fun close() {
        this.session.close()
        this.session = null
    }*/

    fun enable_write_access() {
        this._access.write_permitted = true
    }

    fun transaction(): _AccessContext {
        return this._access()
    }

    fun _get_object_by_id( object_id: Id ): Obj? {
        val obj = this.session.objects.find {
            Objects.object_id eq object_id
        } ?: return null

        return ObjectFactory.model_obj_to_higu_obj( this, obj )
    }

    fun get_object_by_id( object_id: Id ): Obj? {
        return this._access().with {
            this._get_object_by_id( object_id )
        }
    }

    /* TODO
    fun get_stream_by_id( stream_id ) {

        this._access().with {
            stream = this.session.query( model.Stream ) \
                         .filter( model.Stream.stream_id == stream_id ) \
                         .first()
            if( stream is None ):
                return None

            return ObjectFactory.model_stream_to_higu_stream( this, stream )
        }
    }

    fun all_albums_or_free_files() {

        from sqlalchemy.sql.expression import func

        files = this.session.query( model.Object.object_id ) \
                .filter( model.Object.object_type == TYPE_FILE )
        albums = this.session.query( model.Object.object_id ) \
                .filter( model.Object.object_type == TYPE_ALBUM )
        all_children = this.session.query( model.Relation.child_id ) \
                .filter( model.Relation.parent_id.in_( albums ) )
        free_files = files.filter( ~model.Object.object_id.in_( all_children ) )

        select_ids = free_files.union( albums )

        return ModelObjToHiguObjIterator( this, 
                this.session.query( model.Object )
                    .filter( model.Object.object_id.in_( select_ids ) )
                    .order_by( func.random() ) )
    }

    fun unowned_files() {

        from sqlalchemy.sql.expression import func
        from sqlalchemy import or_

        all_children = this.session.query( model.Relation.child_id )
        return ModelObjToHiguObjIterator( this,
                this.session.query( model.Object )
                    .filter( model.Object.object_type.in_( [ TYPE_FILE, TYPE_ALBUM ] ) )
                    .filter( ~model.Object.object_id.in_( all_children ) )
                    .order_by( func.random() ) )
    }*/

    fun lookup_streams_by_details( file_length: Long? = null,
                                   hash_crc32: String? = null,
                                   hash_md5: String? = null,
                                   hash_sha1: String? = null ): List<Stream>
    {
        var q = this.session.streams

        file_length?.let { v -> q = q.filter { Streams.stream_length eq v } }
        hash_crc32?.let { v -> q = q.filter { Streams.hash_crc32 eq v } }
        hash_md5?.let { v -> q = q.filter { Streams.hash_md5 eq v } }
        hash_sha1?.let { v -> q = q.filter { Streams.hash_sha1 eq v} }

        return q.map { ObjectFactory.model_stream_to_higu_stream( this, it ) }
    }

    fun lookup_streams_by_details( details: Details ): List<Stream> {
        return lookup_streams_by_details( details.length,
                                          details.crc32,
                                          details.md5,
                                          details.sha1 )
    }

    /* TODO
    fun lookup_untagged_files() {
        return this.unowned_files()
    }

    fun all_tags() {

        var objs = this.session.query( model.Object ) \
                        .filter( model.Object.object_type == TYPE_CLASSIFIER ) \
                        .order_by( model.Object.name )

        return ModelObjToHiguObjIterator( this, objs )
    }*/

    fun get_tag( name: String ): Tag {
        val obj = this.session.objects.find {
            (Objects.name eq name) and
            (Objects.object_type eq TYPE_CLASSIFIER)
        } ?: throw NoSuchElementException( "No such tag ${name}" )

        return ObjectFactory.model_obj_to_higu_obj( this, obj ) as Tag
    }

    fun _make_tag( name: String ): Tag {

        check_tag_name( name )
        try {
            return this.get_tag( name )
        } catch( ex: NoSuchElementException ) {
            val _timestamp = Instant.now().getEpochSecond()

            val mobj = ModelObject {
                this.object_type = TYPE_CLASSIFIER
                this.create_ts = _timestamp
                this.name = name
            }
            this.session.objects.add( mobj )
            return ObjectFactory.model_obj_to_higu_obj( this, mobj ) as Tag
        }
    }

    fun make_tag( name: String ): Tag {
        return this._access( write = true ).with {
            this._make_tag( name )
        }
    }

    /* TODO
    fun delete_tag( tag: String ) {
        val obj = this.get_tag( tag )
        self.delete_object( obj )
    }

    fun move_tag( tag: String, target: String ) {

        from sqlalchemy import and_

        this._access( write = True ).use {

            check_tag_name( target )
            c = this.get_tag( tag ).obj

            try {
                d = this.get_tag( target ).obj

                # Remove tag where it would be a duplicate
                dups = this.session.query( model.Relation.child_id ) \
                    .filter( model.Relation.parent_id == d.object_id ) \
                    .subquery()
                this.session.query( model.Relation ) \
                    .filter( and_( model.Relation.parent_id == c.object_id,
                                   model.Relation.child_id.in_( dups ) ) ) \
                    .delete( synchronize_session = 'fetch' )
                this.session.flush()
                this.session.query( model.Relation ) \
                    .filter( model.Relation.parent_id == c.object_id ) \
                    .update( { 'parent_id' : d.object_id } )
                this.session.delete( c )
            } catch( ex: KeyError ) {
                c.name = target
            }
        }
    }

    fun copy_tag( tag: String, target: String ) {

        this._access( write = True ).use {
            check_tag_name( target )
            c = this.get_tag( tag ).obj

            try:
                d = this.get_tag( target ).obj
            except KeyError:
                d = model.Object( TYPE_CLASSIFIER, target )
                this.session.add( d )

            for rel in c.child_rel:
                rel_copy = model.Relation( rel.sort )
                rel_copy.parent_obj = d
                rel_copy.child_obj = rel.child_obj
        }
    }

    fun __recover_file( path: String ): Boolean {
        import mimetypes

        val name = os.path.split( path )[1]

        details = calculate_details( path )
        streams = this.lookup_streams_by_details( *details )

        if( len( streams ) == 0 ) return false

        if( not streams[0]._verify() ) {
            this.imgdb.load_data( path, streams[0].stream.stream_id,
                                        streams[0].stream.priority,
                                        streams[0].stream.extension )

            val ext = os.path.splitext( path )[1]
            assert ext[0] == '.'
            streams[0].stream.extension = ext[1:]
            streams[0].stream.mime_type = mimetypes.guess_type( path, strict=False )[0]
        }
        return true
    }

    fun recover_files( files ) {

        self._access( write = True ).use {
            for f in files:
                if( not this.__recover_file( f ) ):
                    #log.warn( '%s was not found in the db and was ignored', f )
                    pass
        }
    }

    fun __create_album( tags = [], name = None, text = None ) {
        album = model.Object( TYPE_ALBUM )
        self.session.add( album )
        album = model_obj_to_higu_obj( this, album )

        if( name is not None ) {
            album.obj.name = make_unicode( name )
        }

        if( text is not None ) {
            album.obj['text'] = make_unicode( text )
        }

        for t in tags:
            album._assign( t, None )

        return album
    }

    fun create_album( tags = [], name = None, text = None ) {

        this._access( write = True ).use {
            return this.__create_album( tags, name, text )
        }
    }*/

    data class RegistrationResult( val file: File, val stream: Stream, val was_known: Boolean )

    private fun __register_file( path: String, name_policy: NamePolicy ): RegistrationResult
    {
        val _timestamp = Instant.now().getEpochSecond()

        val _path = Paths.get( path )
        val _file = _path.toFile()

        val _name = _file.getName()
        val _ext = _name.split("\\.(?=[^\\.]+$)".toRegex()).getOrNull(1)
        val _mime_type = Files.probeContentType( _path )

        val details = Details.calculate( _file.inputStream() )

        val streams = this.lookup_streams_by_details( details )
        var new_stream = false

        var f: File? = null
        var stream: Stream? = null

        if( streams.isEmpty() ) {
            // Add object
            val mobj = ModelObject {
                object_type = TYPE_FILE
                create_ts = _timestamp
            }
            this.session.objects.add( mobj )

            // Add stream
            val mstream = ModelStream {
                object_id = mobj.object_id
                name = "."
                priority = SP_NORMAL
                origin_stream_id = null
                extension = _ext
                mime_type = _mime_type
                stream_length = details.length
                hash_crc32 = details.crc32
                hash_md5 = details.md5
                hash_sha1 = details.sha1
            }
            this.session.streams.add( mstream )

            mobj.root_stream_id = mstream.stream_id
            mobj.flushChanges()

            f = ObjectFactory.model_obj_to_higu_obj( this, mobj ) as File
            stream = ObjectFactory.model_stream_to_higu_stream( this, mstream )
            new_stream = true

            f._on_created( stream )
        } else {
            stream = streams[0]
            if( stream.stream.mime_type == null ) {
                stream.stream.mime_type = _mime_type
                stream.stream.flushChanges()
            }

            f = stream._get_file()
        }

        val log = if( name_policy == NAME_POLICY_DONT_REGISTER ) {
                StreamLogEntry {
                    stream_id = stream.stream.stream_id
                    timestamp = _timestamp
                    origin_method = "hdbfs:register"
                    origin_stream_id = null
                    origin_name = null
                }
            } else {
                StreamLogEntry {
                    stream_id = stream.stream.stream_id
                    timestamp = _timestamp
                    origin_method = "hdbfs:register"
                    origin_stream_id = null
                    origin_name = _name
                }
            }

        this.session.stream_log.add( log )

        if( name_policy == NAME_POLICY_SET_ALWAYS
         || (name_policy == NAME_POLICY_SET_IF_UNDEF
          && f.obj.name == null) )
         {
            f.obj.name = _name
         }
         f.obj.flushChanges()

        if( !stream._verify() ) {
            this.imgdb.load_data( path, stream.stream.stream_id,
                                        stream.stream.priority,
                                        stream.stream.extension )
        }

        return RegistrationResult( f, stream, !new_stream )
    }

    fun register_file( path: String, name_policy: NamePolicy = NAME_POLICY_SET_IF_UNDEF )
            : RegistrationResult
    {

        return this._access( write = true ).with {
            this.__register_file( path, name_policy )
        }
    }

    private fun __register_thumb( path: String, obj: Obj, origin: Stream, _name: String ): Stream {

        val _timestamp = Instant.now().getEpochSecond()

        val _path = Paths.get( path )
        val _file = _path.toFile()

        val _ext = _name.split("\\.(?=[^\\.]+$)".toRegex()).getOrNull(1)
        val _mime_type = Files.probeContentType( _path )

        val details = Details.calculate( _file.inputStream() )

        val mstream = ModelStream {
            object_id = obj.obj.object_id
            name = _name
            priority = SP_EXPENDABLE
            origin_stream_id = origin.stream.stream_id
            extension = _ext
            mime_type = _mime_type
            stream_length = details.length
            hash_crc32 = details.crc32
            hash_md5 = details.md5
            hash_sha1 = details.sha1
        }
        this.session.streams.add( mstream )

        val log = StreamLogEntry {
            stream_id = mstream.stream_id
            timestamp = _timestamp
            origin_method = "imgdb:${_name}"
            origin_stream_id = origin.stream.stream_id
            origin_name = null
        }
        this.session.stream_log.add( log )

        this.imgdb.load_data( path, mstream.stream_id,
                                    mstream.priority,
                                    mstream.extension )

        return ObjectFactory.model_stream_to_higu_stream( this, mstream )
    }

    fun register_thumb( path: String, obj: Obj, origin: Stream, name: String ): Stream {
        return this._access( write = true ).with {
            this.__register_thumb( path, obj, origin, name )
        }
    }

    /* TODO
    fun batch_add_files( files, tags = [], tags_new = [],
                         name_policy = NAME_POLICY_SET_IF_UNDEF,
                         create_album = False, album_name = None, album_text = None )
    {
        this._access( write = True ).use {
            // Load tags
            taglist = []
            taglist += map( this.get_tag, tags )
            taglist += map( this._make_tag, tags_new )

            if( create_album ):
                album = this.__create_album( taglist, album_name, album_text )
            else:
                album = None

            for f in files:
                x, stream, is_new = this.__register_file( f, name_policy )

                if( album is not None ):
                    x._assign( album, None )
                else:
                    for t in taglist:
                        x._assign( t, None )
        }
    }*/

    fun _merge_objects( primary_obj: File, merge_obj: File ) {

        val obj_p = primary_obj.obj
        val obj_m = merge_obj.obj

        if( obj_p.object_id == obj_m.object_id ) return

        merge_obj._drop_expendable_streams()

        // Rename the root stream of the object to be merged so that it
        // appears as a duplicate stream
        val stream = this.session.streams.find { Streams.stream_id eq obj_m.root_stream_id!! }!!
        stream.name = "dup:${stream.hash_sha1}"
        stream.flushChanges()

        // Move all streams from the object to be merged to the 
        this.session.update( Streams ) {
            set( Streams.object_id, obj_p.object_id )
            where {
                Streams.object_id eq obj_m.object_id
            }
        }

        // Delete the metadata on the object to be merged, it will not be
        // persisted
        this.session.object_metadata.removeIf {
            ObjectMetadata.object_id eq obj_m.object_id
        }

        // Drop relationships with duplicate
        /* TODO
        this.session.query( model.Relation ) \
            .filter( and_( model.Relation.parent_id == obj_p.object_id,
                           model.Relation.child_id == obj_m.object_id ) ) \
            .delete()
        this.session.query( model.Relation ) \
            .filter( and_( model.Relation.parent_id == obj_m.object_id,
                           model.Relation.child_id == obj_p.object_id ) ) \
            .delete()

        // Move relationships which do not conflict
        r_i = aliased( model.Relation )

        this.session.query( model.Relation ) \
            .filter( and_( model.Relation.parent_id == obj_m.object_id,
                           ~this.session.query( r_i )
                                .filter( and_( r_i.parent_id == obj_p.object_id,
                                               r_i.child_id == model.Relation.child_id ) )
                               .exists() ) ) \
            .update( { 'parent_id' : obj_p.object_id },
                     synchronize_session = 'fetch' )
        this.session.query( model.Relation ) \
            .filter( and_( model.Relation.child_id == obj_m.object_id,
                           ~this.session.query( r_i )
                                .filter( and_( r_i.parent_id == model.Relation.parent_id,
                                               r_i.child_id == obj_p.object_id ) )
                               .exists() ) ) \
            .update( { 'child_id' : obj_p.object_id },
                     synchronize_session = 'fetch' )

        // Copy sort from relationships that conflict
        for r_m in this.session.query( model.Relation ) \
                       .filter( model.Relation.parent_id == obj_m.object_id ):

            r_p = this.session.query( model.Relation ) \
                      .filter( and_( model.Relation.parent_id == obj_p.object_id,
                                     model.Relation.child_id == r_m.child_id ) ) \
                      .first()

            if( r_p.sort is None ):
                r_p.sort = r_m.sort

        for r_m in this.session.query( model.Relation ) \
                       .filter( model.Relation.child_id == obj_m.object_id ):

            r_p = this.session.query( model.Relation ) \
                      .filter( and_( model.Relation.child_id == obj_p.object_id,
                                     model.Relation.parent_id == r_m.parent_id ) ) \
                      .first()

            if( r_p.sort is None ):
                r_p.sort = r_m.sort

        this.session.query( model.Relation ) \
            .filter( and_( model.Relation.parent_id == obj_m.object_id,
                           this.session.query( r_i )
                               .filter( and_( r_i.parent_id == model.Relation.parent_id,
                                              r_i.child_id == model.Relation.child_id ) )
                               .exists() ) ) \
            .update( { 'sort' : obj_p.object_id },
                     synchronize_session = 'fetch' )

        // Drop remaining relationships
        this.session.query( model.Relation ) \
                    .filter( or_( model.Relation.parent_id == obj_m.object_id,
                                  model.Relation.child_id == obj_m.object_id ) ) \
                    .delete()
        */

        this.session.objects.removeIf {
            Objects.object_id eq obj_m.object_id
        }
    }

    fun merge_objects( primary_obj: File, merge_obj: File ) {
        this._access( write = true ).with {
            this._merge_objects( primary_obj, merge_obj )
        }
    }

    fun delete_object( obj: Obj ) {

        this._access( write = true ).with {

            val object_id = obj.obj.object_id

            (obj as? File)?.let {
                it._drop_streams()
                this.obj_del_list.add( object_id )
            }

            this.session.object_metadata.removeIf { ObjectMetadata.object_id eq object_id }
            /* TODO
            this.session.query( model.Relation ) \
                .filter( model.Relation.parent_id == object_id ) \
                .delete()
            this.session.query( model.Relation ) \
                .filter( model.Relation.child_id == object_id ) \
                .delete()*/
            this.session.objects.removeIf { Objects.object_id eq object_id }
        }
    }

    companion object {
        var defaultLibrary: Path

        init {
            defaultLibrary = Paths.get( System.getProperty( "user.home" ), ".higu" )

            ObjectFactory.add_stream_factory( { db, stream ->
                // TODO pick only image mime types?
                ImageStream( db, stream )
            } )
            ObjectFactory.add_obj_factory( { db, obj ->
                when {
                    obj.object_type == TYPE_FILE -> ImageFile( db, obj )
                    obj.object_type == TYPE_ALBUM -> Album( db, obj )
                    obj.object_type == TYPE_CLASSIFIER -> Tag( db, obj )
                    else -> null
                }
            } )
        }

        /* TODO
        fun init( library_path: String? = null ) {
            global _LIBRARY

            if( library_path != null )
                _LIBRARY = library_path
            else
                _LIBRARY = DEFAULT_LIBRARY

            if( !os.path.isdir( _LIBRARY ) )
                os.makedirs( _LIBRARY )

            model.init( os.path.join( _LIBRARY, HIGURASHI_DB_NAME ),
                        _LIBRARY )
        }

        fun dispose() {
            model.dispose()
            _LIBRARY = null
        }

        fun compare_details( a, b ): Booean {
            return long( a[0] ) == long( b[0] ) \
                && str( a[1] ) == str( b[1] ) \
                && str( a[2] ) == str( b[2] ) \
                && str( a[3] ) == str( b[3] )
        }*/

        fun check_tag_name( name: String ) {
            "^[\\w\\-_:]+$".toRegex().matchEntire( name )
                    ?: throw IllegalArgumentException( "\"${name}\" is not a valid tag name" )
        }
    }
}