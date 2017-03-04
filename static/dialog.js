// module
var dialogs = (function() {

/**
 * class TagDialog
 */
var TagDialog = function()

    // Constructor
    {
        this.elem = $( '#tag-dialog' );
        this.elem.data( 'obj', this );

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
        this.elem = $( '#dup-dialog' );
        this.elem.data( 'obj', this );

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

            if( result == 'duplicate' ) {
                tab.merge_duplicates( this.received, this.dropped );
            } else if( result == 'variant' ) {
                tab.set_variant( this.received, this.dropped );
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
        this.elem = $( '#name-dialog' );
        this.elem.data( 'obj', this );

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
        this.elem = $( '#text-dialog' );
        this.elem.data( 'obj', this );

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
        this.elem = $( '#error-dialog' );
        this.elem.data( 'obj', this );

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
