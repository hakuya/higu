
// module
var dialogs = (function() {

var dialogs = [];

var public_register_dialog = function( name, obj )
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

var public_show_dialog = function( name, data )
{
    var dialog = dialogs.find( ( it ) => { return it.name == name; } );
    dialog.obj.show( data );
};

var public_show_tag_dialog = function()
{
    public_show_dialog( 'tag', {} );
};

var public_show_dup_dialog = function( dropped, received )
{
    public_show_dialog( 'dup', {
        dropped: dropped,
        received: received,
    });
};

var public_show_name_dialog = function()
{
    public_show_dialog( 'name', {} );
};

var public_show_text_dialog = function( text )
{
    public_show_dialog( 'text', {
        text: text
    } );
};

var public_show_error_dialog = function( msg )
{
    public_show_dialog( 'err', {
        msg: msg
    } );
};

return {
    register_dialog: public_register_dialog,
    show_tag_dialog: public_show_tag_dialog,
    show_dup_dialog: public_show_dup_dialog,
    show_name_dialog: public_show_name_dialog,
    show_text_dialog: public_show_text_dialog,
    show_error_dialog: public_show_error_dialog,
};

})();
