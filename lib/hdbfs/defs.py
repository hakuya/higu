import logging
import os

import hdbfs.model as model

VERSION = 1
REVISION = 0

DB_VERSION  = model.VERSION
DB_REVISION = model.REVISION

DEFAULT_LIBRARY = os.path.join( os.environ['HOME'], '.higu' )
HIGURASHI_DB_NAME = 'hfdb.dat'

TYPE_FILE       = model.TYPE_FILE
TYPE_DUPLICATE  = model.TYPE_DUPLICATE
TYPE_GROUP      = model.TYPE_GROUP
TYPE_ALBUM      = model.TYPE_ALBUM
TYPE_PUBLISHED  = model.TYPE_PUBLISHED
TYPE_CLASSIFIER = model.TYPE_CLASSIFIER

FILE_TYPES      = model.FILE_TYPES
ALBUM_TYPES     = model.ALBUM_TYPES

NAME_POLICY_DONT_REGISTER   = 0
NAME_POLICY_DONT_SET        = 1
NAME_POLICY_SET_IF_UNDEF    = 2
NAME_POLICY_SET_ALWAYS      = 3

LOG = logging.getLogger( __name__ )
