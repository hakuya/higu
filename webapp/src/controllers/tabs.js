// Local module vars
var tabs_counter = 1;

var login_tab = null;
var admin_tab = null;
var tagslist_tab = null;

var tabs = [];
var active_tab_id = null;
var tabs_listeners = [];

/**
 * create_tab( title ) - creates a tab with the given title
 */
var create_tab = function( title, type )
{
    var count = tabs_counter;
    var id_val = 'tabs-' + count;

    var tab = {
        title: title,
        type: type,
        id: id_val
    };

    tabs_counter++;

    return tab;
};

/**
 * add_tab( tab ) - adds the given tab
 */
var add_tab = function( tab )
{
    tabs.push( tab );
    active_tab_id = tab.id;

    tabs_listeners.forEach( function( it, idx, arr ) { it.on_tab_added( tab ); } )
};

function notify_tab_selected( tab )
{
    tabs_listeners.forEach( function( it, idx, arr ) { it.on_tab_selected( tab ); } )
    if( tab != null && tab.onEvent ) {
        tab.onEvent( { type: 'tab_focus' } );
    }
}

/**
 * init() - Initialize the module
 */
export function init()
{}

/**
 * all_tabs() - returns all tabs
 */
export function all_tabs()
{
    return tabs;
};

export function register_tabs_listener( listener )
{
    tabs_listeners.push( listener );
}

export function notify_tab_changed( tab )
{
    tabs_listeners.forEach( function( it, idx, arr ) { it.on_tab_changed( tab ); } )
}

/**
 * active() - returns active tab
 */
export function active()
{
    if( active_tab_id == null ) return null;
    return tabs.find( ( it ) => { return it.id == active_tab_id; } );
};

/**
 * on_event()
 */
export function on_event( e )
{
    tabs.forEach( ( it ) => {
        if( it.onEvent ) {
            it.onEvent( e );
        }
    });
    tabs_listeners.forEach( function( it, idx, arr ) { it.on_tab_event( e ); } )
};

/**
 * select( tab ) - selects the given tab
 */
export function select( tab_id )
{
    if( active_tab_id == tab_id ) return;

    var tab = tabs.find( ( it ) => { return it.id == tab_id; } );
    if( tab ) {
        active_tab_id = tab_id;
        notify_tab_selected( tab );
    }
};

/**
 * create_display_tab( title, provider ) - creates a new display tab
 */
export function create_display_tab( title, provider )
{
    var dt = create_tab( title, 'display' );

    dt.provider = provider;
    dt.onClose = function() {
        this.provider.close();
        remove( this );
    }

    add_tab( dt );
}

/**
 * show_login_tab() - shows the login tab
 */
export function show_login_tab()
{
    if( login_tab != null ) {
        select( login_tab );
        return;
    }

    login_tab = create_tab( 'Login', 'login' );
    login_tab.onClose = () => {
        remove( login_tab );
        login_tab = null;
    }

    add_tab( login_tab );
}

/**
 * show_admin_tab() - shows the admin tab
 */
export function show_admin_tab()
{
    if( admin_tab != null ) {
        select( admin_tab );
        return;
    }

    admin_tab = create_tab( 'Admin', 'admin' );
    admin_tab.onClose = () => {
        remove( admin_tab );
        admin_tab = null;
    }

    add_tab( admin_tab );
}

/**
 * show_taglist_tab() - shows the taglist tab
 */
export function show_tagslist_tab()
{
    if( tagslist_tab != null ) {
        select( tagslist_tab );
        return;
    }

    tagslist_tab = create_tab( 'Taglist', 'taglist' );
    tagslist_tab.onClose = () => {
        remove( tagslist_tab );
        tagslist_tab = null;
    }

    add_tab( tagslist_tab );
}

/**
 * Removes the given tab
 */
export function remove( tab )
{
    var idx = tabs.findIndex( function( it ) { return it === tab; } );
    if( idx < 0 ) return;

    if( active_tab_id == tabs[idx].id ) {
        // If the removed tab is selected, we need to select a new tab
        var new_tab = (idx > 0 ? tabs[idx-1] : null);
        active_tab_id = (new_tab != null ? new_tab.id : null);
        notify_tab_selected( new_tab );
    }

    tabs.splice( idx, 1 );
    tabs_listeners.forEach( function( it, idx, arr ) { it.on_tab_removed( tab ); } )
};
