window_width = -1;
window_height = -1;

// Singletons
var tabs;
var tag_dialog;
var error_dialog;

// Classes
var SearchTab;

$( function() {

$(document).keypress( function( e ) {
    if( $( '.ui-dialog' ).is( ':visible' ) || $( '.nokb' ).is( ':focus' ) ) {
        return;
    }

    e = window.event || e;

    tab = tabs.active();

    if( tab.data( 'selection_id' ) ) {
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
                step_display( tab, 1 );
                break;
            case 107: // k
                step_display( tab, -1 );
                break;
            default:
        }
    }
});

$( 'a[href="#allimg"]' ).click( function() {
    var request = {
        'action' : 'search',
        'mode' : 'all',
    };
    new SearchTab( 'All', request );
});

$( 'a[href="#untagged"]' ).click( function() {
    var request = {
        'action' : 'search',
        'mode' : 'untagged',
    };
    new SearchTab( 'Untagged', request );
});

$( 'a[href="#albums"]' ).click( function() {
    var request = {
        'action' : 'search',
        'mode' : 'albums',
    };
    new SearchTab( 'Albums', request );
});

/*
$( 'a[href="#newsel"]' ).click( function() {
    new SelectionTab();
});*/

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
        return this.elem.find( '.ui-tabs-nav > li' ).eq( idx );
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
 * class SearchTab
 */
SearchTab = function( title, request )
{
    this.elem = tabs.create( title );
    this.elem.data( 'obj', this );
    
    load3( request, this.elem );

    this.close = function()
    {
        selection_id = this.elem.data( 'selection_id' );
        if( selection_id ) {
            var request = {
                'action' : 'selection_close',
                'selection' : selection_id,
            }
            load3( request, null );
        }
        tabs.remove( this.elem );
    }
};

/**
 * class SelectionTab
 */
SelectionTab = function()
{
    this.elem = tabs.create( 'Selection' );
    this.elem.data( 'obj', this );

    this.elem.html( "<li class='thumbslist sortable'></li>" );
    tabs.get_nav_elem( this.elem ).droppable({
        accept: '.thumbslist > li',
        drop: function( event, ui ) {
            alert( 'dropped' );
        },
    });
};

$( '#tagsearch' ).submit( function() {
    tags = $( this ).children( 'input' ).val();

    var request = {
        'action' : 'search',
        'tags' : tags,
    }
    new SearchTab( 'Search', request );
    $( this ).children( 'input' ).val( '' );
    $( document ).focus();
});

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
        $( this ).data( 'obj' ).close( true );
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

        if( tab.data( 'selection_id' ) ) {
            var obj = tab.data( 'object_id' );
            var request = {
                'action' : 'tag',
                'target' : obj,
                'tags' : tags,
            };
            load3( request, tab.find( '.info' ) );
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

load3( { 'action' : 'taglist' }, $( '#taglist-tab' ) );
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

            var request = {
                'action' : 'search',
                'tags' : tag,
            }
            new SearchTab( tag, request );
        });
    });

    par.find( '.albumlink' ).each( function( idx ) {
        $( this ).click( function() {
            var target = $( this ).attr( 'href' ).substring( 1 ).split( '-' );
            var request = {
                'action' : 'search',
                'mode' : 'album',
                'album' : parseInt( target[0] ),
                'index' : parseInt( target[1] ),
            };
            new SearchTab( 'Album', request );
        });
    });

    par.find( '.sortable li' ).each( function( idx ) {
        $( this ).draggable( {
            helper : 'clone',
        } );
        $( this ).disableSelection();
    });
}
