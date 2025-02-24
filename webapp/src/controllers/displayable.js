
/**
 * class DisplayableBase
 */
export class DisplayableBase
{
    constructor()
    {
        this.change_listeners = [];
    }

    is_sortable()
    {
        return false;
    }

    set_selected_items( items )
    {}

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

    get_obj_drop_data()
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