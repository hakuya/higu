import * as React from 'react';
import * as ReactBootstrap from 'react-bootstrap';

import * as tabs from '../controllers/tabs';

import { WelcomeTab } from './tabs/welcome';
import { DisplayTab } from './tabs/display';
import { LoginTab } from './tabs/login';
import { AdminTab } from './tabs/admin';
import { TaglistTab } from './tabs/taglist';

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

    on_tab_changed( tab ) {}
    on_tab_event( e ) {}

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
