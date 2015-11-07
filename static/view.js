var TAGLINK_TEMPLATE = "<li><a class='taglink' href='##{tag}'>#{tag}</a></li>";

// module
var tabs = (function() {

var TABS_TEMPLATE = "<li><a href='#{href}'>#{label}</a> <span class='ui-icon ui-icon-close' role='presentation'>Remove Tab</span></li>";

// Local module vars
var tabs_elem = null;
var tabs_counter = 1;

/**
 * create_tab( title ) - creates a tab with the given title
 */
create_tab = function( title )
{
    var count = tabs_counter;
    var id_val = 'tabs-' + count;
    var li = $( TABS_TEMPLATE.replace( /#\{href\}/g, "#" + id_val ).replace( /#\{label\}/g, title ) );
    tabs_elem.find( '.ui-tabs-nav' ).append( li );
    tabs_elem.append( "<div class='tab' id='" + id_val + "'>loading...</div>" );
    tabs_elem.tabs( 'refresh' );
    tabs_counter++;

    tab = $( '#' + id_val );
    public_select( tab );

    return tab;
};

/**
 * class TagslistTab
 */
TagslistTab = function()

    // Constructor
    {
        this.elem = $( '#taglist-tab' );
        this.elem.data( 'obj', this );

        this.on_tags_changed();
    };

    TagslistTab.prototype.on_tags_loaded = function( data, response )
    {
        this.elem.html( '' );
        this.elem.append( "<ul class='taglist'></ul>" );
        var ls = this.elem.children().first();

        for( i = 0; i < response.tags.length; i++ ) {
            var li = TAGLINK_TEMPLATE.replace( /#\{tag\}/g, response.tags[i]);
            ls.append( li );
        }

        activate_links( ls );
    };

    TagslistTab.prototype.on_event = function( e )
    {
        if( e.type == 'info_changed' ) {
            this.on_tags_changed();
        }
    }

    TagslistTab.prototype.on_tags_changed = function()
    {
        load_async( { 'action' : 'taglist' }, this, 'on_tags_loaded', null );
    };

/**
 * class AdminTab
 */
AdminTab = function()

    // Constructor
    {
        this.elem = $( '#admin-tab' );
        this.elem.data( 'obj', this );

        this.elem.html( '' );
        this.elem.append( 'Tag: <input type="text" id="adm-tag-src"/>' );
        this.elem.append( 'New: <input type="text" id="adm-tag-tgt"/>' );

        // Delete
        button = $( '<input type="button" value="Delete"/>' );
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
        this.elem.append( button );

        // Copy
        button = $( '<input type="button" value="Copy"/>' );
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
        this.elem.append( button );

        // Move
        button = $( '<input type="button" value="Move"/>' );
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
        this.elem.append( button );
    };

    AdminTab.prototype.on_event = function( e ) {}

/**
 * class DisplayTab
 */
DisplayTab = function( title, provider )

    // Constructor
    {
        this.elem = create_tab( title );
        this.elem.data( 'obj', this );

        this.provider = provider;
        this.display = null;
        this.title = title;

        nav = tabs.get_nav_elem( this.elem );
        nav.data( 'tab', this );
        nav.droppable({
            accept: '.objitem',
            hoverClass: 'ui-state-hover',
            drop: function( event, ui ) {
                tab = $( this ).data( 'tab' );
                item = $( ui.draggable );
                item.draggable( 'option', 'revert', false );

                tab.drop( item.data( 'obj_id' ), item.data( 'repr' ),
                        item.data( 'type' ) );
            },
        });

        this.provider.init( this, 'on_init_complete' );
    };

    DisplayTab.prototype.close = function()
    {
        // XXX - this should be handled in tabs
        tabs.get_nav_elem( this.elem ).remove();
        tab.on_close();
    };

    DisplayTab.prototype.on_close = function()
    {
        this.provider.close();
        tabs.remove( this.elem );
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

    DisplayTab.prototype.set_duplication = function( original, variant, is_duplicate )
    {
        if( this.display ) {
            this.display.set_duplication( original, variant, is_duplicate );
        }
    };

    DisplayTab.prototype.drop = function( obj_id, repr, type )
    {
        if( this.display ) {
            this.display.drop( obj_id, repr, type );
        }
    };

    DisplayTab.prototype.rm = function( obj_id, repr, type )
    {
        if( this.display ) {
            this.display.rm( obj_id, repr, type );
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
{
    tabs_elem = $( '#tabs' );

    tabs_elem.tabs({
        fit : true,
        heightStyle : 'fill',
        activate: function( e ) {
            tabs.on_select();
        }
    });

    tabs_elem.delegate( "span.ui-icon-close", "click", function() {
        var panelId = $( this ).closest( "li" ).remove().attr( "aria-controls" );
        var tab_elem = $( "#" + panelId );
        var tab = tab_elem.data( 'obj' );
        
        if( !tab || !tab.on_close ) {
            tabs.remove( tab_elem );
        } else {
            tab.on_close();
        }
    });

    // Init basic tabs
    new TagslistTab();
    new AdminTab();
};

/**
 * active() - returns active tab
 */
var public_active = function()
{
    idx = tabs_elem.tabs( 'option', 'active' );
    return tabs_elem.find( '.tab' ).eq( idx );
};

/**
 * get_head_elem()
 */
var public_get_nav_elem = function( tab )
{
    var idx = $( '#tabs > div' ).index( tab );
    return tabs_elem.find( '.ui-tabs-nav li' ).eq( idx );
};

/**
 * on_event()
 */
var public_on_event = function( e )
{
    $( '#tabs > div' ).each( function( idx ) {
        obj = $( this ).data( 'obj' );
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
public_select = function( tab )
{
    var idx = $( '#tabs > div' ).index( tab );
    tabs_elem.tabs( 'option', 'active', idx );
};

/**
 * create_display_tab( title, provider ) - creates a new display tab
 */
public_create_display_tab = function( title, provider )
{
    new DisplayTab( title, provider );
}

/**
 * remove( elem ) - removes the given tab
 */
public_remove = function( elem )
{
    elem.remove();
    tabs_elem.tabs( "refresh" );
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
    };

    // extends Provider
    public_SelectionProvider.prototype = new public_Provider();
    public_SelectionProvider.prototype.constructor = public_SelectionProvider;

    // Member functions
    public_SelectionProvider.prototype.init = function( obj, callback )
    {
        eval( 'obj.' + callback + '( this.selection )' );
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
            return this.fetch( idx );
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

        if( response.result != 'ok' ) {
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
    active: public_active,
    get_nav_elem: public_get_nav_elem,
    on_event: public_on_event,
    on_select: public_on_select,
    select: public_select,
    create_display_tab: public_create_display_tab,
    remove: public_remove,
    Provider: public_Provider,
    SelectionProvider: public_SelectionProvider,
    SingleProvider: public_SingleProvider,
    SearchProvider: public_SearchProvider,
};

})(); // module tabs
