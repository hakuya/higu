import { load_async } from '../script';
import * as dialogs from '../controllers/dialogs';
import * as tabs from '../controllers/tabs';
import * as util from '../util';

import {
    SingleProvider,
    SearchProvider,
    info_set,
    field_set
} from '../models/providers';

import { DisplayableBase } from './displayable';
import { get_selection } from '../models/selection';

/**
 * class DisplayableObject
 */
export class DisplayableObject extends DisplayableBase
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

        load_async( request, this._rename_cb.bind( this ), {} );
    }

    _rename_cb( data, response )
    {
        tabs.on_event( { type: 'info_changed', affected: [ this.obj_id ] } );
    }

    tag( tags, callback )
    {
        var request = {
            'action' : 'tag',
            'targets' : [ this.obj_id ],
            'query' : tags,
        };

        load_async(
                request,
                this._tag_cb.bind( this ),
                { callback: callback }
             );
    }

    _tag_cb( data, response )
    {
        if( response.result == 'ok' ) {
            tabs.on_event( { type: 'info_changed', affected: [ this.obj_id ] } );
            data.callback( { result: 'ok' } );
        } else {
            data.callback( response );
        }
    }

    rm_group()
    {
        var request = {
            action:     'group_delete',
            group:      this.obj_id,
        };

        load_async( request, this._rm_group_cb.bind( this ), {} );
    }

    _rm_group_cb( data, response )
    {
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

        load_async( request, this._gather_tags_cb.bind( this ), {} );
    }

    _gather_tags_cb( data, response )
    {
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
        load_async( request, this._reorder_cb.bind( this ), {} );
    }

    _reorder_cb( data, response )
    {
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

        load_async( request, this._set_field_cb.bind( this ), {} );
    }

    _set_field_cb( data, response )
    {
        tabs.on_event( { type: 'info_changed', affected: [ this.obj_id, ] } );
    }

    set_variant( original, variant )
    {
        var request = {
            action:     'link_files',
            original:   original,
            variant:    variant,
        };

        load_async(
                request,
                this._set_variant_cb.bind( this ),
                {
                    original: original,
                    variant:  variant
                }
            );
    }

    _set_variant_cb( data, response )
    {
        tabs.on_event( { type: 'info_changed', affected: [ original, variant ] } );
    }

    clear_variant( original, variant )
    {
        var request = {
            action:     'clear_variant',
            original:   original,
            variant:    variant,
        };

        load_async(
                request,
                this._clear_variant_cb.bind( this ),
                {
                    original: original,
                    variant:  variant
                }
            );
    }

    _clear_variant_cb( data, response )
    {
        tabs.on_event( { type: 'info_changed', affected: [ data.original, data.variant ] } );
    }

    link_duplicates( original, duplicate )
    {
        var request = {
            action:         'link_files',
            original:       original,
            variant:        duplicate,
            is_duplicate:   true,
        };

        load_async(
                request,
                this._link_duplicates_cb.bind( this ),
                {
                    original:  original,
                    duplicate: duplicate
                }
            );
    }

    _link_duplicates_cb( data, response )
    {
        tabs.on_event( { type: 'info_changed', affected: [ data.original, data.duplicate ] } );
    }

    unlink_duplicate( original, duplicate )
    {
        var request = {
            action:         'unlink_files',
            original:       original,
            variant:        duplicate,
        };

        load_async(
                request,
                this._unlink_duplicates_cb.bind( this ),
                {
                    original:  original,
                    duplicate: duplicate
                }
            );
    }

    _unlink_duplicates_cb( data, response )
    {
        tabs.on_event( { type: 'info_changed', affected: [ data.original, data.duplicate ] } );
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
        load_async( request, this._transform_cb.bind( this ), {} );
    }

    _transform_cb( data, response )
    {
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
        load_async( request, this._set_as_main_stream_cb.bind( this ), {} );
    }

    _set_as_main_stream_cb( data, response )
    {
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
                if( type != 'file'
                 && type != 'selection'
                 && type != 'album')
                {
                    alert( 'Cannot be added to albums' );
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

                load_async(
                        request,
                        this._on_event_drop_album_cb.bind( this ),
                        {
                            disp:        disp,
                            obj_id:      obj_id,
                            drop_method: e.drop_method,
                            drop_data:   e.drop_data
                        }
                    );
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

                load_async(
                        request,
                        this._on_event_trash_cb.bind( this ),
                        { obj_id: obj_id }
                    );
            }
        } else if( e.type == 'replaced' ) {
            this.obj_id = e.new_id;
        } else if( e.type == 'info_changed' ) {
            this.refresh_info( e );
        } else if( e.type == 'files_changed' ) {
            this.refresh_info( e );
        } else if( e.type == 'push_selection' ) {
            var selection = get_selection( e.selection );
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

    _on_event_drop_album_cb( data, response )
    {
        tabs.on_event( { type: 'files_changed', affected:
                [ this.obj_id ] } );
        tabs.on_event( { type: 'info_changed', affected:
                [ data.obj_id ] } );

        if( data.disp ) {
            data.disp.on_event( {
                    type: 'dropped',
                    drop_target: this,
                    drop_method: data.drop_method,
                    drop_data: data.drop_data,
                } );
        }
    }

    _on_event_trash_cb( data, response )
    {
        tabs.on_event( { type: 'files_changed', affected:
                [ this.obj_id ] } );
        tabs.on_event( { type: 'info_changed', affected:
                [ data.obj_id ].concat( targets ) } );
    }

    refresh_info( e )
    {
        var request = {
            action:     'info',
            target:     this.obj_id,
            items:      info_set,
            fields:     field_set,
        };

        load_async( request, this._refresh_info_cb.bind( this ), { e: e } );
    }

    _refresh_info_cb( data, response )
    {
        this.info = response.info;
        this.fields = response.fields;

        this.notify_change( data.e );
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

            return new SearchProvider( search_args );
        } else {
            return new SingleProvider( this.obj_id );
        }
    }
}
