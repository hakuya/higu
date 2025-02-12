import logging
import os

import hdbfs.model as model

VERSION = 1
REVISION = 0

DB_VERSION  = model.VERSION
DB_REVISION = model.REVISION

DEFAULT_LIBRARY = os.path.join( os.environ['HOME'], '.higu' )
HIGURASHI_DB_NAME = 'hfdb.dat'

from hdbfs.model import ObjectClass, ObjectType

NAME_POLICY_DONT_REGISTER   = 0
NAME_POLICY_DONT_SET        = 1
NAME_POLICY_SET_IF_UNDEF    = 2
NAME_POLICY_SET_ALWAYS      = 3

LOG = logging.getLogger( __name__ )
