import os
import sys

import hdbfs.model as model

from hdbfs.defs import *

from hdbfs.imgdb.defs import *

from hdbfs.imgdb.objects import \
    ImageStream, \
    ImageFile, \
    Album

from hdbfs.imgdb.cache import ThumbCache

class ImageDbDataConfig:

    def __init__( self, imgdb_path ):

        self.imgdb_path = imgdb_path

    def get_file_vol_path( self, vol_id, priority ):

        if( priority > model.SP_EXPENDABLE ):
            path = os.path.join( self.imgdb_path, IMGDB_DATA_PATH )
        else:
            path = os.path.join( self.imgdb_path, IMGDB_THUMB_PATH )

        lv2 = vol_id & 0xfff
        lv3 = (vol_id >> 12) & 0xfff
        lv4 = (vol_id >> 24) & 0xfff

        assert lv4 == 0

        path = os.path.join( path, '%03x' % ( lv3 ),
                                   '%03x' % ( lv2 ) )

        return path

def init_module():

    from PIL import ImageFile
    ImageFile.LOAD_TRUNCATED_IMAGES = True

    from hdbfs.imgdb.objects import add_factories
    from hdbfs.imgdb.metadata_init import add_hook

    add_factories()
    add_hook()
