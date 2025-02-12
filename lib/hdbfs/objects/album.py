import datetime

from hdbfs.session import Session, SessionObject
from hdbfs.objects.groups import OrderedGroup
from hdbfs.objects.metadata import MetadataManager

import hdbfs.model as model

class Album( OrderedGroup ):

    def __init__( self, session: Session, metaman: MetadataManager, obj: model.Object ):

        super().__init__( session, obj )
        self.metaman = metaman

    def _on_created( self, stream ):

        self.metaman.require_metadata_init( self, None )

    def _on_children_changed( self ):

        self.metaman.require_metadata_init( self, None )

    @SessionObject._with_access( write = True )
    def make_formal_album( self ):

        if( self.obj.get_type() == model.ObjectType.ALBUM_FREE ):
            # Ensure all children are formal
            for alb in self.get_albums():
                assert alb.obj.get_type() in [
                            model.ObjectType.ALBUM_FORMAL,
                            model.ObjectType.ALBUM_CLOSED
                        ]

            self.obj.set_type( model.ObjectType.ALBUM_FORMAL )

        elif( self.obj.get_type() in [
                    model.ObjectType.ALBUM_FORMAL,
                    model.ObjectType.ALBUM_CLOSED
                ] ):
            pass

        else:
            assert False

    @SessionObject._with_access( write = True )
    def make_free_album( self ):

        if( self.obj.get_type() == model.ObjectType.ALBUM_FREE ):
            pass

        if( self.obj.get_type() in [
                    model.ObjectType.ALBUM_FORMAL,
                    model.ObjectType.ALBUM_CLOSED
                ] ):

            # There can't be any duplicates in an unpublished album
            assert len( [f for f in self.get_files()
                    if f.obj.get_type() == model.ObjectType.DUPLICATE] ) == 0

            self.obj.set_type( model.ObjectType.ALBUM_FREE )

        else:
            assert False

    @SessionObject._with_access( write = True )
    def close_album( self ):

        if( self.obj.get_type() in [
                    model.ObjectType.ALBUM_FREE,
                    model.ObjectType.ALBUM_FORMAL
                ] ):

            # Ensure all children are closed
            for alb in self.get_albums():
                assert alb.obj.get_type() == model.ObjectType.ALBUM_CLOSED

            self.obj.set_type( model.ObjectType.ALBUM_CLOSED )

        elif( self.obj.get_type() == model.ObjectType.ALBUM_CLOSED ):
            pass

        else:
            assert False

    @SessionObject._with_access( write = True )
    def open_album( self ):

        if( self.obj.get_type() in [
                    model.ObjectType.ALBUM_FREE,
                    model.ObjectType.ALBUM_FORMAL
                ] ):
            pass

        elif( self.obj.get_type() == model.ObjectType.ALBUM_CLOSED ):
            self.obj.set_type( model.ObjectType.ALBUM_FORMAL )

        else:
            assert False

    def get_origin_time( self ):

        self.check_metadata()
        try:
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

        self.metaman.check_metadata( self, None )
