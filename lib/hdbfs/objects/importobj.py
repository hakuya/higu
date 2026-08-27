from hdbfs.session import Session, SessionObject
from hdbfs.objects.basic import Obj

import hdbfs.model as model

from typing import List, Optional

class Import( Obj ):
    """ Represents a batch import operation.

    Import objects track files added to the database during a single import
    session. They support two states:

    - OPEN: Import is in progress, files can be added
    - CLOSED: Import is complete, no more files can be added

    Imports maintain ordered relationships with their files, preserving
    the sequence in which files were imported.

    Attributes:
        obj: The underlying model.Object database record
    """

    def __init__( self, session: Session, obj: model.Object ):

        super().__init__( session, obj )

    @SessionObject._with_access( write = True )
    def open_import( self ) -> None:
        """ Reopen a closed import to allow adding more files.

        Changes the import state from CLOSED to OPEN, allowing additional
        files to be added to this import batch.
        """

        self.obj.set_type( model.ObjectType.IMPORT_OPEN )

    @SessionObject._with_access( write = True )
    def close_import( self ) -> None:
        """ Close the import to prevent further modifications.

        Changes the import state from OPEN to CLOSED, finalizing the
        import batch. No more files can be added after closing.
        """

        self.obj.set_type( model.ObjectType.IMPORT_CLOSED )

    def get_items( self, limit: Optional[int] = None ) -> List[Obj]:
        """ Get all items (files) in this import.

        Args:
            limit: Maximum number of items to return

        Returns:
            List of File objects in import order
        """

        return self.get_children( [
                    model.ObjectClass.FILE,
                ], limit )

    def get_files( self, limit: Optional[int] = None ) -> List['File']:
        """ Get all files in this import.

        Args:
            limit: Maximum number of files to return

        Returns:
            List of File objects in import order
        """

        return self.get_children( model.ObjectClass.FILE, limit )
