/**
 * class Viewer
 */
ImageViewer = function( tab, im )
{
    /**
     * apply_zoom( zoom ) - zoom the image to the given amount
     */
    this.apply_zoom = function( zoom )
    {
        this.im.width = this.im_width * zoom;
        this.im.height = this.im_height * zoom;
    };

    this.compute_zoom = function()
    {
        if( this.zoom == 'fit_inside' || this.zoom == 'fit_outside' ) {
            tab_div = this.tab.find( '.tab' );
            info_div = this.tab.find( '.info' );

            container_width = this.tab.width() - info_div.width() - 20;
            container_height = this.tab.height();

            width_ratio = 1.0 * container_width / this.im_width;
            height_ratio = 1.0 * container_height / this.im_height;

            if( this.zoom == 'fit_inside' ) {
                if( width_ratio < height_ratio ) {
                    return width_ratio;
                } else {
                    return height_ratio;
                }
            } else {
                if( width_ratio < height_ratio ) {
                    return height_ratio;
                } else {
                    return width_ratio;
                }
            }
        } else {
            return this.zoom;
        }
    }

    /**
     * refresh() - reapply the set zoom mode
     */
    this.refresh = function()
    {
        this.apply_zoom( this.compute_zoom() );
    };

    /**
     * set_zoom( zoom ) - set the zoom mode. If zoom is a positive number, the
     *   image is set to that zoom level. If zoom is a negative number, the
     *   image is zoomed by the given amount relative to the current zoom.
     *   Otherwise, zoom may be 'fit_inside' or 'fit_outside' which zoom the
     *   image relative to the container.
     */
    this.set_zoom = function( zoom )
    {
        if( zoom == 'fit_inside' || zoom == 'fit_outside' || zoom > 0 ) {
            this.zoom = zoom;
        } else if( zoom < 0 ) {
            this.zoom = this.compute_zoom();
            this.zoom *= -zoom;
        } else {
            // do nothing
        }

        this.refresh();
    };

    this.im = im;
    this.tab = tab;

    this.im_width = this.im.width;
    this.im_height = this.im.height;
    this.zoom = 'fit_inside';

    tab.data( 'viewer', this );

    this.refresh();
};

function register_image( im )
{
    tab = $( im ).closest( '.tab' );
    return new ImageViewer( tab, im );
}

function get_viewer( elem )
{
    tab = $( elem ).closest( '.tab' );
    return tab.data( 'viewer' );
}

function resize_image( elem, zoom )
{
    viewer = get_viewer( elem );
    if( viewer ) {
        viewer.set_zoom( zoom );
    }
}

function refresh_image( elem )
{
    viewer = get_viewer( elem );
    if( viewer ) {
        viewer.refresh();
    }
}
