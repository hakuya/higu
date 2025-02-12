from hdbfs.objects.basic import Obj
from hdbfs.objects.file import File
from hdbfs.session import Session

import hdbfs.model as model

from typing import List

class Group( Obj ):

    def __init__( self, session: Session, obj: model.Object ):

        super().__init__( session, obj )

    def is_ordered( self ) -> bool:
        '''Returns true if this group is ordered.'''

        return False

    def get_items( self, limit = None ) -> List[Obj]:

        return self.get_children( [
                    model.ObjectClass.FILE,
                    model.ObjectClass.ALBUM
                ], limit )

    def get_albums( self, limit = None ) -> List['Album']:

        return self.get_children( model.ObjectClass.ALBUM, limit )

    def get_files( self, limit = None ) -> List[File]:

        return self.get_children( model.ObjectClass.FILE, limit )

class OrderedGroup( Group ):

    def __init__( self, session: Session, obj: model.Object ):

        super().__init__( session, obj )

    def is_ordered( self ) -> bool:

        #TODO: check if ordered
        return True

    def clear_order( self ) -> None:

        all_objs = self.get_files()

        for child in all_objs:
            child.reorder( self )

    def set_order( self, children ):

        with self.session._access( write = True ):

            all_objs = self.get_items()

            for child in enumerate( children ):
                assert( child[1] in all_objs )
                all_objs.remove( child[1] )

                child[1].reorder( self, child[0] )

            offset = len( children )

            for child in enumerate( all_objs ):
                child[1].reorder( self, offset + child[0] )


class Tag( Group ):

    def __init__( self, db, obj: model.Object ):

        Group.__init__( self, db, obj )
