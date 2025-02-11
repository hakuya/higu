import sys


from hdbfs.defs import *
from hdbfs.session import Session

from hdbfs.imgdb.dataconfig import *
from hdbfs.imgdb.defs import *

from hdbfs.imgdb.objects import \
    ImageStream, \
    ImageFile

from hdbfs.imgdb.cache import ThumbCache

def init_module():

    from PIL import ImageFile
    ImageFile.LOAD_TRUNCATED_IMAGES = True

def init_session( session: Session, tbcache: ThumbCache ):

    from hdbfs.imgdb.objects import add_factories
    add_factories( session, tbcache )
