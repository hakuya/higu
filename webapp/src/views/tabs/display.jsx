import * as React from 'react';

import $ from 'jquery';
import 'jquery-ui/ui/widgets/draggable';

import * as tabs from '../../controllers/tabs';
import * as displib from '../../displib';

import { InfoPane, NavigatePane } from '../infopane';
import { ViewPane } from '../viewpane';

export class DisplayTab extends React.Component
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
        this.props.data.display = display.disp;
        this.props.data.view = display.view;
        tabs.notify_tab_changed( this.props.data );
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
