package ca._4haven.higu.hdbfs.imgdb

import ca._4haven.higu.hdbfs.*
import ca._4haven.higu.hdbfs.basic_objects.*
import ca._4haven.higu.hdbfs.model.*

class ImageFile( db: Database, obj: ModelObject ) : File( db, obj ) {

    /* TODO
    def set_root_stream( self, stream ):

        File.set_root_stream( self, stream )
        self.db.tbcache.purge_thumbs( self )
        self.db.tbcache.init_object_metadata( self )

        # Trigger a metadata update on the albums
        for album in self.get_albums():
            album._on_children_changed()

    def _on_created( self, stream ):

        _require_( self, stream )

    def get_dimensions( self ):

        return self.db.tbcache.get_dimensions( self )

    def get_origin_time( self ):

        return self.db.tbcache.get_origin_time( self )

    def set_text( self, text ):

        self['text'] = text

    def get_text( self ):

        try:
            return self['text']
        except KeyError:
            return None*/

    private fun __reorient( remap: List<Int> ) {

        this.db._access( write = true ).with {
            val root_stream = this.get_root_stream() ?: return@with

            var orientation = (root_stream.getItem( "orientation" ) as? Int) ?: 1

            orientation = remap[orientation-1]
            root_stream.setItem( "orientation", orientation )

            // We need to purge the size
            this.delItem( "width" )
            this.delItem( "height" )

            this.db.tbcache.purge_thumbs( this )
        }
    }

    fun rotate_cw() {
        val CW_REMAP = listOf( 6, 5, 8, 7, 4, 3, 2, 1 )
        this.__reorient( CW_REMAP )
    }

    fun rotate_ccw() {
        val CCW_REMAP = listOf( 8, 7, 6, 5, 2, 1, 4, 3 )
        this.__reorient( CCW_REMAP )
    }

    fun mirror() {
        val MIRROR_REMAP = listOf( 2, 1, 4, 3, 8, 7, 6, 5 )
        this.__reorient( MIRROR_REMAP )
    }

    /* TODO
    def auto_orientation( self ):

        with self.db._access( write = True ):
            try:
                del self.obj.root_stream['orientation']
            except KeyError:
                pass

            try:
                del self.obj['width']
            except KeyError:
                pass

            try:
                del self.obj['height']
            except KeyError:
                pass

        self.db.tbcache.purge_thumbs( self )*/

    fun get_thumb_stream( exp: Int ): ImageStream? {
        return this.db.tbcache.make_thumb( this, exp )
    }

    /* TODO
    def check_metadata( self ):

        try:
            ver = self['.metaver']
            if( ver == METADATA_VERSION ):
                return
        except:
            pass
        
        self.db.tbcache.init_object_metadata( self )*/
}