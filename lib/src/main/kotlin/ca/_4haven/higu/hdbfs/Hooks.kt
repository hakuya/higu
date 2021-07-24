package ca._4haven.higu.hdbfs

typealias Hook = ( db: Database, is_rollback: Boolean ) -> Unit

class Hooks( val db: Database ) {

    private var _PRE_COMMIT_HOOKS = mutableListOf<Hook>()
    private var _POST_COMMIT_HOOKS = mutableListOf<Hook>()

    fun add_pre_commit_hook( h: Hook ) {
        this._PRE_COMMIT_HOOKS.add( h )
    }

    fun add_post_commit_hook( h: Hook ) {
        _POST_COMMIT_HOOKS.add( h )
    }

    fun trigger_pre_commit_hooks( is_rollback: Boolean ) {
        _PRE_COMMIT_HOOKS.forEach { h ->
            try {
                h( db, is_rollback )
            } catch( ex: Exception ) {
                Log.warning( "Pre commit hook \"${h}\" failed: ${ex}" )
            }
        }
    }

    fun trigger_post_commit_hooks( is_rollback: Boolean ) {
        _POST_COMMIT_HOOKS.forEach { h ->
            try {
                h( db, is_rollback )
            } catch( ex: Exception ) {
                Log.warning( "Post commit hook \"${h}\" failed: ${ex}" )
            }
        }
    }
}