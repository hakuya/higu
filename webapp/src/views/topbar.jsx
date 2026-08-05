import * as React from 'react';

import Dropdown from 'react-bootstrap/Dropdown';
import DropdownButton from 'react-bootstrap/DropdownButton';

import $ from 'jquery';
import 'jquery-ui/ui/widgets/droppable';

import * as dialogs from '../controllers/dialogs';
import * as tabs from '../controllers/tabs';

import { SelectionProvider, SearchProvider } from '../models/providers';

class QueryLink extends React.Component
{
    handleClick() {
        var provider = new SearchProvider( { mode: this.props.mode } );
        tabs.create_display_tab( this.props.tabTitle, provider );
    }
    render() {
        return (
            <a href='#' onClick={ this.handleClick.bind( this ) }>{ this.props.label }</a>
         );
    }
}

class SelectionLink extends React.Component
{
    handleClick() {
        var provider = new SelectionProvider();
        tabs.create_display_tab( 'Selection ' + (provider.selection_id + 1), provider );
    }
    render() {
        return (
            <a href='#' onClick={ this.handleClick.bind( this ) }>selection</a>
         );
    }
}

class TaglistLink extends React.Component
{
    render() {
        return (
            <a href='#' onClick={ tabs.show_tagslist_tab }>taglist</a>
         );
    }
}

class AdminLink extends React.Component
{
    render() {
        return (
            <a href='#' onClick={ tabs.show_admin_tab }>admin</a>
         );
    }
}

class LoginLink extends React.Component
{
    render() {
        return (
            <a href='#' onClick={ tabs.show_login_tab }>login</a>
         );
    }
}

class QueryBox extends React.Component
{
    handleSubmit( evt ) {
        evt.preventDefault();

        var query = $( this.el ).children( 'input' ).val();
        if( query.startsWith( ">" ) ) {
            if( query.startsWith( ">sel " ) ) {
                var provider = new SelectionProvider();
                provider.init_query = query.replace( ">sel ", "" );
                tabs.create_display_tab( 'Selection ' + (provider.selection_id + 1), provider );
            } else {
                alert( "Bad target" );
            }
        } else {
            var provider = new SearchProvider( { query: query } );
            tabs.create_display_tab( query, provider );
        }

        $( this.el ).children( 'input' ).val( '' );
        $( document ).focus();
        return false;
    }
    render() {
        return (
            <form id='tagsearch'
                  ref={ ( el ) => { this.el = el; } }
                  style={{ display: 'inline' }}
                  onSubmit={ this.handleSubmit.bind( this ) }>
                <input type="text" className='nokb'/>
            </form>
         );
    }
}

export class Header extends React.Component
{
    render() {
        var username = localStorage.getItem( 'username' );

        if( username != null ) {
            return (
                <div id="header">
                    <a href='/do_logout'>logout</a> { ' / ' }
                    <QueryLink mode='all' tabTitle='All' label='all'/> { ' / ' }
                    <QueryLink mode='untagged' tabTitle='Untagged' label='untagged'/> { ' / ' }
                    <SelectionLink/> { ' / ' }
                    <TaglistLink/> { ' / ' }
                    { username == 'admin' &&
                        <AdminLink/>
                    }
                    { username == 'admin' && ' / ' }
                    <QueryBox/>
                </div>
             );
        } else {
            return (
                <div id="header">
                    <LoginLink/>
                </div>
            );
        }
    }
}

class PartitionAction extends React.Component
{
    render() {
        return (
            <Dropdown.Item
                onClick={ () => {
                        this.props.display.partition( this.props.dropData );
                    } }>
                    { 'Partition' }
            </Dropdown.Item>
        );
    }
}

class RemoveAction extends React.Component
{
    render() {
        return (
            <Dropdown.Item
                onClick={ () => {
                        this.props.display.on_event( {
                            type: 'trash',
                            drop_data: this.props.dropData,
                        } );
                    } }>
                    { this.props.label }
            </Dropdown.Item>
        );
    }
}

class TagAction extends React.Component
{
    render() {
        return (
            <Dropdown.Item
                onClick={ () => {
                        dialogs.show_tag_dialog( this.props.display );
                    } }>
                    { 'Tag' }
            </Dropdown.Item>
        );
    }
}

class NameAction extends React.Component
{
    render() {
        return (
            <Dropdown.Item
                onClick={ () => {
                        dialogs.show_name_dialog(
                                this.props.display,
                                this.props.display.info.repr );
                    } }>
                    { 'Name' }
            </Dropdown.Item>
        );
    }
}

class MakeSelectionAction extends React.Component
{
    render() {
        return (
            <Dropdown.Item
                onClick={ () => {
                        this.props.display.make_selection( this.props.inplace );
                    } }>
                    { this.props.inplace ? 'Extract Selection' : 'Make Selection' }
            </Dropdown.Item>
        );
    }
}

