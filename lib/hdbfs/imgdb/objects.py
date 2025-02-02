import datetime

from hdbfs.basic_objs import *
from hdbfs.obj_factory import add_obj_factory

from hdbfs.imgdb.defs import *
from hdbfs.imgdb.info import StreamInfo, ImageInfo
from hdbfs.imgdb.metadata_init import require_metadata_init

from hdbfs.model import ImageRequestPriority

from enum import Enum
from typing import Optional

class ThumbRequestPrio( Enum ):
    OPTIONAL = "optional"
    MARK_REQUESTED = "mark"
    IMMEDIATE = "immediate"

class ImageStream( Stream ):

    def __init__( self, db, stream ):

        Stream.__init__( self, db, stream )

    def get_exif( self ):

        with StreamInfo( self.db, self ) as sinfo:
            return sinfo.get_exif()

    def get_dimensions( self ):

        with StreamInfo( self.db, self ) as sinfo:
            return sinfo.get_dims()

    def get_origin_time( self ):

        with StreamInfo( self.db, self ) as sinfo:
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

        self.db.tbcache.init_stream_metadata( self )

class ImageFile( File ):

    def __init__( self, db: 'hdbfs.Database', obj: model.Object ):

        File.__init__( self, db, obj )

    def _on_created( self, stream ):

        require_metadata_init( self, stream )

    def get_exif( self ):

        with self.db._access():
            return self.get_root_stream().get_exif()

    def get_dimensions( self ):

        return self.db.tbcache.get_dimensions( self )

    def get_origin_time( self ):

        return self.db.tbcache.get_origin_time( self )

    def set_text( self, text ):

        self['text'] = text

    def get_text( self ):

        try:
            return self['text']
        except KeyError:
            return None

    def __drop_info( self ):

        this.obj.info = None

    def rotate_cw( self ):

        CW_REMAP = [ 6, 5, 8, 7, 4, 3, 2, 1 ]
        self.db.tbcache.reorient_image( self, remap = CW_REMAP )

    def rotate_ccw( self ):

        CCW_REMAP = [ 8, 7, 6, 5, 2, 1, 4, 3 ]
        self.db.tbcache.reorient_image( self, remap = CCW_REMAP )

    def mirror( self ):

        MIRROR_REMAP = [ 2, 1, 4, 3, 8, 7, 6, 5 ]
        self.db.tbcache.reorient_image( self, remap = MIRROR_REMAP )

    def auto_orientation( self ):

        self.db.tbcache.reorient_image( self )

    def get_orientation( self ):

        return self.db.tbcache.get_orientation( self )

    def get_generation( self ):

        return self.db.tbcache.get_generation( self )

    def get_thumb_stream( self,
                exp: int,
                request: ThumbRequestPrio = ThumbRequestPrio.OPTIONAL
            ) -> Optional[ImageStream]:

        if( self.obj.object_type == model.TYPE_FILE ):
            return self.db.tbcache.get_thumb( self, exp, request )
        else:
            return self.get_root_stream()

    def get_thumb_sizes( self ):

        if( self.obj.object_type == model.TYPE_FILE ):
            return self.db.tbcache.get_thumb_sizes( self )
        else:
            w, h = self.get_dimensions()
            return [ ( None, w, h, True ), ]

    def get_avail_exp_mask( self ) -> Optional[int]:

        if( self.obj.object_type == model.TYPE_FILE ):
            return self.db.tbcache.get_avail_exp_mask( self )
        else:
            return None

    def request_thumbs( self, prio: ImageRequestPriority = ImageRequestPriority.BACKGROUND ) -> Optional[int]:
        '''Checks if all appropriate thumbs have been created. If they haven't
        then marks the thumbs as requested in the database.
        '''

        if( self.obj.object_type != model.TYPE_FILE ):
            return None

        return self.db.tbcache.request_thumbs( self, prio )

    def check_metadata( self ):

        try:
            ver = self['.metaver']
            if( ver == METADATA_VERSION ):
                return
        except:
            pass

        self.db.tbcache.init_object_metadata( self )

    def assign( self, parent,
                order = None,
                name = None,
                is_duplicate = None,
                force = None ):

        File.assign( self, parent, order, name, is_duplicate, force )
        if( self.obj.object_type == model.TYPE_DUPLICATE ):
            self.db.tbcache.purge_thumbs( self )

    def __getitem__( self, key ):

        if( key == 'width' ):
            return self.get_dimensions()[0]
        elif( key == 'height' ):
            return self.get_dimensions()[1]
        else:
            return Obj.__getitem__( self, key )

    def __setitem__( self, key, value ):

        assert key not in [ 'width', 'height' ]
        return Obj.__setitem__( self, key, value )

class Album( OrderedGroup ):

    def __init__( self, db, obj ):

        OrderedGroup.__init__( self, db, obj )

    def _on_created( self, stream ):

        require_metadata_init( self, None )

    def _on_children_changed( self ):

        require_metadata_init( self, None )

    def publish( self ):

        with self.db._access( write = True ):
            if( self.obj.object_type == model.TYPE_ALBUM ):
                # Ensure all children are published
                for alb in self.get_albums():
                    assert alb.obj.object_type == model.TYPE_PUBLISHED

                self.obj.object_type = model.TYPE_PUBLISHED
            elif( self.obj.object_type == model.TYPE_PUBLISHED ):
                pass
            else:
                assert False

    def unpublish( self ):

        with self.db._access( write = True ):
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

        try:
            ver = self['.metaver']
            if( ver == METADATA_VERSION ):
                return
        except:
            pass

        self.db.tbcache.init_album_metadata( self )

def _img_stream_factory( db, stream ):

    #TODO pick only image mime types?
    return ImageStream( db, stream )

def _img_obj_factory( db, obj ):

    if( obj.object_type == model.TYPE_FILE
     or obj.object_type == model.TYPE_DUPLICATE ):
        return ImageFile( db, obj )
    elif( obj.object_type == model.TYPE_ALBUM
       or obj.object_type == model.TYPE_PUBLISHED ):
        return Album( db, obj )
    else:
        return None

def add_factories():

    add_stream_factory( _img_stream_factory )
    add_obj_factory( _img_obj_factory )
