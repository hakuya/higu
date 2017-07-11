import time

import hdbfs
import hdbfs.ark
import hdbfs.model

class ThumbGenerator:

    def __init__( self ):

        self.__objects = []

    def __pop_object( self, db ):

        if( len( self.__objects ) == 0 ):
            
            # TODO, this is hacky!
            self.__objects = [ obj_id[0] for obj_id in
                    db.session.query( hdbfs.model.Object.object_id ) \
                    .filter( hdbfs.model.Object.object_type == hdbfs.TYPE_FILE ) \
                    .order_by( 'RANDOM()' ).limit( 500 ) ]

        if( len( self.__objects ) == 0 ):
            return None

        obj_id = self.__objects.pop()
        return db.get_object_by_id( obj_id )

    def run( self, max_exp, force = False, sleep = None ):

        db = hdbfs.Database()

        try:
            db.enable_write_access() 

            obj = self.__pop_object( db )
            if( obj is None ):
                return

            print 'Generating thumbs for', obj.get_id()
            exp = hdbfs.ark.MIN_THUMB_EXP

            while( db.tbcache.make_thumb( obj, exp ) is not None
               and exp <= max_exp ):

                exp += 1

                if( sleep is not None ):
                    time.sleep( sleep )
        finally:
            db.close()
