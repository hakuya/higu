selected_im=null;
selected_width=-1;
selected_height=-1;

selected_zoom=1.0;

function set_image_zoom( zoom )
{
    selected_zoom = zoom;
    selected_im.width = selected_width * zoom;
    selected_im.height = selected_height * zoom;
}

function resize_image( zoom )
{
    switch( zoom ) {
        case 0:
            set_image_zoom( 1.0 );
            break;
        case -1:
        case -2:
            container_width = parseInt( selected_im.parentNode.style.width );
            container_height = parseInt( selected_im.parentNode.style.height );

            width_ratio = 1.0 * container_width / selected_width;
            height_ratio = 1.0 * container_height / selected_height;

            if( zoom == -1 ) {
                if( width_ratio < height_ratio ) {
                    set_image_zoom( width_ratio );
                } else {
                    set_image_zoom( height_ratio );
                }
            } else {
                if( width_ratio < height_ratio ) {
                    set_image_zoom( height_ratio );
                } else {
                    set_image_zoom( width_ratio );
                }
            }
            break;
        default:
            set_image_zoom( selected_zoom * zoom );
            break;
    }
}

function register_image( im )
{
    selected_im = im;
    selected_width = im.width;
    selected_height = im.height;

    resize_image( -1 );
}
