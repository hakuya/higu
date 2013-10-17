function rm() {
    if( confirm( 'Are you sure you want to delete the selected files?' ) ) {
        load( '/callback?id=' + selected + '&action=rm' );
    }
}

function do_begin_display( target, response )
{
    target.data( 'selection_id', response.selection );
    target.data( 'object_id', response.object_id );
    target.data( 'display_idx', response.index );
    load_html( target, response.data );
}

function do_step_display( target, response )
{
    target.data( 'object_id', response.object_id );
    target.data( 'display_idx', response.index );
    load_html( target, response.data );
}

function do_show_html( target, response )
{
    load_html( target, response.data );
}

function load3( request, target )
{
    $.ajax( {
        url:            '/callback_new',
        type:           'POST',
        contentType:    'application/json',
        data:           JSON.stringify( request ),
        processData:    false,
        dataType:       'json',
        success:        function( response ) {
            if( response.action == 'begin-display' ) {
                do_begin_display( target, response )
            } else if( response.action == 'step-display' ) {
                do_step_display( target, response )
            } else if( response.action == 'show-html' ) {
                do_show_html( target, response )
            }
        },
        error:          function( xhr ) {
            error_dialog.open( xhr.responseText );
        }
    } );
}

function load4( request, obj, callback )
{
    $.ajax( {
        url:            '/callback_new',
        type:           'POST',
        contentType:    'application/json',
        data:           JSON.stringify( request ),
        processData:    false,
        dataType:       'json',
        success:        function( response ) {
            eval( 'obj.' + callback + '( response )' );
        },
        error:          function( xhr ) {
            error_dialog.open( xhr.responseText );
        }
    } );
}

function load_async( request, obj, callback, data )
{
    $.ajax( {
        url:            '/callback_new',
        type:           'POST',
        contentType:    'application/json',
        data:           JSON.stringify( request ),
        processData:    false,
        dataType:       'json',
        success:        function( response ) {
            eval( 'obj.' + callback + '( data, response )' );
        },
        error:          function( xhr ) {
            error_dialog.open( xhr.responseText );
        }
    } );
}

function load_sync( request )
{
    result = null;
    
    $.ajax( {
        url:            '/callback_new',
        type:           'POST',
        contentType:    'application/json',
        data:           JSON.stringify( request ),
        processData:    false,
        async:          false,
        dataType:       'json',
        success:        function( response ) {
            result = response;
        },
        error:          function( xhr ) {
            error_dialog.open( xhr.responseText );
        }
    } );

    return result;
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

            provider = new SearchProvider( { query: tag } );
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

$( function() {

$(document).keypress( function( e ) {
    if( $( '.ui-dialog' ).is( ':visible' ) || $( '.nokb' ).is( ':focus' ) ) {
        return;
    }

    e = window.event || e;

    tab = tabs.active();

    obj = tab.data( 'obj' );
    if( obj && obj.display ) {
        switch( e.charCode ) {
            case 116: // t
                tag_dialog.open();
                break;
            case 114: // r
                name_dialog.open();
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

$( '#tagsearch' ).submit( function() {
    tags = $( this ).children( 'input' ).val();

    provider = new SearchProvider( { query: tags } );
    new DisplayTab( tags, provider );

    $( this ).children( 'input' ).val( '' );
    $( document ).focus();
});

$( '#trash' ).droppable({
    accept: '.objitem',
    hoverClass: 'ui-state-hover',
    drop: function( event, ui ) {
        tab = tabs.active();
        item = $( ui.draggable );
        
        tab = tab.data( 'obj' );
        if( tab && tab.rm ) {
            tab.rm( item.data( 'obj_id' ), item.data( 'repr' ),
                    item.data( 'type' ) );
        }
    },
});

$( 'a[href="#newsel"]' ).click( function() {
    provider = new SelectionProvider();
    new DisplayTab( 'Selection', provider );
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

init_view();
init_dialog();

$( window ).resize();
});

// vim:sts=4:sw=4:et
