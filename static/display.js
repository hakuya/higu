// module
var util = (function() {

function public_make_draggable( elem, obj_id, repr, type )
{
    elem.data( 'obj_id', obj_id );
    elem.data( 'repr', repr );
    elem.data( 'type', type );

    elem.draggable( {
        helper:     function() {
            orig = $( this );
            clone = orig.clone();

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
            slot = $( this );
            item = $( ui.draggable );

            display = slot.data( 'display' );
            index = slot.data( 'index' );
            obj_id = item.data( 'obj_id' );

            display.reorder( obj_id, index );
        },
    });
    elem.data( 'display', disp );
    elem.data( 'index', index );
};

function private_make_link( repr, target, extra, action )
{
    label = $( '<a href="#">' + repr + '</a>' );
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
        target = $( this ).data( 'target' );
        repr = $( this ).data( 'repr' );

        provider = new tabs.SingleProvider( target );
        tabs.create_display_tab( repr, provider );
    }

    if( typeof ext_actions !== 'undefined' && ext_actions.length > 0 ) {
        span = $( '<span></span>' )
        span.append( private_make_link( repr, target, null, main_action ) );
        span.append( ' (' )
        span.append( private_make_link( ext_actions[0].label,
                                        target,
                                        ext_actions[0].extra,
                                        ext_actions[0].action ) );
        for( i = 1; i < ext_actions.length; i++ ) {
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

    span = $( '<span></span>' );
    span.append( public_make_link2( list[0], ext_actions ) );

    for( i = 1; i < list.length; i++ ) {
        span.append( ', ' );
        span.append( public_make_link2( list[i], ext_actions ) );
    }

    return span;
};

return {
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
DisplayableBase = function()

    // Constructor
    {
        this.change_listeners = [];
    };

    DisplayableBase.prototype.tag = function( tags )
    {
        return { result: 'notimpl' };
    };

    DisplayableBase.prototype.rename = function( name, saveold ) {};
    DisplayableBase.prototype.drop = function( obj_id, repr, type ) {};
    DisplayableBase.prototype.rm = function( obj_id, repr, type ) {};
    DisplayableBase.prototype.set_variant = function(
            original, variant ) {}
    DisplayableBase.prototype.clear_variant = function(
            original, variant ) {}
    DisplayableBase.prototype.merge_duplicates = function(
            original, duplicate ) {}
    DisplayableBase.prototype.rotate = function( rot ) {};
    DisplayableBase.prototype.reorder = function( obj_id, idx ) {};
    DisplayableBase.prototype.on_event = function( e ) { return null; };
    DisplayableBase.prototype.refresh_info = function( e ) {};

    DisplayableBase.prototype.display_info = function( div )
    {
        div.html( '&nbsp;' );
    };

    DisplayableBase.prototype.get_obj_id = function() { return null; };
    DisplayableBase.prototype.get_files = function() { return []; };

    DisplayableBase.prototype.register_change_listener = function( listener )
    {
        this.change_listeners.push( listener );
    };

    DisplayableBase.prototype.notify_change = function( e )
    {
        for( var i = 0; i < this.change_listeners.length; i++ ) {
            this.change_listeners[i].on_displayable_changed( this, e );
        }
    };

/**
 * class DisplayableObject
 */
DisplayableObject = function( obj_id, info )

    // Constructor
    {
        DisplayableBase.call( this );

        this.obj_id = obj_id;
        this.info = info;
    };

    // extends Displayable
    DisplayableObject.prototype = new DisplayableBase();
    DisplayableObject.prototype.constructor = DisplayableObject;

    DisplayableObject.prototype.rename = function( name, saveold )
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
    };

    DisplayableObject.prototype.tag = function( tags )
    {
        var request = {
            'action' : 'tag',
            'targets' : [ this.obj_id ],
            'query' : tags,
        };
        response = load_sync( request );

        if( response.result == 'ok' ) {
            tabs.on_event( { type: 'info_changed', affected: [ this.obj_id ] } );
            return { result: 'ok' };
        } else {
            return response;
        }
    };

    DisplayableObject.prototype.drop = function( obj_id, repr, type )
    {
        if( this.info.type == 'file') {
            if( obj_id == this.obj_id ) {
                alert( 'Cannot drop file on itself' );
                return;
            } else if( type != 'file' ) {
                alert( 'Only a file may be dropped on a file' );
                return;
            }

            dialogs.show_dup_dialog( obj_id, this.obj_id );
        } else {
            if( this.find_item( obj_id ) != -1 ) {
                alert( repr + ' already in album' );
            } else if( type != 'file' ) {
                alert( 'Only files may be added to albums' );
            }

            var request = {
                action:     'group_append',
                group:      this.obj_id,
                targets:    [ obj_id ],
            };

            load_sync( request );
            tabs.on_event( { type: 'files_changed', affected:
                    [ this.obj_id ] } );
            tabs.on_event( { type: 'info_changed', affected:
                    [ obj_id ] } );
        }
    };

    DisplayableObject.prototype.rm = function( obj_id, repr, type )
    {
        if( this.info.type == 'file') {
            alert( 'delete ' + repr );
        } else {
            if( obj_id == this.obj_id ) {
                this.rm_group();
                return;
            } else if( this.find_item( obj_id ) == -1 ) {
                alert( repr + ' not in album' );
                return;
            }

            var request = {
                action:     'group_remove',
                group:      this.obj_id,
                targets:    [ obj_id ],
            };

            load_sync( request );
            tabs.on_event( { type: 'files_changed', affected:
                    [ this.obj_id ] } );
            tabs.on_event( { type: 'info_changed', affected:
                    [ obj_id ] } );
        }
    };

    DisplayableObject.prototype.rm_group = function()
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
    };

    DisplayableObject.prototype.gather_tags = function()
    {
        var request = {
            action:     'gather_tags',
            target:     this.obj_id,
        };

        load_sync( request );
        if( this.info.type == 'file') {
            affected = [ this.obj_id ];
        } else {
            affected = this.obj_id_list();
            affected.push( this.obj_id );
        }

        tabs.on_event( { type: 'info_changed', affected: affected } );
    };

    DisplayableObject.prototype.reorder = function( obj_id, idx )
    {
        src_idx = this.find_item( obj_id )
        if( src_idx == -1 ) {
            alert( obj_id + ' not in album' );
            return;
        } else if( src_idx == idx ) {
            // Do nothing
            return;
        }

        obj = this.info.files[src_idx];

        this.info.files.splice( src_idx, 1 );
        if( idx < src_idx ) {
            this.info.files.splice( idx, 0, obj );
        } else {
            this.info.files.splice( idx - 1, 0, obj );
        }

        obj_ids = this.obj_id_list();
        var request = {
            action:     'group_reorder',
            group:      this.obj_id,
            items:      obj_ids,
        };
        load_sync( request );
        tabs.on_event( { type: 'files_changed', affected:
                [ this.obj_id ] } );
    };

    DisplayableObject.prototype.set_variant = function(
            original, variant )
    {
        var request = {
            action:     'set_variant',
            original:   original,
            variant:    variant,
        };

        load_sync( request );
        tabs.on_event( { type: 'info_changed', affected: [ original, variant ] } );
    };

    DisplayableObject.prototype.clear_variant = function(
            original, variant )
    {
        var request = {
            action:     'clear_variant',
            original:   original,
            variant:    variant,
        };

        load_sync( request );
        tabs.on_event( { type: 'info_changed', affected: [ original, variant ] } );
    };

    DisplayableObject.prototype.merge_duplicates = function(
            original, duplicate )
    {
        var request = {
            action:     'merge_duplicates',
            original:   original,
            duplicate:  duplicate,
        };

        load_sync( request );
        tabs.on_event( { type: 'info_changed', affected: [ original ] } );
        tabs.on_event( { type: 'removed', affected: [ duplicate ] } );
    };

    DisplayableObject.prototype.rotate = function( rot )
    {
        if( this.info.type != 'file') {
            return;
        }

        var request = {
            action:     'rotate',
            target:     this.obj_id,
            rot:        rot,
        };
        load_sync( request );
        tabs.on_event( { type: 'files_changed', affected:
                [ this.obj_id ] } );
    };

    DisplayableObject.prototype.on_event = function( e )
    {
        if( e.affected && e.affected.indexOf( this.obj_id ) == -1 ) {
            return;
        }
        
        if( e.type == 'info_changed' ) {
            this.refresh_info( e );
        } else if( e.type == 'files_changed' ) {
            this.refresh_info( e );
        }
    };

    DisplayableObject.prototype.refresh_info = function( e )
    {
        var request = {
            action:     'info',
            targets:    [ this.obj_id ],
            items:      [ 'type', 'repr', 'tags', 'names',
                'variants', 'variants_of', 'dup_streams',
                'albums', 'files', 'text', 'thumb_gen',
                'width', 'height', 'creation_time' ],
        };
        
        response = load_sync( request );
        this.info = response.info[0];

        this.notify_change( e );
    };

    DisplayableObject.prototype.display_info = function( div )
    {
        div.html( '' );

        var label = $( '<div class="objlabel objitem"></div>' );
        label.append( util.make_link( this.info.repr, this.obj_id ) );
        util.make_draggable( label, this.obj_id, this.info.repr, this.info.type );

        div.append( label );
        div.append( '<br/>' );

        /* Display album info?
    #        if( isinstance( obj, higu.Album ) ):
    #
    #            html.header( 'Files' )
    #            fs = obj.get_files()
    #            html.list( '<a href="javascript:selectfromalbum( %d, %d )">%s</a>', fs,
    #                    lambda x: ( obj.get_id(), x.get_id(), x.get_repr(), ) )
        */

        div.append( '<h1>Tags</h1>' );
        div.append( "<ul class='infotaglist'></ul>" );
        var ls = div.find( '.infotaglist' );

        for( i = 0; i < this.info.tags.length; i++ ) {
            var li = TAGLINK_TEMPLATE.replace( /#\{tag\}/g, this.info.tags[i]);
            ls.append( li );
        }

        div.append( '<h1>Names</h1>' );
        div.append( "<ul class='infonamlist'></ul>" );
        ls = div.find( '.infonamlist' );

        for( i = 0; i < this.info.names.length; i++ ) {
            var li = '<li>' + this.info.names[i] + '</li>'
            ls.append( li );
        }

        if( this.info.type == 'file') {
            this.display_file_info( div );
        } else {
            this.display_group_info( div );
        }
    };

    DisplayableObject.prototype.display_file_info = function( div )
    {
        div.append( 'Size: ' + this.info.width + 'x' + this.info.height + '<br/>' );
        if( this.info.creation_time !== null ) {
            div.append( 'Created: ' + this.info.creation_time + '<br/>' );
        }

        if( this.info.albums && this.info.albums.length > 0 ) {
            div.append( 'Albums: ' );
            div.append( util.make_link_list( this.info.albums ) );
            div.append( '<br/>' );
        }

        if( this.info.variants_of && this.info.variants_of.length > 0 ) {
            rem_variant_of_action = function( e ) {
                target = $( this ).data( 'target' );
                extra = $( this ).data( 'extra' );
                extra.obj.clear_variant( target, extra.obj.obj_id );
            }

            actions = [ { label: 'del',
                          extra: { obj: this, },
                          action: rem_variant_of_action, } ]

            div.append( 'Variant of: ' );
            div.append( util.make_link_list( this.info.variants_of, actions ) );
            div.append( '<br/>' );
        }

        if( this.info.variants && this.info.variants.length > 0 ) {
            rem_variant_action = function( e ) {
                target = $( this ).data( 'target' );
                extra = $( this ).data( 'extra' );
                extra.obj.clear_variant( extra.obj.obj_id, target );
            }

            actions = [ { label: 'del',
                          extra: { obj: this, },
                          action: rem_variant_action, } ]

            div.append( 'Variants: ' );
            div.append( util.make_link_list( this.info.variants, actions ) );
            div.append( '<br/>' );
        }

        div.append( 'Rotate: ' );
        var rotate_ccw = $( '<a href="#">ccw</a>' );
        rotate_ccw.data( 'obj', this );
        rotate_ccw.click( function( e ) {
            obj = $( this ).data( 'obj' );
            obj.rotate( -1 );
        });
        div.append( rotate_ccw );
        div.append( ', ' );
        var rotate_cw = $( '<a href="#">cw</a>' );
        rotate_cw.data( 'obj', this );
        rotate_cw.click( function( e ) {
            obj = $( this ).data( 'obj' );
            obj.rotate( 1 );
        });
        div.append( rotate_cw );
        div.append( '<br/>' );

        var vieworig = $( '<a href="/img?id=' + this.obj_id +'">'
                + 'View Original</a><br/>' );
        div.append( vieworig );

        if( this.info.dup_streams && this.info.dup_streams.length > 0 ) {
            div.append( 'Duplicates: ' );

            for( i = 0; i < this.info.dup_streams.length; i++ ) {
                var viewdup = $( '<a href="/img?id=' + this.obj_id
                               + '&stream=' + this.info.dup_streams[i] + '">'
                               + (i + 1) + '</a> ' );
                div.append( viewdup );
            }
            div.append( '<br/>' );
        }

        activate_links( div );
    };

    DisplayableObject.prototype.display_group_info = function( div )
    {
        if( this.info.text ) {
            var view_text = $( '<a href="#">View text</a><br/>' );
            view_text.data( 'obj', this );
            view_text.click( function( e ) {
                obj = $( this ).data( 'obj' );
                dialogs.show_text_dialog( obj.info.text );
            });

            div.append( view_text );
        }

        var gather = $( '<a href="#">Gather Tags</a><br/>' );
        gather.data( 'obj', this );
        gather.click( function( e ) {
            obj = $( this ).data( 'obj' );
            obj.gather_tags();
        });

        div.append( gather );

        activate_links( div );
    };

    DisplayableObject.prototype.find_item = function( obj_id )
    {
        for( i = 0; i < this.info.files.length; i++ ) {
            if( this.info.files[i][0] == obj_id ) {
                return i;
            }
        }
        return -1;
    };

    DisplayableObject.prototype.obj_id_list = function()
    {
        var obj_ids = [];

        for( i = 0; i < this.info.files.length; i++ ) {
            obj_ids.push( this.info.files[i][0] );
        }

        return obj_ids;
    };

    DisplayableObject.prototype.get_obj_id = function()
    {
        return this.obj_id;
    };

    DisplayableObject.prototype.get_files = function()
    {
        return this.info.files;
    };

/**
 * class DisplayableSelection
 */
DisplayableSelection = function()

    // Constructor
    {
        DisplayableBase.call( this );

        this.objs = [];
    }

    // extends Displayable
    DisplayableSelection.prototype = new DisplayableBase();
    DisplayableSelection.prototype.constructor = DisplayableSelection;

    DisplayableSelection.prototype.tag = function( tags )
    {
        var targets = this.obj_id_list();
        var request = {
            'action' : 'tag',
            'targets' : targets,
            'query' : tags,
        };
        response = load_sync( request );

        if( response.result == 'ok' ) {
            tabs.on_event( { type: 'info_changed', affected: targets } );
            return { result: 'ok' };
        } else {
            return response;
        }
    };

    DisplayableSelection.prototype.rename = function( name, saveold )
    {
        alert( 'Selections cannot be renamed' );
    };

    DisplayableSelection.prototype.drop = function( obj_id, repr, type )
    {
        if( this.find_item( obj_id ) != -1 ) return;

        this.objs.push( [ obj_id, repr, type ] );
        this.notify_change( null );
        alert( 'dropped ' + type + ' ' + repr + ' on selection' );
    };

    DisplayableSelection.prototype.rm = function( obj_id, repr, type )
    {
        index = this.find_item( obj_id );
        if( index == -1 ) return;

        this.objs.splice( index, 1 );
        this.notify_change( null );
    };

    DisplayableSelection.prototype.make_group = function()
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

        response = load_sync( request );
        provider = new tabs.SingleProvider( response.group );
        tabs.create_display_tab( 'New Album', provider );
        tabs.on_event( { type: 'info_changed', affected: targets } );
    };

    DisplayableSelection.prototype.sort_by_id = function()
    {
        this.objs.sort( function( a, b ) {
            return a[0] - b[0];
        });

        this.notify_change( null );
    };

    DisplayableSelection.prototype.sort_by_name = function()
    {
        this.objs.sort( function( a, b ) {
            return a[1].localeCompare( b[0] );
        });

        this.notify_change( null );
    };

    DisplayableSelection.prototype.reorder = function( obj_id, idx )
    {
        src_idx = this.find_item( obj_id )
        if( src_idx == -1 ) {
            alert( obj_id + ' not in selection' );
            return;
        } else if( src_idx == idx ) {
            // Do nothing
            return;
        }

        obj = this.objs[src_idx];

        this.objs.splice( src_idx, 1 );
        if( idx < src_idx ) {
            this.objs.splice( idx, 0, obj );
        } else {
            this.objs.splice( idx - 1, 0, obj );
        }

        this.notify_change( null );
    };

    DisplayableSelection.prototype.display_info = function( div )
    {
        div.html( '' );

        div.append( 'Selection' );

        div.append( '<h1>Options</h1>' );

        var ul = $( document.createElement( 'ul' ) ); div.append( ul );
        var li;

        li = $( document.createElement( 'li' ) ); ul.append( li );
        var tool = $( '<a href="#">Sort by ID</a>' );
        tool.data( 'obj', this );
        tool.click( function( e ) {
            obj = $( this ).data( 'obj' );
            obj.sort_by_id();
        });
        li.append( tool );

        li = $( document.createElement( 'li' ) ); ul.append( li );
        var tool = $( '<a href="#">Sort by Name</a>' );
        tool.data( 'obj', this );
        tool.click( function( e ) {
            obj = $( this ).data( 'obj' );
            obj.sort_by_name();
        });
        li.append( tool );

        li = $( document.createElement( 'li' ) ); ul.append( li );
        var tool = $( '<a href="#">Make Album</a>' );
        tool.data( 'obj', this );
        tool.click( function( e ) {
            obj = $( this ).data( 'obj' );
            obj.make_group();
        });
        li.append( tool );
    };

    DisplayableSelection.prototype.find_item = function( obj_id )
    {
        for( i = 0; i < this.objs.length; i++ ) {
            if( this.objs[i][0] == obj_id ) {
                return i;
            }
        }
        return -1;
    };

    DisplayableSelection.prototype.obj_id_list = function()
    {
        var obj_ids = [];

        for( i = 0; i < this.objs.length; i++ ) {
            obj_ids.push( this.objs[i][0] );
        }

        return obj_ids;
    };

    DisplayableSelection.prototype.get_files = function()
    {
        return this.objs;
    };

/**
 * class ViewBase
 */
ViewBase = function() {}

    ViewBase.prototype.display_view = function( disp, div ) 
    {
        div.html( '&nbsp;' );
    };

    ViewBase.prototype.on_event = function( e ) {};

HtmlView = function( html )

    // Constructor
    {
        ViewBase.call( this );

        this.html = html;
    };

    // extends ViewBase
    HtmlView.prototype = new ViewBase();
    HtmlView.prototype.constructor = HtmlView;

    HtmlView.prototype.display_view = function( disp, div )
    {
        div.html( this.html );
    };

/**
 * class ImageView
 */
ImageView = function()

    // Constructor
    {
        ViewBase.call( this );

        this.viewer = null;
    }

    // extends ViewBase
    ImageView.prototype = new ViewBase();
    ImageView.prototype.constructor = ImageView;

    ImageView.prototype.display_view = function( disp, div )
    {
        div.html( '' );

//        if( !disp.info.mime ) {
//            div.append( 'Image not available<br/>' );
//            return;
//        }

        this.viewer = attach_image(
            div, disp.obj_id, disp.info.thumb_gen, disp.info.repr, disp.info.type );

        div.append( '<br/>' );
    };

    ImageView.prototype.on_event = function( e )
    {
        if( !this.viewer ) {
            return;
        }

        if( e.type == 'resized' || e.type == 'focused' ) {
            this.viewer.refresh();
        } else if( e.type == 'zoom' ) {
            this.viewer.set_zoom( e.zoom );
        }
    };

ThumbView = function()

    // Constructor
    {
        ViewBase.call( this );

        // Calculate the thumb tile exponent
        exp_w = 0;
        while( (window.width / (1 << exp_w)) > 16 ) exp_w++;

        // Calculate the exponent for the thumb image
        factor_i = 0;
        while( window.devicePixelRatio > (1 << factor_i) ) factor_i++;
        exp_i = exp_w + factor_i;

        GROUPLINK_TEMPLATE =
            '<a class="albumlink objitem sortable" href="#">'
          + '  <img src="/img?id=#{obj}&exp='
            + exp_i + '" style="max-width: 100%; max-height: 100%"/>'
          + '</a>';
        GROUPLINK_LI_SIZE = (1 << exp_w);
    };

    // extends ViewBase
    ThumbView.prototype = new ViewBase();
    ThumbView.prototype.constructor = ThumbView;

    ThumbView.prototype.display_view = function( disp, div )
    {
        // Workaround for jQuery exection when removing draggable during
        // drag event
        div.find( '.objitem' ).remove();
        div.html( '' );

        var request = {
            action:     'info',
            targets:    [ this.obj_id ],
            items:      [ 'files' ],
        }

        div.append( '<ul class="thumbslist"></ul>' );
        var ls = div.children().first();

        group_id = disp.get_obj_id();
        files = disp.get_files();

        for( i = 0; i < files.length; i++ ) {
            var li = $( '<li></li>' );
            var img = $( GROUPLINK_TEMPLATE
                    .replace( /#\{obj\}/g, files[i][0] ) );

            util.make_draggable( img, files[i][0],
                    files[i][1], files[i][2] );
            util.make_sortable( disp, li, i );

            // obj_id and repr copied to obj by make_draggable
            img.data( 'grp_id', group_id );
            img.data( 'grp_idx', i );

            img.click( function( e ) {
                var provider = null;

                var obj_id = $( this ).data( 'obj_id' );
                var repr = $( this ).data( 'repr' );
                var grp_id = $( this ).data( 'grp_id' );
                var grp_idx = $( this ).data( 'grp_idx' );

                if( grp_id == null ) {
                    provider = new tabs.SingleProvider( obj_id );
                } else {
                    provider = new tabs.SearchProvider( {
                        mode:   'album',
                        album:  grp_id,
                        index:  grp_idx,
                    });
                }
                tabs.create_display_tab( repr, provider );
            });

            li.append( img );
            li.width( GROUPLINK_LI_SIZE );
            li.height( GROUPLINK_LI_SIZE );
            ls.append( li );
        }

        li = $( '<li></li>' );
        li.width( GROUPLINK_LI_SIZE );
        li.height( GROUPLINK_LI_SIZE );
        ls.append( li );
    };

    ThumbView.prototype.on_event = function( e )
    {
        if( e.type == 'files_changed' ) {
            return true;
        }
    };

/**
 * class Display
 */
Display = function( disp, view )

    // Constructor
    {
        this.disp = disp;
        this.view = view;
        this.pane = null;

        this.disp.register_change_listener( this );
    }

    Display.prototype.attach = function( pane )
    {
        this.pane = pane;
        this.on_display( true );
    };

    Display.prototype.tag = function( tags )
    {
        return this.disp.tag( tags );
    };

    Display.prototype.rename = function( name, saveold )
    {
        this.disp.rename( name, saveold );
    };

    Display.prototype.drop = function( obj_id, repr, type )
    {
        this.disp.drop( obj_id, repr, type );
    };

    Display.prototype.rm = function( obj_id, repr, type )
    {
        this.disp.rm( obj_id, repr, type );
    };

    Display.prototype.set_variant = function(
            original, variant )
    {
        this.disp.set_variant( original, variant );
    };

    Display.prototype.clear_variant = function(
            original, variant )
    {
        this.disp.clear_variant( original, variant );
    };

    Display.prototype.merge_duplicates = function( original, duplicate )
    {
        this.disp.merge_duplicates( original, duplicate );
    }

    Display.prototype.reorder = function( obj_id, idx )
    {
        this.disp.reorder( obj_id, idx );
    };

    Display.prototype.on_event = function( e )
    {
        this.disp.on_event( e );
        this.view.on_event( e );

        if( e.affected
         && e.affected.indexOf( this.disp.get_obj_id() ) != -1
         && e.type == 'removed' )
        {
            return public_make_dummy_display( 'This object has been removed' );
        } else {
            return null;
        }
    };

    Display.prototype.on_display = function( refresh_view )
    {
        var info_div = this.pane.find( '.info' );
        var view_div = this.pane.find( '.disp' );

        this.disp.display_info( info_div );
        if( refresh_view ) {
            this.view.display_view( this.disp, view_div );
        }
    };

    Display.prototype.refresh_info = function( reload_all )
    {
        this.disp.refresh_info( reload_all );
    };

    Display.prototype.on_displayable_changed = function( disp, e )
    {
        this.on_display( e == null || e.type == 'files_changed' );
    };

var make_file_display = function( obj_id, info )
{
    disp = new DisplayableObject( obj_id, info );
    view = new ImageView();
    return new Display( disp, view );
};

var make_group_display = function( obj_id, info )
{
    disp = new DisplayableObject( obj_id, info );
    view = new ThumbView();
    return new Display( disp, view );
};

var public_make_dummy_display = function( msg )
{
    disp = new DisplayableBase();
    view = new HtmlView( '<p>' + msg + '</p>');
    return new Display( disp, view );
};

/**
 * make_object_display( obj_id ) - factory method for creating
 * the appropriate display.
 */
var public_make_object_display = function( obj_id )
{
    var request = {
        action:     'info',
        targets:    [ obj_id ],
        items:      [ 'type', 'repr', 'tags', 'names',
            'variants', 'variants_of', 'dup_streams',
            'albums', 'files', 'text', 'thumb_gen',
            'width', 'height', 'creation_time' ],
    };
    
    response = load_sync( request );
    info = response.info[0];

    if( info.type == 'file' ) {
        return make_file_display( obj_id, info );
    } else if( info.type == 'album' ) {
        return make_group_display( obj_id, info );
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
    disp = new DisplayableSelection();
    view = new ThumbView();
    return new Display( disp, view );
};

return {
    make_dummy_display: public_make_dummy_display,
    make_object_display: public_make_object_display,
    make_selection_display: public_make_selection_display,
};

})(); // module displib


