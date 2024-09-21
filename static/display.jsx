// module
var util = (function() {

function public_make_basic_drop_data( disp, obj_id, repr, type )
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

function public_make_group_drop_data( disp, obj_id, files, repr, type )
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

function public_make_draggable( elem, drop_data )
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

function public_make_sortable( disp, elem, index )
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

function public_make_link( repr, target, ext_actions )
{
    main_action = function( e ) {
        var target = $( this ).data( 'target' );
        var repr = $( this ).data( 'repr' );

        var provider = new tabs.SingleProvider( target );
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

function public_make_link2( pair, ext_actions )
{
    return public_make_link( pair[1], pair[0], ext_actions );
};

function public_make_link_list( list, ext_actions )
{
    if( list.length == 0 ) return;

    var span = $( '<span></span>' );
    span.append( public_make_link2( list[0], ext_actions ) );

    for( var i = 1; i < list.length; i++ ) {
        span.append( ', ' );
        span.append( public_make_link2( list[i], ext_actions ) );
    }

    return span;
};

return {
    make_basic_drop_data: public_make_basic_drop_data,
    make_group_drop_data: public_make_group_drop_data,
    make_draggable: public_make_draggable,
    make_sortable: public_make_sortable,
    make_link: public_make_link,
    make_link2: public_make_link2,
    make_link_list: public_make_link_list,
};
})(); // module util

// module
var displib = (function() {

/**
 * class DisplayableBase
 */
class DisplayableBase
{
    constructor()
    {
        this.change_listeners = [];
    }

    is_sortable()
    {
        return false;
    }

    set_field( field, value )
    {}

    set_variant( original, variant )
    {}

    clear_variant( original, variant )
    {}

    link_duplicates( original, duplicate )
    {}

    unlink_duplicates( original, duplicate )
    {}

    transform( xform )
    {}

    reorder( drop_data, idx )
    {}

    show_stream( stream_id )
    {}

    set_as_main_stream()
    {}

    on_event( e )
    { return null; }

    refresh_info( e )
    {}

    get_obj_id()
    { return null; }

    get_files()
    { return []; }

    create_provider( args )
    { return null; }

    register_change_listener( listener )
    {
        this.change_listeners.push( listener );
    }

    unregister_change_listener( listener )
    {
        var i = this.change_listeners.indexOf( listener );
        this.change_listeners.splice( i, 1 );
    }

    notify_change( e )
    {
        for( var i = 0; i < this.change_listeners.length; i++ ) {
            this.change_listeners[i].on_displayable_changed( this, e );
        }
    }
}

/**
 * class DisplayableObject
 */
class DisplayableObject extends DisplayableBase
{
    constructor( obj_id, info, fields )
    {
        super();

        this.type = 'object';
        this.obj_id = obj_id;
        this.stream_id = null;
        this.info = info;
        this.fields = fields;
    }

    is_sortable()
    {
        return this.info.type == 'album';
    }

    rename( name, saveold )
    {
        var request = {
            'action' : 'rename',
            'target' : this.obj_id,
            'name' : name,
        };

        if( saveold ) {
            request.saveold = true;
        }
        load_sync( request );
        tabs.on_event( { type: 'info_changed', affected: [ this.obj_id ] } );
    }

    tag( tags )
    {
        var request = {
            'action' : 'tag',
            'targets' : [ this.obj_id ],
            'query' : tags,
        };
        var response = load_sync( request );

        if( response.result == 'ok' ) {
            tabs.on_event( { type: 'info_changed', affected: [ this.obj_id ] } );
            return { result: 'ok' };
        } else {
            return response;
        }
    }

    rm_group()
    {
        var request = {
            action:     'group_delete',
            group:      this.obj_id,
        };

        load_sync( request );
        tabs.on_event( { type: 'info_changed', affected:
                this.obj_id_list() } );
        tabs.on_event( { type: 'removed', affected:
                [ this.obj_id ] } );
    }

    gather_tags()
    {
        var request = {
            action:     'gather_tags',
            target:     this.obj_id,
        };

        load_sync( request );

        var affected = null;
        if( this.info.type == 'file') {
            affected = [ this.obj_id ];
        } else {
            affected = this.obj_id_list();
            affected.push( this.obj_id );
        }

        tabs.on_event( { type: 'info_changed', affected: affected } );
    }

    reorder( drop_data, idx )
    {
        var files = drop_data.get_files()

        var src_idxs = []
        var src_objs = []

        for( var i = 0; i < files.length; i++ ) {
            var src_idx = this.find_item( files[i][0] );
            if( src_idx == -1 ) {
                alert( files[i][1] + ' not in album' );
                return;
            }

            src_idxs.push( src_idx );
        }

        src_idxs.sort();
        for( var i = 0; i < src_idxs.length; i++ ) {
            src_objs.push( this.info.files[src_idxs[i]] )
        }

        var output = []
        for( var i = 0; i < this.info.files.length; i++ ) {
            if( i == idx ) {
                for( var j = 0; j < src_objs.length; j++ ) {
                    output.push( src_objs[j] );
                }
            }

            if( src_idxs.indexOf( i ) >= 0 ) continue;
            output.push( this.info.files[i] );
        }

        var changed = false;
        for( var i = 0; i < this.info.files.length; i++ ) {
            if( this.info.files[i][0] != output[i][0] ) {
                changed = true;
                break;
            }
        }
        if( !changed ) return;

        this.info.files = output;
        var obj_ids = this.obj_id_list();
        var request = {
            action:     'group_reorder',
            group:      this.obj_id,
            items:      obj_ids,
        };
        load_sync( request );
        tabs.on_event( { type: 'files_changed', affected:
                [ this.obj_id ] } );
    }

    set_field( field, value )
    {
        var request = {
            action:     'set_field',
            target:     this.obj_id,
            field:      field,
            value:      value,
        };

        load_sync( request );
        tabs.on_event( { type: 'info_changed', affected: [ this.obj_id, ] } );
    }

    set_variant( original, variant )
    {
        var request = {
            action:     'link_files',
            original:   original,
            variant:    variant,
        };

        load_sync( request );
        tabs.on_event( { type: 'info_changed', affected: [ original, variant ] } );
    }

    clear_variant( original, variant )
    {
        var request = {
            action:     'clear_variant',
            original:   original,
            variant:    variant,
        };

        load_sync( request );
        tabs.on_event( { type: 'info_changed', affected: [ original, variant ] } );
    }

    link_duplicates( original, duplicate )
    {
        var request = {
            action:         'link_files',
            original:       original,
            variant:        duplicate,
            is_duplicate:   true,
        };

        load_sync( request );
        tabs.on_event( { type: 'info_changed', affected: [ original, duplicate ] } );
    }

    unlink_duplicate( original, duplicate )
    {
        var request = {
            action:         'unlink_files',
            original:       original,
            variant:        duplicate,
        };

        load_sync( request );
        tabs.on_event( { type: 'info_changed', affected: [ original, duplicate ] } );
    }

    transform( xform )
    {
        if( this.info.type != 'file') {
            return;
        }

        var request = {
            action:     xform,
            target:     this.obj_id,
        };
        load_sync( request );
        tabs.on_event( { type: 'files_changed', affected:
                [ this.obj_id ] } );
    }

    show_stream( stream_id )
    {
        this.stream_id = stream_id;
        this.refresh_info( { type: 'files_changed', affected:
                [ this.obj_id ] } );
    }

    set_as_main_stream()
    {
        var request = {
            action: 'set_root_stream',
            target: this.obj_id,
            stream: this.stream_id,
        };
        load_sync( request );

        this.stream_id = null;
        tabs.on_event( { type: 'files_changed', affected:
                [ this.obj_id ] } );
    }

    on_event( e )
    {
        if( e.affected && e.affected.indexOf( this.obj_id ) == -1 ) {
            return;
        }
        
        if( e.type == 'key' ) {
            switch( e.charCode ) {
                case 116: // t
                    dialogs.show_tag_dialog( this );
                    break;
                case 110: // n
                    dialogs.show_name_dialog( this );
                    break;
                case 114: // r
                    this.refresh_info( e );
                    break;
                case 49: // 1
                case 50: // 2
                case 51: // 3
                case 52: // 4
                case 53: // 5
                case 54: // 6
                case 55: // 7
                case 56: // 8
                case 57: // 9
                    this.on_event( { type: 'push_selection', selection: e.charCode - 49 } )
                    break;
                case 48: // 0
                    this.on_event( { type: 'push_selection', selection: 10 } )
                    break;
                default:
                    break;
            }
            return;
        } else if( e.type == 'drop' ) {
            var disp = e.drop_data.get_display();
            var obj_id = e.drop_data.get_object()
            var repr = e.drop_data.get_repr()
            var type = e.drop_data.get_type()

            if( this.info.type == 'file') {
                if( obj_id == this.obj_id ) {
                    alert( 'Cannot drop file on itself' );
                    return;
                } else if( type != 'file' ) {
                    alert( 'Only a file may be dropped on a file' );
                    return;
                }

                dialogs.show_dup_dialog( this, obj_id, this.obj_id );
            } else if( this.info.type == 'album' ) {
                if( type != 'file' && type != 'selection' ) {
                    alert( 'Only files may be added to albums' );
                    return;
                }

                var to_append = []
                var files = e.drop_data.get_files()

                var changed = false;
                for( var i = 0; i < files.length; i++ ) {
                    var obj_id = files[i][0];

                    if( this.find_item( obj_id ) != -1 ) continue;
                    to_append.push( obj_id );
                    changed = true;
                }
                if( !changed ) {
                    alert( 'Already in album' );
                    return;
                }

                var request = {
                    action:     'group_append',
                    group:      this.obj_id,
                    targets:    to_append,
                };

                load_sync( request );
                tabs.on_event( { type: 'files_changed', affected:
                        [ this.obj_id ] } );
                tabs.on_event( { type: 'info_changed', affected:
                        [ obj_id ] } );

                if( disp ) {
                    disp.on_event( {
                            type: 'dropped',
                            drop_target: this,
                            drop_method: e.drop_method,
                            drop_data: e.drop_data,
                        } );
                }
            } else if( this.info.type == 'published' ) {
                alert( 'Published albums may not be modified' );
            }
        } else if( e.type == 'trash' ) {
            var obj_id = e.drop_data.get_object()
            var repr = e.drop_data.get_repr()
            var type = e.drop_data.get_type()

            if( this.info.type == 'file') {
                alert( 'delete ' + repr );
            } else if( this.info.type == 'album' || this.info.type == 'published' ) {

                if( this.info.type == 'published'
                 && !confirm( 'Are you sure you want to remove this published album?' ) )
                {
                    return;
                }

                if( obj_id == this.obj_id ) {
                    this.rm_group();
                    return;
                } else if( this.find_item( obj_id ) == -1 ) {
                    alert( repr + ' not in album' );
                    return;
                }

                var targets = e.drop_data.get_files().map( ( it ) => {
                                    return it[0];
                                } )

                var request = {
                    action:     'group_remove',
                    group:      this.obj_id,
                    targets:    targets
                };

                load_sync( request );
                tabs.on_event( { type: 'files_changed', affected:
                        [ this.obj_id ] } );
                tabs.on_event( { type: 'info_changed', affected:
                        [ obj_id ].concat( targets ) } );
            }
        } else if( e.type == 'replaced' ) {
            this.obj_id = e.new_id;
        } else if( e.type == 'info_changed' ) {
            this.refresh_info( e );
        } else if( e.type == 'files_changed' ) {
            this.refresh_info( e );
        } else if( e.type == 'push_selection' ) {
            var selection = displib.get_selection( e.selection );
            if( selection == null ) return;

            selection.on_event( {
                type: 'drop',
                drop_data: util.make_basic_drop_data( this,
                                this.obj_id,
                                this.info.repr,
                                this.info.type )
            } );
        }
    }

    refresh_info( e )
    {
        var request = {
            action:     'info',
            target:     this.obj_id,
            items:      tabs.get_info_set(),
            fields:     tabs.get_field_set(),
        };
        
        var response = load_sync( request );
        this.info = response.info;
        this.fields = response.fields;

        this.notify_change( e );
    }

    find_item( obj_id )
    {
        for( var i = 0; i < this.info.files.length; i++ ) {
            if( this.info.files[i][0] == obj_id ) {
                return i;
            }
        }
        return -1;
    }

    obj_id_list()
    {
        var obj_ids = [];

        for( var i = 0; i < this.info.files.length; i++ ) {
            obj_ids.push( this.info.files[i][0] );
        }

        return obj_ids;
    }

    get_obj_id()
    {
        return this.obj_id;
    }

    get_files()
    {
        return this.info.files;
    }

    create_provider( args )
    {
        if( this.info.type == 'album'
         || this.info.type == 'published' )
        {
            var search_args = {
                mode: 'album',
                album: this.obj_id,
            }

            if( args && args.start_id ) {
                var start_idx = this.info.files.findIndex( ( it ) =>
                                        { return it[0] == args.start_id; } );
                if( start_idx >= 0 ) {
                    search_args.index = start_idx;
                }
            }

            return new tabs.SearchProvider( search_args );
        } else {
            return new tabs.SingleProvider( this.obj_id );
        }
    }
}

/**
 * class DisplayableSelection
 */
class DisplayableSelection extends DisplayableBase
{
    constructor()
    {
        super();

        this.type = 'selection';
        this.objs = [];
    }

    is_sortable()
    { return true; }

    tag( tags )
    {
        var targets = this.obj_id_list();
        var request = {
            'action' : 'tag',
            'targets' : targets,
            'query' : tags,
        };
        var response = load_sync( request );

        if( response.result == 'ok' ) {
            tabs.on_event( { type: 'info_changed', affected: targets } );
            return { result: 'ok' };
        } else {
            return response;
        }
    }

    make_group()
    {
        if( this.objs.length == 0 ) {
            alert( 'No objects selected' );
            return;
        }

        var targets = this.obj_id_list();
        var request = {
            action:     'group_create',
            targets:    targets,
        };

        var response = load_sync( request );
        var provider = new tabs.SingleProvider( response.group );
        tabs.create_display_tab( 'New Album', provider );
        tabs.on_event( { type: 'info_changed', affected: targets } );
    }

    sort_by_id()
    {
        this.objs.sort( function( a, b ) {
            return a[0] - b[0];
        });

        this.notify_change( null );
    }

    sort_by_name()
    {
        this.objs.sort( function( a, b ) {
            return a[1].localeCompare( b[0] );
        });

        this.notify_change( null );
    }

    reverse_sort()
    {
        this.objs.reverse();
        this.notify_change( null );
    }

    reorder( drop_data, idx )
    {
        var files = drop_data.get_files()

        var src_idxs = []
        var src_objs = []

        for( var i = 0; i < files.length; i++ ) {
            var src_idx = this.find_item( files[i][0] );
            if( src_idx == -1 ) {
                alert( files[i][1] + ' not in selection' );
                return;
            }

            src_idxs.push( src_idx );
        }

        src_idxs.sort();
        for( var i = 0; i < src_idxs.length; i++ ) {
            src_objs.push( this.objs[src_idxs[i]] )
        }

        var output = []
        for( var i = 0; i < this.objs.length; i++ ) {
            if( i == idx ) {
                for( var j = 0; j < src_objs.length; j++ ) {
                    output.push( src_objs[j] );
                }
            }

            if( src_idxs.indexOf( i ) >= 0 ) continue;
            output.push( this.objs[i] );
        }

        var changed = false;
        for( var i = 0; i < this.objs.length; i++ ) {
            if( this.objs[i][0] != output[i][0] ) {
                changed = true;
                break;
            }
        }
        if( !changed ) return;

        this.objs = output;
        this.notify_change( null );
    }

    on_event( e )
    {
        if( e.type == 'key' ) {
            switch( e.charCode ) {
                case 116: // t
                    dialogs.show_tag_dialog( this );
                    break;
                default:
                    break;
            }
            return;
        } else if( e.type == 'drop' ) {
            var disp = e.drop_data.get_display();
            var files = e.drop_data.get_files();
            var repr = e.drop_data.get_repr();
            var type = e.drop_data.get_type();

            var changed = false;
            for( var i = 0; i < files.length; i++ ) {
                if( this.find_item( files[i][0] ) != -1 ) continue;
                this.objs.push( files[i] );
                changed = true;
            }
            if( !changed ) return;

            this.notify_change( null );
            if( disp ) {
                disp.on_event( {
                        type: 'dropped',
                        drop_target: this,
                        drop_method: e.drop_method,
                        drop_data: e.drop_data,
                    } );
            }
        } else if( e.type == 'trash'
                || (e.type == 'dropped'
                    && e.drop_method == 'move') )
        {
            var files = e.drop_data.get_files();
            var removed = false;

            for( var i = 0; i < files.length; i++ ) {
                var index = this.find_item( files[i][0] );
                if( index == -1 ) continue;
                this.objs.splice( index, 1 );
                removed = true;
            }

            if( removed ) {
                this.notify_change( null );
            }
        }
    }

    find_item( obj_id )
    {
        for( var i = 0; i < this.objs.length; i++ ) {
            if( this.objs[i][0] == obj_id ) {
                return i;
            }
        }
        return -1;
    }

    obj_id_list()
    {
        var obj_ids = [];

        for( var i = 0; i < this.objs.length; i++ ) {
            obj_ids.push( this.objs[i][0] );
        }

        return obj_ids;
    }

    get_files()
    {
        return this.objs;
    }

    create_provider( args )
    {
        var provider = new tabs.ListProvider( this.objs );

        if( args && args.start_id ) {
            provider.obj_id = args.start_id;
        }

        return provider;
    }
}

/**
 * class ViewBase
 */
class ViewBase
{
    display_view( disp, div ) 
    {
        div.html( '&nbsp;' );
    }

    on_event( e )
    {}
}

class HtmlView extends ViewBase
{
    constructor( html )
    {
        super();
        this.html = html;
    }

    display_view( disp, div )
    {
        div.html( this.html );
    }
}

/**
 * class ImageView
 */
class ImageView extends ViewBase
{
    constructor()
    {
        super();
        this.viewer = null;
    }

    display_view( disp, div )
    {
        div.html( '' );

//        if( !disp.info.mime ) {
//            div.append( 'Image not available<br/>' );
//            return;
//        }

        var image_info = {
            obj_id: disp.obj_id,
            repr: disp.info.repr,
            type: disp.info.type,
            gen: disp.info.thumb_gen,
        };

        if( disp.stream_id !== null ) {
            image_info.stream_id = disp.stream_id;
        } else {
            image_info.sizes = disp.info.sizes;
        }

        this.viewer = attach_image( div, image_info );

        div.append( '<br/>' );
    }

    on_event( e )
    {
        if( !this.viewer ) {
            return;
        }

        if( e.type == 'key' ) {
            switch( e.charCode ) {
                case 97: // a
                    this.on_event( { type: 'zoom', zoom: -0.5 } )
                    break;
                case 115: // s
                    this.on_event( { type: 'zoom', zoom: -2.0 } )
                    break;
                case 122: // z
                    this.on_event( { type: 'zoom', zoom: 1.0 } )
                    break;
                case 120: // x
                    this.on_event( { type: 'zoom', zoom: 'fit_outside' } )
                    break;
                case 99:  // c
                    this.on_event( { type: 'zoom', zoom: 'fit_inside' } )
                    break;
                default:
                    break;
            }
        } else if( e.type == 'resized' || e.type == 'focused' ) {
            this.viewer.refresh();
        } else if( e.type == 'zoom' ) {
            this.viewer.set_zoom( e.zoom );
        }
    }
}

class ThumbView extends ViewBase
{
    constructor()
    {
        super();

        this.selection = [];
        this.type = 'thumb';
        this.pane = null;
    }

    on_event( e )
    {
        if( this.pane ) {
            this.pane.onEvent( e );
        }
    }
}

var make_file_display = function( obj_id, info, fields )
{
    return {
        disp: new DisplayableObject( obj_id, info, fields ),
        view: new ImageView()
    }
};

var make_group_display = function( obj_id, info, fields )
{
    return {
        disp: new DisplayableObject( obj_id, info, fields ),
        view: new ThumbView()
    }
};

var public_make_dummy_display = function( msg )
{
    return {
        disp: new DisplayableBase(),
        view: new HtmlView( '<p>' + msg + '</p>')
    }
};

/**
 * make_object_display( obj_id ) - factory method for creating
 * the appropriate display.
 */
var public_make_object_display = function( info, fields )
{
    if( info.type == 'file'
     || info.type == 'duplicate' )
    {
        return make_file_display( info.object_id, info, fields );
    } else if( info.type == 'album'
            || info.type == 'published' )
    {
        return make_group_display( info.object_id, info, fields );
    } else {
        return public_make_dummy_display( 'This is a placeholder for an object '
            + 'that does not exist or has been removed.' );
    }
};

/**
 * make_selection_display()
 */
var public_make_selection_display = function()
{
    return {
        disp: new DisplayableSelection(),
        view: new ThumbView()
    }
};

var public_register_selection = function( selection )
{
    var i = 0;
    for( var i = 0; i < this.selection_map.length; i++ ) {
        if( this.selection_map[i] == null ) {
            this.selection_map[i] = selection;
            return i;
        }
    }

    this.selection_map.push( selection );
    return i;
};

var public_unregister_selection = function( selection )
{
    for( var i = 0; i < this.selection_map.length; i++ ) {
        if( this.selection_map[i] === selection ) {
            this.selection_map[i] = null;
        }
    }
};

var public_get_selection = function( idx )
{
    if( this.selection_map.length > idx ) {
        return this.selection_map[idx];
    } else {
        return null;
    }
}

return {
    selection_map: [],
    make_dummy_display: public_make_dummy_display,
    make_object_display: public_make_object_display,
    make_selection_display: public_make_selection_display,
    register_selection: public_register_selection,
    unregister_selection: public_unregister_selection,
    get_selection: public_get_selection,
};

})(); // module displib

window.util = util;
window.displib = displib;
