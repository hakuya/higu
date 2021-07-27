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
            return None

    def __reorient( self, remap ):

        with self.db._access( write = True ):
            if( self.obj.root_stream is None ):
                return

            try:
                orientation = self.obj.root_stream['orientation']
            except:
                orientation = 1

            orientation = remap[orientation-1]
            self.obj.root_stream['orientation'] = orientation

            # We need to purge the size
            try:
                del self.obj['width']
            except KeyError:
                pass

            try:
                del self.obj['height']
            except KeyError:
                pass

        self.db.tbcache.purge_thumbs( self )

    def rotate_cw( self ):

        CW_REMAP = [ 6, 5, 8, 7, 4, 3, 2, 1 ]
        self.__reorient( CW_REMAP )

    def rotate_ccw( self ):

        CCW_REMAP = [ 8, 7, 6, 5, 2, 1, 4, 3 ]
        self.__reorient( CCW_REMAP )

    def mirror( self ):

        MIRROR_REMAP = [ 2, 1, 4, 3, 8, 7, 6, 5 ]
        self.__reorient( MIRROR_REMAP )

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