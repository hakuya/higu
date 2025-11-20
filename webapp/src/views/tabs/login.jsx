import * as React from 'react';
import $ from 'jquery';
import * as dialogs from '../../controllers/dialogs';

export class LoginTab extends React.Component {
    handleSubmit( e ) {
        e.preventDefault();

        var username = $( this.el ).children( '#username' );
        var password = $( this.el ).children( '#password' );

        var result = null;

        $.ajax( {
            url:            '/do_login',
            type:           'POST',
            data:           { username: username.val(),
                              password: password.val(),
                              json: 1 },
            dataType:       'json',
            async:          false,
            success:        function( response ) {
                result = response;
            },
            error:          function( xhr ) {
                dialogs.show_error_dialog( xhr.responseText );
            }
        } );

        if( result != null && result.success ) {
            localStorage.setItem( 'username', result.username );
            localStorage.setItem( 'session_id', result.session_id );
            document.location.href = '/';
        } else {
            if( result != null ) {
                alert( 'Bad username or password ');
            }

            username.val( '' );
            password.val( '' );
        }
    }
    render() {
        return (
            <div className='tab'>
                <form ref={ ( el ) => { this.el = el; } }
                      onSubmit={ this.handleSubmit.bind( this ) }>
                  Username: <input type="text" id="username"/>,
                  Password: <input type="password" id="password"/>
                  <input type="submit" value="Login"/>
                </form>
            </div>
        );
    }
}
