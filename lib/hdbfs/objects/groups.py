from hdbfs.objects.basic import Obj
from hdbfs.objects.file import File
from hdbfs.session import Session, SessionObject

import hdbfs.model as model

from enum import Enum
from typing import List

import random

class Group( Obj ):

    class Order( Enum ):

        UNORDERED = 0
        EXPLICIT = 1
        NAME = 2
        DATE = 3

    def __init__( self, session: Session, obj: model.Object ):

        super().__init__( session, obj )

    def get_ordering( self ) -> 'Group.Order':
        '''Gets the ordering for this group.'''

        return Group.Order.UNORDERED

    def get_items( self, limit = None ) -> List[Obj]:

        items = self.get_children( [
                    model.ObjectClass.FILE,
                    model.ObjectClass.ALBUM
                ], limit )
        if( self.get_ordering() == Group.Order.UNORDERED ):
            # Will cause mismatch in ordering between the tag
            # view and opening up the tile in the webui
            # random.shuffle( items )
            pass
        elif( self.get_ordering() == Group.Order.NAME ):
            items.sort( key = lambda it: it.get_name()
                       if it.get_name() is not None else '' )
        elif( self.get_ordering() == Group.Order.DATE ):
            items.sort( key = lambda it: it.get_origin_time()
                       if it.get_origin_time() is not None else it.get_add_time() )

        return items

    def get_albums( self, limit = None ) -> List['Album']:

        return self.get_children( model.ObjectClass.ALBUM, limit )

    def get_files( self, limit = None ) -> List[File]:

        return self.get_children( model.ObjectClass.FILE, limit )

class OrderedGroup( Group ):

    def __init__( self, session: Session, obj: model.Object ):

        super().__init__( session, obj )

    def get_ordering( self ) -> Group.Order:

        return Group.Order.EXPLICIT

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


class Tag( OrderedGroup ):

    def __init__( self, db, obj: model.Object ):

        Group.__init__( self, db, obj )

    def get_ordering( self ) -> Group.Order:

        return {
            model.ObjectType.CLASSIFIER_UNORDERED  : Group.Order.UNORDERED,
            model.ObjectType.CLASSIFIER_ORDERED    : Group.Order.EXPLICIT,
            model.ObjectType.CLASSIFIER_NAME_ORDER : Group.Order.NAME,
            model.ObjectType.CLASSIFIER_DATE_ORDER : Group.Order.DATE,
        }[self.obj.get_type()]

    @SessionObject._with_access( write = True )
    def set_ordering( self, ordering: Group.Order ) -> None:

        if( self.obj.get_type() == model.ObjectType.CLASSIFIER_ORDERED
        and ordering != Group.Order.EXPLICIT ):

            self.clear_order()

        self.obj.set_type( {
                Group.Order.UNORDERED : model.ObjectType.CLASSIFIER_UNORDERED,
                Group.Order.EXPLICIT  : model.ObjectType.CLASSIFIER_ORDERED,
                Group.Order.NAME      : model.ObjectType.CLASSIFIER_NAME_ORDER,
                Group.Order.DATE      : model.ObjectType.CLASSIFIER_DATE_ORDER,
            }[ordering] )
