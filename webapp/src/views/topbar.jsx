import * as React from 'react';

import $ from 'jquery';
import 'jquery-ui/ui/widgets/droppable';

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

export class Trash extends React.Component
{
    componentDidMount() {
        $( this.el ).droppable({
            accept: '.objitem',
            hoverClass: 'ui-state-hover',
            drop: function( event, ui ) {
                if( ui.helper.is( '.dropped' ) ) {
                    return false;
                }

                var tab = tabs.active();
                var item = $( ui.draggable );

                if( tab && tab.onEvent ) {
                    tab.onEvent( {
                        type: 'trash',
                        drop_data: item.data( 'drop_data' )
                    } );
                }

                ui.helper.addClass( 'dropped' );
            },
        });
    }
    render() {
        return (
            <div id="trash" ref={ ( el ) => { this.el = el; } }>Trash</div>
        );
    }
}
