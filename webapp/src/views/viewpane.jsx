import * as React from 'react';

import $ from 'jquery';
import 'jquery-ui/ui/widgets/draggable';

import * as tabs from '../controllers/tabs';
import { SingleProvider, SelectionProvider } from '../models/providers';

import { TileView } from './tiles';

class TileViewPane extends React.Component
{
    constructor( props ) {
        super( props );
        this.state = {
            selection: []
        };

        this.props.view.pane = this;
    }
    openItem( drop_data ) {
        var provider = this.props.display.create_provider( { start_id: drop_data.get_object() } );

        if( !provider ) {
            provider = new SingleProvider( drop_data.get_object() );
        }

        tabs.create_display_tab( drop_data.get_repr(), provider );
    }
    removeItem( drop_data ) {
        this.props.display.on_event( {
                type: 'trash',
                drop_data: drop_data,
            } );
    }
    setSelection( selection ) {
        this.props.display.set_selected_items( selection );
        this.setState( { selection: selection } );
    }
    toggleSelection( drop_data ) {
        if( this.selectionIndexOf( drop_data.get_object() ) < 0 ) {
            this.setSelection(
                this.state.selection.concat(
                            [ [ drop_data.get_object(),
                                drop_data.get_repr(),
                                drop_data.get_type() ] ] )
            );
        } else {
            this.setSelection(
                this.state.selection.filter( ( it ) => {
                                return it[0] != drop_data.get_object();
                            } )
            );
        }
    }
    toggleSelectAll() {
        if( this.state.selection.length == 0 ) {
            this.setSelection( [].concat( this.props.display.get_files() ) );
        } else {
            this.setSelection( [] );
        }
    }
    selectUntil( drop_data ) {
        // don't do anything if already selected
        if( this.selectionIndexOf( drop_data.get_object() ) >= 0 ) return;

        if( this.state.selection.length == 0 ) {
            this.toggleSelection( drop_data );
            return;
        }

        var files = this.props.display.get_files();

        // index of the new item in the list of files
        var newIdx = files.findIndex( ( it ) => {
                        return it[0] == drop_data.get_object();
                    } );

        if( newIdx < 0 ) return;

        // index of the last selection in the list of files
        var lastIdx = files.findIndex( ( it ) => {
                        return it[0] == this.state.selection[this.state.selection.length - 1][0];
                    } );

        if( lastIdx == newIdx ) return;

        if( lastIdx < 0 ) {
            this.toggleSelection( drop_data );
            return;
        }

        var dir = (newIdx > lastIdx ? 1 : -1);

        var new_selection = this.state.selection;
        for( var i = lastIdx + dir; i != newIdx; i += dir ) {
            if( this.selectionIndexOf( files[i][0] ) < 0 ) {
                new_selection = new_selection.concat( [ files[i] ] );
            }
        }
        if( this.selectionIndexOf( files[newIdx][0] ) < 0 ) {
            new_selection = new_selection.concat( [ files[newIdx] ] );
        }
        this.setSelection( new_selection );
    }
    itemClicked( e, drop_data ) {
        if( e.metaKey ) {
            if( e.shiftKey ) {
                this.removeItem( drop_data );
            } else {
                this.toggleSelection( drop_data );
            }
        } else if( e.shiftKey ) {
            this.selectUntil( drop_data );
        } else {
            this.openItem( drop_data );
        }
    }
    onEvent( e ) {
        if( e.type == 'key' ) {
            switch( e.charCode ) {
                case 96: // `
                    this.toggleSelectAll();
                    break;
                default:
                    break;
            }
        }
    }
    selectionIndexOf( obj_id )
    {
        return this.state.selection.findIndex( ( it ) => {
                    return it[0] == obj_id;
                } );
    }
    computeMetrics() {
        // Calculate the thumb tile exponent
        var exp_w = 0;
        while( (window.innerWidth / (1 << exp_w)) > 16 ) exp_w++;

        // Calculate the exponent for the thumb image
        var factor_i = 0;
        while( window.devicePixelRatio > (1 << factor_i) ) factor_i++;
        var exp_i = exp_w + factor_i;

        return {
            exp_w: exp_w,
            exp_i: exp_i,
            size: (1 << exp_w),
        };
    }
    componentDidUpdate() {
        // We need to filter our selection, to 'deselect' items that no longer exist
        var files = this.props.display.get_files();
        var new_selection = this.state.selection.filter( ( it ) => {
                                return files.findIndex( ( jt ) => {
                                            return jt[0] == it[0];
                                        } ) >= 0;
                            } );
        if( new_selection.length != this.state.selection.length ) {
            this.setState( { selection: new_selection } );
        }
    }
    render() {
        // Workaround for jQuery exection when removing draggable during
        // drag event
        //div.find( '.objitem' ).remove();
        //div.html( '' );

        var group_id = this.props.display.get_obj_id();
        var files = this.props.display.get_files();

        var metrics = this.computeMetrics();

        return (
            <div className='disp' ref={ ( el ) => { this.el = el; } }>
                <ul className='thumbslist'>
                    {
                        files.map( ( it, i ) => (
                            <TileView key={ it[0] }
                                      display={ this.props.display }
                                      view={ this }
                                      selected={ this.selectionIndexOf( it[0] ) >= 0 }
                                      metrics={ metrics }
                                      obj_id={ it[0] }
                                      repr={ it[1] }
                                      type={ it[2] }
                                      index={ i }/>
                        ) )
                    }
                    <li style={{
                            width: metrics.size,
                            height: metrics.size
                        }}/>
                </ul>
            </div>
        );
    }
}

class MiscViewPane extends React.Component
{
    componentDidMount() {
        this.componentDidUpdate();
    }
    componentDidUpdate() {
        this.props.view.display_view( this.props.display, $( this.el ) );
    }
    render() {
        return (
            <div className='disp' ref={ ( el ) => { this.el = el; } }></div>
        );
    }
}

export class ViewPane extends React.Component
{
    render() {
        if( this.props.view.type == 'thumb' ) {
            return (
                <TileViewPane display={ this.props.display }
                              view={ this.props.view }
                              gen={ this.props.gen }/>
            );
        } else {
            return (
                <MiscViewPane display={ this.props.display }
                              view={ this.props.view }
                              gen={ this.props.gen }/>
            );
        }
    }
}
