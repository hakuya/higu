
function search( tags ) {
    load( '/search_new?tags=' + tags );
}

function step_display( tab, offset ) {
    if( offset == 0 ) return;

    selection_id = tab.data( 'selection_id' );
    display_idx = tab.data( 'display_idx' );

    var request = {
        'action' : 'selection_fetch',
        'selection' : selection_id,
        'index' : display_idx + offset,
    };
    load3( request, tab );
}

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
            open_error_dialog( xhr.responseText );
        }
    } );
}

function load_new( page, target )
{
    r = null;
    if( !window.XMLHttpRequest ) {
        alert( "Unsupported browser" );
        return;
    }

    r = window.XMLHttpRequest();
    r.onreadystatechange = function() {
        if( this.readyState != 4 ) return;

        if( this.status != 200 ) {
            open_error_dialog( this.responseText );
            return;
        }

        var response = eval( '(' + this.responseText + ')' );

        if( response.action == 'begin-display' ) {
            do_begin_display( target, response )
        } else if( response.action == 'step-display' ) {
            do_step_display( target, response )
        } else if( response.action == 'show-html' ) {
            do_show_html( target, response )
        }
    }

    //r.div = div;
    //open_view( div ).innerHTML = '<h1>Loading...</h1>';

    r.open( 'GET', page, true )
    r.send( null );
}

// vim:sts=4:sw=4:et
