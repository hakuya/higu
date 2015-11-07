window_width = 0;
window_height = 0;

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
            dialogs.show_error_dialog( xhr.responseText );
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
            dialogs.show_error_dialog( xhr.responseText );
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

            provider = new tabs.SearchProvider( { query: tag } );
            tabs.create_display_tab( tag, provider );
        });
    });

    par.find( '.albumlink' ).each( function( idx ) {
        $( this ).click( function() {
            var target = $( this ).attr( 'href' ).substring( 1 ).split( '-' );

            provider = new tabs.SearchProvider( {
                mode:   'album',
                album:  parseInt( target[0] ),
                index:  parseInt( target[1] ),
            });
            tabs.create_display_tab( 'Album', provider );
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
                dialogs.show_tag_dialog();
                break;
            case 114: // r
                dialogs.show_name_dialog();
                break;
            case 65: // A
                select_all();
                break;
            case 97: // a
                obj.on_event( { type: 'zoom', zoom: -0.5 } )
                break;
            case 115: // s
                obj.on_event( { type: 'zoom', zoom: -2.0 } )
                break;
            case 122: // z
                obj.on_event( { type: 'zoom', zoom: 1.0 } )
                break;
            case 120: // x
                obj.on_event( { type: 'zoom', zoom: 'fit_outside' } )
                break;
            case 99:  // c
                obj.on_event( { type: 'zoom', zoom: 'fit_inside' } )
                break;
            case 106: // j
                obj.down();
                break;
            case 107: // k
                obj.up();
                break;
            default:
        }
    }
});

$( 'a[href="#allimg"]' ).click( function() {
    provider = new tabs.SearchProvider( { mode: 'all' } );
    tabs.create_display_tab( 'All', provider );
});

$( 'a[href="#untagged"]' ).click( function() {
    provider = new tabs.SearchProvider( { mode: 'untagged' } );
    tabs.create_display_tab( 'Untagged', provider );
});

$( '#tagsearch' ).submit( function() {
    tags = $( this ).children( 'input' ).val();

    provider = new tabs.SearchProvider( { query: tags } );
    tabs.create_display_tab( tags, provider );

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
    provider = new tabs.SelectionProvider();
    tabs.create_display_tab( 'Selection', provider );
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

    tab = tabs.active();
    obj = tab.data( 'obj' );
    if( obj && obj.display ) {
        obj.on_event( { type: 'resized' } );
    }
} );

tabs.init();

$( window ).resize();
});

// vim:sts=4:sw=4:et
