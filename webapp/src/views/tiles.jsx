import * as React from 'react';

import $ from 'jquery';
import 'jquery-ui/ui/widgets/draggable';

import { load_async } from '../script';
import * as util from '../util';

class ThumbTile extends React.Component
{
    constructor( props ) {
        super( props );
        this.state = {
            imgSrc: '/img?id=' + this.props.obj_id + '&exp=' + this.props.metrics.exp_i
        }
    }
    componentDidMount() {
        this.drop_data = {
            view:   this.props.view,
            disp:   this.props.display,

            obj_id: this.props.obj_id,
            repr:   this.props.repr,
            type:   this.props.type,

            get_display: function() { return this.disp; },
            get_object: function() { return this.obj_id; },
            get_repr:   function() { return this.repr; },
            get_type:   function() { return this.type; },

            get_files: function() {
                if( this.view.selectionIndexOf( this.obj_id ) >= 0 ) {
                    return this.view.state.selection;
                } else {
                    return [ [ this.obj_id, this.repr, this.type ] ];
                }
            },
        };
        util.make_draggable( $( this.el ), this.drop_data );
    }
    componentDidUpdate() {
        $( this.el ).draggable( 'destroy' );
        this.componentDidMount();
    }
    onError() {
        this.setState( {
            imgSrc: '/static/hourglass.png'
        } )
    }
    render() {
        return (
            <div ref={ ( el ) => { this.el = el; } }
                 style={{
                     width: this.props.metrics.size,
                     height: this.props.metrics.size
                 }}
                 className={ 'thumbtile tilelink objitem sortable' + (this.props.selected ? ' selected' : '') }>
                <img src={ this.state.imgSrc }
                     style={{
                            maxWidth: '100%',
                            maxHeight: '100%',
                        }}
                     loading={ 'lazy' }
                     onError={ () => { this.onError() } }
                     onClick={ ( e ) => {
                            e.preventDefault();
                            this.props.view.itemClicked( e, this.drop_data );
                        } }/>
            </div>
        );
    }
}

class AlbumThumb extends React.Component
{
    render() {
        return (
            <div style={{
                     width: this.props.metrics.size,
                     height: this.props.metrics.size
                 }}>
                <img src={ '/img?id=' + this.props.obj_id + '&exp=' + this.props.metrics.exp_i }
                     loading={ 'lazy' }
                     style={{
                            maxWidth: '100%',
                            maxHeight: '100%',
                        }}/>
            </div>
        );
    }
}

class AlbumTile extends React.Component
{
    constructor( props ) {
        super( props );
        this.state = {}
    }
    componentDidMount() {
        this.drop_data = {
            view:   this.props.view,
            disp:   this.props.display,

            obj_id: this.props.obj_id,
            repr:   this.props.repr,
            type:   this.props.type,

            get_display: function() { return this.disp; },
            get_object: function() { return this.obj_id; },
            get_repr:   function() { return this.repr; },
            get_type:   function() { return this.type; },

            get_files: function() {
                if( this.view.selectionIndexOf( this.obj_id ) >= 0 ) {
                    return this.view.state.selection;
                } else {
                    return [ [ this.obj_id, this.repr, this.type ] ];
                }
            },
        };
        util.make_draggable( $( this.el ), this.drop_data );

        if( !this.state.files ) {
            this.loadContent();
        }
    }
    componentDidUpdate() {
        $( this.el ).draggable( 'destroy' );
        this.componentDidMount();
    }
    loadContent()
    {
        var request = {
            action:     'info',
            target:     this.props.obj_id,
            items:      [ 'short_files' ],
            fields:     [],
        };

        load_async( request, this.onContentLoaded.bind( this ), {} );
    }
    onContentLoaded( data, response ) {
        if( response.result == 'ok' ) {
            this.setState( { files: response.info.files } );
        } else {
            this.setState( { files: [] } );
        }
    }
    render() {
        var thumb_list = ( <span>{ 'Loading items...' }</span> );

        if( this.state.files ) {
            var items = this.state.files.map( it => (
                    <li key={ it[0] }>
                        <AlbumThumb obj_id={ it[0] } metrics={ this.props.metrics }/>
                    </li>
                ) );
            thumb_list = (
                    <ul className={ 'thumbslist' }
                        style={{
                            height: this.props.metrics.size
                        }}>
                        { items }
                    </ul>
                );
        }

        return (
            <div ref={ ( el ) => { this.el = el; } }
                 style={{
                     width: '100%',
                     height: this.props.metrics.size + 30,
                 }}
                 className={ 'albumtile tilelink objitem sortable' + (this.props.selected ? ' selected' : '') }>
                <a href='#' onClick={ ( e ) => {
                            e.preventDefault();
                            this.props.view.itemClicked( e, this.drop_data );
                        } }>
                    { this.props.repr }
                </a>
                { thumb_list }
            </div>
        );
    }
}

export class TileView extends React.Component
{
    componentDidMount() {
        if( this.props.display.is_sortable() ) {
            util.make_sortable( this.props.display, $( this.el ), this.props.index );
        }
    }
    componentDidUpdate() {
        if( this.props.display.is_sortable() ) {
            $( this.el ).droppable( 'destroy' );
        }
        this.componentDidMount();
    }
    render() {
        if( this.props.type.split( ':' )[0] == 'album' ) {
            return (
                <li ref={ ( el ) => { this.el = el; } }
                    style={{
                        width: '100%'
                    }}>
                    <AlbumTile display={ this.props.display }
                               view={ this.props.view }
                               selected={ this.props.selected }
                               metrics={ this.props.metrics }
                               obj_id={ this.props.obj_id }
                               repr={ this.props.repr }
                               type={ this.props.type }/>
                </li>
            );
        } else {
            return (
                <li ref={ ( el ) => { this.el = el; } }>
                    <ThumbTile display={ this.props.display }
                               view={ this.props.view }
                               selected={ this.props.selected }
                               metrics={ this.props.metrics }
                               obj_id={ this.props.obj_id }
                               repr={ this.props.repr }
                               type={ this.props.type }/>
                </li>
            );
        }
    }
}
