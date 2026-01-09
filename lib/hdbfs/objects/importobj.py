from hdbfs.session import Session, SessionObject
from hdbfs.objects.basic import Obj

import hdbfs.model as model

from typing import List

class Import( Obj ):

    def __init__( self, session: Session, obj: model.Object ):

        super().__init__( session, obj )

    @SessionObject._with_access( write = True )
    def close_import( self ) -> None:

        self.obj.set_type( model.ObjectType.IMPORT_CLOSED )

    def get_items( self, limit = None ) -> List[Obj]:

        return self.get_children( [
                    model.ObjectClass.FILE,
                ], limit )

    def get_files( self, limit = None ) -> List['File']:

        return self.get_children( model.ObjectClass.FILE, limit )
