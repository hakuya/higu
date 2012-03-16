right_visible = 0;

selected=-1;

list_filelist = new Array();
viewer_filelist = list_filelist;

selection = new Array();

function init() {
    width = window.innerWidth;
    height = window.innerHeight;

    info = document.getElementById( 'info' );
    list = document.getElementById( 'list' );
    main = document.getElementById( 'main' );

    sidebar_w = width / 10;
    if( sidebar_w < 250 ) sidebar_w = 250;

    info.style.width = sidebar_w;
    list.style.width = sidebar_w;
    info.style.height = (height - 60)/2;
    list.style.height = (height - 60)/2;

    main.style.width = width - 20 - sidebar_w;
    main.style.height = height - 60;
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
    load( 'viewer', '/view?id=' + curr );
    load( 'info', '/info?id=' + curr );
}

function group( action ) {
    load( 'info', '/info?id=' + selected + '&action=' + action );
}

function rm() {
    if( confirm( 'Are you sure you want to delete the selected files?' ) ) {
        load( 'info', '/info?id=' + selected + '&action=rm' );
    }
}

function selectfromalbum( cid, fid ) {
    load( 'viewer', '/view?id=' + fid );
    load( 'info', '/info?id=' + fid );
    load( 'list', '/list?mode=album&id=' + cid + '&selected=' + fid );
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

function show_dialog( title, width, height )
{
    overlay = document.getElementById( 'overlay' );
    box = document.getElementById( 'dialogbox' );

    box.style.width = width;
    box.style.height = height;

    box.style.left = (window.innerWidth - width) / 2;
    box.style.top = (window.innerHeight - height) / 2;

    document.getElementById( 'dialogtitle' ).innerHTML = title;

    overlay.style.visibility = 'visible';

    return document.getElementById( 'dialog' );
}

function dismiss_dialog()
{
    overlay.style.visibility = 'hidden';
}

function show_and_load( title, width, height, page )
{
    show_dialog( title, width, height );
    load( 'dialog', page );
}

function dismiss_and_load( div, page )
{
    dismiss_dialog();
    load( div, page );
}

function load( div, page )
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
            show_dialog( 'Error', 800, 400 ).innerHTML = this.responseText;
            return;
        }

        open_view( this.div ).innerHTML = this.responseText;
    }

    r.div = div;

    open_view( div ).innerHTML = '<h1>Loading...</h1>';

    r.open( 'GET', page, true )
    r.send( null );
}

function make_group( type ) {
    this_img = document.forms[0].fid.value;
    parent   = parent.viewer.document.forms[0].fid.value;
    action = "group|" + type + " " + parent;

    location.href = "/view?id=" + this_img + "&secondary=1&action=" + action;
}

document.onkeypress = function( e )
{
    if( document.activeElement.type && document.activeElement.type == 'text' ) return;

    e = window.event || e;

    if( document.getElementById( 'overlay' ).style.visibility == 'visible' ) {
        return;
    }

    switch( e.charCode ) {
        case 116: // t
            if( selection.length > 0 ) {
                show_and_load( 'Tag', 300, 70, '/dialog?kind=tag' );
            }
            break;
        case 114: // r
            if( selection.length == 1 ) {
                show_and_load( 'Rename', 300, 80, '/dialog?kind=rename' );
            }
            break;
        case 65: // A
            select_all();
            break;
        case 97: // a
            resize_image( 0.5 );
            break;
        case 115: // s
            resize_image( 2.0 );
            break;
        case 122: // z
            resize_image( 0 );
            break;
        case 120: // x
            resize_image( -2 );
            break;
        case 99:  // c
            resize_image( -1 );
            break;
        case 106: // j
            nextfile( 1 );
            break;
        case 107: // k
            nextfile( -1 );
            break;
        default:
    }
}

// vim:sts=4:sw=4:et
