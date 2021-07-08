class CompositeLink extends React.Component
{
    render() {
        if( this.props.actions && this.props.actions.length > 0 ) {
            return (
                <span>
                    <a href='#' onClick={ this.props.onClick }>{ this.props.label }</a>
                    { '(' }
                        {  this.props.actions.map( ( it, i ) => (
                                <span key={ i }>
                                    { i > 0 && ', ' }
                                    <a href='#' onClick={ it.onClick }>{ it.label }</a>
                                </span>
                        ) ) }
                    { ')' }
                </span>
            );
        } else {
            return (
                <a href='#' onClick={ this.props.onClick }>{ this.props.label }</a>
            );
        }
    }
}

class ObjectLink extends React.Component
{
    render() {
        return (
            <CompositeLink label={ this.props.label }
                           onClick={ () => {
                                var provider = new tabs.SingleProvider( this.props.target );
                                tabs.create_display_tab( this.props.label, provider );
                            } }
                           actions={ this.props.actions }/>
        );
    }
}

class TagLink extends React.Component
{
    render() {
        return (
            <a className='taglink'
               href='#'
               onClick={ () => {
                    var provider = new tabs.SearchProvider( { query: this.props.tag } );
                    tabs.create_display_tab( this.props.tag, provider );
                } }>{ this.props.tag }</a>
        );
    }
}

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
        if( d.info.type == 'file') {
            util.make_draggable( $( this.el ), util.make_basic_drop_data(
                d.obj_id, d.info.repr, d.info.type ) );
        } else {
            util.make_draggable( $( this.el ), util.make_group_drop_data(
                d.obj_id, d.info.files, d.info.repr, d.info.type ) );
        }
    }
    render() {
        var d = this.props.display;
        return (
            <div className="objlabel objitem" ref={ ( el ) => { this.el = el; } }>
                <ObjectLink label={ d.info.repr } target={ d.obj_id }/>
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

            get_object: function() { return null; },
            get_files:  function() { return d.get_files(); },
            get_repr:   function() { return 'Selection'; },
            get_type:   function() { return 'selection'; },
        });
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
    renderFileInfo( info ) {
        return (
            <div>
                { 'Size: ' } { info.width } { 'x' } { info.height } <br/>
                { info.albums && info.albums.length > 0 &&
                    <ObjectList label='Albums: ' objects={ info.albums }/>
                }
                { info.albums && info.albums.length > 0 && <br/> }
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
                </a> <br/>
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
    render() {
        var info = this.props.display.info;

        return (
            <div className='info'>
                <ObjectLabel display={ this.props.display }/> <br/>
                <h1>Tags</h1>
                <ul className='infotaglist'>
                    {
                        info.tags.map( ( it ) => (
                            <li key={ it }><TagLink tag={ it }/></li>
                        ) )
                    }
                </ul>
                <h1>Names</h1>
                <ul className='infonamlist'>
                    {
                        info.names.map( ( it ) => (
                            <li key={ it }>{ it }</li>
                        ) )
                    }
                </ul>
                { info.origin_time &&
                    <span> { 'Created: ' } { info.origin_time } </span>
                }
                { info.origin_time && <br/> }
                { info.creation_time &&
                    <span> { 'Added: ' } { info.creation_time } </span>
                }
                { info.creation_time && <br/> }
                { info.type == 'file' &&
                    this.renderFileInfo( info )
                }
                { info.type != 'file' &&
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
            <div className='info'>
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
                                        this.props.display.make_group();
                                    } }>
                        { 'Make Album' }
                    </a></li>
                </ul>
            </div>
        );
    }
}

class InfoPane extends React.Component
{
    render() {
        if( this.props.display.type == 'object' ) {
            return ( <ObjectInfoPane display={ this.props.display }/> );
        } else if( this.props.display.type == 'selection' ) {
            return ( <SelectionInfoPane display={ this.props.display }/> );
        } else {
            return ( <div className='info'/> );
        }
    }
}

class ViewPane extends React.Component
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

