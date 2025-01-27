import sys

from hdbfs.defs import *
from hdbfs.hooks import *

_METADATA_INIT_REQUIRED = []

def _commit_hook( db, is_rollback ):
    global _METADATA_INIT_REQUIRED

    # This hook can cause a write, which will trigger this hook again.
    # Make sure to clear the list before triggering a commit
    flist = _METADATA_INIT_REQUIRED
    _METADATA_INIT_REQUIRED = []

    if( not is_rollback ):
        for obj, stream in flist:
            try:
                db.tbcache.init_metadata( obj, stream )
            except:
                LOG.warning( 'Failed loading metadata for "%s": %s',
                             obj.get_repr(), str( sys.exc_info()[1] ) )

def require_metadata_init( obj, stream ):

    global _METADATA_INIT_REQUIRED
    _METADATA_INIT_REQUIRED.append( ( obj, stream ) )

def add_hook():

    add_pre_commit_hook( _commit_hook )
