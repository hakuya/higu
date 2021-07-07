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

/**
 * create_tab( title ) - creates a tab with the given title
 */
create_tab = function( title, obj )
{
    var count = tabs_counter;
    var id_val = 'tabs-' + count;

    var tab = {
        title: title,
        obj: obj,
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
 * class TagslistTab
 */
TagslistTab = function()

    // Constructor
    {
        this.tab = create_tab( 'Taglist', this );
        this.elem = null;
    };

    TagslistTab.prototype.set_elem = function( el )
    {
        if( this.elem != null ) return;

        this.elem = $( el );
        this.elem.data( 'obj', this );

        this.load_content();
    };

    TagslistTab.prototype.on_content_ready = function( response )
    {
        if( response != null ) {
            this.elem.html( response );
        }

        activate_links( this.elem.children().first() );
    };

    TagslistTab.prototype.load_content = function()
    {
        $.ajax( {
            url:            '/taglist',
            type:           'GET',
            contentType:    'text/html',
            thiz:           this,
            success:        function( response ) {
                this.thiz.on_content_ready( response );
            },
            error:          function( xhr ) {
                dialogs.show_error_dialog( xhr.responseText );
            }
        } );
    };

    TagslistTab.prototype.close = function()
    {
        tagslist_tab = null;
        tabs.remove( this );
    };

    TagslistTab.prototype.on_event = function( e )
    {
        if( e.type == 'info_changed' ) {
            this.load_content();
        }
    }

    TagslistTab.prototype.on_tags_changed = function()
    {
        this.on_content_invalidated();
    };

/**
 * class AdminTab
 */
LoginTab = function()

    // Constructor
    {
        this.tab = create_tab( 'Login', this );
        this.elem = null;
    };

    LoginTab.prototype.set_elem = function( el )
    {
        if( this.elem != null ) return;

        this.elem = $( el );
        this.elem.data( 'obj', this );

        this.load_content();
    };

    LoginTab.prototype.on_content_ready = function( response )
    {
        if( response != null ) {
            this.elem.html( response );
        }
    };

    LoginTab.prototype.close = function()
    {
        login_tab = null;
        tabs.remove( this );
    };

    LoginTab.prototype.load_content = function()
    {
        thiz = this;

        $.ajax( {
            url:            '/login',
            type:           'GET',
            contentType:    'text/html',
            success:        function( response ) {
                thiz.on_content_ready( response );
            },
            error:          function( xhr ) {
                dialogs.show_error_dialog( xhr.responseText );
            }
        } );
    };

    LoginTab.prototype.on_event = function( e ) {}

/**
 * class AdminTab
 */
AdminTab = function()

    // Constructor
    {
        this.tab = create_tab( 'Admin', this );
        this.elem = null;
    };

    AdminTab.prototype.set_elem = function( el )
    {
        if( this.elem != null ) return;

        this.elem = $( el );
        this.elem.data( 'obj', this );

        this.load_content();
    };

    AdminTab.prototype.on_content_ready = function( response )
    {
        if( response != null ) {
            this.elem.html( response );
        }

        // Delete
        button = $( '#adm-tag-rm-button' );
        button.click( function( e ) {
            src = $( '#adm-tag-src' );
            tgt = $( '#adm-tag-tgt' );

            var request = {
                action:     'tag_delete',
                tag:        src.val(),
            };
            load_sync( request );

            src.val( '' );
            tgt.val( '' );
        });

        // Copy
        button = $( '#adm-tag-cp-button' );
        button.click( function( e ) {
            src = $( '#adm-tag-src' );
            tgt = $( '#adm-tag-tgt' );

            var request = {
                action:     'tag_copy',
                tag:        src.val(),
                target:     tgt.val(),
            };
            load_sync( request );

            src.val( '' );
            tgt.val( '' );
        });

        // Move
        button = $( '#adm-tag-mv-button' );
        button.click( function( e ) {
            src = $( '#adm-tag-src' );
            tgt = $( '#adm-tag-tgt' );

            var request = {
                action:     'tag_move',
                tag:        src.val(),
                target:     tgt.val(),
            };
            load_sync( request );

            src.val( '' );
            tgt.val( '' );
        });
    };

    AdminTab.prototype.close = function()
    {
        admin_tab = null;
        tabs.remove( this );
    };

    AdminTab.prototype.load_content = function()
    {
        thiz = this;

        $.ajax( {
            url:            '/admin',
            type:           'GET',
            contentType:    'text/html',
            success:        function( response ) {
                thiz.on_content_ready( response );
            },
            error:          function( xhr ) {
                dialogs.show_error_dialog( xhr.responseText );
            }
        } );
    };

    AdminTab.prototype.on_event = function( e ) {}

/**
 * class DisplayTab
 */
DisplayTab = function( title, provider )

    // Constructor
    {
        this.tab = create_tab( title, this );

        this.elem = null;
        this.provider = provider;
        this.display = null;
    };

    DisplayTab.prototype.set_elem = function( el )
    {
        if( this.elem != null ) return;

        this.elem = $( el );
        this.elem.data( 'obj', this );

        nav = $( '#tabs-tab-' + this.tab.id );

        nav.data( 'tab', this );
        nav.droppable({
            accept: '.objitem',
            hoverClass: 'ui-state-hover',
            drop: function( event, ui ) {
                if( ui.helper.is( '.dropped' ) ) {
                    return false;
                }

                tab = $( this ).data( 'tab' );
                item = $( ui.draggable );
                item.draggable( 'option', 'revert', false );

                tab.drop( item.data( 'drop_data' ) );

                ui.helper.addClass( 'dropped' );
            },
        });

        this.provider.init( this, 'on_init_complete' );
    };

    DisplayTab.prototype.close = function()
    {
        this.provider.close();
        tabs.remove( this );
    };

    DisplayTab.prototype.tag = function( tags )
    {
        if( this.display ) {
            return this.display.tag( tags );
        } else {
            return { result: 'ok' };
        }
    };

    DisplayTab.prototype.rename = function( name, saveold )
    {
        if( this.display ) {
            this.display.rename( name, saveold );
        }
    };

    DisplayTab.prototype.set_variant = function( original, variant )
    {
        if( this.display ) {
            this.display.set_variant( original, variant );
        }
    }

    DisplayTab.prototype.merge_duplicates = function( original, duplicate )
    {
        if( this.display ) {
            this.display.merge_duplicates( original, duplicate );
        }
    }

    DisplayTab.prototype.drop = function( drop_data )
    {
        if( this.display ) {
            this.display.drop( drop_data )
        }
    };

    DisplayTab.prototype.rm = function( drop_data )
    {
        if( this.display ) {
            this.display.rm( drop_data )
        }
    };

    DisplayTab.prototype.down = function()
    {
        display = this.provider.next();
        if( display ) {
            this.display = display;
            this.display.attach( this.elem );
        }
    };

    DisplayTab.prototype.up = function()
    {
        display = this.provider.prev();
        if( display ) {
            this.display = display;
            this.display.attach( this.elem );
        }
    };

    DisplayTab.prototype.on_init_complete = function( display )
    {
        this.elem.html( '' );
        this.elem.append( "<div class='info'></div>" );
        this.elem.append( "<div class='disp'></div>" );

        this.display = display;
        this.display.attach( this.elem );
    };

    DisplayTab.prototype.on_event = function( e )
    {
        if( this.display ) {
            display = this.display.on_event( e );
            if( display ) {
                this.display = display;
                this.display.attach( this.elem );
            }
        }
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
        var obj = it.obj;
        if( obj && obj.on_event ) {
            obj.on_event( e );
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
    var dt = new DisplayTab( title, provider );
    add_tab( dt.tab );
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

    login_tab = new LoginTab();
    add_tab( login_tab.tab );
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

    admin_tab = new AdminTab();
    add_tab( admin_tab.tab );
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

    tagslist_tab = new TagslistTab();
    add_tab( tagslist_tab.tab );
}

/**
 * remove( elem ) - removes the given tab
 */
public_remove = function( obj )
{
    var idx = all_tabs.findIndex( function( it ) { return it.obj === obj; } );
    if( idx >= 0 ) {
        if( active_tab_id == all_tabs[idx].id ) {
            if( idx == 0 ) {
                active_tab_id = null;
            } else {
                active_tab_id = all_tabs[idx-1].id;
            }
        }
        all_tabs.splice( idx, 1 );
        tabs_listeners.forEach( function( it, idx, arr ) { it.on_tab_removed( obj ); } )

        obj.elem.remove();
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
        this.selection_id = displib.register_selection( this.selection );
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
        displib.unregister_selection( this.selection );
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
    };

    // extends Provider
    public_SingleProvider.prototype = new public_Provider();
    public_SingleProvider.prototype.constructor = public_SingleProvider;

    // Member functions
    public_SingleProvider.prototype.init = function( obj, callback )
    {
        display = displib.make_object_display( this.obj_id );
        eval( 'obj.' + callback + '( display )' );
    };

    public_SingleProvider.prototype.repr = function()
    {
        return 'Single';
    };

    public_SingleProvider.prototype.fetch = function( idx )
    {
        if( idx == 0 ) {
            return displib.make_object_display( this.obj_id );
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
        this.last = null;
    };

    // extends Provider
    public_SearchProvider.prototype = new public_Provider();
    public_SearchProvider.prototype.constructor = public_SearchProvider;

    public_SearchProvider.prototype.init = function( obj, callback )
    {
        if( this.sid ) {
            return this.fetch( this.last );
        }

        var request = { action: 'search' };

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
            this.last = null;

            if( response.msg ) {
                display = displib.make_dummy_display(
                    'The search failed: ' + response.msg );
            } else {
                display = displib.make_dummy_display(
                    'The search failed: ' + response.except + ' error' );
            }
        } else if( response.results > 0 ) {
            this.sid = response.selection;
            this.last = response.index;

            display = displib.make_object_display( response.first );
        } else {
            this.sid = null;
            this.last = null;

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
        };
        response = load_sync( request );

        if( response == null || response.result != 'ok' ) {
            return null;
        }

        this.last = idx;
        display = displib.make_object_display( response.object_id );
        return display;
    };

    public_SearchProvider.prototype.offset = function( off )
    {
        return this.fetch( this.last + off );
    };

    public_SearchProvider.prototype.next = function()
    {
        return this.offset( 1 );
    };

    public_SearchProvider.prototype.prev = function()
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
};

})(); // module tabs
