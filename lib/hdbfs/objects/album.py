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
    def publish( self ):

        if( self.obj.object_type == model.TYPE_ALBUM ):
            # Ensure all children are published
            for alb in self.get_albums():
                assert alb.obj.object_type == model.TYPE_PUBLISHED

            self.obj.object_type = model.TYPE_PUBLISHED
        elif( self.obj.object_type == model.TYPE_PUBLISHED ):
            pass
        else:
            assert False

    @SessionObject._with_access( write = True )
    def unpublish( self ):

        if( self.obj.object_type == model.TYPE_ALBUM ):
            pass
        elif( self.obj.object_type == model.TYPE_PUBLISHED ):
            # There can't be any duplicates in an unpublished album
            assert len( [f for f in self.get_files()
                    if f.obj.object_type == model.TYPE_DUPLICATE] ) == 0
            self.obj.object_type = model.TYPE_ALBUM
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
