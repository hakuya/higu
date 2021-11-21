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
            if( response.result == 'err' && response.except == 'nosession' ) {
                alert( 'Your session has expired' );
                localStorage.removeItem( 'username' );
                localStorage.removeItem( 'session_id' );
                document.location.href = '/';
                return null;
            }

            eval( 'obj.' + callback + '( data, response )' );
        },
        error:          function( xhr ) {
            dialogs.show_error_dialog( xhr.responseText );
        }
    } );
}

function load_sync( request )
{
    var result = null;

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

    if( result != null && result.result == 'err' && result.except == 'nosession' ) {
        alert( 'Your session has expired' );
        localStorage.removeItem( 'username' );
        localStorage.removeItem( 'session_id' );
        document.location.href = '/';
        return null;
    }

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

// vim:sts=4:sw=4:et
