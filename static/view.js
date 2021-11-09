var TAGLINK_TEMPLATE = "<li><a class='taglink' href='##{tag}'>#{tag}</a></li>";

// module
var tabs = (function() {

// Local module vars
var tabs_counter = 1;

var login_tab = null;
var admin_tab = null;
var tagslist_tab = null;

var all_tabs = [];
var active_tab_id = null;
var tabs_listeners = [];

var info_set = [ 'object_id', 'type', 'repr', 'tags',
    'names', 'variants', 'variants_of',
    'dup_streams', 'albums', 'files', 'text', 'thumb_gen',
    'width', 'height', 'sizes', 'origin_time', 'creation_time' ];

/**
 * create_tab( title ) - creates a tab with the given title
 */
create_tab = function( title, type )
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
add_tab = function( tab )
{
    all_tabs.push( tab );
    active_tab_id = tab.id;

    tabs_listeners.forEach( function( it, idx, arr ) { it.on_tab_added( tab ); } )
};

/**
 * init() - Initialize the module
 */
var public_init = function()
{};

/**
 * all_tabs() - returns all tabs
 */
var public_all_tabs = function()
{
    return all_tabs;
};

var public_register_tabs_listener = function( listener )
{
    tabs_listeners.push( listener );
}

/**
 * active() - returns active tab
 */
var public_active = function()
{
    if( active_tab_id == null ) return null;
    return all_tabs.find( ( it ) => { return it.id == active_tab_id; } );
};

/**
 * on_event()
 */
var public_on_event = function( e )
{
    all_tabs.forEach( ( it ) => {
        if( it.onEvent ) {
            it.onEvent( e );
        }
    });
};

/**
 * on_select()
 */
var public_on_select = function()
{
    tab = tabs.active();
    obj = tab.data( 'obj' );
    if( obj && obj.display ) {
        obj.on_event( { type: 'focused' } );
    }
};

/**
 * select( tab ) - selects the given tab
 */
public_select = function( tab_id )
{
    if( active_tab_id == tab_id ) return;

    var tab = all_tabs.find( ( it ) => { return it.id == tab_id; } );
    if( tab ) {
        active_tab_id = tab_id;
        tabs_listeners.forEach( function( it, idx, arr ) { it.on_tab_selected( tab ); } )
    }
};

/**
 * create_display_tab( title, provider ) - creates a new display tab
 */
public_create_display_tab = function( title, provider )
{
    var dt = create_tab( title, 'display' );

    dt.provider = provider;
    dt.onClose = function() {
        this.provider.close();
        tabs.remove( this );
    }

    add_tab( dt );
}

/**
 * show_login_tab() - shows the login tab
 */
public_show_login_tab = function()
{
    if( login_tab != null ) {
        public_select( login_tab );
        return;
    }

    login_tab = create_tab( 'Login', 'login' );
    login_tab.onClose = () => {
        tabs.remove( login_tab );
        login_tab = null;
    }

    add_tab( login_tab );
}

/**
 * show_admin_tab() - shows the admin tab
 */
public_show_admin_tab = function()
{
    if( admin_tab != null ) {
        public_select( admin_tab );
        return;
    }

    admin_tab = create_tab( 'Admin', 'admin' );
    admin_tab.onClose = () => {
        tabs.remove( admin_tab );
        admin_tab = null;
    }

    add_tab( admin_tab );
}

/**
 * show_taglist_tab() - shows the taglist tab
 */
public_show_tagslist_tab = function()
{
    if( tagslist_tab != null ) {
        public_select( tagslist_tab );
        return;
    }

    tagslist_tab = create_tab( 'Taglist', 'taglist' );
    tagslist_tab.onClose = () => {
        tabs.remove( tagslist_tab );
        tagslist_tab = null;
    }

    add_tab( tagslist_tab );
}

/**
 * remove( elem ) - removes the given tab
 */
public_remove = function( tab )
{
    var idx = all_tabs.findIndex( function( it ) { return it === tab; } );
    if( idx >= 0 ) {
        if( active_tab_id == all_tabs[idx].id ) {
            if( idx == 0 ) {
                active_tab_id = null;
            } else {
                active_tab_id = all_tabs[idx-1].id;
            }
        }
        all_tabs.splice( idx, 1 );
        tabs_listeners.forEach( function( it, idx, arr ) { it.on_tab_removed( tab ); } )

    }
};

/**
 * class Provider
 */
var public_Provider = function() {};

    public_Provider.prototype.init = function() {}
    public_Provider.prototype.close = function() {}
    public_Provider.prototype.repr = 0;
    public_Provider.prototype.fetch = function( idx ) { return null; }
    public_Provider.prototype.offset = function( off ) { return null; }
    public_Provider.prototype.next = function() { return null; }
    public_Provider.prototype.prev = function() { return null; }

/**
 * class SelectionProvider
 */
public_SelectionProvider = function()

    // Constructor
    {
        this.selection = displib.make_selection_display();
        this.selection_id = displib.register_selection( this.selection.disp );

        this.index = null;
        this.count = 1;
    };

    // extends Provider
    public_SelectionProvider.prototype = new public_Provider();
    public_SelectionProvider.prototype.constructor = public_SelectionProvider;

    // Member functions
    public_SelectionProvider.prototype.init = function( obj, callback )
    {
        eval( 'obj.' + callback + '( this.selection )' );
    };

    public_SelectionProvider.prototype.close = function()
    {
        displib.unregister_selection( this.selection.disp );
    };

    public_SelectionProvider.prototype.repr = function()
    {
        return 'Single';
    };

    public_SelectionProvider.prototype.fetch = function( idx )
    {
        if( idx == 0 ) {
            return this.selection;
        } else {
            return null;
        }
    };

    public_SelectionProvider.prototype.offset = function( off )
    {
        return this.fetch( off );
    };

/**
 * class SingleProvider
 */
public_SingleProvider = function( obj_id )

    // Constructor
    {
        this.obj_id = obj_id;
        this.info = null;
        this.index = null;
        this.count = 1;
    };

    // extends Provider
    public_SingleProvider.prototype = new public_Provider();
    public_SingleProvider.prototype.constructor = public_SingleProvider;

    // Member functions
    public_SingleProvider.prototype.init = function( obj, callback )
    {
        var request = {
            action:     'stream_info',
            target:     this.obj_id,
            stream:     null,
            items:      info_set,
        };

        load_async( request, this, 'on_init_load', {
            obj: obj,
            callback: callback,
        });
    };

    public_SingleProvider.prototype.on_init_load = function( data, response )
    {
        this.info = response.info;
        display = displib.make_object_display( this.info );
        eval( 'data.obj.' + data.callback + '( display )' );
    };

    public_SingleProvider.prototype.repr = function()
    {
        return 'Single';
    };

    public_SingleProvider.prototype.fetch = function( idx )
    {
        if( idx == 0 ) {
            return displib.make_object_display( this.info );
        } else {
            return null;
        }
    };

    public_SingleProvider.prototype.offset = function( off )
    {
        return this.fetch( off );
    };

/**
 * class SearchProvider
 */
public_SearchProvider = function( query )

    // Constructor
    {
        this.query = query;
        this.sid = null;

        this.index = null;
        this.count = null;
    };

    // extends Provider
    public_SearchProvider.prototype = new public_Provider();
    public_SearchProvider.prototype.constructor = public_SearchProvider;

    public_SearchProvider.prototype.init = function( obj, callback )
    {
        if( this.sid ) {
            return this.fetch( this.index );
        }

        var request = {
            action: 'search',
            info: info_set,
         };

        if( this.query.mode ) {
            if( this.query.mode == 'album' ) {
                request.album = this.query.album;
            }

            request.mode = this.query.mode;
        } else {
            request.query = this.query.query;
        }

        if( this.query.index ) {
            request.index = this.query.index;
        }

        load_async( request, this, 'on_init_load', {
            obj: obj,
            callback: callback,
        });
    };

    public_SearchProvider.prototype.on_init_load = function( data, response )
    {
        if( response.result != 'ok' ) {
            this.sid = null;
            this.index = null;
            this.count = null;

            if( response.msg ) {
                display = displib.make_dummy_display(
                    'The search failed: ' + response.msg );
            } else {
                display = displib.make_dummy_display(
                    'The search failed: ' + response.except + ' error' );
            }
        } else if( response.results > 0 ) {
            this.sid = response.selection;
            this.index = response.index;
            this.count = response.results;

            display = displib.make_object_display( response.first );
        } else {
            this.sid = null;
            this.index = null;
            this.count = null;

            display = displib.make_dummy_display( 'The search had no results' );
        }
        eval( 'data.obj.' + data.callback + '( display )' );
    };

    public_SearchProvider.prototype.close = function()
    {
        if( !this.sid ) return null;
        
        var request = {
            'action' : 'selection_close',
            'selection' : this.sid,
        }
        load_sync( request );
    };

    public_SearchProvider.prototype.repr = function()
    {
        return this.query;
    };

    public_SearchProvider.prototype.fetch = function( idx )
    {
        if( !this.sid ) return null;

        var request = {
            action:     'selection_fetch',
            selection:  this.sid,
            index:      idx,
            info:       info_set,
        };
        response = load_sync( request );

        if( response == null || response.result != 'ok' ) {
            return null;
        }

        this.index = idx;
        display = displib.make_object_display( response );
        return display;
    };

    public_SearchProvider.prototype.offset = function( off )
    {
        return this.fetch( this.index + off );
    };

    public_SearchProvider.prototype.next = function()
    {
        return this.offset( 1 );
    };

    public_SearchProvider.prototype.prev = function()
    {
        return this.offset( -1 );
    };

/**
 * class ListProvider
 */
public_ListProvider = function( list )

    // Constructor
    {
        this.list = list;
        this.obj_id = null;

        this.index = null;
        this.count = list.length;
    };

    // extends Provider
    public_ListProvider.prototype = new public_Provider();
    public_ListProvider.prototype.constructor = public_ListProvider;

    public_ListProvider.prototype.init = function( obj, callback )
    {
        if( this.obj_id ) {
            this.index = this.list.findIndex( ( it ) =>
                                { return it[0] == this.obj_id; } );
        }

        if( !this.index || this.index < 0 || this.index >= this.list.length ) {
            this.index = 0;
        }

        this.obj_id = this.list[this.index][0];

        var request = {
            action:     'stream_info',
            target:     this.obj_id,
            stream:     null,
            items:      info_set,
        };

        load_async( request, this, 'on_init_load', {
            obj: obj,
            callback: callback,
        });
    };

    public_ListProvider.prototype.on_init_load = function( data, response )
    {
        display = displib.make_object_display( response.info );
        eval( 'data.obj.' + data.callback + '( display )' );
    };

    public_ListProvider.prototype.repr = function()
    {
        return 'List';
    };

    public_ListProvider.prototype.fetch = function( idx )
    {
        if( idx < 0 || idx >= this.list.length ) {
            return null;
        }

        this.index = idx;

        this.obj_id = this.list[this.index][0];

        var request = {
            action:     'stream_info',
            target:     this.obj_id,
            stream:     null,
            items:      info_set,
        };
        response = load_sync( request );

        return displib.make_object_display( response.info );
    };

    public_ListProvider.prototype.offset = function( off )
    {
        return this.fetch( this.index + off );
    };

    public_ListProvider.prototype.next = function()
    {
        return this.offset( 1 );
    };

    public_ListProvider.prototype.prev = function()
    {
        return this.offset( -1 );
    };

return {
    init: public_init,
    all_tabs: public_all_tabs,
    register_tabs_listener: public_register_tabs_listener,
    active: public_active,
    on_event: public_on_event,
    on_select: public_on_select,
    select: public_select,
    create_display_tab: public_create_display_tab,
    show_login_tab: public_show_login_tab,
    show_admin_tab: public_show_admin_tab,
    show_tagslist_tab: public_show_tagslist_tab,
    remove: public_remove,
    Provider: public_Provider,
    SelectionProvider: public_SelectionProvider,
    SingleProvider: public_SingleProvider,
    SearchProvider: public_SearchProvider,
    ListProvider: public_ListProvider,
};

})(); // module tabs
