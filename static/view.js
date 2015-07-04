window_width = -1;
window_height = -1;

// Singletons
var tabs;

// Classes
var SearchProvider;
var DisplayTab;

function init_view()
{
/**
 * class tabs
 */
tabs = new function()
{
    this.elem = $( '#tabs' );
    this.counter = 1;
    this.template = "<li><a href='#{href}'>#{label}</a> <span class='ui-icon ui-icon-close' role='presentation'>Remove Tab</span></li>";

    // Begin constructor
    this.elem.tabs({
        fit : true,
        heightStyle : 'fill',
        activate: function( e ) {
            tabs.on_select();
        }
    });

    this.elem.delegate( "span.ui-icon-close", "click", function() {
        var panelId = $( this ).closest( "li" ).remove().attr( "aria-controls" );
        var tab_elem = $( "#" + panelId );
        var tab = tab_elem.data( 'obj' );
        
        if( !tab || !tab.on_close ) {
            tabs.remove( tab_elem );
        } else {
            tab.on_close();
        }
    });
    // End constructor

    /**
     * active() - returns active tab
     */
    this.active = function()
    {
        idx = this.elem.tabs( 'option', 'active' );
        return this.elem.find( '.tab' ).eq( idx );
    };

    /**
     * get_head_elem()
     */
    this.get_nav_elem = function( tab )
    {
        var idx = $( '#tabs > div' ).index( tab );
        return this.elem.find( '.ui-tabs-nav li' ).eq( idx );
    }

    /**
     * on_event()
     */
    this.on_event = function( e )
    {
        $( '#tabs > div' ).each( function( idx ) {
            obj = $( this ).data( 'obj' );
            if( obj && obj.on_event ) {
                obj.on_event( e );
            }
        });
    }

    /**
     * on_select()
     */
    this.on_select = function()
    {
        tab = tabs.active();
        obj = tab.data( 'obj' );
        if( obj && obj.display ) {
            obj.on_event( { type: 'focused' } );
        }
    }

    /**
     * select( tab ) - selects the given tab
     */
    this.select = function( tab )
    {
        var idx = $( '#tabs > div' ).index( tab );
        this.elem.tabs( 'option', 'active', idx );
    };

    /**
     * create( title ) - creates a tab with the given title
     */
    this.create = function( title )
    {
        var count = this.counter;
        var id_val = 'tabs-' + count;
        var li = $( this.template.replace( /#\{href\}/g, "#" + id_val ).replace( /#\{label\}/g, title ) );
        this.elem.find( '.ui-tabs-nav' ).append( li );
        this.elem.append( "<div class='tab' id='" + id_val + "'>loading...</div>" );
        this.elem.tabs( 'refresh' );
        this.counter++;

        tab = $( '#' + id_val );
        this.select( tab );

        return tab;
    };

    /**
     * remove( elem ) - removes the given tab
     */
    this.remove = function( elem )
    {
        elem.remove();
        this.elem.tabs( "refresh" );
    }
};

/**
 * singleton taglist_tab
 */
taglist_tab = new function()
{
    this.elem = $( '#taglist-tab' );
    this.elem.data( 'obj', this );

    TAGLINK_TEMPLATE = "<li><a class='taglink' href='##{tag}'>#{tag}</a></li>";

    // Member functions
    this.on_tags_loaded = function( data, response )
    {
        this.elem.html( '' );
        this.elem.append( "<ul class='taglist'></ul>" );
        var ls = this.elem.children().first();

        for( i = 0; i < response.tags.length; i++ ) {
            var li = TAGLINK_TEMPLATE.replace( /#\{tag\}/g, response.tags[i]);
            ls.append( li );
        }

        activate_links( ls );
    };

    this.on_event = function( e )
    {
        if( e.type == 'info_changed' ) {
            this.on_tags_changed();
        }
    }

    this.on_tags_changed = function()
    {
        load_async( { 'action' : 'taglist' }, this, 'on_tags_loaded', null );
    };

    // Constructor
    this.on_tags_changed();
};

/**
 * singleton admin_tab
 */
admin_tab = new function()
{
    this.elem = $( '#admin-tab' );
    this.elem.data( 'obj', this );

    // Member functions
    this.on_event = function( e )
    {
    }

    // Constructor
    this.elem.html( '' );
    this.elem.append( 'Tag: <input type="text" id="adm-tag-src"/>' );
    this.elem.append( 'New: <input type="text" id="adm-tag-tgt"/>' );

    // Delete
    button = $( '<input type="button" value="Delete"/>' );
    button.click( function( e ) {
        src = $( '#adm-tag-src' );
        tgt = $( '#adm-tag-tgt' );

        var request = {
            action:     'tag_delete',
            tag:        src.val(),
        };
        load_sync( request );

        src.val( '' );
        tgt.val( '' );
    });
    this.elem.append( button );

    // Copy
    button = $( '<input type="button" value="Copy"/>' );
    button.click( function( e ) {
        src = $( '#adm-tag-src' );
        tgt = $( '#adm-tag-tgt' );

        var request = {
            action:     'tag_copy',
            tag:        src.val(),
            target:     tgt.val(),
        };
        load_sync( request );

        src.val( '' );
        tgt.val( '' );
    });
    this.elem.append( button );

    // Move
    button = $( '<input type="button" value="Move"/>' );
    button.click( function( e ) {
        src = $( '#adm-tag-src' );
        tgt = $( '#adm-tag-tgt' );

        var request = {
            action:     'tag_move',
            tag:        src.val(),
            target:     tgt.val(),
        };
        load_sync( request );

        src.val( '' );
        tgt.val( '' );
    });
    this.elem.append( button );
};

/**
 * class SelectionProvider
 */
SelectionProvider = function()
{
    this.selection = new SelectionDisplay();

    // Member functions
    this.init = function( obj, callback )
    {
        eval( 'obj.' + callback + '( this.selection )' );
    };

    this.close = function()
    {
    };

    this.repr = function()
    {
        return 'Single';
    };

    this.fetch = function( idx )
    {
        if( idx == 0 ) {
            return this.selection;
        } else {
            return null;
        }
    };

    this.offset = function( off )
    {
        return this.fetch( off );
    };

    this.next = function()
    {
        return null;
    };

    this.prev = function()
    {
        return null;
    };
};

/**
 * class SingleProvider
 */
SingleProvider = function( obj_id )
{
    this.obj_id = obj_id;

    // Member functions
    this.init = function( obj, callback )
    {
        display = make_display( this.obj_id );
        eval( 'obj.' + callback + '( display )' );
    };

    this.close = function()
    {
    };

    this.repr = function()
    {
        return 'Single';
    };

    this.fetch = function( idx )
    {
        if( idx == 0 ) {
            return make_display( this.obj_id );
        } else {
            return null;
        }
    };

    this.offset = function( off )
    {
        return this.fetch( off );
    };

    this.next = function()
    {
        return null;
    };

    this.prev = function()
    {
        return null;
    };
};

/**
 * class SearchProvider
 */
SearchProvider = function( query )
{
    this.query = query;
    this.sid = null;
    this.last = null;

    // Member functions
    this.init = function( obj, callback )
    {
        if( this.sid ) {
            return this.fetch( idx );
        }

        var request = { action: 'search' };

        if( query.mode ) {
            if( query.mode == 'album' ) {
                request.album = query.album;
            }

            request.mode = query.mode;
        } else {
            request.query = query.query;
        }

        if( query.index ) {
            request.index = query.index;
        }

        load_async( request, this, 'on_init_load', {
            obj: obj,
            callback: callback,
        });
    };

    this.on_init_load = function( data, response )
    {
        if( response.result != 'ok' ) {
            this.sid = null;
            this.last = null;

            if( response.msg ) {
                display = new DummyDisplay(
                    'The search failed: ' + response.msg );
            } else {
                display = new DummyDisplay(
                    'The search failed: ' + response.except + ' error' );
            }
        } else if( response.results > 0 ) {
            this.sid = response.selection;
            this.last = response.index;

            display = make_display( response.first );
        } else {
            this.sid = null;
            this.last = null;

            display = new DummyDisplay( 'The search had no results' );
        }
        eval( 'data.obj.' + data.callback + '( display )' );
    }

    this.close = function()
    {
        if( !this.sid ) return null;
        
        var request = {
            'action' : 'selection_close',
            'selection' : this.sid,
        }
        load_sync( request );
    }

    this.repr = function()
    {
        return query;
    }

    this.fetch = function( idx )
    {
        if( !this.sid ) return null;

        var request = {
            action:     'selection_fetch',
            selection:  this.sid,
            index:      idx,
        };
        response = load_sync( request );

        if( response.result != 'ok' ) {
            return null;
        }

        this.last = idx;
        display = make_display( response.object_id );
        return display;
    };

    this.offset = function( off )
    {
        return this.fetch( this.last + off );
    };

    this.next = function()
    {
        return this.offset( 1 );
    };

    this.prev = function()
    {
        return this.offset( -1 );
    };

    this.slice = function( begin, end )
    {
    };
};

/**
 * class DisplayTab
 */
DisplayTab = function( title, provider )
{
    this.elem = tabs.create( title );
    this.elem.data( 'obj', this );

    this.provider = provider;
    this.display = null;
    this.title = title;

    TAGLINK_TEMPLATE = "<li><a class='taglink' href='##{tag}'>#{tag}</a></li>";
    
    // Member functions
    this.close = function()
    {
        // XXX - this should be handled in tabs
        tabs.get_nav_elem( this.elem ).remove();
        tab.on_close();
    };

    this.on_close = function()
    {
        this.provider.close();
        tabs.remove( this.elem );
    };

    this.tag = function( tags )
    {
        if( this.display ) {
            return this.display.tag( tags );
        } else {
            return { result: 'ok' };
        }
    }

    this.rename = function( name, saveold )
    {
        if( this.display ) {
            this.display.rename( name, saveold );
        }
    }

    this.set_duplication = function( original, variant, is_duplicate )
    {
        if( this.display ) {
            this.display.set_duplication( original, variant, is_duplicate );
        }
    }

    this.drop = function( obj_id, repr, type )
    {
        if( this.display ) {
            this.display.drop( obj_id, repr, type );
        }
    }

    this.rm = function( obj_id, repr, type )
    {
        if( this.display ) {
            this.display.rm( obj_id, repr, type );
        }
    }

    this.down = function()
    {
        display = this.provider.next();
        if( display ) {
            this.display = display;
            this.display.attach( this.elem );
        }
    }

    this.up = function()
    {
        display = this.provider.prev();
        if( display ) {
            this.display = display;
            this.display.attach( this.elem );
        }
    }

    this.on_init_complete = function( display )
    {
        this.elem.html( '' );
        this.elem.append( "<div class='info'></div>" );
        this.elem.append( "<div class='disp'></div>" );

        this.display = display;
        this.display.attach( this.elem );
    };

    this.on_event = function( e )
    {
        if( this.display ) {
            display = this.display.on_event( e );
            if( display ) {
                this.display = display;
                this.display.attach( this.elem );
            }
        }
    }

    // Constructor

    nav = tabs.get_nav_elem( this.elem );
    nav.data( 'tab', this );
    nav.droppable({
        accept: '.objitem',
        hoverClass: 'ui-state-hover',
        drop: function( event, ui ) {
            tab = $( this ).data( 'tab' );
            item = $( ui.draggable );
            item.draggable( 'option', 'revert', false );

            tab.drop( item.data( 'obj_id' ), item.data( 'repr' ),
                    item.data( 'type' ) );
        },
    });

    this.provider.init( this, 'on_init_complete' );
};

} // end init_view()
