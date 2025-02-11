
import * as React from 'react';

import $ from 'jquery';
import 'jquery-ui/ui/widgets/draggable';

import * as dialogs from '../controllers/dialogs';
import * as tabs from '../controllers/tabs';
import * as util from '../util';

import { ObjectLink, TagLink } from './links';

class ObjectList extends React.Component
{
    render() {
        return (
            <span>
                { this.props.label } { ' ' }
                    { this.props.objects.map( ( it, i ) => (
                        <span key={ i }>
                            { i > 0 && ', ' }
                            <ObjectLink label={ it[1] }
                                        target={ it[0] }
                                        actions={
                                            this.props.actions
                                                ?  this.props.actions.map( ( jt ) => {
                                                        return {
                                                            label: jt.label,
                                                            onClick: () => {
                                                                jt.onClick( it[0] );
                                                            }
                                                        }
                                                    } )
                                                : null
                                        }/>
                        </span>
                    ) ) }
            </span>
        );
    }
}

class ObjectLabel extends React.Component
{
    componentDidMount() {
        var d = this.props.display;
        util.make_draggable( $( this.el ), util.make_basic_drop_data(
            d, d.obj_id, d.info.repr, d.info.type ) );
    }
    componentDidUpdate() {
        $( this.el ).draggable( 'destroy' );
        this.componentDidMount();
    }
    starClicked( value ) {
        this.props.display.set_field( 'rating', value );
    }
    renderRatingStar( value, current ) {
        return (
            <a href='#' onClick={ () => { this.starClicked( value ) } }>
                { current >= value ? "\u2605" : "\u2606" }
            </a>
        );
    }
    renderRating() {
        var d = this.props.display;
        return (
            <div>
                { this.renderRatingStar( 2, d.fields.rating ) }
                { this.renderRatingStar( 4, d.fields.rating ) }
                { this.renderRatingStar( 6, d.fields.rating ) }
                { this.renderRatingStar( 8, d.fields.rating ) }
                { this.renderRatingStar( 10, d.fields.rating ) }
            </div>
        );
    }
    render() {
        var d = this.props.display;
        return (
            <div className='objitem'>
                { d.info.album &&
                  <div className='alblabel'>{ d.info.album[1] + ' /' }</div> }
                <div className='objlabel objitem' ref={ ( el ) => { this.el = el; } }>
                    <ObjectLink label={ d.info.repr } target={ d.obj_id }/>
                </div>
                <div className='objinfo'>
                    <div>{ 'id: ' } { d.obj_id }</div>
                    { this.renderRating() }
                    { (d.info.type == 'file' || d.info.type == 'duplicate') &&
                        <div>{ d.info.width } { 'x' } { d.info.height }</div> }
                    { (d.info.type == 'album' || d.info.type == 'published') &&
                        <div>{ d.info.files.length } { 'images' }</div> }
                </div>
            </div>
        );
    }
}

class SelectionLabel extends React.Component
{
    componentDidMount() {
        var d = this.props.display;
        util.make_draggable( $( this.el ), {
            selection: this,

            get_display: function() { return d; },
            get_object: function() { return null; },
            get_files:  function() { return d.get_files(); },
            get_repr:   function() { return 'Selection'; },
            get_type:   function() { return 'selection'; },
        });
    }
    componentDidUpdate() {
        $( this.el ).draggable( 'destroy' );
        this.componentDidMount();
    }
    render() {
        var d = this.props.display;
        return (
            <div className='objlabel objitem' ref={ ( el ) => { this.el = el; } }>
                { 'Selection' }
            </div>
        );
    }
}

