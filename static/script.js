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

    selstr = '' + selection[0];

    for( i = 1; i < selection.length; i++ ) {
        selstr += ' ' + selection[i];
    }

    return selstr;
}

function onselectionchanged( prev, curr ) {
    load( 'viewer', '/view?id=' + curr );
    load( 'info', '/info?id=' + getselectionstring() );
}

function group( type ) {
    action = 'group|' + type
    load( 'info', '/info?id=' + getselectionstring() + '&action=' + action );
}

function rm() {
    if( confirm( 'Are you sure you want to delete the selected files?' ) ) {
        load( 'info', '/info?id=' + getselectionstring() + '&action=rm' );
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

function nextfile( id, dir ) {
    current = -1;

    form = document.forms["list"];

    if( form.elements.length == 0 ) return;

    for( i = 0; i < form.elements.length; i++ ) {
        e = form.elements[i];
        if( parseInt( e.value ) == id ) {
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
    if( view == 'viewer2' ) {
        right = document.getElementById( 'right' );
        alert( right.style.visibility );
        if( !right_visible ) {
            main = document.getElementById( 'main' );
            main.style.width = (window.innerWidth - 300)/2;
            right.style.width = (window.innerWidth - 300)/2;
            right.style.visibility = 'visible';
            right_visible = 1;
        }
        return right;
    } else if( view == 'viewer' ) {
        return document.getElementById( 'main' );
    } else if( view == 'main' ) {
        main = document.getElementById( 'main' );
        right = document.getElementById( 'right' );
        if( right_visible ) {
            right.style.visibility = 'hidden';
            main.style.width = window.innerWidth - 300;
            right_visible = 0;
        }
        return main
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

function load( div, page ) {
    r = null;
    if( !window.XMLHttpRequest ) {
        alert( "Unsupported browser" );
        return;
    }

    r = window.XMLHttpRequest();
    r.onreadystatechange = function() {
        if( this.readyState != 4 ) return;

        if( this.status != 200 ) {
            open_view( 'viewer' ).innerHTML = this.responseText;
            return;
        }

        open_view( this.div ).innerHTML = this.responseText;
    }

    r.div = div;

    open_view( div ).innerHTML = '<h1>Loading...</h1>';

    r.open( 'GET', page, true )
    r.send( null );
}

function resize_image( im ) {
    if( right_visible ) {
        max_width = (window.innerWidth - 300) / 2;
    } else {
        max_width = window.innerWidth - 300;
    }

    max_height = window.innerHeight - 100;

    if( im.width > max_width ) {
        h = im.height * max_width / im.width;
        if( h > max_height ) {
            im.height = max_height;
        } else {
            im.width = max_width;
        }
    } else if( im.height > max_height ) {
        im.height = max_height;
    }
}

function make_group( type ) {
    this_img = document.forms[0].fid.value;
    parent   = parent.viewer.document.forms[0].fid.value;
    action = "group|" + type + " " + parent;

    location.href = "/view?id=" + this_img + "&secondary=1&action=" + action;
}
