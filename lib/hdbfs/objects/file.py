from hdbfs.objects.basic import Obj, Stream
from hdbfs.session import Session, SessionObject

import hdbfs.model as model

from typing import List

class File( Obj ):

    def __init__( self, session: Session, obj: model.Object ):

        super().__init__( session, obj )

    def get_imports( self ) -> List['Import']:

        return self.get_parents( model.ObjectClass.IMPORT )

    def get_variants_of( self ) -> List['File']:

        if( self.obj.get_type() == model.ObjectType.FILE ):
            return self.get_parents( model.ObjectType.FILE )
        else:
            return []

    def get_variants( self ) -> List['File']:

        return self.get_children( model.ObjectType.FILE )

    def get_original_file( self ) -> 'File':

        if( self.obj.get_type() == model.ObjectType.DUPLICATE ):
            # Only one duplicate parent is permitted
            return self.get_parents( model.ObjectType.FILE )[0]
        else:
            return None

    def get_duplicates( self ) -> List['File']:

        return self.get_children( model.ObjectType.DUPLICATE )

    @SessionObject._with_access()
    def get_origin_names( self ) -> List[str]:

        from sqlalchemy import and_

        return [ log.origin_name for log in
            self.session.model.query( model.StreamLog.origin_name )
                .filter( and_( model.StreamLog.stream_id == self.obj.root_stream.stream_id,
                                model.StreamLog.origin_name != None ) )
                .distinct() ]

    def get_repr( self, group = None ) -> str:

        name = self.get_name( group )
        if( name is not None ):
            return name
        else:
            with self.session._access():
                obj_id = self.obj.object_id
                stream_id = self.obj.root_stream.stream_id
                priority = self.obj.root_stream.priority
                extension = self.obj.root_stream.extension

            if( extension == None ):
                return '%016x' % ( obj_id, )
            else:
                return '%016x.%s' % ( obj_id, extension, )

    def _get_stream( self, name ) -> Stream:

        s = self.obj.streams \
                .filter( model.Stream.name == name ) \
                .first()

        if( s is not None ):
            return self.session._construct_session_object( s )
        else:
            return None

    @SessionObject._with_access()
    def get_stream( self, name ) -> Stream:

        return self._get_stream( name )

    def _list_streams( self ) -> List[str]:

        return [ rs[0] for rs in
            self.session.model.query( model.Stream.name )
                .filter( model.Stream.object_id == self.obj.object_id )
                .order_by( model.Stream.stream_id ) ]

    @SessionObject._with_access()
    def list_streams( self ) -> List[str]:

        return self._list_streams()

    def _get_streams( self ) -> List[Stream]:

        return [ self.session._construct_session_object( s ) for s in
            self.session.model.query( model.Stream )
                .filter( model.Stream.object_id == self.obj.object_id )
                .order_by( model.Stream.stream_id ) ]

    @SessionObject._with_access()
    def get_streams( self ) -> List[Stream]:

        return self._get_streams()

    def _drop_streams( self ) -> None:

        for s in self._get_streams():
            s._drop_data()

            self.session.model.query( model.StreamMetadata ) \
                .filter( model.StreamMetadata.stream_id == s.stream.stream_id ) \
                .delete()

            self.session.model.query( model.StreamLog ) \
                .filter( model.StreamLog.stream_id == s.stream.stream_id ) \
                .delete()

        self.session.model.query( model.Stream ) \
            .filter( model.Stream.object_id == self.obj.object_id ) \
            .delete()

    def _drop_expendable_streams( self ) -> None:

        for s in self.session.model.query( model.Stream ) \
                     .filter( model.Stream.object_id == self.obj.object_id ) \
                     .filter( model.Stream.priority < model.StreamPriority.NORMAL.value ):

            stream = self.session._construct_session_object( s )
            stream._drop_data()

            self.session.model.query( model.StreamMetadata ) \
                .filter( model.StreamMetadata.stream_id == s.stream_id ) \
                .delete()

            self.session.model.query( model.StreamLog ) \
                .filter( model.StreamLog.stream_id == s.stream_id ) \
                .delete()

        self.session.model.query( model.Stream ) \
            .filter( model.Stream.object_id == self.obj.object_id ) \
            .filter( model.Stream.priority < model.StreamPriority.NORMAL.value ) \
            .delete()

    @SessionObject._with_access( write = True )
    def drop_expendable_streams( self ):

        self._drop_expendable_streams()

    @SessionObject._with_access()
    def get_root_stream( self ) -> Stream:

        return self.session._construct_session_object( self.obj.root_stream )

    @SessionObject._with_access()
    def verify( self ):

        for s in self._get_streams():
            s.verify()