class MakeAlbumAction extends React.Component
{
    render() {
        return (
            <Dropdown.Item
                onClick={ () => {
                        this.props.display.make_group();
                    } }>
                    { 'Make Album' }
            </Dropdown.Item>
        );
    }
}

class ModifyAlbumAction extends React.Component
{
    render() {
        return (
            <Dropdown.Item
                onClick={ () => {
                        this.props.display.change_album( this.props.target );
                    } }>
                    { this.props.label }
            </Dropdown.Item>
        );
    }
}

class ModifyTagAction extends React.Component
{
    render() {
        return (
            <Dropdown.Item
                onClick={ () => {
                        this.props.display.change_tag( this.props.target );
                    } }>
                    { this.props.label }
            </Dropdown.Item>
        );
    }
}

class GatherTagsAction extends React.Component
{
    render() {
        return (
            <Dropdown.Item
                onClick={ () => {
                        this.props.display.gather_tags();
                    } }>
                    { 'Gather Tags' }
            </Dropdown.Item>
        );
    }
}

class TransformFileAction extends React.Component
{
    render() {
        return (
            <Dropdown.Item
                onClick={ () => {
                        this.props.display.transform( this.props.transform );
                    } }>
                    { this.props.label }
            </Dropdown.Item>
        );
    }
}

export class ActionsGroup extends React.Component
{
    constructor( props ) {
        super( props );
        this.state = {
            display: null,
            view: null,
            selected: null,
            gen: 0
        };
    }

    componentDidMount() {
        tabs.register_tabs_listener( this );
    }

    // for tab_listener
    on_tab_added( tab ) {}
    on_tab_removed( tab ) {}
    on_tab_selected( tab ) {
        if( tab !== null && tab.type == 'display' ) {
            this.setState( {
                display: tab.display,
                view: tab.view,
                selected: tab.display.selected_items,
                gen: this.state.gen,
            } );
        } else {
            this.setState( {
                display: null,
                view: null,
                selected: null,
                gen: 0,
            } );
        }
    }
    on_tab_changed( tab ) {
        if( tabs.active().id == tab.id ) {
            this.on_tab_selected( tab );
        }
    }
    on_tab_event( e ) {
        if( e.type == 'selected_items_changed'
         && e.display == this.state.display )
        {
            this.setState( {
                display: this.state.display,
                view: this.state.view,
                selected: this.state.display.selected_items,
                gen: this.state.gen,
            } );
        } else if( e.affected
            && this.state.display
            && this.state.display.obj_id
            && e.affected.indexOf( this.state.display.obj_id ) >= 0 )
        {
            this.setState( {
                display: this.state.display,
                view: this.state.view,
                selected: this.state.selected,
                gen: this.state.gen + 1,
            } );
        }
    }

    selection_drop_data() {
        return {
            view:   this.state.view,
            disp:   this.state.display,

            obj_id: this.state.selected[0][0],
            repr:   this.state.selected[0][1],
            type:   this.state.selected[0][2],

            files:  [...this.state.selected],

            get_display: function() { return this.disp; },
            get_object: function() { return this.obj_id; },
            get_repr:   function() { return this.repr; },
            get_type:   function() { return this.type; },

            get_files: function() {
                return this.files;
            },
        };
    }

    renderSelectedItemsObjectContext() {
        return (
            <div id='editmenu'>
                { this.state.selected.length + ' selected' }
                <DropdownButton size='sm' algin='end' title='Edit'>
                    <PartitionAction
                        display={ this.state.display }
                        dropData={ this.selection_drop_data() }/>
                    <Dropdown.Divider/>
                    <RemoveAction
                        label='Remove'
                        display={ this.state.display }
                        dropData={ this.selection_drop_data() }/>
                </DropdownButton>
            </div>
        );
    }

    renderSelectedItemsSelectionContext() {
        return (
            <div id='editmenu'>
                { this.state.selected.length + ' selected' }
                <DropdownButton size='sm' algin='end' title='Edit'>
                    <MakeSelectionAction display={ this.state.display } inplace={ false }/>
                    <MakeSelectionAction display={ this.state.display } inplace={ true }/>
                    <Dropdown.Divider/>
                    <MakeAlbumAction display={ this.state.display }/>
                    <Dropdown.Divider/>
                    <RemoveAction
                        label='Remove'
                        display={ this.state.display }
                        dropData={ this.selection_drop_data() }/>
                </DropdownButton>
            </div>
        );
    }

