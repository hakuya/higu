var dialogs = [];

export function register_dialog( name, obj )
{
    var dialog = dialogs.find( ( it ) => { return it.name == name; } );
    if( dialog ) {
        dialog.obj = obj;
    } else {
        dialog = {
            name: name,
            obj: obj,
        }
        dialogs.push( dialog );
    }
};

function show_dialog( name, data )
{
    var dialog = dialogs.find( ( it ) => { return it.name == name; } );
    dialog.obj.show( data );
};

export function show_tag_dialog( obj )
{
    show_dialog( 'tag', { obj: obj } );
};

export function show_dup_dialog( obj, dropped, received )
{
    show_dialog( 'dup', {
        obj: obj,
        dropped: dropped,
        received: received,
    });
};

export function show_name_dialog( obj )
{
    show_dialog( 'name', { obj: obj } );
};

export function show_text_dialog( text, savecb )
{
    show_dialog( 'text', {
        text: text,
        savecb: savecb
    } );
};

export function show_error_dialog( msg )
{
    show_dialog( 'err', {
        msg: msg
    } );
};
