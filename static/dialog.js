var tag_dialog;
var dup_dialog;
var error_dialog;

function init_dialog()
{

/**
 * class tag_dialog
 */
tag_dialog = new function()
{
    this.elem = $( '#tag-dialog' );
    this.elem.data( 'obj', this );

    // Begin Constructor
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
    // End Constructor

    this.open = function()
    {
        this.elem.dialog( 'open' );
        $( '#tags' ).focus();
        $( '#tags' ).select();
    };

    this.submit = function( tags )
    {
        var tab = tabs.active();

        if( tab.data( 'obj' ) ) {
            tab.data( 'obj' ).tag( tags );
        }
    }

    this.close = function( submit )
    {
        if( submit ) {
            this.submit( $( '#tags' ).val() );
        }
        $( document ).focus();
        this.elem.dialog( 'close' );
    }
};

/**
 * class dup_dialog
 */
dup_dialog = new function()
{
    this.elem = $( '#dup-dialog' );
    this.elem.data( 'obj', this );

    this.dropped = null;
    this.received = null;

    // Begin Constructor
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
    // End Constructor

    this.open = function( dropped, received )
    {
        this.dropped = dropped;
        this.received = received;
        this.elem.dialog( 'open' );
    };

    this.submit = function( result )
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

    this.close = function( submit )
    {
        if( submit ) {
            var result = this.elem.find( 'input:radio:checked' ).val();
            this.submit( result );
        }
        $( document ).focus();
        this.elem.dialog( 'close' );
    };
};

/**
 * class name_dialog
 */
name_dialog = new function()
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

    this.open = function()
    {
        $( '#fname' ).val( '' );
        this.elem.dialog( 'open' );
        $( '#fname' ).focus();
        $( '#fname' ).select();
    };

    this.submit = function( name, saveold )
    {
        var tab = tabs.active();

        if( tab.data( 'obj' ) && name ) {
            tab.data( 'obj' ).rename( name, saveold );
        }
    }

    this.close = function( submit )
    {
        if( submit ) {
            this.submit( $( '#fname' ).val(), 
                    $( '#saveold' ).is( ':checked' ) );
        }
        $( document ).focus();
        this.elem.dialog( 'close' );
    }
};

/**
 * class error_dialog
 */
error_dialog = new function()
{
    this.elem = $( '#error-dialog' );
    this.elem.data( 'obj', this );

    // Begin Constructor
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
    // End Constructor

    this.open = function( msg )
    {
        $( '#error-msg' ).html( msg );
        this.elem.dialog( 'open' );
    };

    this.close = function()
    {
        $( document ).focus();
        this.elem.dialog( 'close' );
    }
};

} // end init_dialog()

function open_rename_dialog( saveold_allowed ) {
    $( '#saveold' ).disabled( !saveold_allowed );
    $( '#name-dialog' ).dialog( 'open' );
    $( '#fname' ).focus();
}
