function set_image_zoom( tab, zoom )
{
    im = tab.data( 'im' );

    if( !im ) return;

    tab.data( 'im-zoom', zoom );

    im.width = tab.data( 'im-width' ) * zoom;
    im.height = tab.data( 'im-height' ) * zoom;
}

function resize_image( tab, zoom )
{
    im = tab.data( 'im' );
    if( !im ) return;

    switch( zoom ) {
        case 0:
            set_image_zoom( tab, 1.0 );
            break;
        case -1:
        case -2:
            img_div = tab.find( '.img' )

            container_width = img_div.width();
            container_height = img_div.height();

            img_width = tab.data( 'im-width' );
            img_height = tab.data( 'im-height' );

            width_ratio = 1.0 * container_width / img_width;
            height_ratio = 1.0 * container_height / img_height;

            if( zoom == -1 ) {
                if( width_ratio < height_ratio ) {
                    set_image_zoom( tab, width_ratio );
                } else {
                    set_image_zoom( tab, height_ratio );
                }
            } else {
                if( width_ratio < height_ratio ) {
                    set_image_zoom( tab, height_ratio );
                } else {
                    set_image_zoom( tab, width_ratio );
                }
            }
            break;
        default:
            set_image_zoom( tab, tab.data( 'im-zoom' ) * zoom );
            break;
    }
}

function register_image( im )
{
    elem = $( im );
    tab = elem.closest( '.tab' );

    tab.data( 'im', im );
    tab.data( 'im-width', im.width );
    tab.data( 'im-height', im.height );
    tab.data( 'im-zoom', 1.0 );

    resize_image( tab, -1 );
}
