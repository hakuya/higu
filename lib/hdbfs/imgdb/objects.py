import datetime

from hdbfs.session import Session, SessionObject

from hdbfs.objects.basic import Stream
from hdbfs.objects.file import File

from hdbfs.imgdb.defs import *
from hdbfs.imgdb.info import StreamInfo, ImageInfo

import hdbfs.model as model
from hdbfs.model import ImageRequestPriority

from enum import Enum
from typing import Optional

class ThumbRequestPrio( Enum ):
    OPTIONAL = "optional"
    MARK_REQUESTED = "mark"
    IMMEDIATE = "immediate"

class ImageStream( Stream ):

    def __init__( self, session: Session, stream: model.Stream ):

        super().__init__( session, stream )

    def get_exif( self ):

        with StreamInfo( self.session, self ) as sinfo:
            return sinfo.get_exif()

    def get_dimensions( self ):

        with StreamInfo( self.session, self ) as sinfo:
            return sinfo.get_dims()

    def get_origin_time( self ):

        with StreamInfo( self.session, self ) as sinfo:
            origin_ts = sinfo.get_origin_time()
            if( origin_ts is None ):
                return None

            return datetime.datetime\
                    .utcfromtimestamp( origin_ts )

    def check_metadata( self ):

        try:
            ver = self['.metaver']
            if( ver == METADATA_VERSION ):
                return
        except:
            pass

        self.session.tbcache.init_stream_metadata( self )

class ImageFile( File ):

    def __init__( self, session: Session, tbcache: 'ThumbCache', obj: model.Object ):

        super().__init__( session, obj )
        self.tbcache = tbcache

    def _on_created( self, stream ):

        self.tbcache.require_metadata_init( self, stream )

    @SessionObject._with_access()
    def get_exif( self ):

        return self.get_root_stream().get_exif()

    def get_dimensions( self ):

        return self.tbcache.get_dimensions( self )

    def get_origin_time( self ):

        return self.tbcache.get_origin_time( self )

    def set_text( self, text ):

        self['text'] = text

    def get_text( self ):

        try:
            return self['text']
        except KeyError:
            return None

    def __drop_info( self ):

        self.obj.info = None

    def rotate_cw( self ):

        CW_REMAP = [ 6, 5, 8, 7, 4, 3, 2, 1 ]
        self.tbcache.reorient_image( self, remap = CW_REMAP )

    def rotate_ccw( self ):

        CCW_REMAP = [ 8, 7, 6, 5, 2, 1, 4, 3 ]
        self.tbcache.reorient_image( self, remap = CCW_REMAP )

    def mirror( self ):

        MIRROR_REMAP = [ 2, 1, 4, 3, 8, 7, 6, 5 ]
        self.tbcache.reorient_image( self, remap = MIRROR_REMAP )

    def auto_orientation( self ):

        self.tbcache.reorient_image( self )

    def get_orientation( self ):

        return self.tbcache.get_orientation( self )

    def get_generation( self ):

        return self.tbcache.get_generation( self )

    def get_thumb_stream( self,
                exp: int,
                request: ThumbRequestPrio = ThumbRequestPrio.OPTIONAL
            ) -> Optional[ImageStream]:

        if( self.obj.object_type == model.TYPE_FILE ):
            return self.tbcache.get_thumb( self, exp, request )
        else:
            return self.get_root_stream()

    def get_thumb_sizes( self ):

        if( self.obj.object_type == model.TYPE_FILE ):
            return self.tbcache.get_thumb_sizes( self )
        else:
            w, h = self.get_dimensions()
            return [ ( None, w, h, True ), ]

    def get_avail_exp_mask( self ) -> Optional[int]:

        if( self.obj.object_type == model.TYPE_FILE ):
            return self.tbcache.get_avail_exp_mask( self )
        else:
            return None

    def request_thumbs( self, prio: ImageRequestPriority = ImageRequestPriority.BACKGROUND ) -> Optional[int]:
        '''Checks if all appropriate thumbs have been created. If they haven't
        then marks the thumbs as requested in the database.
        '''

        if( self.obj.object_type != model.TYPE_FILE ):
            return None

        return self.tbcache.request_thumbs( self, prio )

    def check_metadata( self ):

        try:
            ver = self['.metaver']
            if( ver == METADATA_VERSION ):
                return
        except:
            pass

        self.tbcache.init_object_metadata( self )

    def assign( self, parent,
                order = None,
                name = None,
                is_duplicate = None,
                force = None ):

        File.assign( self, parent, order, name, is_duplicate, force )
        if( self.obj.object_type == model.TYPE_DUPLICATE ):
            self.tbcache.purge_thumbs( self )

    def __getitem__( self, key ):

        if( key == 'width' ):
            return self.get_dimensions()[0]
        elif( key == 'height' ):
            return self.get_dimensions()[1]
        else:
            return super().__getitem__( key )

    def __setitem__( self, key, value ):

        assert key not in [ 'width', 'height' ]
        return super().__setitem__( key, value )

class _ObjectFactory:

    def __init__( self, session: Session, tbcache: 'ThumbCache' ):

        self.session = session
        self.tbcache = tbcache

    def __call__( self, session: Session, model_obj: any ):

        assert session == self.session

        if( isinstance( model_obj, model.Stream ) ):
            #TODO pick only image mime types?
            return ImageStream( session, model_obj )

        elif( isinstance( model_obj, model.Object ) ):

            if( model_obj.object_type == model.TYPE_FILE
            or model_obj.object_type == model.TYPE_DUPLICATE ):
                return ImageFile( session, self.tbcache, model_obj )

        return None

def add_factories( session: Session, tbcache: 'ThumbCache' ):

    session._add_session_object_factory( _ObjectFactory( session, tbcache ) )