class ObjectInfoPane extends React.Component
{
    renderAlternates( info ) {
        var d = this.props.display;
        return (
            <div>
                <h1>Alternates</h1>
                { d.stream_id !== null &&
                    <a href='#' onClick={ () => {
                                    d.set_as_main_stream( null );
                                } }>
                        { 'Set as Main' }
                    </a>
                }
                { d.stream_id !== null && <br/> }
                { d.stream_id !== null &&
                    <a href='#' onClick={ () => {
                                    d.show_stream( null );
                                } }>
                        { 'View Main' }
                    </a>
                }
                { d.stream_id !== null && <br/> }
                { 'Duplicates:' }
                { info.dup_streams.map( ( it, i ) => (
                    <span key={i}> { ' ' }
                        <a href='#' onClick={ () => {
                                        d.show_stream( it );
                                    } }>
                            { ( i + 1 ) }
                        </a>
                    </span>
                ) ) }
            </div>
        );
    }
    hasLinks( info ) {
        return info.albums && info.albums.length > 0
            || info.original_file
            || info.variants_of && info.variants_of.length > 0
            || info.variants && info.variants.length > 0
            || info.duplicates && info.duplicates.length > 0
    }
    renderLinks( info ) {
        return (
            <div>
                { info.albums && info.albums.length > 0 &&
                    <ObjectList label='Albums: ' objects={ info.albums }/>
                }
                { info.albums && info.albums.length > 0 && <br/> }
                { info.original_file &&
                    <ObjectList label='Duplicate of: ' objects={ [ info.original_file ] }/>
                }
                { info.original_file && <br/> }
                { info.variants_of && info.variants_of.length > 0 &&
                    <ObjectList label='Variant of: '
                                objects={ info.variants_of }
                                actions={ [ {
                                    label: 'del',
                                    onClick: ( obj_id ) => {
                                        var d = this.props.display;
                                        d.clear_variant( obj_id, d.get_obj_id() );
                                    }
                                } ] }/>
                }
                { info.variants_of && info.variants_of.length > 0 && <br/> }
                { info.variants && info.variants.length > 0 &&
                    <ObjectList label='Variants: '
                                objects={ info.variants }
                                actions={ [ {
                                    label: 'del',
                                    onClick: ( obj_id ) => {
                                        var d = this.props.display;
                                        d.clear_variant( d.get_obj_id(), obj_id );
                                    }
                                } ] }/>
                }
                { info.variants && info.variants.length > 0 && <br/> }
                { info.duplicates && info.duplicates.length > 0 &&
                    <ObjectList label='Duplicates: '
                                objects={ info.duplicates }
                                actions={ [ {
                                    label: 'del',
                                    onClick: ( obj_id ) => {
                                        var d = this.props.display;
                                        d.unlink_duplicate( d.get_obj_id(), obj_id );
                                    }
                                } ] }/>
                }
                { info.duplicates && info.duplicates.length > 0 && <br/> }
            </div>
        )
    }
    renderFileInfo( info ) {
        return (
            <div>
                { info.type == 'file' &&
                    <span>
                        { 'Transform: ' }
                        <a href='#' onClick={ () => {
                                            this.props.display.transform( 'auto_orientation' )
                                        } }>
                            { 'auto' }
                        </a> { ' | ' }
                        <a href='#' onClick={ () => {
                                            this.props.display.transform( 'rotate_ccw' )
                                        } }>
                            { 'ccw' }
                        </a> { ' | ' }
                        <a href='#' onClick={ () => {
                                            this.props.display.transform( 'rotate_cw' )
                                        } }>
                            { 'cw' }
                        </a> { ' | ' }
                        <a href='#' onClick={ () => {
                                            this.props.display.transform( 'mirror' )
                                        } }>
                            { 'mirror' }
                        </a>
                    </span>
                }
                { info.type == 'file' && <br/> }
                { this.props.display.stream_id === null &&
                    <a href={ '/img?id=' + this.props.display.obj_id } target='_blank'>
                        { 'View Fullsize' }
                    </a>
                }
                { this.props.display.stream_id !== null &&
                    <a href={ '/img?id=' + this.props.display.obj_id
                            + '&stream=' + this.props.display.stream_id }
                       target='_blank'>
                        { 'View Fullsize' }
                    </a>
                }
                { info.dup_streams && info.dup_streams.length > 0 &&
                    this.renderAlternates( info )
                }
            </div>
        )
    }
    renderGroupInfo( info ) {
        return (
            <div>
                { info.text &&
                    <a href='#' onClick={ () => {
                                    dialogs.show_text_dialog( info.text );
                                } }>
                        { 'View text' }
                    </a>
                }
                { info.text && <br/> }
                <a href='#' onClick={ () => {
                                this.props.display.gather_tags();
                            } }>
                    { 'Gather Tags' }
                </a>
            </div>
        );
    }
    renderExifInfo( info ) {
        var keys = Object.keys( info.exif );

        return (
            <table className='exiftable'>
                {
                    keys.map( ( it ) => (
                        <tr key={ it }>
                            <td> { it + ':' } </td> <td> { info.exif[it] } </td>
                        </tr>
                    ) )
                }
            </table>
        );
    }
    render() {
        var info = this.props.display.info;

        return (
            <div className='iteminfo'>
                <ObjectLabel display={ this.props.display }/> <br/>
                <h1>Tags</h1>
                <ul className='infotaglist'>
                    { info.tags &&
                        info.tags.map( ( it ) => (
                            <li key={ it }><TagLink label={ it } tag={ it }/></li>
                        ) )
                    }
                </ul>
                <h1>Names</h1>
                <ul className='infonamlist'>
                    { info.names &&
                        info.names.map( ( it ) => (
                            <li key={ it }>{ it }</li>
                        ) )
                    }
                </ul>
                <hr/>
                { info.origin_time &&
                    <span> { 'Created: ' } { info.origin_time } </span>
                }
                { info.origin_time && <br/> }
                { info.creation_time &&
                    <span> { 'Added: ' } { info.creation_time } </span>
                }
                <hr/>
                { this.hasLinks( info ) &&
                    this.renderLinks( info )
                }
                { this.hasLinks( info ) && <hr/> }
                { info.exif != null &&
                    this.renderExifInfo( info )
                }
                { info.exif && <hr/> }
                { (info.type == 'file' || info.type == 'duplicate') &&
                    this.renderFileInfo( info )
                }
                { (info.type == 'album' || info.type == 'published') &&
                    this.renderGroupInfo( info )
                }
            </div>
        );
    }
}

