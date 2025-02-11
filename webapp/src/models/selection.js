var selection_map = [];

export function register_selection( selection )
{
    var i = 0;
    for( var i = 0; i < selection_map.length; i++ ) {
        if( selection_map[i] == null ) {
            selection_map[i] = selection;
            return i;
        }
    }

    selection_map.push( selection );
    return i;
};

export function unregister_selection( selection )
{
    for( var i = 0; i < selection_map.length; i++ ) {
        if( selection_map[i] === selection ) {
            selection_map[i] = null;
        }
    }
};

export function get_selection( idx )
{
    if( selection_map.length > idx ) {
        return selection_map[idx];
    } else {
        return null;
    }
}