import $ from 'jquery';
import 'jquery-ui/ui/widgets/draggable';

import * as tabs from './controllers/tabs';

import { SingleProvider } from './models/providers';

export function make_basic_drop_data( disp, obj_id, repr, type )
{
    return {
        disp:   disp,
        obj_id: obj_id,
        repr:   repr,
        type:   type,

        get_display: function() { return this.disp; },
        get_object: function() { return this.obj_id; },
        get_files: function() { return [ [ this.obj_id, this.repr, this.type ] ]; },
        get_repr:   function() { return this.repr; },
        get_type:   function() { return this.type; }
    };
}

export function make_group_drop_data( disp, obj_id, files, repr, type )
{
    return {
        disp:   disp,
        obj_id: obj_id,
        files:  files,
        repr:   repr,
        type:   type,

        get_display: function() { return this.disp; },
        get_object: function() { return this.obj_id; },
        get_files: function() { return this.files; },
        get_repr:   function() { return this.repr; },
        get_type:   function() { return this.type; }
    };
}

export function make_draggable( elem, drop_data )
{
    elem.data( 'drop_data', drop_data );

    elem.draggable( {
        helper:     function() {
            var orig = $( this );
            var clone = orig.clone();

            // FIXME: bugfix to prevent clone from calling onload which
            // causes whacky image resizing when the dragable is created
            clone[0].onload = null;
            return clone;
        },
        appendTo:   $( '#page' ),
        //helper:     'clone',
        //cursor:     'move',
        opacity:    0.3,
        distance:   30,
        start: function( event, ui ) {
            $( this ).draggable("option", "cursorAt", {
                left:   Math.floor( ui.helper.width() / 2 ),
                top:    Math.floor( ui.helper.height() / 2 )
            });
        },
        /*stop: function( event, ui ) {
            alert( ui.helper[0].width );
        },*/
    });
};

export function make_sortable( disp, elem, index )
{
    elem.droppable({
        accept: '.sortable',
        hoverClass: 'hover',
        drop: function( event, ui ) {
            if( ui.helper.is( '.dropped' ) ) {
                return false;
            }

            var slot = $( this );
            var item = $( ui.draggable );

            var display = slot.data( 'display' );
            var index = slot.data( 'index' );
            var drop_data = item.data( 'drop_data' );

            display.reorder( drop_data, index );

            ui.helper.addClass( 'dropped' );
        },
    });
    elem.data( 'display', disp );
    elem.data( 'index', index );
};

function private_make_link( repr, target, extra, action )
{
    var label = $( '<a href="#">' + repr + '</a>' );
    label.data( 'repr', repr );
    label.data( 'target', target );
    if( extra !== null ) {
        label.data( 'extra', extra );
    }

    label.click( action );

    return label;
}

export function make_link( repr, target, ext_actions )
{
    main_action = function( e ) {
        var target = $( this ).data( 'target' );
        var repr = $( this ).data( 'repr' );

        var provider = new SingleProvider( target );
        tabs.create_display_tab( repr, provider );
    }

    if( typeof ext_actions !== 'undefined' && ext_actions.length > 0 ) {
        var span = $( '<span></span>' )
        span.append( private_make_link( repr, target, null, main_action ) );
        span.append( ' (' )
        span.append( private_make_link( ext_actions[0].label,
                                        target,
                                        ext_actions[0].extra,
                                        ext_actions[0].action ) );
        for( var i = 1; i < ext_actions.length; i++ ) {
            span.append( ', ' );
            span.append( private_make_link( ext_actions[i].label,
                                            target,
                                            ext_actions[i].extra,
                                            ext_actions[i].action ) );
        }
        span.append( ')' )

        return span;
    } else {
        return private_make_link( repr, target, null, main_action );
    }
};

export function make_link2( pair, ext_actions )
{
    return make_link( pair[1], pair[0], ext_actions );
};

export function make_link_list( list, ext_actions )
{
    if( list.length == 0 ) return;

    var span = $( '<span></span>' );
    span.append( make_link2( list[0], ext_actions ) );

    for( var i = 1; i < list.length; i++ ) {
        span.append( ', ' );
        span.append( make_link2( list[i], ext_actions ) );
    }

    return span;
};
