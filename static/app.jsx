class QueryLink extends React.Component
{
    handleClick() {
        var provider = new tabs.SearchProvider( { mode: this.props.mode } );
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
        var provider = new tabs.SelectionProvider();
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

        var tags = $( this.el ).children( 'input' ).val();

        var provider = new tabs.SearchProvider( { query: tags } );
        tabs.create_display_tab( tags, provider );

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

class Header extends React.Component
{
    render() {
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
}

class Trash extends React.Component
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

class TabsView extends React.Component
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
                <window.Tabs.ContentTab data={ it }/>
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

class MainView extends React.Component
{
    render() {
        return (
            <div id='main'>
                <TabsView/>
            </div>
        );
    }
}

class TagDialog extends React.Component
{
    constructor( props ) {
        super( props );
        this.state = {
            show: false,
            query: '',
            errText: ''
        }
    }
    show( data ) {
        this.setState( {
            show: true,
            query: this.state.query,
            errText: ''
        } );
        this.obj = data.obj;
    }
    onApply( evt ) {
        evt.preventDefault();

        var tags = $( '#tags' ).val();
        var r = this.obj.tag( tags );

        if( r.result == 'ok' ) {
            $( document ).focus();
            this.setState( {
                show: false,
                query: tags,
                errText: ''
            } );
        } else {
            this.setState( {
                show: true,
                query: tags,
                errText: r.msg
            } );
        }
    }
    onCancel() {
        this.setState( {
            show: false,
            query: this.state.query,
            errText: ''
        } );
    }
    onEntered() {
        $( '#tags' ).focus();
        $( '#tags' ).select();
    }
    componentDidMount() {
        dialogs.register_dialog( 'tag', this );
    }
    render() {
        var Button = ReactBootstrap.Button;
        var Modal = ReactBootstrap.Modal;

        return (
            <Modal show={ this.state.show }
                   onEntered={ this.onEntered.bind( this ) }
                   onHide={ this.onCancel.bind( this ) }>
                <Modal.Header closeButton>
                    <Modal.Title>Tag Image</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <p>Enter a series of tags separated by spaces.
                    Prefix a tag with a dash to remove it<br/>
                    <span id='tag-err-text' className='err-text'>{ this.state.errText }</span></p>
                    <form id='tag-dialog-form' onSubmit={ this.onApply.bind( this ) }><fieldset>
                    <label htmlFor='tags'>Tags</label>
                    <input type='text' name='tags' id='tags' defaultValue={ this.state.query }/>
                    </fieldset></form>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="primary" onClick={ this.onApply.bind( this ) }>Apply</Button>
                    <Button variant="secondary" onClick={ this.onCancel.bind( this ) }>Cancel</Button>
                </Modal.Footer>
            </Modal>
        );
    }
}

class DupDialog extends React.Component
{
    constructor( props ) {
        super( props );
        this.state = {
            show: false,
        }
    }
    show( data ) {
        this.setState( {
            show: true,
            received: data.received,
            dropped: data.dropped,
        } );
        this.obj = data.obj;
    }
    onLink() {
        this.obj.set_variant( this.state.received, this.state.dropped );
        this.setState( {
            show: false,
        } );
    }
    onMerge() {
        this.obj.merge_duplicates( this.state.received, this.state.dropped );
        this.setState( {
            show: false,
        } );
    }
    onCancel() {
        this.setState( {
            show: false,
        } );
    }
    componentDidMount() {
        dialogs.register_dialog( 'dup', this );
    }
    render() {
        var Button = ReactBootstrap.Button;
        var Modal = ReactBootstrap.Modal;

        return (
            <Modal show={ this.state.show }
                   onHide={ this.onCancel.bind( this ) }>
                <Modal.Header closeButton>
                    <Modal.Title>Link Image</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <p>Select the relationship of the dropped image:</p>
                    <ul>
                        <li>Link: the dropped file is a variation</li>
                        <li>Merge: the dropped file is a duplicate</li>
                    </ul>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="primary" onClick={ this.onLink.bind( this ) }>Link</Button>
                    <Button variant="secondary" onClick={ this.onMerge.bind( this ) }>Merge</Button>
                    <Button variant="secondary" onClick={ this.onCancel.bind( this ) }>Cancel</Button>
                </Modal.Footer>
            </Modal>
        );
    }
}

class NameDialog extends React.Component
{
    constructor( props ) {
        super( props );
        this.state = {
            show: false,
        }
    }
    show( data ) {
        this.setState( {
            show: true,
        } );
        this.obj = data.obj;
    }
    onApply( evt ) {
        evt.preventDefault();

        var name = $( '#fname' ).val();
        var saveOld = $( '#saveold' ).is( ':checked' );

        if( name == '' ) {
            alert( 'Please enter a name' );
            return;
        } else if( name == '-' ) {
            name = null;
        }

        this.obj.rename( name, saveOld );

        $( document ).focus();
        this.setState( {
            show: false,
        } );
    }
    onCancel() {
        $( document ).focus();
        this.setState( {
            show: false,
        } );
    }
    onEntered() {
        $( '#fname' ).focus();
    }
    componentDidMount() {
        dialogs.register_dialog( 'name', this );
    }
    render() {
        var Button = ReactBootstrap.Button;
        var Modal = ReactBootstrap.Modal;

        return (
            <Modal show={ this.state.show }
                   onEntered={ this.onEntered.bind( this ) }
                   onHide={ this.onCancel.bind( this ) }>
                <Modal.Header closeButton>
                    <Modal.Title>Rename Image</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <p>Enter a new filename, or use '-' to clear the name.</p>

                    <form id='name-dialog-form' onSubmit={ this.onApply.bind( this ) }><fieldset>
                    <label htmlFor='fname'>Name</label>
                    <input type='text' name='fname' id='fname'/>
                    { ' ' }
                    <label htmlFor='saveold'>Save old name</label>
                    <input type='checkbox' name='saveold' id='saveold'/>
                    </fieldset></form>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="primary" onClick={ this.onApply.bind( this ) }>Apply</Button>
                    <Button variant="secondary" onClick={ this.onCancel.bind( this ) }>Cancel</Button>
                </Modal.Footer>
            </Modal>
        );
    }
}

class TextDialog extends React.Component
{
    constructor( props ) {
        super( props );
        this.state = {
            show: false,
            text: ''
        }
    }
    show( data ) {
        this.setState( {
            show: true,
            text: data.text
        } );
    }
    onCancel() {
        $( document ).focus();
        this.setState( {
            show: false,
        } );
    }
    componentDidMount() {
        dialogs.register_dialog( 'text', this );
    }
    render() {
        var Button = ReactBootstrap.Button;
        var Modal = ReactBootstrap.Modal;

        return (
            <Modal show={ this.state.show }
                   onHide={ this.onCancel.bind( this ) }>
                <Modal.Header closeButton>
                    <Modal.Title>Info</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <textarea id='info-text' style='width:100%;height:100%;resize:none' readonly='true'>{ this.state.text }</textarea>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="primary" onClick={ this.onCancel.bind( this ) }>OK</Button>
                </Modal.Footer>
            </Modal>
        );
    }
}

class ErrorDialog extends React.Component
{
    constructor( props ) {
        super( props );
        this.state = {
            show: false,
            msg: ''
        }
    }
    show( data ) {
        this.setState( {
            show: true,
            msg: data.msg
        } );
    }
    onCancel() {
        $( document ).focus();
        this.setState( {
            show: false,
        } );
    }
    componentDidMount() {
        dialogs.register_dialog( 'err', this );
    }
    render() {
        var Button = ReactBootstrap.Button;
        var Modal = ReactBootstrap.Modal;

        return (
            <Modal show={ this.state.show }
                   onHide={ this.onCancel.bind( this ) }>
                <Modal.Header closeButton>
                    <Modal.Title>Oops, something went wrong</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <span id='error-msg' dangerouslySetInnerHTML={{ __html: this.state.msg }}></span>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="primary" onClick={ this.onCancel.bind( this ) }>OK</Button>
                </Modal.Footer>
            </Modal>
        );
    }
}

class Application extends React.Component
{
  render() {
    return (
       <div id="page">
         <div>
           <Header/>
           <Trash/>
         </div>
         <MainView/>

         <TagDialog/>
         <DupDialog/>
         <NameDialog/>
         <TextDialog/>
         <ErrorDialog/>
       </div>
     );
   }
}

var window_width = 0;
var window_height = 0;

$( function() {

ReactDOM.render(
  <Application/>,
  document.getElementById('app')
);

$(document).keypress( function( e ) {
    if( $( '.modal-dialog' ).is( ':visible' ) || $( '.nokb' ).is( ':focus' ) ) {
        return;
    }

    e = window.event || e;

    var tab = tabs.active();

    if( tab && tab.onEvent ) {
        tab.onEvent( { type: 'key', charCode: e.charCode } );
    }
});

$( window ).resize( function() {
    var width = window.innerWidth;
    var height = window.innerHeight;

    if( width == window_width && height == window_height ) return;

    window_width = width;
    window_height = height;

    var tab = tabs.active();
    if( tab ) {
        if( tab.obj && tab.obj.display ) {
            tab.obj.on_event( { type: 'resized' } );
        }
    }
} );

$( window ).resize();

});
