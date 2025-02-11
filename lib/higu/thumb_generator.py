import time

import hdbfs
import hdbfs.ark
import hdbfs.imgdb
import hdbfs.model

from hdbfs import ImageFile
from hdbfs import ThumbRequestPrio

from typing import Optional

class ThumbGenerator:

    def __init__( self ):

        self.__objects = []

    def __pop_object( self, db ):

        from sqlalchemy.sql.expression import func
        from sqlalchemy import or_

        if( len( self.__objects ) == 0 ):

            # TODO, this is hacky!
            self.__objects = [ obj_id[0] for obj_id in
                    db.model.query( hdbfs.model.Object.object_id ) \
                    .filter( or_( hdbfs.model.Object.object_type == hdbfs.TYPE_FILE,
                                  hdbfs.model.Object.object_type == hdbfs.TYPE_GROUP ) ) \
                    .order_by( func.random() ).limit( 500 ) ]

        if( len( self.__objects ) == 0 ):
            return None

        obj_id = self.__objects.pop()
        return db.get_object_by_id( obj_id )

    def do_thumb_pass( self, min_prio: ThumbRequestPrio ) -> Optional[str]:

        db = hdbfs.Database()

        try:
            db.enable_write_access()

            im = db.process_next_thumb_request( min_prio )
            if( im is not None ):
                return repr( im )
            else:
                return None

        finally:
            db.close()

    def do_metadata_pass( self ):

        db = hdbfs.Database()

        try:
            db.enable_write_access()

            obj = self.__pop_object( db )
            if( obj is None ):
                return

            if( isinstance( obj, hdbfs.ImageFile ) ):
                print( f'Generating metadata for file {obj!r}' )
                obj.check_metadata()

            elif( isinstance( obj, hdbfs.Album ) ):
                print( f'Generating metadata for album {obj!r}' )
                obj.check_metadata()

                db.tbcache.init_album_metadata( obj )

        finally:
            db.close()

    def run( self, max_exp, force = False, sleep = None ):

            while( True ):
                im = self.do_thumb_pass( ThumbRequestPrio.MARK_REQUESTED )
                if( im is None ):
                    break
                print( f'Generating thumb for file {im}' )
                time.sleep( 0.2 )

            self.do_thumb_pass( ThumbRequestPrio.OPTIONAL )
            self.do_metadata_pass()

            if( sleep is not None ):
                time.sleep( sleep )