class SelectionInfoPane extends React.Component
{
    render() {
        var info = this.props.display.info;

        return (
            <div className='iteminfo'>
                <SelectionLabel display={ this.props.display }/> <br/>
                <h1>Options</h1>
                <ul>
                    <li><a href='#' onClick={ () => {
                                        this.props.display.sort_by_id();
                                    } }>
                        { 'Sort by ID' }
                    </a></li>
                    <li><a href='#' onClick={ () => {
                                        this.props.display.sort_by_name();
                                    } }>
                        { 'Sort by Name' }
                    </a></li>
                    <li><a href='#' onClick={ () => {
                                        this.props.display.reverse_sort();
                                    } }>
                        { 'Reverse Sort' }
                    </a></li>
                    <li><a href='#' onClick={ () => {
                                        this.props.display.make_group();
                                    } }>
                        { 'Make Album' }
                    </a></li>
                </ul>
            </div>
        );
    }
}

export class InfoPane extends React.Component
{
    render() {
        if( this.props.display.type == 'object' ) {
            return ( <ObjectInfoPane display={ this.props.display } gen={ this.props.gen }/> );
        } else if( this.props.display.type == 'selection' ) {
            return ( <SelectionInfoPane display={ this.props.display } gen={ this.props.gen }/> );
        } else {
            return ( <div/> );
        }
    }
}

export class NavigatePane extends React.Component
{
    doNextPress() {
        var tab = tabs.active();

        if( tab && tab.onEvent ) {
            tab.onEvent( { type: 'navigate', direction: 'next' } );
        }
    }
    doPrevPress() {
        var tab = tabs.active();

        if( tab && tab.onEvent ) {
            tab.onEvent( { type: 'navigate', direction: 'prev' } );
        }
    }
    render() {
        return (
            <div className='navigate'>
                <div className='prev'>
                    <a href='#' onClick={ this.doPrevPress }> { '<< prev' } </a>
                </div>
                <div className='count'>
                    { (this.props.provider.index + 1) + ' of ' + this.props.provider.count }
                </div>
                <div className='next'>
                    <a href='#' onClick={ this.doNextPress }> { 'Next >>' } </a>
                </div>
            </div>
        );
    }
}
