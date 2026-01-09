import * as React from 'react';
import * as ReactBootstrap from 'react-bootstrap';

import $ from 'jquery';

import { load_async } from '../../script';
import * as dialogs from '../../controllers/dialogs';
import * as tabs from '../../controllers/tabs';

export class AdminTab extends React.Component {
    componentDidMount() {
        // Delete
        var button = $( '#adm-tag-rm-button' );
        button.click( function( e ) {
            var src = $( '#adm-tag-src' );
            var tgt = $( '#adm-tag-tgt' );

            var request = {
                action:     'tag_delete',
                tag:        src.val(),
            };
            load_async(
                    request,
                    function( data, response )
                    {
                        tabs.on_event( { type: 'info_changed' } );
                        src.val( '' );
                        tgt.val( '' );
                    },
                    {}
                );
        });

        // Copy
        button = $( '#adm-tag-cp-button' );
        button.click( function( e ) {
            var src = $( '#adm-tag-src' );
            var tgt = $( '#adm-tag-tgt' );

            var request = {
                action:     'tag_copy',
                tag:        src.val(),
                target:     tgt.val(),
            };
            load_async(
                    request,
                    function( data, response )
                    {
                        tabs.on_event( { type: 'info_changed' } );
                        src.val( '' );
                        tgt.val( '' );
                    },
                    {}
                );
        });

        // Move
        button = $( '#adm-tag-mv-button' );
        button.click( function( e ) {
            var src = $( '#adm-tag-src' );
            var tgt = $( '#adm-tag-tgt' );

            var request = {
                action:     'tag_move',
                tag:        src.val(),
                target:     tgt.val(),
            };
            load_async(
                    request,
                    function( data, response )
                    {
                        tabs.on_event( { type: 'info_changed' } );
                        src.val( '' );
                        tgt.val( '' );
                    },
                    {}
                );
        });
    }
    doBulk( commit ) {
        var select = $( '#adm-bulk-select' );
        var exec = $( '#adm-bulk-exec' );

        var request = {
            action:     'bulk',
            query:      select.val(),
            exec:       exec.val(),
            commit:     commit
        };

        load_async( request, this.doBulkCallback.bind( this ), {} );
    }
    doBulkCallback( data, response )
    {
        if( response.result == 'ok' ) {
            var lines = [ response.affected + ' rows affected' ];
            lines = lines.concat( response.changes.map( ( it ) => {
                                        return it[0] + ': ' + it[1];
                                    } ));

            dialogs.show_text_dialog( lines.join( '\n' ), null );
        } else {
            alert( response.msg );
        }
    }
    render() {
        var Button = ReactBootstrap.Button;

        return (
            <div className='tab' ref={ ( el ) => { this.el = el } }>
                <h1>Tag Management</h1>
                <form>
                  Src: <input type="text" id="adm-tag-src"/>,
                  Dst: <input type="text" id="adm-tag-tgt"/><br/>
                  <input type="button" id="adm-tag-rm-button" value="Delete"/>
                  <input type="button" id="adm-tag-cp-button" value="Copy"/>
                  <input type="button" id="adm-tag-mv-button" value="Move"/>
                </form><hr/>

                <h1>Bulk Operation</h1>
                <form>
                  { 'Select: ' } <input type="text" id="adm-bulk-select"/>
                  { ' Execute: ' } <input type="text" id="adm-bulk-exec"/><br/>
                  <input type="button" value="Run" onClick={ ( e ) => {
                            e.preventDefault();
                            this.doBulk( true );
                        } }/>
                  <input type="button" value="Pretend" onClick={ ( e ) => {
                            e.preventDefault();
                            this.doBulk( false );
                        } }/>

                </form>
            </div>
        );
    }
}
