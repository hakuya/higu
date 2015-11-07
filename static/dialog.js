// module
var dialogs = (function() {

TAG_DIALOG_TEMPLATE =
    "<div id='tag-dialog' title='Tag Image'>"
  + "    <p>Enter a series of tags separated by spaces."
  + "    Prefix a tag with a dash to remove it<br/>"
  + "    <span id='tag-err-text' class='err-text'></span></p>"
  + "    <form id='tag-dialog-form' onsubmit='return false'><fieldset>"
  + "    <label for='tags'>Tags</label>"
  + "    <input type='text' name='tags' id='tags'/>"
  + "    </fieldset></form>"
  + "</div>";

DUP_DIALOG_TEMPLATE =
    "<div id='dup-dialog' title='Duplicate Image'>"
  + "    <p>Select the relationship of the dropped image:</p>"
  + ""
  + "    <form id='dup-dialog-form' onsubmit='return false'><fieldset>"
  + "    <input type='radio' name='dup' value='orig_dup'>Original of the duplicate in the tab</input><br/>"
  + "    <input type='radio' name='dup' value='orig_var'>Original of the variant in the tab</input><br/>"
  + "    <input type='radio' name='dup' value='duplicate'>Duplicate of the original in the tab</input><br/>"
  + "    <input type='radio' name='dup' value='variant'>Variant of the original in the tab</input><br/>"
  + "    </fieldset></form>"
  + "</div>";

NAME_DIALOG_TEMPLATE =
    "<div id='name-dialog' title='Tag Image'>"
  + "    <p>Enter a new filename</p>"
  + ""
  + "    <form id='name-dialog-form' onsubmit='return false'><fieldset>"
  + "    <label for='fname'>Name</label>"
  + "    <input type='text' name='fname' id='fname'/>"
  + "    <label for='saveold'>Save old name</label>"
  + "    <input type='checkbox' name='saveold' id='saveold'/>"
  + "    </fieldset></form>"
  + "</div>";

TEXT_DIALOG_TEMPLATE =
    "<div id='text-dialog' title='Info'>"
  + "    <textarea id='info-text' style='width:100%;height:100%;resize:none' readonly='true'></textarea>"
  + "</div>";

ERROR_DIALOG_TEMPLATE =
    "<div id='error-dialog' title='Oops, something went wrong'>"
  + "    <span id='error-msg'></span>"
  + "</div>";

/**
 * class TagDialog
 */
var TagDialog = function()

    // Constructor
    {
        this.elem = $( TAG_DIALOG_TEMPLATE );
        this.elem.data( 'obj', this );
        $( 'body' ).append( this.elem );

        this.elem.dialog({
            autoOpen: false,
            width: 600,
            height: 300,
            modal: true,
            buttons: {
                'Apply': function() {
                    $( this ).data( 'obj' ).close( true );
                },
                Cancel: function() {
                    $( this ).data( 'obj' ).close( false );
                }
            },
        });

        $( '#tag-dialog-form' ).submit( function() {
            $( '#tag-dialog' ).data( 'obj' ).close( true );
        });
    };

    TagDialog.prototype.open = function()
    {
        $( '#tag-err-text' ).html( '' );

        this.elem.dialog( 'open' );
        $( '#tags' ).focus();
        $( '#tags' ).select();
    };

    TagDialog.prototype.submit = function( tags )
    {
        var tab = tabs.active();

        if( tab.data( 'obj' ) ) {
            return tab.data( 'obj' ).tag( tags );
        } else {
            return { result: 'ok' };
        }
    };

    TagDialog.prototype.close = function( submit )
    {
        r = { result: 'ok' };

        if( submit ) {
            r = this.submit( $( '#tags' ).val() );
        }

        if( r.result == 'ok' ) {
            $( document ).focus();
            this.elem.dialog( 'close' );
        } else {
            $( '#tag-err-text' ).html( r.msg );
        }
    };

/**
 * class DupDialog
 */
var DupDialog = function()

    // Constructor
    {
        this.elem = $( DUP_DIALOG_TEMPLATE );
        this.elem.data( 'obj', this );
        $( 'body' ).append( this.elem );

        this.dropped = null;
        this.received = null;

        this.elem.dialog({
            autoOpen: false,
            width: 600,
            height: 300,
            modal: true,
            buttons: {
                'Apply': function() {
                    $( this ).data( 'obj' ).close( true );
                },
                Cancel: function() {
                    $( this ).data( 'obj' ).close( false );
                }
            },
        });

        $( '#dup-dialog-form' ).submit( function() {
            $( 'dup-dialog' ).data( 'obj' ).close( true );
        });
    };

    DupDialog.prototype.open = function( dropped, received )
    {
        this.dropped = dropped;
        this.received = received;
        this.elem.dialog( 'open' );
    };

    DupDialog.prototype.submit = function( result )
    {
        var tab = tabs.active();

        if( tab.data( 'obj' ) ) {
            tab = tab.data( 'obj' );

            if( result == 'orig_dup' ) {
                tab.set_duplication( this.dropped, this.received, true );
            } else if( result == 'orig_var' ) {
                tab.set_duplication( this.dropped, this.received, false );
            } else if( result == 'duplicate' ) {
                tab.set_duplication( this.received, this.dropped, true );
            } else if( result == 'variant' ) {
                tab.set_duplication( this.received, this.dropped, false );
            }
        }
    };

    DupDialog.prototype.close = function( submit )
    {
        if( submit ) {
            var result = this.elem.find( 'input:radio:checked' ).val();
            this.submit( result );
        }
        $( document ).focus();
        this.elem.dialog( 'close' );
    };

/**
 * class NameDialog
 */
var NameDialog = function()

    // Constructor
    {
        this.elem = $( NAME_DIALOG_TEMPLATE );
        this.elem.data( 'obj', this );
        $( 'body' ).append( this.elem );

        this.elem.dialog({
            autoOpen: false,
            width: 600,
            height: 300,
            modal: true,
            buttons: {
                'Apply': function() {
                    $( this ).data( 'obj' ).close( true );
                },
                Cancel: function() {
                    $( this ).data( 'obj' ).close( false );
                }
            },
        });
    };

    NameDialog.prototype.open = function()
    {
        $( '#fname' ).val( '' );
        this.elem.dialog( 'open' );
        $( '#fname' ).focus();
        $( '#fname' ).select();
    };

    NameDialog.prototype.submit = function( name, saveold )
    {
        var tab = tabs.active();

        if( tab.data( 'obj' ) && name ) {
            tab.data( 'obj' ).rename( name, saveold );
        }
    };

    NameDialog.prototype.close = function( submit )
    {
        if( submit ) {
            this.submit( $( '#fname' ).val(), 
                    $( '#saveold' ).is( ':checked' ) );
        }
        $( document ).focus();
        this.elem.dialog( 'close' );
    };

/**
 * class TextDialog
 */
var TextDialog = function()

    // Constructor
    {
        this.elem = $( TEXT_DIALOG_TEMPLATE );
        this.elem.data( 'obj', this );
        $( 'body' ).append( this.elem );

        this.elem.dialog({
            autoOpen: false,
            width: 800,
            height: 500,
            modal: true,
            buttons: {
                Cancel: function() {
                    $( this ).data( 'obj' ).close();
                }
            },
        });
    };

    TextDialog.prototype.open = function( text )
    {
        $( '#info-text' ).val( text );
        this.elem.dialog( 'open' );
    };

    TextDialog.prototype.close = function()
    {
        $( document ).focus();
        this.elem.dialog( 'close' );
    };

/**
 * class ErrorDialog
 */
var ErrorDialog = function()

    // Constructor
    {
        this.elem = $( ERROR_DIALOG_TEMPLATE );
        this.elem.data( 'obj', this );
        $( 'body' ).append( this.elem );

        this.elem.dialog({
            autoOpen: false,
            width: 800,
            height: 500,
            modal: true,
            buttons: {
                Cancel: function() {
                    $( this ).data( 'obj' ).close();
                }
            },
        });
    };

    ErrorDialog.prototype.open = function( msg )
    {
        $( '#error-msg' ).html( msg );
        this.elem.dialog( 'open' );
    };

    ErrorDialog.prototype.close = function()
    {
        $( document ).focus();
        this.elem.dialog( 'close' );
    };

var tag_dialog = null;
var dup_dialog = null;
var name_dialog = null;
var text_dialog = null;
var error_dialog = null;

var public_show_tag_dialog = function()
{
    if( tag_dialog == null ) {
        tag_dialog = new TagDialog();
    };

    tag_dialog.open();
};

var public_show_dup_dialog = function( dropped, received )
{
    if( dup_dialog == null ) {
        dup_dialog = new DupDialog();
    };

    dup_dialog.open( dropped, received );
};

var public_show_name_dialog = function()
{
    if( name_dialog == null ) {
        name_dialog = new NameDialog();
    };

    name_dialog.open();
};

var public_show_text_dialog = function( text )
{
    if( text_dialog == null ) {
        text_dialog = new TextDialog();
    };

    text_dialog.open( text );
};

var public_show_error_dialog = function( msg )
{
    if( error_dialog == null ) {
        error_dialog = new ErrorDialog();
    };

    error_dialog.open( msg );
};

return {
    show_tag_dialog: public_show_tag_dialog,
    show_dup_dialog: public_show_dup_dialog,
    show_name_dialog: public_show_name_dialog,
    show_text_dialog: public_show_text_dialog,
    show_error_dialog: public_show_error_dialog,
};

})();
