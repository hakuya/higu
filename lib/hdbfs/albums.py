from hdbfs.session import \
        Session, \
        SessionObject

from hdbfs.objects.album import Album
from hdbfs.objects.importobj import Import
from hdbfs.objects.file import File

import hdbfs.model as model

from hdbfs.model import ObjectType

from typing import List

class Albums_interface( SessionObject ):
    """ Interface for managing models in the database. """

    def __init__( self, session: Session ):

        self.session = session

    @SessionObject._with_access( write = True )
    def create( self,
                tags = [],
                name = None,
                text = None
            ) -> Album:
        """ Creates an album.

        Arguments:
        tags -- a set of tags to assign the album to
        name -- a string name for the album
        text -- textual description of the album
        """

        model_album = model.Object( model.ObjectType.ALBUM_FREE )
        self.session.model.add( model_album )

        album = self.session._construct_session_object( model_album )
        assert isinstance( album, Album )

        if( name is not None ):
            album.obj.name = name

        if( text is not None ):
            album.obj['text'] = text

        for t in tags:
            album.assign( t, None )

        return album

    @SessionObject._with_access( write = True )
    def create_from_files( self,
                from_files : List[File],
                tags = [],
                name = None,
                text = None,
                alb_type : ObjectType = ObjectType.ALBUM_FREE
            ) -> Album:
        """ Creates a closed album from a set of files.

        Arguments:
        from_files -- a list of files to include
        tags -- a set of tags to assign the album to
        name -- a string name for the album
        text -- textual description of the album
        """

        assert alb_type in [
                ObjectType.ALBUM_FREE,
                ObjectType.ALBUM_FORMAL,
                ObjectType.ALBUM_CLOSED
            ]

        album = self.create( tags, name, text )

        if( alb_type in [ ObjectType.ALBUM_FORMAL, ObjectType.ALBUM_CLOSED ] ):
            album.make_formal_album()
        for it, f in enumerate( from_files ):
            f.assign( album, it, f.get_name() )
        if( alb_type == ObjectType.ALBUM_CLOSED ):
            album.close_album()

        return album

    @SessionObject._with_access( write = True )
    def create_from_import( self,
                from_import : Import,
                tags = [],
                name = None,
                text = None,
            ) -> Album:
        """ Creates an album from an import.

        Arguments:
        tags -- a set of tags to assign the album to
        name -- a string name for the album
        text -- textual description of the album
        """

        if( name is None ):
            name = from_import.get_name()
        if( text is None ):
            text = from_import['text']

        album = self.create( tags, name, text )

        album.make_formal_album()
        for it, f in enumerate( from_import.get_files() ):
            f.assign( album, it, f.get_name( from_import, it ) )
        album.close_album()

        return album

    @SessionObject._with_access( write = True )
    def partition( self,
                album : Album,
                files : List[File]
            ) -> Album:

        album_files = album.get_files()
        album_type = album.get_type()
        order = None

        assert album_type != ObjectType.ALBUM_CLOSED

        # All the files in the partition must be in the album
        for f in files:
            assert f in album_files

            f_order = f.get_order( album )
            if( order is None
                or (f_order is not None and f_order < order) ):

                order = f_order

        part = self.create()

        if( album_type == ObjectType.ALBUM_FORMAL ):
            part.make_formal_album()

        # Assign to the partition, preserving the local name
        for it, f in enumerate( files ):
            f.assign( part, it, f.get_name( album, it ) )
        
        # Now remove the files from the album
        for f in files:
            f.unassign( album )

        # And add the partition in
        part.assign( album, order = order )

        return part

