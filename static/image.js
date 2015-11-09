/**
 * class Viewer
 */
ImageViewer = function( pane, obj_id, gen, repr, type )
{
    this.get_container_dims = function()
    {
        tab = this.pane.closest( '.tab' );
        container_width = tab.width() - tab.find( '.info' ).width() - 20;
        container_height = this.pane.height();

        return [ container_width, container_height ]
    };

    /**
     * apply_zoom( zoom ) - zoom the image to the given amount
     */
    this.apply_zoom = function( zoom )
    {
        if( this.im == null ) return;

        this.im.width = this.im_width * zoom;
        this.im.height = this.im_height * zoom;
    };

    this.compute_zoom = function()
    {
        if( this.im == null ) return null;

        if( this.zoom == 'fit_inside' || this.zoom == 'fit_outside' ) {
            container_dims = this.get_container_dims();

            width_ratio = 1.0 * container_dims[0] / this.im_width;
            height_ratio = 1.0 * container_dims[1] / this.im_height;

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
        if( this.im == null ) return;

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
        if( this.im == null ) return;

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

    this.on_image_loaded = function( im )
    {
        this.im = im;

        this.im_width = im.width;
        this.im_height = im.height;
        this.zoom = 'fit_inside';

        this.refresh();
    };

    this.pane = pane;

    this.im = null;
    this.im_width = null;
    this.im_height = null;
    this.zoom = null;

    dpr = window.devicePixelRatio;
    container_dims = this.get_container_dims();

    exp_w = 0;
    exp_h = 0;
    while( (1 << exp_w) < container_dims[0] * dpr ) exp_w++;
    while( (1 << exp_h) < container_dims[1] * dpr ) exp_h++;

    exp = Math.min( exp_w, exp_h );

    img_tag = $( '<img class="objitem" src="/img?id=' + obj_id
            + '&exp=' + exp + '&gen=' + gen + '" class="picture" '
            + 'onload="on_image_loaded( this )"/>' );

    util.make_draggable( img_tag, obj_id, repr, type );
    pane.append( img_tag );

    pane.data( 'viewer', this );
};

function attach_image( pane, id, gen, repr, type )
{
    return new ImageViewer( pane, id, gen, repr, type );
}

function on_image_loaded( im )
{
    pane = $( im ).closest( '.disp' );
    viewer = pane.data( 'viewer' )

    viewer.on_image_loaded( im );
}

function get_viewer( elem )
{
    pane = $( elem ).find( '.disp' )
    return pane.data( 'viewer' );
}
