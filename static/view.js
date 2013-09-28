window_width = -1;
window_height = -1;

// Singletons
var tabs;
var tag_dialog;
var error_dialog;

// Classes
var SearchProvider;
var DisplayTab;

$( function() {

$(document).keypress( function( e ) {
    if( $( '.ui-dialog' ).is( ':visible' ) || $( '.nokb' ).is( ':focus' ) ) {
        return;
    }

    e = window.event || e;

    tab = tabs.active();

    if( tab.data( 'obj' ) ) {
        switch( e.charCode ) {
            case 116: // t
                tag_dialog.open();
                break;
            case 114: // r
                /*
                if( selection.length == 1 ) {
                    load( '/dialog?kind=rename' );
                }*/
                break;
            case 65: // A
                select_all();
                break;
            case 97: // a
                resize_image( tab, 0.5 );
                break;
            case 115: // s
                resize_image( tab, 2.0 );
                break;
            case 122: // z
                resize_image( tab, 0 );
                break;
            case 120: // x
                resize_image( tab, -2 );
                break;
            case 99:  // c
                resize_image( tab, -1 );
                break;
            case 106: // j
                tab.data( 'obj' ).down();
                break;
            case 107: // k
                tab.data( 'obj' ).up();
                break;
            default:
        }
    }
});

$( 'a[href="#allimg"]' ).click( function() {
    provider = new SearchProvider( { mode: 'all' } );
    new DisplayTab( 'All', provider );
});

$( 'a[href="#untagged"]' ).click( function() {
    provider = new SearchProvider( { mode: 'untagged' } );
    new DisplayTab( 'Untagged', provider );
});

$( 'a[href="#albums"]' ).click( function() {
    provider = new SearchProvider( { mode: 'albums' } );
    new DisplayTab( 'Albums', provider );
});

$( '#tagsearch' ).submit( function() {
    tags = $( this ).children( 'input' ).val();

    provider = new SearchProvider( { tags: tags } );
    new DisplayTab( tags, provider );

    $( this ).children( 'input' ).val( '' );
    $( document ).focus();
});


$( 'a[href="#newsel"]' ).click( function() {
    provider = new SelectionProvider();
    new DisplayTab( 'Selection', provider );
});

/**
 * class tabs
 */
tabs = new function()
{
    this.elem = $( '#tabs' );
    this.counter = 1;
    this.template = "<li><a href='#{href}'>#{label}</a> <span class='ui-icon ui-icon-close' role='presentation'>Remove Tab</span></li>";

    // Begin constructor
    this.elem.tabs({
        fit : true,
        heightStyle : 'fill',
    });

    this.elem.delegate( "span.ui-icon-close", "click", function() {
        var panelId = $( this ).closest( "li" ).remove().attr( "aria-controls" );
        var tab_elem = $( "#" + panelId );
        var tab = tab_elem.data( 'obj' );
        
        if( !tab || !tab.close ) {
            tabs.remove( tab_elem );
        } else {
            tab.close();
        }
    });
    // End constructor

    /**
     * active() - returns active tab
     */
    this.active = function()
    {
        idx = this.elem.tabs( 'option', 'active' );
        return this.elem.find( '.tab' ).eq( idx );
    };

    /**
     * get_head_elem()
     */
    this.get_nav_elem = function( tab )
    {
        var idx = $( '#tabs > div' ).index( tab );
        return this.elem.find( '.ui-tabs-nav li' ).eq( idx );
    }

    /**
     * select( tab ) - selects the given tab
     */
    this.select = function( tab )
    {
        var idx = $( '#tabs > div' ).index( tab );
        this.elem.tabs( 'option', 'active', idx );
    };

    /**
     * create( title ) - creates a tab with the given title
     */
    this.create = function( title )
    {
        var count = this.counter;
        var id_val = 'tabs-' + count;
        var li = $( this.template.replace( /#\{href\}/g, "#" + id_val ).replace( /#\{label\}/g, title ) );
        this.elem.find( '.ui-tabs-nav' ).append( li );
        this.elem.append( "<div class='tab' id='" + id_val + "'>loading...</div>" );
        this.elem.tabs( 'refresh' );
        this.counter++;

        tab = $( '#' + id_val );
        this.select( tab );

        return tab;
    };

    /**
     * remove( elem ) - removes the given tab
     */
    this.remove = function( elem )
    {
        elem.remove();
        this.elem.tabs( "refresh" );
    }
};

/**
 * singleton taglist_tab
 */
taglist_tab = new function()
{
    this.elem = $( '#taglist-tab' );
    this.elem.data( 'obj', this );

    TAGLINK_TEMPLATE = "<li><a class='taglink' href='##{tag}'>#{tag}</a></li>";

    // Member functions
    this.on_tags_loaded = function( response )
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

    this.on_tags_changed = function()
    {
        load4( { 'action' : 'taglist' }, this, 'on_tags_loaded' );
    };

    // Constructor
    this.on_tags_changed();
};

/**
 * class SelectionProvider
 */
SelectionProvider = function()
{
    this.selection = new SelectionDisplay();

    // Member functions
    this.init = function( obj, callback )
    {
        eval( 'obj.' + callback + '( this.selection )' );
    };

    this.close = function()
    {
    };

    this.repr = function()
    {
        return 'Single';
    };

    this.fetch = function( idx )
    {
        if( idx == 0 ) {
            return this.selection;
        } else {
            return null;
        }
    };

    this.offset = function( off )
    {
        return this.fetch( off );
    };

    this.next = function()
    {
        return null;
    };

    this.prev = function()
    {
        return null;
    };
};

/**
 * class SingleProvider
 */
SingleProvider = function( obj_id )
{
    this.obj_id = obj_id;

    // Member functions
    this.init = function( obj, callback )
    {
        display = make_display( this.obj_id );
        eval( 'obj.' + callback + '( display )' );
    };

    this.close = function()
    {
    };

    this.repr = function()
    {
        return 'Single';
    };

    this.fetch = function( idx )
    {
        if( idx == 0 ) {
            return make_display( this.obj_id );
        } else {
            return null;
        }
    };

    this.offset = function( off )
    {
        return this.fetch( off );
    };

    this.next = function()
    {
        return null;
    };

    this.prev = function()
    {
        return null;
    };
};

/**
 * class SearchProvider
 */
SearchProvider = function( query )
{
    this.query = query;
    this.sid = null;
    this.last = null;

    // Member functions
    this.init = function( obj, callback )
    {
        if( this.sid ) {
            return this.fetch( idx );
        }

        var request = { action: 'search' };

        if( query.mode ) {
            if( query.mode == 'album' ) {
                request.album = query.album;
            }

            request.mode = query.mode;
        } else {
            request.tags = query.tags;
        }

        if( query.index ) {
            request.index = query.index;
        }

        load_async( request, this, 'on_init_load', {
            obj: obj,
            callback: callback,
        });
    };

    this.on_init_load = function( data, response )
    {
        this.sid = response.selection;
        this.last = response.index;

        display = make_display( response.object_id );
        eval( 'data.obj.' + data.callback + '( display )' );
    }

    this.close = function()
    {
        var request = {
            'action' : 'selection_close',
            'selection' : this.sid,
        }
        load_sync( request );
    }

    this.repr = function()
    {
        return query;
    }

    this.fetch = function( idx )
    {
        var request = {
            action:     'selection_fetch',
            selection:  this.sid,
            index:      idx,
        };
        response = load_sync( request );

        this.last = response.index;
        display = make_display( response.object_id );
        return display;
    };

    this.offset = function( off )
    {
        return this.fetch( this.last + off );
    };

    this.next = function()
    {
        return this.offset( 1 );
    };

    this.prev = function()
    {
        return this.offset( -1 );
    };

    this.slice = function( begin, end )
    {
    };
};

/**
 * class DisplayTab
 */
DisplayTab = function( title, provider )
{
    this.elem = tabs.create( title );
    this.elem.data( 'obj', this );

    this.provider = provider;
    this.display = null;

    TAGLINK_TEMPLATE = "<li><a class='taglink' href='##{tag}'>#{tag}</a></li>";
    
    // Member functions
    this.close = function()
    {
        this.provider.close();
        tabs.remove( this.elem );
    };

    this.tag = function( tags )
    {
        if( this.display ) {
            this.display.tag( tags );
        }
    }

    this.drop = function( obj_id, repr )
    {
        if( this.display ) {
            this.display.drop( obj_id, repr );
        }
    }

    this.down = function()
    {
        display = this.provider.next();
        if( display ) {
            this.display = display;
            this.display.attach( this.elem );
        }
    }

    this.up = function()
    {
        display = this.provider.prev();
        if( display ) {
            this.display = display;
            this.display.attach( this.elem );
        }
    }

    this.on_init_complete = function( display )
    {
        this.elem.html( '' );
        this.elem.append( "<div class='info'></div>" );
        this.elem.append( "<div class='disp'></div>" );

        this.display = display;
        this.display.attach( this.elem );
    };

    // Constructor

    nav = tabs.get_nav_elem( this.elem );
    nav.data( 'tab', this );
    nav.droppable({
        accept: '.objitem',
        hoverClass: 'ui-state-hover',
        drop: function( event, ui ) {
            tab = $( this ).data( 'tab' );
            item = $( ui.draggable );

            tab.drop( item.data( 'obj_id' ), item.data( 'repr' ) );
        },
    });

    this.provider.init( this, 'on_init_complete' );
};

/**
 * class error_dialog
 */
error_dialog = new function()
{
    this.elem = $( '#error-dialog' );
    this.elem.data( 'obj', this );

    // Begin Constructor
    this.elem.dialog({
        autoOpen: false,
        width: 800,
        height: 500,
        modal: true,
        buttons: {
            Cancel: function() {
                $( this ).data( 'obj' ).close();
            }
        },
    });
    // End Constructor

    this.open = function( msg )
    {
        $( '#error-msg' ).html( msg );
        this.elem.dialog( 'open' );
    };

    this.close = function()
    {
        $( document ).focus();
        this.elem.dialog( 'close' );
    }
};

/**
 * class tag_dialog
 */
tag_dialog = new function()
{
    this.elem = $( '#tag-dialog' );
    this.elem.data( 'obj', this );

    // Begin Constructor
    this.elem.dialog({
        autoOpen: false,
        width: 600,
        height: 300,
        modal: true,
        buttons: {
            'Apply': function() {
                $( this ).data( 'obj' ).close( true );
            },
            Cancel: function() {
                $( this ).data( 'obj' ).close( false );
            }
        },
    });

    $( '#tag-dialog-form' ).submit( function() {
        $( '#tag-dialog' ).data( 'obj' ).close( true );
    });
    // End Constructor

    this.open = function()
    {
        this.elem.dialog( 'open' );
        $( '#tags' ).focus();
        $( '#tags' ).select();
    };

    this.submit = function( tags )
    {
        var tab = tabs.active();

        if( tab.data( 'obj' ) ) {
            tab.data( 'obj' ).tag( tags );
        }
    }

    this.close = function( submit )
    {
        if( submit ) {
            this.submit( $( '#tags' ).val() );
        }
        $( document ).focus();
        this.elem.dialog( 'close' );
    }
};

/**
 * class name_dialog
 */
name_dialog = new function()
{
    this.elem = $( '#name-dialog' );
    this.elem.data( 'obj', this );

    this.elem.dialog({
        autoOpen: false,
        width: 600,
        height: 300,
        modal: true,
        buttons: {
            'Apply': function() {
                $( this ).data( 'obj' ).close();
            },
            Cancel: function() {
                $( this ).data( 'obj' ).close();
            }
        },
    });

    this.open = function()
    {
        this.elem.dialog( 'open' );
        this.elem.focus();
        this.elem.select();
    };

    this.close = function( submit )
    {
        $( document ).focus();
        this.elem.dialog( 'close' );
    }
};

$( window ).resize( function() {
    width = window.innerWidth;
    height = window.innerHeight;

    if( width == window_width && height == window_height ) return;

    window_width = width;
    window_height = height;

    head_h = $( '#header' ).height();
    main_h = height - head_h;

    $( '#main' ).height( main_h - 50 );
    $( '#tabs' ).tabs( 'refresh' );
} );

var request;

load3( { 'action' : 'admin' }, $( '#admin-tab' ) );

$( window ).resize();
});

function open_rename_dialog( saveold_allowed ) {
    $( '#saveold' ).disabled( !saveold_allowed );
    $( '#name-dialog' ).dialog( 'open' );
    $( '#fname' ).focus();
}

function load_html( elem, content )
{
    elem.html( content );
    activate_links( elem );
}

function activate_links( par )
{
    par.find( '.taglink' ).each( function( idx ) {
        $( this ).click( function() {
            tag = $( this ).attr( 'href' ).substring( 1 );

            provider = new SearchProvider( { tags: tag } );
            new DisplayTab( tag, provider );
        });
    });

    par.find( '.albumlink' ).each( function( idx ) {
        $( this ).click( function() {
            var target = $( this ).attr( 'href' ).substring( 1 ).split( '-' );

            provider = new SearchProvider( {
                mode:   'album',
                album:  parseInt( target[0] ),
                index:  parseInt( target[1] ),
            });
            new DisplayTab( 'Album', provider );
        });
    });

    par.find( '.sortable li' ).each( function( idx ) {
        $( this ).draggable( {
            helper : 'clone',
        } );
        $( this ).disableSelection();
    });
}
