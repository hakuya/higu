import time

import ark
import higu
import model

class ThumbGenerator:

    def __init__( self ):

        self.__object_ids = []

    def __pop_object( self, db ):

        if( len( self.__object_ids ) == 0 ):
            
            self.__objects = [ obj_id[0] for obj_id in
                    db.session.query( model.Object.id ) \
                    .filter( model.Object.type == higu.TYPE_FILE ) \
                    .order_by( 'RANDOM()' ).limit( 500 ) ]

        obj_id = self.__objects.pop()
        return db.get_object_by_id( obj_id )

    def run( self, max_exp, force = False, sleep = None ):

        db = higu.Database()
        db.enable_write_access() 

        obj = self.__pop_object( db )

        print 'Generating thumbs for', obj.get_id()
        exp = ark.MIN_THUMB_EXP

        while( db.tbcache.make_thumb( obj, exp ) is not None
           and exp <= max_exp ):

            exp += 1

            if( sleep is not None ):
                time.sleep( sleep )