class DisplayTab extends React.Component
{
    constructor( props ) {
        super( props );
        this.state = {}

        this.props.data.onEvent = ( e ) => { this.onEvent( e ) };
    }

    onEvent( e )
    {
        if( e.type == 'key' && e.charCode == 106 /* j */ ) {
            var display = this.props.data.provider.next();
            if( display ) {
                this.setDisplay( display );
            }
        } else if( e.type =='key' && e.charCode == 107 /* k */ ) {
            var display = this.props.data.provider.prev();
            if( display ) {
                this.setDisplay( display );
            }
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
            info_gen: 0,
            view_gen: 0,
        } );
    }

    onInitComplete( display )
    {
        this.setDisplay( display );
    }

    on_displayable_changed( disp, e )
    {
        this.setState( {
            display: this.state.display,
            view: this.state.view,
            info_gen: this.state.info_gen + 1,
            view_gen: e == null || e.type == 'files_changed'
                        ? this.state.view_gen + 1 : this.state.view_gen
        } );
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

                if( tab && tab.onEvent ) {
                    tab.onEvent( {
                        type: 'drop',
                        drop_data: item.data( 'drop_data' )
                    } );
                }

                item.draggable( 'option', 'revert', false );
                ui.helper.addClass( 'dropped' );
            },
        });

        this.props.data.provider.init( this, 'onInitComplete' );
    }

    render() {
        if( this.state.display ) {
            return (
                <div className='tab'
                     ref={ ( el ) => { this.el = el } }>
                    <InfoPane display={ this.state.display } gen={ this.state.info_gen }/>
                    <ViewPane display={ this.state.display }
                              view={ this.state.view }
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
    render() {
        return (
            <div className='tab'>
                <form action="/do_login" method="POST">
                  Username: <input type="text" name="username"/>,
                  Password: <input type="password" name="password"/>
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
            src = $( '#adm-tag-src' );
            tgt = $( '#adm-tag-tgt' );

            var request = {
                action:     'tag_delete',
                tag:        src.val(),
            };
            load_sync( request );

            src.val( '' );
            tgt.val( '' );
        });

        // Copy
        button = $( '#adm-tag-cp-button' );
        button.click( function( e ) {
            src = $( '#adm-tag-src' );
            tgt = $( '#adm-tag-tgt' );

            var request = {
                action:     'tag_copy',
                tag:        src.val(),
                target:     tgt.val(),
            };
            load_sync( request );

            src.val( '' );
            tgt.val( '' );
        });

        // Move
        button = $( '#adm-tag-mv-button' );
        button.click( function( e ) {
            src = $( '#adm-tag-src' );
            tgt = $( '#adm-tag-tgt' );

            var request = {
                action:     'tag_move',
                tag:        src.val(),
                target:     tgt.val(),
            };
            load_sync( request );

            src.val( '' );
            tgt.val( '' );
        });
    }
    render() {
        return (
            <div className='tab' ref={ ( el ) => { this.el = el } }>
                <form>
                  Src: <input type="text" id="adm-tag-src"/>,
                  Dst: <input type="text" id="adm-tag-tgt"/><br/>
                  <input type="button" id="adm-tag-rm-button" value="Delete"/>
                  <input type="button" id="adm-tag-cp-button" value="Copy"/>
                  <input type="button" id="adm-tag-mv-button" value="Move"/>
                </form>
            </div>
        );
    }
}

class TaglistTab extends React.Component {
    constructor( props ) {
        super( props );
        this.state = {}

        this.props.data.onEvent = function( e ) {
            if( e.type == 'info_changed' ) {
                this.loadContent();
            }
        }

        this.loadContent();
    }
    loadContent()
    {
        load_async( { action: 'taglist' }, this, 'onContentLoaded', {} );
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
            var rendered_tags = this.state.tags.map( ( it ) => (
                <li key={ it }><TagLink tag={ it }/></li>
            ) );
            return (
                <div className='tab'>
                    <ul className='taglist'>
                        { rendered_tags }
                    </ul>
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

window.Tabs = {
    ContentTab: ContentTab
};
