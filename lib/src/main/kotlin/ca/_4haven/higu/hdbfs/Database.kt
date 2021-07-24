package ca._4haven.higu.hdbfs

import ca._4haven.higu.hdbfs.ark.*
import ca._4haven.higu.hdbfs.basic_objects.*
import ca._4haven.higu.hdbfs.imgdb.*
import ca._4haven.higu.hdbfs.model.*
import java.nio.file.Paths
import java.nio.file.Path
import kotlin.io.path.isDirectory

val HIGURASHI_DB_NAME = "hfdb.dat"

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

                    if( !is_except ) {
                        try {
                            this.__db._commit()
                            committed = true
                        } catch( ex: Exception ) {}
                    }

                    if( !committed ) {
                        this.__db._rollback()
                    }
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
    //val session = model.Session();

    val hooks = Hooks( this )
    val imgdb: StreamDatabase
    val tbcache: ThumbCache

    val _access = AccessManager( this )
    var _trans_write = false;

    var obj_del_list = listOf<Obj>()

    init {
        if( library_path != null ) {
            this.library = Paths.get( library_path )
        } else {
            this.library = Paths.get( System.getProperty( "user.home" ), ".higu" )
        }

        if( !this.library.toFile().isDirectory() ) {
            this.library.toFile().mkdirs()
        }

        this.model.init( this.library.resolve( HIGURASHI_DB_NAME ).toString(),
                         this.library.toString() )

        val imgdat_config = Config( this.library.toString() )
        this.imgdb = StreamDatabase( imgdat_config )
        this.tbcache = ThumbCache( this, this.imgdb )
    }

    /*def __del__( self ):

        if( self.session is not None ):
            self.session.close()*/

    fun _begin() {

        /*assert not self._trans_write
        self.session.execute( 'BEGIN EXCLUSIVE' )
        self._trans_write = True*/
    }

    fun _commit() {
        /* TODO
        if( !this._trans_write ) return

        this.imgdb.prepare_commit()

        try {
            this.hooks.trigger_pre_commit_hooks( false )
            this.session.commit()
            this.imgdb.complete_commit()
        } catch {
            this.imgdb.unprepare_commit()
            throw
        }

        this.obj_del_list = listOf()
        this._trans_write = false

        this.hooks.trigger_post_commit_hooks( false )*/
    }

    fun _rollback() {
        /* TODO
        if( !this._trans_write ) return

        this.hooks.trigger_pre_commit_hooks( true )

        this.imgdb.rollback()
        this.session.rollback()
        this._trans_write = false

        this.hooks.trigger_post_commit_hooks( true )*/
    }

    /* TODO
    fun close() {
        this.session.close()
        this.session = null
    }

    fun enable_write_access() {
        this._access.write_permitted = true
    }

    fun transaction(): _AccessContext {
        return this._access()
    }

    fun _get_object_by_id( object_id ) {
        val obj = self.session.query( model.Object ) \
                    .filter( model.Object.object_id == object_id ) \
                    .first()
        if( obj == null ) return null

        return ObjectFactory.model_obj_to_higu_obj( this, obj )
    }

    fun get_object_by_id( object_id ) {
        this._access().with {
            return this._get_object_by_id( object_id )
        }
    }

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
    }

    fun lookup_streams_by_details( file_length = null,
                                   hash_crc32 = null,
                                   hash_md5 = null,
                                   hash_sha1 = null )
    {
        var q = this.session.query( model.Stream )
        if( file_length is not None ):
            q = q.filter( model.Stream.stream_length == file_length )
        if( hash_crc32 is not None ):
            q = q.filter( model.Stream.hash_crc32 == hash_crc32 )
        if( hash_md5 is not None ):
            q = q.filter( model.Stream.hash_md5 == hash_md5 )
        if( hash_sha1 is not None ):
            q = q.filter( model.Stream.hash_sha1 == hash_sha1 )

        return [ model_stream_to_higu_stream( this, s ) for s in q ]
    }

    fun lookup_untagged_files() {
        return this.unowned_files()
    }

    fun all_tags() {

        var objs = this.session.query( model.Object ) \
                        .filter( model.Object.object_type == TYPE_CLASSIFIER ) \
                        .order_by( model.Object.name )

        return ModelObjToHiguObjIterator( this, objs )
    }

    fun get_tag( name: String ) {

        var obj = this.session.query( model.Object ) \
                    .filter( model.Object.object_type == TYPE_CLASSIFIER ) \
                    .filter( model.Object.name == name ).first()
        if( obj == null ) {
            raise KeyError, 'No such tag "%s"' % ( name, )
        }

        return model_obj_to_higu_obj( this, obj )
    }

    fun _make_tag( name: String ) {

        check_tag_name( name )
        try {
            return this.get_tag( name )
        } catch( ex: KeyError ) {
            obj = model.Object( TYPE_CLASSIFIER, name )
            self.session.add( obj )
            return model_obj_to_higu_obj( this, obj )
        }
    }

    fun make_tag( name: String ) {
        this._access( write = True ).use {
            return this._make_tag( name )
        }
    }

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
    }

    fun __register_file( path: String, name_policy ) {

        import mimetypes

        name = os.path.split( path )[1].decode( sys.getfilesystemencoding() )
        ext = os.path.splitext( name )[1]
        assert ext[0] == '.'
        ext = ext[1:]

        details = calculate_details( path )

        mime_type = mimetypes.guess_type( path, strict=False )[0]
        streams = this.lookup_streams_by_details( *details )
        new_stream = False

        if( len( streams ) == 0 ) {
            obj = model.Object( TYPE_FILE )
            this.session.add( obj )
            stream = model.Stream( obj, '.', model.SP_NORMAL,
                                   None, ext, mime_type )
            stream.set_details( *details )
            this.session.add( stream )
            obj.root_stream = stream

            f = model_obj_to_higu_obj( this, obj )
            stream = model_stream_to_higu_stream( this, stream )
            new_stream = True

            this.session.flush()
            f._on_created( stream )
        } else {
            stream = streams[0]
            if( stream.stream.mime_type is None ):
                stream.stream.mime_type = mime_type

            f = stream._get_file()
        }

        if( name_policy == NAME_POLICY_DONT_REGISTER ) {
            log = model.StreamLog( stream.stream, 'hdbfs:register',
                                   None, None )
        } else {
            log = model.StreamLog( stream.stream, 'hdbfs:register',
                                   None, name )
        }

        this.session.add( log )

        if( name_policy == NAME_POLICY_SET_ALWAYS
         or (name_policy == NAME_POLICY_SET_IF_UNDEF
         and f.obj.name is None) )
         {
            f.obj.name = name
         }

        if( !stream._verify() ) {
            this.imgdb.load_data( path, stream.stream.stream_id,
                                        stream.stream.priority,
                                        stream.stream.extension )
        }

        return f, stream, new_stream
    }

    fun register_file( path: String, name_policy = NAME_POLICY_SET_IF_UNDEF ) {

        this._access( write = True ).use {
            f, stream, is_new = this.__register_file( path, name_policy )
        }

        return f
    }

    fun __register_thumb( path: String, obj, origin, name ) {

        import mimetypes

        var ext = os.path.splitext( path )[1]
        assert ext[0] == '.'
        ext = ext[1:]

        val details = calculate_details( path )
        val mime_type = mimetypes.guess_type( path, strict=False )[0]

        val stream = model.Stream( obj.obj, name, model.SP_EXPENDABLE,
                                   origin.stream, ext, mime_type )
        stream.set_details( *details )
        this.session.add( stream )

        val log = model.StreamLog( stream, 'imgdb:' + name,
                                   origin.stream, None )
        this.session.add( log )
        this.session.flush()

        this.imgdb.load_data( path, stream.stream_id,
                                    stream.priority,
                                    stream.extension )

        return model_stream_to_higu_stream( this, stream )
    }

    fun register_thumb( path: String, obj, origin, name ) {

        this._access( write = True ).use {
            return this.__register_thumb( path, obj, origin, name )
        }
    }

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
    }

    fun _merge_objects( primary_obj, merge_obj ) {

        from sqlalchemy import and_, or_
        from sqlalchemy.orm import aliased

        assert isinstance( primary_obj, File ), 'Expected File got %r' % ( merge_obj )
        assert isinstance( merge_obj, File ), 'Expected File got %r' % ( merge_obj )

        obj_p = primary_obj.obj
        obj_m = merge_obj.obj

        assert obj_p != obj_m

        merge_obj._drop_expendable_streams()

        // Rename the root stream of the object to be merged so that it
        // appears as a duplicate stream
        stream = obj_m.root_stream
        stream.name = 'dup:' + stream.hash_sha1

        // Move all streams from the object to be merged to the 
        this.session.query( model.Stream ) \
            .filter( model.Stream.object_id == obj_m.object_id ) \
            .update( { 'object_id' : obj_p.object_id } )

        // Delete the metadata on the object to be merged, it will not be
        // persisted
        this.session.query( model.ObjectMetadata ) \
            .filter( model.ObjectMetadata.object_id == obj_m.object_id ) \
            .delete()

        // Drop relationships with duplicate
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

        merge_obj.obj = primary_obj.obj
        this.session.query( model.Object ) \
            .filter( model.Object.object_id == obj_m.object_id ) \
            .delete()
    }

    fun merge_objects( primary_obj, merge_obj ) {
        this._access( write = True ) {
            this._merge_objects( primary_obj, merge_obj )
        }
    }

    fun delete_object( obj ) {

        with this._access( write = True ):

            object_id = obj.obj.object_id

            if( isinstance( obj, File ) ) {
                obj._drop_streams()
                this.obj_del_list.append( object_id )
            }

            this.session.query( model.ObjectMetadata ) \
                .filter( model.ObjectMetadata.object_id == object_id ) \
                .delete()
            this.session.query( model.Relation ) \
                .filter( model.Relation.parent_id == object_id ) \
                .delete()
            this.session.query( model.Relation ) \
                .filter( model.Relation.child_id == object_id ) \
                .delete()
            this.session.query( model.Object ) \
                .filter( model.Object.object_id == object_id ) \
                .delete()
    }

    companion object {
        var _LIBRARY: String? = null

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
        }
    }*/
}