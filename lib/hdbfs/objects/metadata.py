from typing import Protocol

from hdbfs.objects.basic import Obj, Stream

class MetadataManager( Protocol ):

    def init_metadata( self, obj: Obj, stream: Stream ) -> None:
        ...

    def check_metadata( self, obj: Obj, stream: Stream ) -> None:
        ...

    def require_metadata_init( self, obj: Obj, stream: Stream ) -> None:
        ...