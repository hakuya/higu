import { attach_image } from './image';

/**
 * class ViewBase
 */
class ViewBase
{
    display_view( disp, div )
    {
        div.html( '&nbsp;' );
    }

    on_event( e )
    {}
}

export class HtmlView extends ViewBase
{
    constructor( html )
    {
        super();
        this.html = html;
    }

    display_view( disp, div )
    {
        div.html( this.html );
    }
}

/**
 * class ImageView
 */
export class ImageView extends ViewBase
{
    constructor()
    {
        super();
        this.viewer = null;
    }

    display_view( disp, div )
    {
        div.html( '' );

//        if( !disp.info.mime ) {
//            div.append( 'Image not available<br/>' );
//            return;
//        }

        var image_info = {
            obj_id: disp.obj_id,
            repr: disp.info.repr,
            type: disp.info.type,
            gen: disp.info.thumb_gen,
        };

        if( disp.stream_id !== null ) {
            image_info.stream_id = disp.stream_id;
        } else {
            image_info.sizes = disp.info.sizes;
        }

        this.viewer = attach_image( div, image_info );

        div.append( '<br/>' );
    }

    on_event( e )
    {
        if( !this.viewer ) {
            return;
        }

        if( e.type == 'key' ) {
            switch( e.charCode ) {
                case 97: // a
                    this.on_event( { type: 'zoom', zoom: -0.5 } )
                    break;
                case 115: // s
                    this.on_event( { type: 'zoom', zoom: -2.0 } )
                    break;
                case 122: // z
                    this.on_event( { type: 'zoom', zoom: 1.0 } )
                    break;
                case 120: // x
                    this.on_event( { type: 'zoom', zoom: 'fit_outside' } )
                    break;
                case 99:  // c
                    this.on_event( { type: 'zoom', zoom: 'fit_inside' } )
                    break;
                default:
                    break;
            }
        } else if( e.type == 'resized' || e.type == 'focused' ) {
            this.viewer.refresh();
        } else if( e.type == 'zoom' ) {
            this.viewer.set_zoom( e.zoom );
        }
    }
}

export class ThumbView extends ViewBase
{
    constructor()
    {
        super();

        this.selection = [];
        this.type = 'thumb';
        this.pane = null;
    }

    on_event( e )
    {
        if( this.pane ) {
            this.pane.onEvent( e );
        }
    }
}
