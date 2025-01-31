/**
 * class Viewer
 */
ImageViewer = function( pane, image_info )
{
    this.get_container_dims = function()
    {
        tab = this.pane.closest( '.tab' );
        container_width = tab.width() - tab.find( '.info' ).width() - 20;
        container_height = this.pane.height();

        return [ container_width, container_height ]
    };

    this.choose_image_dims = function()
    {
        if( this.im_width == null ) return null;

        cd = this.get_container_dims();
        rd = [ cd[1] * this.im_width / this.im_height,
               cd[0] * this.im_height / this.im_width ];

        if( this.zoom == 'fit_inside' ) {
            if( cd[1] < rd[1] ) {
                // Height constrainted
                return [ rd[0], cd[1] ];
            } else {
                // Width constrainted
                return [ cd[0], rd[1] ];
            }
        } else if( this.zoom == 'fit_outside' ) {
            if( cd[1] < rd[1] ) {
                // Height constrainted
                return [ cd[0], rd[1] ];
            } else {
                // Width constrainted
                return [ rd[0], cd[1] ];
            }
        } else {
            return [ this.im_width * this.zoom,
                     this.im_height * this.zoom ];
        }
    }

    /**
     * apply_zoom( zoom ) - zoom the image to the given amount
     */
    this.apply_zoom_css = function( im )
    {
        dims = this.choose_image_dims();
        if( !dims ) return;

        im.width( dims[0] );
        im.height( dims[1] );
    };

    this.apply_zoom = function()
    {
        if( this.im == null ) return;

        var im = $( this.im );
        var src = this.choose_src();

        if( src != im.attr( 'src' ) ) {
            im.attr( 'src', src );
        }

        this.apply_zoom_css( im );
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
        if( zoom < 0 ) {
            if( typeof this.zoom == 'number' ) {
                this.zoom *= -zoom;
            } else {
                this.zoom = 1.0;
            }
        } else {
            this.zoom = zoom;
        }
        this.apply_zoom();
    };

    this.on_image_loaded = function( im )
    {
        this.im = im;

        if( this.im_width == null ) {
            this.im_width = im.width;
            this.im_height = im.height;
        }
        this.apply_zoom();
    };

    this.choose_src = function()
    {
        s = '/img?id=' + this.image_info.obj_id;

        if( this.image_info.sizes && this.image_info.sizes.length > 0 ) {
            var dims = this.choose_image_dims();
            var size = null;
            for( var i = 0; i < this.image_info.sizes.length; i++ ) {
                size = this.image_info.sizes[i];
                if( size[1] >= dims[0] && size[2] >= dims[1] ) {
                    break;
                }
            }
            if( size[0] != null ) {
                s += '&exp=' + size[0];
            }
        }

        if( this.image_info.stream_id ) {
            s += '&stream=' + this.image_info.stream_id;
        }

        if( this.image_info.gen ) {
            s += '&gen=' + this.image_info.gen;
        }

        return s;
    }

    this.attach_image = function()
    {
        if( this.image_info.sizes && this.image_info.sizes.length > 0 ) {
            this.im_width = this.image_info.sizes[ this.image_info.sizes.length - 1][1];
            this.im_height = this.image_info.sizes[ this.image_info.sizes.length - 1][2];
        }

        var img_tag = $( '<img class="objitem" src="' + this.choose_src() + '" '
                       + 'onload="on_image_loaded( this )"/>' );

        this.apply_zoom_css( img_tag );

        util.make_draggable( img_tag, util.make_basic_drop_data( null,
                                            this.image_info.obj_id,
                                            this.image_info.repr,
                                            this.image_info.type ) );

        pane.append( img_tag );
    }

    this.pane = pane;
    this.image_info = image_info;

    this.im = null;
    this.im_width = null;
    this.im_height = null;
    this.im_src = null;
    this.zoom = 'fit_inside';

    this.attach_image();

    pane.data( 'viewer', this );
};

function attach_image( pane, image_info )
{
    return new ImageViewer( pane, image_info );
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
