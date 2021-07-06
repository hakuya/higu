var QueryLink = React.createClass({
    handleClick: function() {
        var provider = new tabs.SearchProvider( { mode: this.props.mode } );
        tabs.create_display_tab( this.props.tabTitle, provider );
    },
    render: function() {
        return (
            <a href='#' onClick={ this.handleClick }>{ this.props.label }</a>
         );
    }
});

var SelectionLink = React.createClass({
    handleClick: function() {
        var provider = new tabs.SelectionProvider();
        tabs.create_display_tab( 'Selection ' + (provider.selection_id + 1), provider );
    },
    render: function() {
        return (
            <a href='#' onClick={ this.handleClick }>selection</a>
         );
    }
});

var TaglistLink = React.createClass({
    render: function() {
        return (
            <a href='#' onClick={ tabs.show_tagslist_tab }>taglist</a>
         );
    }
});

var AdminLink = React.createClass({
    render: function() {
        return (
            <a href='#' onClick={ tabs.show_admin_tab }>admin</a>
         );
    }
});

var LoginLink = React.createClass({
    render: function() {
        return (
            <a href='#' onClick={ tabs.show_login_tab }>login</a>
         );
    }
});

var QueryBox = React.createClass({
    mountRef: function( el ) {
        this.el = el;
    },
    handleSubmit: function() {
        var tags = $( this.el ).children( 'input' ).val();

        var provider = new tabs.SearchProvider( { query: tags } );
        tabs.create_display_tab( tags, provider );

        $( this.el ).children( 'input' ).val( '' );
        $( document ).focus();
        return false;
    },
    render: function() {
        return (
            <form id='tagsearch' ref={ this.mountRef } style={{ display: 'inline' }} onSubmit={ this.handleSubmit }>
                <input type="text" className='nokb'/>
            </form>
         );
    }
});

var Header = React.createClass({
    render: function() {
        if( document.username != null ) {
            return (
                <div id="header">
                    <a href='/do_logout'>logout</a> { ' / ' }
                    <QueryLink mode='all' tabTitle='All' label='all'/> { ' / ' }
                    <QueryLink mode='untagged' tabTitle='Untagged' label='untagged'/> { ' / ' }
                    <SelectionLink/> { ' / ' }
                    <TaglistLink/> { ' / ' }
                    { document.username == 'admin' &&
                        <AdminLink/>
                    }
                    { document.username == 'admin' && ' / ' }
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
});

var Trash = React.createClass({
    mountRef: function( el ) {
        this.el = el;
    },
    componentDidMount: function() {
        $( this.el ).droppable({
            accept: '.objitem',
            hoverClass: 'ui-state-hover',
            drop: function( event, ui ) {
                if( ui.helper.is( '.dropped' ) ) {
                    return false;
                }

                tab = tabs.active();
                item = $( ui.draggable );
                
                tab = tab.data( 'obj' );
                if( tab && tab.rm ) {
                    tab.rm( item.data( 'drop_data' ) );
                }

                ui.helper.addClass( 'dropped' );
            },
        });
    },
    render: function() {
        return (
            <div id="trash" ref={ this.mountRef }>Trash</div>
        );
    }
});

var WelcomeTab = React.createClass({
    render: function() {
        return (
            <div className='tab' id='welcome-tab'>
                <h2>Welcome to Higu</h2>

                <p>Higu is a tag oriented image organizer with an advanced web interface</p>
            </div>
        );
    }
});

var TabsView = React.createClass({
    componentDidMount: function() {
        tabs.init();
    },
    render: function() {
        return (
            <div id='tabs'>
                <ul>
                    <li><a href='#welcome-tab'>Begin</a></li>
                </ul>
                <WelcomeTab/>
            </div>
        );
    }
});

var MainView = React.createClass({
    render: function() {
        return (
            <div id='main'>
                <TabsView/>
            </div>
        );
    }
});

var Application = React.createClass({
  render: function() {
    return (
       <div id="page">
         <Header/>
         <Trash/>
         <MainView/>
       </div>
     );
   }
});

var window_width = 0;
var window_height = 0;

$( function() {

ReactDOM.render(
  <Application/>,
  document.getElementById('app')
);

$(document).keypress( function( e ) {
    if( $( '.ui-dialog' ).is( ':visible' ) || $( '.nokb' ).is( ':focus' ) ) {
        return;
    }

    e = window.event || e;

    tab = tabs.active();

    obj = tab.data( 'obj' );
    if( obj && obj.display ) {
        switch( e.charCode ) {
            case 116: // t
                dialogs.show_tag_dialog();
                break;
            case 114: // r
                dialogs.show_name_dialog();
                break;
            case 65: // A
                select_all();
                break;
            case 97: // a
                obj.on_event( { type: 'zoom', zoom: -0.5 } )
                break;
            case 115: // s
                obj.on_event( { type: 'zoom', zoom: -2.0 } )
                break;
            case 122: // z
                obj.on_event( { type: 'zoom', zoom: 1.0 } )
                break;
            case 120: // x
                obj.on_event( { type: 'zoom', zoom: 'fit_outside' } )
                break;
            case 99:  // c
                obj.on_event( { type: 'zoom', zoom: 'fit_inside' } )
                break;
            case 106: // j
                obj.down();
                break;
            case 107: // k
                obj.up();
                break;

            case 49: // 1-9
            case 50:
            case 51:
            case 52:
            case 53:
            case 54:
            case 55:
            case 56:
            case 57:
            case 58:
                obj.on_event( { type: 'push_selection', selection: e.charCode - 49 } )
                break;

            case 48: // 0
                obj.on_event( { type: 'push_selection', selection: 10 } )

            default:
        }
    }
});

$( window ).resize( function() {
    var width = window.innerWidth;
    var height = window.innerHeight;

    if( width == window_width && height == window_height ) return;

    window_width = width;
    window_height = height;

    var head_h = $( '#header' ).height();
    var main_h = height - head_h;

    $( '#main' ).height( main_h - 50 );
    $( '#tabs' ).tabs( 'refresh' );

    var tab = tabs.active();
    var obj = tab.data( 'obj' );
    if( obj && obj.display ) {
        obj.on_event( { type: 'resized' } );
    }
} );

$( window ).resize();

});
