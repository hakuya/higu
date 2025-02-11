import hdbfs.model as model

from hdbfs.session import Session

from hdbfs.objects.basic import Stream
from hdbfs.objects.file import File
from hdbfs.objects.album import Album
from hdbfs.objects.groups import Tag
from hdbfs.objects.metadata import MetadataManager

class BasicFactory:

    def __init__( self, session: Session, metaman: MetadataManager ):

        self.session = session
        self.metaman = metaman

    def __call__( self, session: Session, model_obj: any ):

        assert session == self.session

        if( isinstance( model_obj, model.Stream ) ):
            return Stream( session, model_obj )

        elif( isinstance( model_obj, model.Object ) ):
            obj = model_obj

            if( obj.object_type == model.TYPE_FILE
            or obj.object_type == model.TYPE_DUPLICATE ):
                return File( session, obj )
            elif( obj.object_type == model.TYPE_ALBUM
            or obj.object_type == model.TYPE_PUBLISHED ):
                return Album( session, self.metaman, obj )
            elif( obj.object_type == model.TYPE_CLASSIFIER ):
                return Tag( session, obj )
            else:
                return None

def init_basic_factories( session: Session, metaman: MetadataManager ):

    session._add_session_object_factory( BasicFactory( session, metaman ) )
