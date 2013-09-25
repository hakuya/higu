window_width = -1;
window_height = -1;

$( function() {

$(document).keypress( function( e ) {
    if( $( '.ui-dialog' ).is( ':visible' ) || $( '.nokb' ).is( ':focus' ) ) {
        return;
    }

    e = window.event || e;

    tab = active_tab();

    if( tab.data( 'selection_id' ) ) {
        switch( e.charCode ) {
            case 116: // t
                open_tag_dialog();
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
    load3_into_new_tab( 'All', request );
});

$( 'a[href="#untagged"]' ).click( function() {
    load_into_new_tab( 'Untagged', '/search_new?mode=untagged&tags=' );
});

$( 'a[href="#albums"]' ).click( function() {
    load_into_new_tab( 'Albums', '/search_new?mode=albums&tags=' );
});

tabs = $( '#tabs' ).tabs({
    fit : true,
    heightStyle : 'fill',
});

tabs.delegate( "span.ui-icon-close", "click", function() {
    var panelId = $( this ).closest( "li" ).remove().attr( "aria-controls" );
    tab = $( "#" + panelId );

    selection_id = tab.data( 'selection_id' );
    if( selection_id ) {
        var request = {
            'action' : 'selection_close',
            'selection' : selection_id,
        }
        load3( request, null );
    }
    tab.remove();
    
    tabs.tabs( "refresh" );
});

$( '#tagsearch' ).submit( function() {
    tags = $( this ).children( 'input' ).val();
    load_into_new_tab( 'Search', '/search_new?mode=tags&tags=' + tags );
    $( this ).children( 'input' ).val( '' );
    $( document ).focus();
});

$( '#error-dialog' ).dialog({
    autoOpen: false,
    width: 800,
    height: 500,
    modal: true,
    buttons: {
        Cancel: function() {
            $( document ).focus();
            $( this ).dialog( 'close' );
        }
    },
});

$( '#tag-dialog' ).dialog({
    autoOpen: false,
    width: 600,
    height: 300,
    modal: true,
    buttons: {
        'Apply': function() {
            close_tag_dialog( true );
        },
        Cancel: function() {
            close_tag_dialog( false );
        }
    },
});

$( '#tag-dialog-form' ).submit( function() {
    close_tag_dialog( true );
});

$( '#name-dialog' ).dialog({
    autoOpen: false,
    width: 600,
    height: 300,
    modal: true,
    buttons: {
        'Apply': function() {
            $( document ).focus();
            $( this ).dialog( 'close' );
        },
        Cancel: function() {
            $( document ).focus();
            $( this ).dialog( 'close' );
        }
    },
});

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

load_new( '/taglist', $( '#taglist-tab' ) );
load_new( '/admin', $( '#admin-tab' ) );

$( window ).resize();
});

var tab_counter = 1;
var tab_template = "<li><a href='#{href}'>#{label}</a> <span class='ui-icon ui-icon-close' role='presentation'>Remove Tab</span></li>";

function load_into_new_tab( title, page ) {
    tab_id = open_tab( title );
    load_new( page, tab );
}

function load3_into_new_tab( title, request ) {
    var tab_id = open_tab( title );
    load3( request, tab );
}

function active_tab() {
    tabs = $( '#tabs' );

    idx = tabs.tabs( 'option', 'active' );
    return tabs.find( '.tab' ).eq( idx );
}

function select_tab( tab ) {
    var idx = $( '#tabs > div' ).index( tab )
    $( '#tabs' ).tabs( 'option', 'active', idx );
}

function open_tab( title ) {
    var count = tab_counter;
    var id_val = 'tabs-' + count;
    var li = $( tab_template.replace( /#\{href\}/g, "#" + id_val ).replace( /#\{label\}/g, title ) );
    tabs.find( '.ui-tabs-nav' ).append( li );
    tabs.append( "<div class='tab' id='" + id_val + "'>loading...</div>" );
    tabs.tabs( 'refresh' );
    tab_counter++;

    tab = $( '#' + id_val );
    select_tab( tab );

    return tab;
};

function open_tag_dialog() {
    $( '#tag-dialog' ).dialog( 'open' );
    $( '#tags' ).focus();
    $( '#tags' ).select();
};

function submit_tags( tags )
{
    var tab = active_tab();

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

function close_tag_dialog( submit ) {
    if( submit ) {
        submit_tags( $( '#tags' ).val() );
    }
    $( document ).focus();
    $( '#tag-dialog' ).dialog( 'close' );
}

function open_rename_dialog( saveold_allowed ) {
    $( '#saveold' ).disabled( !saveold_allowed );
    $( '#name-dialog' ).dialog( 'open' );
    $( '#fname' ).focus();
}

function open_error_dialog( msg ) {
    $( '#error-msg' ).html( msg );
    $( '#error-dialog' ).dialog( 'open' );
};

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
            load_into_new_tab( tag, '/search_new?mode=tags&tags=' + tag );
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
            load3_into_new_tab( 'Album', request );
        });
    });
}
