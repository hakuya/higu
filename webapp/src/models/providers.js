import { load_async } from '../script';

import {
    register_selection,
    unregister_selection
} from './selection';

import * as displib from '../displib';

export var info_set = [ 'object_id', 'type', 'repr', 'tags',
    'names', 'variants', 'variants_of', 'original_file',
    'duplicates', 'imports', 'albums', 'files', 'text', 'thumb_gen',
    'width', 'height', 'sizes', 'origin_time', 'creation_time',
    'exif' ];
export var field_set = [ 'rating' ];

/**
 * class Provider
 */
export class Provider
{
    init( callback )
    {}

    close()
    {}

    repr()
    { return null; }

    fetch( idx )
    {}

    offset( off )
    {}

    next()
    {}

    prev()
    {}

    reload()
    {}
}

/**
 * class SelectionProvider
 */
export class SelectionProvider extends Provider
{
    constructor()
    {
        super();

        this.selection = displib.make_selection_display();
        this.selection_id = register_selection( this.selection.disp );
        this.init_query = null;
        this.init_objs = null;

        this.index = null;
        this.count = 1;

        this.callback = null;
    }

    init( callback )
    {
        this.callback = callback;
        this.load();
    }

    load()
    {
        if( this.init_query != null ) {
            var request = {
                action: 'search',
                info: [ 'object_id', 'repr', 'type' ],
                fields: [],
                query: this.init_query,
                count: 1000,
                oneshot: true,
            };

            load_async( request, this._load_cb.bind( this ), {} );
        } else {
            if( this.init_objs != null ) {
                this.selection.disp.objs = this.init_objs;
            }
            this.callback( this.selection );
        }
    }

    _load_cb( data, response )
    {
        if( response.result == 'ok' && response.results > 0 ) {
            this.selection.disp.objs = response.items.map( ( it ) => {
                                            return [ it.object_id, it.repr, it.type ];
                                        } );
        }
        this.callback( this.selection );
    }

    close()
    {
        unregister_selection( this.selection.disp );
    }

    repr()
    {
        return 'Single';
    }

    fetch( idx )
    {
        if( idx == 0 ) {
            this.callback( this.selection );
        }
    }

    offset( off )
    {
        this.fetch( off );
    }

    reload()
    {
        this.load();
    }
}

/**
 * class SingleProvider
 */
export class SingleProvider extends Provider
{
    constructor( obj_id )
    {
        super();

        this.obj_id = obj_id;
        this.info = null;
        this.index = null;
        this.count = 1;

        this.callback = null;
    }

    init( callback )
    {
        this.callback = callback;
        this.load();
    }

    load()
    {
        var request = {
            action:     'info',
            target:     this.obj_id,
            items:      info_set,
            fields:     field_set,
        };

        load_async( request, this._load_cb.bind( this ), {} );
    }

    _load_cb( data, response )
    {
        this.info = response.info;
        this.fields = response.fields;

        var display = displib.make_object_display( this.info, this.fields );
        this.callback( display );
    }

    repr()
    {
        return 'Single';
    }

    fetch( idx )
    {
        if( idx == 0 ) {
            this.callback( displib.make_object_display( this.info, this.fields ) );
        }
    }

    offset( off )
    {
        this.fetch( off );
    }

    reload()
    {
        this.load();
    }
}

/**
 * class SearchProvider
 */
export class SearchProvider extends Provider
{
    constructor( query )
    {
        super();

        this.query = query;
        this.sid = null;

        this.index = null;
        this.count = null;

        this.loading = false;
        this.callback = null;
    }

    init( callback )
    {
        this.callback = callback;

        if( this.sid ) {
            return this.fetch( this.index );
        }

        var request = {
            action: 'search',
            info: info_set,
            fields: field_set,
         };

        if( this.query.mode ) {
            if( this.query.mode == 'object_items' ) {
                request.object = this.query.object;
            }

            request.mode = this.query.mode;
        } else {
            request.query = this.query.query;
        }

        if( this.query.index ) {
            request.index = this.query.index;
        }

        this.loading = true;
        load_async( request, this.on_init_load.bind( this ), {} );
    }

    on_init_load( data, response )
    {
        this.loading = false;

        var display = null;

        if( response.result != 'ok' ) {
            this.sid = null;
            this.index = null;
            this.count = null;

            if( response.msg ) {
                display = displib.make_dummy_display(
                    'The search failed: ' + response.msg );
            } else {
                display = displib.make_dummy_display(
                    'The search failed: ' + response.except + ' error' );
            }
        } else if( response.results > 0 ) {
            this.sid = response.selection;
            this.index = response.index;
            this.count = response.results;

            display = displib.make_object_display( response.first, response.fields );
        } else {
            this.sid = null;
            this.index = null;
            this.count = null;

            display = displib.make_dummy_display( 'The search had no results' );
        }

        this.callback( display );
    }

    close()
    {
        if( !this.sid ) return null;

        var request = {
            'action' : 'selection_close',
            'selection' : this.sid,
        }
        load_async( request, null, null );
    }

    repr()
    {
        return this.query;
    }

    fetch( idx )
    {
        if( this.loading ) return;
        if( !this.sid ) return;

        var request = {
            action:     'selection_fetch',
            selection:  this.sid,
            index:      idx,
            info:       info_set,
            fields:     field_set,
        };

        this.loading = true;
        load_async( request, this._fetch_cb.bind( this ), { idx: idx } );
    }

    _fetch_cb( data, response )
    {
        this.loading = false;
        if( response == null || response.result != 'ok' ) return;

        this.index = data.idx;
        this.callback( displib.make_object_display( response.info, response.fields ) );
    }

    offset( off )
    {
        this.fetch( this.index + off );
    }

    next()
    {
        this.offset( 1 );
    }

    prev()
    {
        this.offset( -1 );
    }

    reload()
    {
        this.fetch( this.index );
    }
}

/**
 * class ListProvider
 */
export class ListProvider extends Provider
{
    constructor( list )
    {
        super();

        this.list = list;
        this.obj_id = null;

        this.index = null;
        this.count = list.length;

        this.callback = null;
        this.loading = false;
    }

    init( callback )
    {
        this.callback = callback;

        if( this.obj_id ) {
            this.index = this.list.findIndex( ( it ) =>
                                { return it[0] == this.obj_id; } );
        }

        if( !this.index || this.index < 0 || this.index >= this.list.length ) {
            this.index = 0;
        }

        this.obj_id = this.list[this.index][0];

        var request = {
            action:     'info',
            target:     this.obj_id,
            items:      info_set,
            fields:     field_set,
        };

        this.loading = true;
        load_async( request, this.on_init_load.bind( this ), {} );
    }

    on_init_load( data, response )
    {
        this.loading = false;

        var display = displib.make_object_display( response.info, response.fields );
        this.callback( display );
    }

    repr()
    {
        return 'List';
    }

    fetch( idx )
    {
        if( this.loading ) return;

        if( idx < 0 || idx >= this.list.length ) {
            return;
        }

        this.index = idx;

        this.obj_id = this.list[this.index][0];

        var request = {
            action:     'info',
            target:     this.obj_id,
            items:      info_set,
            fields:     field_set,
        };

        this.loading = true;
        load_async( request, this._fetch_cb.bind( this ), {} );
    }

    _fetch_cb( data, response )
    {
        this.loading = false;
        this.callback( displib.make_object_display( response.info, response.fields ) );
    }

    offset( off )
    {
        this.fetch( this.index + off );
    }

    next()
    {
        this.offset( 1 );
    }

    prev()
    {
        this.offset( -1 );
    }

    reload()
    {
        this.fetch( this.index );
    }
}
