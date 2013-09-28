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

// vim:sts=4:sw=4:et
