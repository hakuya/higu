import sys

from defs import *

_PRE_COMMIT_HOOKS = []
_POST_COMMIT_HOOKS = []

def add_pre_commit_hook( h ):
    global _PRE_COMMIT_HOOKS
    _PRE_COMMIT_HOOKS.append( h )

def add_post_commit_hook( h ):
    global _POST_COMMIT_HOOKS
    _POST_COMMIT_HOOKS.append( h )

def trigger_pre_commit_hooks( db, is_rollback ):
    global _PRE_COMMIT_HOOKS

    for h in _PRE_COMMIT_HOOKS:
        try:
            h( db, is_rollback )
        except:
            LOG.warning( 'Pre commit hook "%s" failed: %s',
                         str( h ), str( sys.exc_info()[1] ) )

def trigger_post_commit_hooks( db, is_rollback ):
    global _POST_COMMIT_HOOKS

    for h in _POST_COMMIT_HOOKS:
        try:
            h( db, is_rollback )
        except:
            LOG.warning( 'Post commit hook "%s" failed: %s',
                         str( h ), str( sys.exc_info()[1] ) )
