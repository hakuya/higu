import { DisplayableBase } from "./controllers/displayable";
import { DisplayableObject } from "./controllers/object";
import { DisplayableSelection } from "./controllers/selection";

import { ImageView, ThumbView, HtmlView } from "./controllers/view";

function make_file_display( obj_id, info, fields )
{
    return {
        disp: new DisplayableObject( obj_id, info, fields ),
        view: new ImageView()
    }
};

function make_group_display( obj_id, info, fields )
{
    return {
        disp: new DisplayableObject( obj_id, info, fields ),
        view: new ThumbView()
    }
};

export function make_dummy_display( msg )
{
    return {
        disp: new DisplayableBase(),
        view: new HtmlView( '<p>' + msg + '</p>')
    }
};

/**
 * make_object_display( obj_id ) - factory method for creating
 * the appropriate display.
 */
export function make_object_display( info, fields )
{
    if( info.type == 'file'
     || info.type == 'duplicate' )
    {
        return make_file_display( info.object_id, info, fields );
    } else if( info.type == 'album'
            || info.type == 'published' )
    {
        return make_group_display( info.object_id, info, fields );
    } else {
        return make_dummy_display( 'This is a placeholder for an object '
            + 'that does not exist or has been removed.' );
    }
};

/**
 * make_selection_display()
 */
export function make_selection_display()
{
    return {
        disp: new DisplayableSelection(),
        view: new ThumbView()
    }
};
