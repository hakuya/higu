right_visible = 0;

selected=-1;

list_filelist = new Array();
viewer_filelist = list_filelist;

selection = new Array();

function search( tags ) {
    load( '/search_new?tags=' + tags );
}

function step_display( tab, offset ) {
    if( offset == 0 ) return;

    search_id = tab.data( 'search_id' );
    display_idx = tab.data( 'display_idx' );

    load_new( '/search_step?search_id=' + search_id + '&idx=' + (display_idx + offset), tab );
}

function clickfile( id, reset ) {

    prev = selected;
    is_deselect = false;

    for( i = 0; i < selection.length; i++ ) {
        if( selection[i] == id ) {
            selection.splice( i, 1 );
            break;
        }
    }

    if( reset ) {
        form = document.forms["list"];

        if( !eval( 'form.list_check' + id ).checked ) {
            for( i = 0; i < form.elements.length; i++ ) {
                e = form.elements[i];
                if( e.type == 'checkbox' ) {
                    e.checked = 0;
                }
            }

            selection = Array();
        }
    } else {
        if( !eval( 'document.forms["list"].list_check' + id ).checked && id != selected ) {
            is_deselect = true;
        }
    }

    if( !is_deselect ) {
        if( selected >= 0 ) {
            sdiv = document.getElementById( 'list_div' + selected );
            if( sdiv ) {
                sdiv.style.background = '';
            }
        }


        selected = id;
        // id is always removed from the selection at the
        // begining of this method so this is safe
        selection.push( id );

        sdiv = document.getElementById( 'list_div' + id );
        sdiv.style.background = 'yellow';
        eval( 'document.forms["list"].list_check' + selected ).checked = true;

        viewer_filelist = list_filelist;
    }
    onselectionchanged( prev, id );
}

function select_all()
{
    selection = Array();

    form = document.forms["list"];
    for( i = 0; i < form.elements.length; i++ ) {
        e = form.elements[i];
        i_id = parseInt( e.value );
        if( i_id != selected ) {
            selection.push( i_id );
            e.checked = 1;
        }
    }

    selection.push( selected );
}

function clickalbum( id ) {

    prev = selected;

    form = document.forms["list"];
    for( i = 0; i < form.elements.length; i++ ) {
	e = form.elements[i];
	if( e.type == 'checkbox' ) {
	    e.checked = 0;
	}
    }

    selection = Array();

    if( selected >= 0 ) {
	sdiv = document.getElementById( 'list_div' + selected );
	if( sdiv ) {
	    sdiv.style.background = '';
	}
    }


    selected = id;
    // id is always removed from the selection at the
    // begining of this method so this is safe
    selection.push( id );

    sdiv = document.getElementById( 'list_div' + id );
    sdiv.style.background = 'yellow';
    eval( 'document.forms["list"].list_check' + selected ).checked = true;

    viewer_filelist = list_filelist;
    
    onselectionchanged( prev, id );
}

function getselectionstring() {
    if( selection.length == 0 ) {
        return '';
    }

    selstr = '&selection=' + selection[0];

    for( i = 1; i < selection.length; i++ ) {
        selstr += ' ' + selection[i];
    }

    return selstr;
}

function onselectionchanged( prev, curr ) {
    load( '/callback?action=select&id=' + curr );
}

function group( action ) {
    load( '/callback?id=' + selected + '&action=' + action );
}

function rm() {
    if( confirm( 'Are you sure you want to delete the selected files?' ) ) {
        load( '/callback?id=' + selected + '&action=rm' );
    }
}

function selectfromalbum( cid, fid ) {
    load( '/callback?action=selalbum&fid=' + fid + '&cid=' + cid );
    selected = fid;
    selection = new Array();
    selection.push( fid );
}

function nextfile( dir ) {
    current = -1;

    form = document.forms["list"];

    if( form.elements.length == 0 ) return;

    for( i = 0; i < form.elements.length; i++ ) {
        e = form.elements[i];
        if( parseInt( e.value ) == selected ) {
            current = i;
            break;
        }
    }

    if( current < 0 ) {
        next = 0;
    } else {
        next = current + dir;
        if( next < 0 || next >= form.elements.length ) {
            return;
        }
    }

    clickfile( parseInt( form.elements[next].value ), true );
}

function open_view( view ) {
    if( view == 'viewer' ) {
        return document.getElementById( 'main' );
    } else {
        return document.getElementById( view );
    }
}

function close_view( view ) {
    if( view == 'viewer2' && right_visible ) {
        right.style.visibility = 'hidden';
        main.style.width = window.innerWidth - 300;
        right_visible = 0;
    }
}

function dismiss_dialog()
{
    overlay.style.visibility = 'hidden';
}

function dismiss_and_load( page )
{
    dismiss_dialog();
    load( page );
}

function do_begin_display( target, response )
{
    target.data( 'search_id', response.search_id );
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

function load( page )
{
    page = page + getselectionstring();

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
            search_id = response.search_id;
            selected = response.object_id;
            display_idx = response.index;
        } else if( response.action == 'step-display' ) {
            selected = response.object_id;
            display_idx = response.index;
        }

        if( response.data ) {
            for( i = 0; i < response.data.length; i++ ) {
                open_view( response.data[i].id ).innerHTML = response.data[i].content;
            }
        }
    }

    //r.div = div;
    //open_view( div ).innerHTML = '<h1>Loading...</h1>';

    r.open( 'GET', page, true )
    r.send( null );
}

function make_group( type ) {
    this_img = document.forms[0].fid.value;
    parent   = parent.viewer.document.forms[0].fid.value;
    action = "group|" + type + " " + parent;

    location.href = "/view?id=" + this_img + "&secondary=1&action=" + action;
}


// vim:sts=4:sw=4:et
