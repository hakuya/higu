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
    'names', 'variants', 'variants_of', 'original_file',
    'duplicates', 'albums', 'files', 'text', 'thumb_gen',
    'width', 'height', 'sizes', 'origin_time', 'creation_time',
    'exif' ];
var field_set = [ 'rating' ];

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
    all_tabs.push( tab );
    active_tab_id = tab.id;

    tabs_listeners.forEach( function( it, idx, arr ) { it.on_tab_added( tab ); } )
};

/**
 * init() - Initialize the module
 */
var public_init = function()
{};

var public_get_info_set = function()
{
    return info_set;
}

var public_get_field_set = function()
{
    return field_set;
}

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
var public_select = function( tab_id )
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
var public_create_display_tab = function( title, provider )
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
var public_show_login_tab = function()
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
var public_show_admin_tab = function()
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
var public_show_tagslist_tab = function()
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
var public_remove = function( tab )
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
class public_Provider
{
    init()
    {}

    close()
    {}

    repr()
    { return null; }

    fetch( idx )
    { return null; }

    offset( off )
    { return null; }

    next()
    { return null; }

    prev()
    { return null; }
}

/**
 * class SelectionProvider
 */
class public_SelectionProvider extends public_Provider
{
    constructor()
    {
        super();

        this.selection = window.displib.make_selection_display();
        this.selection_id = window.displib.register_selection( this.selection.disp );
        this.init_query = null;
        this.init_objs = null;

        this.index = null;
        this.count = 1;
    }

    init( obj, callback )
    {
        if( this.init_query != null ) {
            var request = {
                action: 'search',
                info: [ 'object_id', 'repr', 'type' ],
                fields: [],
                query: this.init_query,
                count: 1000,
                oneshot: true,
            };

            load_async( request, this, 'on_init_load', {
                obj: obj,
                callback: callback,
            });
        } else {
            if( this.init_objs != null ) {
                this.selection.disp.objs = this.init_objs;
            }
            eval( 'obj.' + callback + '( this.selection )' );
        }
    }

    on_init_load( data, response )
    {
        if( response.result == 'ok' && response.results > 0 ) {
            this.selection.disp.objs = response.items.map( ( it ) => {
                                            return [ it.object_id, it.repr, it.type ];
                                        } );
        }
        eval( 'data.obj.' + data.callback + '( this.selection )' );
    }

    close()
    {
        window.displib.unregister_selection( this.selection.disp );
    }

    repr()
    {
        return 'Single';
    }

    fetch( idx )
    {
        if( idx == 0 ) {
            return this.selection;
        } else {
            return null;
        }
    }

    offset( off )
    {
        return this.fetch( off );
    }
}

/**
 * class SingleProvider
 */
class public_SingleProvider extends public_Provider
{
    constructor( obj_id )
    {
        super();

        this.obj_id = obj_id;
        this.info = null;
        this.index = null;
        this.count = 1;
    }

    init( obj, callback )
    {
        var request = {
            action:     'info',
            target:     this.obj_id,
            items:      info_set,
            fields:     field_set,
        };

        load_async( request, this, 'on_init_load', {
            obj: obj,
            callback: callback,
        });
    }

    on_init_load( data, response )
    {
        this.info = response.info;
        this.fields = response.fields;

        var display = window.displib.make_object_display( this.info, this.fields );
        eval( 'data.obj.' + data.callback + '( display )' );
    }

    repr()
    {
        return 'Single';
    }

    fetch( idx )
    {
        if( idx == 0 ) {
            return window.displib.make_object_display( this.info, this.fields );
        } else {
            return null;
        }
    }

    offset( off )
    {
        return this.fetch( off );
    }
}

/**
 * class SearchProvider
 */
class public_SearchProvider extends public_Provider
{
    constructor( query )
    {
        super();

        this.query = query;
        this.sid = null;

        this.index = null;
        this.count = null;
    }

    init( obj, callback )
    {
        if( this.sid ) {
            return this.fetch( this.index );
        }

        var request = {
            action: 'search',
            info: info_set,
            fields: field_set,
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
    }

    on_init_load( data, response )
    {
        var display = null;

        if( response.result != 'ok' ) {
            this.sid = null;
            this.index = null;
            this.count = null;

            if( response.msg ) {
                display = window.displib.make_dummy_display(
                    'The search failed: ' + response.msg );
            } else {
                display = window.displib.make_dummy_display(
                    'The search failed: ' + response.except + ' error' );
            }
        } else if( response.results > 0 ) {
            this.sid = response.selection;
            this.index = response.index;
            this.count = response.results;

            display = window.displib.make_object_display( response.first, response.fields );
        } else {
            this.sid = null;
            this.index = null;
            this.count = null;

            display = window.displib.make_dummy_display( 'The search had no results' );
        }

        eval( 'data.obj.' + data.callback + '( display )' );
    }

    close()
    {
        if( !this.sid ) return null;
        
        var request = {
            'action' : 'selection_close',
            'selection' : this.sid,
        }
        load_sync( request );
    }

    repr()
    {
        return this.query;
    }

    fetch( idx )
    {
        if( !this.sid ) return null;

        var request = {
            action:     'selection_fetch',
            selection:  this.sid,
            index:      idx,
            info:       info_set,
            fields:     field_set,
        };
        var response = load_sync( request );

        if( response == null || response.result != 'ok' ) {
            return null;
        }

        this.index = idx;
        return window.displib.make_object_display( response.info, response.fields );
    }

    offset( off )
    {
        return this.fetch( this.index + off );
    }

    next()
    {
        return this.offset( 1 );
    }

    prev()
    {
        return this.offset( -1 );
    }
}

/**
 * class ListProvider
 */
class public_ListProvider extends public_Provider
{
    constructor( list )
    {
        super();

        this.list = list;
        this.obj_id = null;

        this.index = null;
        this.count = list.length;
    }

    init( obj, callback )
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
            action:     'info',
            target:     this.obj_id,
            items:      info_set,
            fields:     field_set,
        };

        load_async( request, this, 'on_init_load', {
            obj: obj,
            callback: callback,
        });
    }

    on_init_load( data, response )
    {
        var display = window.displib.make_object_display( response.info, response.fields );
        eval( 'data.obj.' + data.callback + '( display )' );
    }

    repr()
    {
        return 'List';
    }

    fetch( idx )
    {
        if( idx < 0 || idx >= this.list.length ) {
            return null;
        }

        this.index = idx;

        this.obj_id = this.list[this.index][0];

        var request = {
            action:     'info',
            target:     this.obj_id,
            items:      info_set,
            fields:     field_set,
        };
        var response = load_sync( request );

        return window.displib.make_object_display( response.info, response.fields );
    }

    offset( off )
    {
        return this.fetch( this.index + off );
    }

    next()
    {
        return this.offset( 1 );
    }

    prev()
    {
        return this.offset( -1 );
    }
}

return {
    init: public_init,
    get_info_set: public_get_info_set,
    get_field_set: public_get_field_set,
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

window.tabs = tabs;
