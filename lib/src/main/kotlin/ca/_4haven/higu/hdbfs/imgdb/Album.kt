package ca._4haven.higu.hdbfs.imgdb

import ca._4haven.higu.hdbfs.*
import ca._4haven.higu.hdbfs.basic_objects.*
import ca._4haven.higu.hdbfs.model.*

class Album( db: Database, obj: ModelObject ) : OrderedGroup( db, obj ) {
    /* TODO
    override fun _on_created( stream: Stream ) {
        _require_metadata_init( this, None )
    }

    def _on_children_changed( self ):

        _require_metadata_init( self, None )

    def get_origin_time( self ):

        print 'GO1'
        self.check_metadata()
        print 'GO2'
        try:
            print 'GO3'
            return datetime.datetime\
                    .utcfromtimestamp( self['origin_time'] )
        except:
            return None

    def set_text( self, text ):

        self['text'] = text

    def get_text( self ):

        try:
            return self['text']
        except KeyError:
            return None

    def check_metadata( self ):

        try:
            ver = self['.metaver']
            if( ver == METADATA_VERSION ):
                return
        except:
            pass
        
        self.db.tbcache.init_album_metadata( self )*/
}