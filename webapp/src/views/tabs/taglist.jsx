import * as React from 'react';

import { load_async } from '../../script';
import * as dialogs from '../../controllers/dialogs';

import { TagLink } from '../links';

export class TaglistTab extends React.Component {
    constructor( props ) {
        super( props );
        this.state = {}

        this.props.data.onEvent = ( e ) => {
            if( e.type == 'info_changed' ) {
                this.loadContent();
            }
        };

        this.loadContent();
    }
    loadContent()
    {
        load_async( { action: 'taglist' }, this.onContentLoaded.bind( this ), {} );
    }
    onContentLoaded( data, response ) {
        if( response.result == 'ok' ) {
            this.setState( { tags: response.tags } );
        } else {
            dialogs.show_error_dialog( xhr.responseText );
        }
    }
    render() {
        if( this.state.tags ) {
            var tags = this.state.tags.map( it => {
                        var m = it[0].match( /(.*):(.*)/ );
                        return (m == null) ? [ null, it[0], it[0], it[1] ] : [ m[1], m[2], it[0], it[1] ];
                    } );
            var groups = [];
            while( tags.length > 0 ) {
                var group = tags[0][0];
                var gtags = tags.filter( it => it[0] == group ).map( it => [ it[1], it[2], it[3] ] );
                tags = tags.filter( it => it[0] != group );
                groups.push( [ group, gtags ] );
            }
            var rendered_tags = groups.map( ( it ) => (
                <div key={ it[0] } className='taggroup'>
                  { it[0] != null && <h1>{ it[0] }</h1> }
                  <ul className='taglist'>
                    { it[1].map( jt => ( <li key={ jt[1] }><TagLink label={ jt[0] + ' (' + jt[2] + ')' } tag={ jt[1] }/></li> ) ) }
                  </ul>
                </div>
            ) );
            return (
                <div className='tab'>
                    { rendered_tags }
                </div>
            );
        } else {
            return (
                <div className='tab'>
                    { 'Loading...' }
                </div>
            );
        }
    }
}
