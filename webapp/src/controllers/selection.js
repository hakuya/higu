import { load_async } from '../script';
import * as dialogs from '../controllers/dialogs';
import * as tabs from '../controllers/tabs';

import {
    SingleProvider,
    SelectionProvider,
    ListProvider
} from '../models/providers';

import { DisplayableBase } from './displayable';

/**
 * Controller for displaying selections.
 */
export class DisplayableSelection extends DisplayableBase
{
    constructor()
    {
        super();

        this.type = 'selection';
        this.objs = [];

        /**
         * List of object tuples for the items which are selected.
         */
        this.selected_items = null;
    }

    is_sortable()
    { return true; }

    set_selected_items( items )
    {
        if( items.length == 0 ) {
            this.selected_items = null;
        } else {
            this.selected_items = items;
        }
        tabs.on_event( {
            type: 'selected_items_changed',
            display: this,
        } );
    }

    tag( tags, callback )
    {
        var targets = this.obj_id_list();
        var request = {
            'action' : 'tag',
            'targets' : targets,
            'query' : tags,
        };
        load_async(
                request,
                this._tag_cb.bind( this ),
                {
                    callback: callback,
                    targets:  targets
                }
            );
    }

    _tag_cb( data, response )
    {
        if( response.result == 'ok' ) {
            tabs.on_event( { type: 'info_changed', affected: data.targets } );
            data.callback( { result: 'ok' } );
        } else {
            data.callback( response );
        }
    }

    make_selection( extract = false )
    {
        // Creates a new selection, copies or moves our selected items
        var provider = new SelectionProvider();
        var objs = (this.selected_items !== null
                        ? this.selected_items
                        : this.objs);

        provider.init_objs = [...objs];
        tabs.create_display_tab( 'Selection ' + (provider.selection_id + 1), provider );

        if( extract ) {
            // We've moving the selection
            var removed = false;

            for( var i = 0; i < objs.length; i++ ) {
                var index = this.find_item( objs[i][0] );
                if( index == -1 ) continue;
                this.objs.splice( index, 1 );
                removed = true;
            }

            if( removed ) {
                this.notify_change( null );
            }
        }
    }

    make_group()
    {
        if( this.objs.length == 0 ) {
            alert( 'No objects in this selection' );
            return;
        }

        // By default, create an album from the whole selection
        var targets = this.obj_id_list();

        // If we have selected items, we'll make the album from the selection
        if( this.selected_items !== null
         && this.selected_items.length != 0 )
        {
            targets = this.selected_item_ids_list();
        }

        // Kick off the request
        var request = {
            action:     'group_create',
            targets:    targets,
        };
        load_async(
                request,
                this._make_group_cb.bind( this ),
                { targets: targets }
            );
    }

    _make_group_cb( data, response )
    {
        if( data.targets.length != this.objs.length
         && data.targets.length == this.selected_items.length )
        {
            // Keep track of the index to insert the album
            var alb_index = null;

            for( var i = 0; i < data.targets.length; i++ ) {
                // Find the object
                var index = this.find_item( data.targets[i] );
                if( index == -1 ) {
                    continue;
                } else if( alb_index === null || index < alb_index ) {
                    alb_index = index;
                }

                // And remove it
                this.objs.splice( index, 1 );
            }

            // Finally, insert the album
            if( alb_index !== null ) {
                this.objs.splice( alb_index, 0, response.group );
                this.selected_items = null;

                this.notify_change( null );
            }
        } else {
            var provider = new SingleProvider( response.group[0] );
            tabs.create_display_tab( 'New Album', provider );
        }

        tabs.on_event( { type: 'info_changed', affected: data.targets } );
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
            return a[1].localeCompare( b[1] );
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
        var files = drop_data.get_files();

        var src_idxs = [];
        var src_objs = [];

        for( var i = 0; i < files.length; i++ ) {
            var src_idx = this.find_item( files[i][0] );
            if( src_idx == -1 ) {
                alert( files[i][1] + ' not in selection' );
                return;
            }

            src_idxs.push( src_idx );
        }

        src_idxs.sort( ( a, b ) => ( a - b ) );
        for( var i = 0; i < src_idxs.length; i++ ) {
            src_objs.push( this.objs[src_idxs[i]] )
        }

        var output = [];
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

    on_key( e )
    {
        switch( e.charCode ) {
            case 116: // t
                dialogs.show_tag_dialog( this );
                break;
            case 46: // .
            case 62: // >
                this.make_selection( e.charCode == 62 );
                break;
            default:
                break;
        }
    }

    on_event( e )
    {
        if( e.type == 'key' ) {
            this.on_key( e );
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

    /**
     * @returns A list of object ids for items that are selected
     */
    selected_item_ids_list()
    {
        var obj_ids = [];

        if( this.selected_items !== null ) {
            for( var i = 0; i < this.selected_items.length; i++ ) {
                obj_ids.push( this.selected_items[i][0] );
            }
        }

        return obj_ids;
    }

    get_files()
    {
        return this.objs;
    }

    create_provider( args )
    {
        var provider = new ListProvider( this.objs );

        if( args && args.start_id ) {
            provider.obj_id = args.start_id;
        }

        return provider;
    }
}
