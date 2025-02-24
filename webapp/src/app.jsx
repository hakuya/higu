import * as React from 'react';
import { createRoot } from 'react-dom/client';

import $ from 'jquery';
import 'jquery-ui/ui/widgets/droppable';

import * as tabs from './controllers/tabs';

import { Header, ActionsGroup } from './views/topbar';
import { TabsView } from './views/tabs';

import {
    TagDialog,
    DupDialog,
    NameDialog,
    TextDialog,
    ErrorDialog
} from './views/dialogs';

class MainView extends React.Component
{
    render() {
        return (
            <div id='main'>
                <TabsView/>
            </div>
        );
    }
}

class Application extends React.Component
{
  render() {
    return (
       <div id="page">
         <div>
           <Header/>
           <ActionsGroup/>
         </div>
         <MainView/>

         <TagDialog/>
         <DupDialog/>
         <NameDialog/>
         <TextDialog/>
         <ErrorDialog/>
       </div>
     );
   }
}

var window_width = 0;
var window_height = 0;

$( function() {

let root = createRoot( document.getElementById( 'app' ) );
root.render( <Application/> );

$(document).keypress( function( e ) {
    if( $( '.modal-dialog' ).is( ':visible' ) || $( '.nokb' ).is( ':focus' ) ) {
        return;
    }

    e = window.event || e;

    var tab = tabs.active();

    if( tab && tab.onEvent ) {
        tab.onEvent( { type: 'key', charCode: e.charCode } );
    }
});

$( window ).resize( function() {
    var width = window.innerWidth;
    var height = window.innerHeight;

    if( width == window_width && height == window_height ) return;

    window_width = width;
    window_height = height;

    var tab = tabs.active();
    if( tab ) {
        if( tab.obj && tab.obj.display ) {
            tab.obj.on_event( { type: 'resized' } );
        }
    }
} );

$( window ).resize();

});