    renderFileContext() {
        return (
            <div id='editmenu'>
                <DropdownButton size='sm' align='end' title='Edit'>
                    <TagAction display={ this.state.display }/>
                    <NameAction display={ this.state.display }/>
                    <Dropdown.Divider/>
                    <TransformFileAction
                        label='Auto'
                        transform='auto_orientation'
                        display={ this.state.display }/>
                    <TransformFileAction
                        label='Rotate CCW'
                        transform='rotate_ccw'
                        display={ this.state.display }/>
                    <TransformFileAction
                        label='Rotate CW'
                        transform='rotate_cw'
                        display={ this.state.display }/>
                    <TransformFileAction
                        label='Mirror'
                        transform='mirror'
                        display={ this.state.display }/>
                    <Dropdown.Divider/>
                    <RemoveAction
                        label='Delete'
                        display={ this.state.display }
                        dropData={ this.state.display.get_obj_drop_data() }/>
                </DropdownButton>
            </div>
        );
    }

    renderAlbumContext() {
        var album_type = this.state.display.info.type.split( ':' )[1];
        return (
            <div id='editmenu'>
                <DropdownButton size='sm' align='end' title='Edit'>
                    <TagAction display={ this.state.display }/>
                    <NameAction display={ this.state.display }/>
                    <Dropdown.Divider/>
                    <GatherTagsAction display={ this.state.display }/>
                    <Dropdown.Divider/>
                    { album_type == 'formal' &&
                        <ModifyAlbumAction
                            label='Make Free'
                            target='free'
                            display={ this.state.display }/>
                    }
                    { album_type == 'free' &&
                        <ModifyAlbumAction
                            label='Make Formal'
                            target='formal'
                            display={ this.state.display }/>
                    }
                    { album_type == 'closed' &&
                        <ModifyAlbumAction
                            label='Open Album'
                            target='formal'
                            display={ this.state.display }/>
                    }
                    { album_type == 'formal' &&
                        <ModifyAlbumAction
                            label='Close Album'
                            target='closed'
                            display={ this.state.display }/>
                    }
                    <Dropdown.Divider/>
                    <RemoveAction
                        label='Delete'
                        display={ this.state.display }
                        dropData={ this.state.display.get_obj_drop_data() }/>
                </DropdownButton>
            </div>
        );
    }

    renderTagContext() {
        var sorting = this.state.display.info.type.split( ':' )[1];
        return (
            <div id='editmenu'>
                <DropdownButton size='sm' align='end' title='Edit'>
                    <NameAction display={ this.state.display }/>
                    <Dropdown.Divider/>
                    { sorting != 'unordered' &&
                        <ModifyTagAction
                            label='Remove Sort'
                            target='unordered'
                            display={ this.state.display }/>
                    }
                    { sorting != 'ordered' &&
                        <ModifyTagAction
                            label='Make Sorted'
                            target='ordered'
                            display={ this.state.display }/>
                    }
                    { sorting != 'nameorder' &&
                        <ModifyTagAction
                            label='Sort by Name'
                            target='nameorder'
                            display={ this.state.display }/>
                    }
                    { sorting != 'dateorder' &&
                        <ModifyTagAction
                            label='Sort by Date'
                            target='dateorder'
                            display={ this.state.display }/>
                    }
                    <Dropdown.Divider/>
                    <RemoveAction
                        label='Delete'
                        display={ this.state.display }
                        dropData={ this.state.display.get_obj_drop_data() }/>
                </DropdownButton>
            </div>
        );
    }

    renderImportContext() {
        return (
            <div id='editmenu'>
                <DropdownButton size='sm' align='end' title='Edit'>
                    <MakeAlbumAction display={ this.state.display }/>
                </DropdownButton>
            </div>
        );
    }

    renderSelectionContext() {
        return (
            <div id='editmenu'>
                <DropdownButton size='sm' align='end' title='Edit'>
                    <TagAction display={ this.state.display }/>
                    <Dropdown.Divider/>
                    <MakeAlbumAction display={ this.state.display }/>
                </DropdownButton>
            </div>
        );
    }

    renderDefaultContext() {
        return (
            <div id='editmenu'>
                <DropdownButton size='sm' align='end' title='Edit' disabled={true}>
                </DropdownButton>
            </div>
        );
    }

    render() {
        if( this.state.selected !== null ) {
            if( this.state.display.type == 'object' ) {
                return this.renderSelectedItemsObjectContext();
            } else if( this.state.display.type == 'selection' ) {
                return this.renderSelectedItemsSelectionContext();
            }
        } else if( this.state.display !== null ) {
            if( this.state.display.type == 'object' ) {
                var obj_type = this.state.display.info.type.split(':')[0];
                if( obj_type == 'file' ) {
                    return this.renderFileContext();
                } else if( obj_type == 'album' ) {
                    return this.renderAlbumContext();
                } else if( obj_type == 'tag' ) {
                    return this.renderTagContext();
                } else if( obj_type == 'import' ) {
                    return this.renderImportContext();
                }
            } else if( this.state.display.type == 'selection' ) {
                return this.renderSelectionContext();
            }
        }
        // Not supported / handled
        return this.renderDefaultContext();
    }
}
