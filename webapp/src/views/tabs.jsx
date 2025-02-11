import * as React from 'react';
import * as ReactBootstrap from 'react-bootstrap';

import $ from 'jquery';
import 'jquery-ui/ui/widgets/draggable';

import { load_async } from '../script';
import * as dialogs from '../controllers/dialogs';
import * as tabs from '../controllers/tabs';

import { InfoPane, NavigatePane } from './infopane';
import { ViewPane } from './viewpane';
import { TagLink } from './links';

class WelcomeTab extends React.Component
{
    render() {
        return (
            <div className='tab' id='welcome-tab'>
                <h2>Welcome to Higu</h2>

                <p>Higu is a tag oriented image organizer with an advanced web interface</p>
            </div>
        );
    }
}

class DisplayTab extends React.Component
{
    constructor( props ) {
        super( props );
        this.state = {}

        this.props.data.onEvent = ( e ) => { this.onEvent( e ) };
    }

    bumpGen( bump_info, bump_view )
    {
        this.setState( {
            display: this.state.display,
            view: this.state.view,
            disp_gen: this.state.disp_gen,
            info_gen: this.state.info_gen + (bump_info ? 1 : 0),
            view_gen: this.state.view_gen + (bump_view ? 1 : 0)
        } );
    }

    onEvent( e )
    {
        if( e.type == 'key' && e.charCode == 106 /* j */
         || e.type == 'navigate' && e.direction == 'next' )
        {
            this.props.data.provider.next();
            // will trigger onDisplayReady when loaded
        } else if( e.type == 'key' && e.charCode == 107 /* k */
                || e.type == 'navigate' && e.direction == 'prev' )
        {
            this.props.data.provider.prev();
            // will trigger onDisplayReady when loaded
        } else if( e.type == 'key' && e.charCode == 114 /* r */ ) {
            this.props.data.provider.reload();
            // will trigger onDisplayReady when loaded
        } else {
            if( this.state.display ) {
                this.state.display.on_event( e );
                this.state.view.on_event( e );

                if( e.affected
                 && e.affected.indexOf( this.state.display.get_obj_id() ) != -1
                 && e.type == 'removed' )
                {
                    this.setDisplay( displib.make_dummy_display( 'This object has been removed' ) );
                }
            }
        }
    }

    setDisplay( display )
    {
        if( this.state.display ) {
            this.state.display.unregister_change_listener( this );
        }
        display.disp.register_change_listener( this );
        this.setState( {
            display: display.disp,
            view: display.view,
            disp_gen: this.state.disp_gen ? this.state.disp_gen + 1 : 1,
            info_gen: this.state.info_gen ? this.state.info_gen + 1 : 1,
            view_gen: this.state.view_gen ? this.state.view_gen + 1 : 1
        } );
    }

    onDisplayReady( display )
    {
        this.setDisplay( display );
    }

    on_displayable_changed( disp, e )
    {
        this.bumpGen( true, (e == null || e.type == 'files_changed') );
    }

    componentDidMount()
    {
        var nav = $( '#tabs-tab-' + this.props.data.id );

        nav.data( 'tab', this );
        nav.droppable({
            accept: '.objitem',
            hoverClass: 'ui-state-hover',
            drop: function( event, ui ) {
                if( ui.helper.is( '.dropped' ) ) {
                    return false;
                }

                var tab = $( this ).data( 'tab' );
                var item = $( ui.draggable );

                var drop_method = 'add';
                if( event.metaKey ) {
                    drop_method = 'move';
                }

                if( tab && tab.onEvent ) {
                    tab.onEvent( {
                        type: 'drop',
                        drop_method: drop_method,
                        drop_data: item.data( 'drop_data' )
                    } );
                }

                item.draggable( 'option', 'revert', false );
                ui.helper.addClass( 'dropped' );
            },
        });

        this.props.data.provider.init( this.onDisplayReady.bind( this ) );
    }

    render() {
        if( this.state.display ) {
            return (
                <div className='tab'
                     ref={ ( el ) => { this.el = el } }>
                    <div className='info'>
                        <InfoPane display={ this.state.display }
                                  key={ 'i' + this.state.disp_gen }
                                  gen={ this.state.info_gen }/>
                        { this.props.data.provider.count &&
                          this.props.data.provider.count > 1 &&
                            <NavigatePane provider={ this.props.data.provider }/> }
                    </div>
                    <ViewPane display={ this.state.display }
                              view={ this.state.view }
                              key={ 'v' + this.state.disp_gen }
                              gen={ this.state.view_gen }/>
                </div>
            );
        } else {
            return (
                <div className='tab'
                     ref={ ( el ) => { this.el = el } }>
                    { 'Loading...' }
                </div>
            );
        }
    }
}

class LoginTab extends React.Component {
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

class AdminTab extends React.Component {
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

            dialogs.show_text_dialog( lines.join( '\n' ) );
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

class TaglistTab extends React.Component {
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

class ContentTab extends React.Component {
    render() {
        if( this.props.data.type == 'display' ) {
            return ( <DisplayTab data={ this.props.data }/> );
        } else if( this.props.data.type == 'login' ) {
            return ( <LoginTab/> );
        } else if( this.props.data.type == 'admin' ) {
            return ( <AdminTab/> );
        } else if( this.props.data.type == 'taglist' ) {
            return ( <TaglistTab data={ this.props.data }/> );
        } else {
            return ( <div className='tab'/> );
        }
    }
}

export class TabsView extends React.Component
{

    constructor( props ) {
        super( props );
        this.state = {
            tabs: tabs.all_tabs(),
            active_key: 'welcome'
        };
    }

    componentDidMount() {
        tabs.init();
        tabs.register_tabs_listener( this );
    }

    on_tab_added( tab ) {
        var active_tab = tabs.active();
        this.setState( {
            tabs: tabs.all_tabs(),
            active_key: active_tab != null ? active_tab.id : 'welcome'
        } );
    }

    on_tab_removed( tab ) {
        var active_tab = tabs.active();
        this.setState( {
            tabs: tabs.all_tabs(),
            active_key: active_tab != null ? active_tab.id : 'welcome'
        } );
    }

    on_tab_selected( tab ) {
        var active_tab = tabs.active();
        this.setState( {
            tabs: tabs.all_tabs(),
            active_key: active_tab != null ? active_tab.id : 'welcome'
        } );
    }

    render() {
        var tab_components = tabs.all_tabs().map( ( it, idx ) => (
            <ReactBootstrap.Tab key={ it.id }
                                eventKey={ it.id }
                                title={ <span>
                                        { it.title }
                                        { it.onClose &&
                                            <span onClick={ () => {
                                                it.onClose();
                                            } }>{ '(X)' }</span>
                                        }
                                    </span> }>
                <ContentTab data={ it }/>
            </ReactBootstrap.Tab>
        ) );
        return (
            <ReactBootstrap.Tabs defaultActiveKey='welcome'
                                 activeKey={ this.state.active_key }
                                 onSelect={ ( key ) => { tabs.select( key ); } }
                                 id="tabs">
                <ReactBootstrap.Tab eventKey="welcome" title="Begin">
                    <WelcomeTab/>
                </ReactBootstrap.Tab>
                { tab_components }
            </ReactBootstrap.Tabs>
        );
    }
}
