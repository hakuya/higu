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
                            <li key={ it }><TagLink tag={ it }/></li>
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

class InfoPane extends React.Component
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

class NavigatePane extends React.Component
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

class ThumbTile extends React.Component
{
    componentDidMount() {
        this.drop_data = {
            view:   this.props.view,

            obj_id: this.props.obj_id,
            repr:   this.props.repr,
            type:   this.props.type,

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
    render() {
        return (
            <div ref={ ( el ) => { this.el = el; } }
                 style={{
                     width: this.props.metrics.size,
                     height: this.props.metrics.size
                 }}
                 className={ 'albumlink objitem sortable' + (this.props.selected ? ' selected' : '') }>
                <img src={ '/img?id=' + this.props.obj_id + '&exp=' + this.props.metrics.exp_i }
                     style={{
                            maxWidth: '100%',
                            maxHeight: '100%',
                        }}
                     onClick={ ( e ) => {
                            e.preventDefault();
                            this.props.view.itemClicked( e, this.drop_data );
                        } }/>
            </div>
        );
    }
}

class ThumbItem extends React.Component
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

class ThumbViewPane extends React.Component
{
    constructor( props ) {
        super( props );
        this.state = {
            selection: []
        };
    }
    openItem( drop_data ) {
        var provider = this.props.display.create_provider( { start_id: drop_data.get_object() } );

        if( !provider ) {
            provider = new tabs.SingleProvider( drop_data.get_object() );
        }

        tabs.create_display_tab( drop_data.get_repr(), provider );
    }
    toggleSelection( drop_data ) {
        if( this.selectionIndexOf( drop_data.get_object() ) < 0 ) {
            this.setState( {
                selection: this.state.selection.concat(
                            [ [ drop_data.get_object(),
                                drop_data.get_repr(),
                                drop_data.get_type() ] ] )
            } );
        } else {
            this.setState( {
                selection: this.state.selection.filter( ( it ) => {
                                return it[0] != drop_data.get_object();
                            } )
            } );
        }
    }
    itemClicked( e, drop_data ) {
        if( e.metaKey ) {
            this.toggleSelection( drop_data );
        } else {
            this.openItem( drop_data );
        }
    }
    selectionIndexOf( obj_id )
    {
        return this.state.selection.findIndex( ( it ) => {
                    return it[0] == obj_id;
                } );
    }
    computeMetrics() {
        // Calculate the thumb tile exponent
        var exp_w = 0;
        while( (window.innerWidth / (1 << exp_w)) > 16 ) exp_w++;

        // Calculate the exponent for the thumb image
        var factor_i = 0;
        while( window.devicePixelRatio > (1 << factor_i) ) factor_i++;
        var exp_i = exp_w + factor_i;

        return {
            exp_w: exp_w,
            exp_i: exp_i,
            size: (1 << exp_w),
        };
    }
    componentDidUpdate() {
        // We need to filter our selection, to 'deselect' items that no longer exist
        var files = this.props.display.get_files();
        var new_selection = this.state.selection.filter( ( it ) => {
                                return files.findIndex( ( jt ) => {
                                            return jt[0] == it[0];
                                        } ) >= 0;
                            } );
        if( new_selection.length != this.state.selection.length ) {
            this.setState( { selection: new_selection } );
        }
    }
    render() {
        // Workaround for jQuery exection when removing draggable during
        // drag event
        //div.find( '.objitem' ).remove();
        //div.html( '' );

        var group_id = this.props.display.get_obj_id();
        var files = this.props.display.get_files();

        var metrics = this.computeMetrics();

        return (
            <div className='disp' ref={ ( el ) => { this.el = el; } }>
                <ul className='thumbslist'>
                    {
                        files.map( ( it, i ) => (
                            <ThumbItem key={ it[0] }
                                       display={ this.props.display }
                                       view={ this }
                                       selected={ this.selectionIndexOf( it[0] ) >= 0 }
                                       metrics={ metrics }
                                       obj_id={ it[0] }
                                       repr={ it[1] }
                                       type={ it[2] }
                                       index={ i }/>
                        ) )
                    }
                    <li style={{
                            width: metrics.size,
                            height: metrics.size
                        }}/>
                </ul>
            </div>
        );
    }
}

class MiscViewPane extends React.Component
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

class ViewPane extends React.Component
{
    render() {
        if( this.props.view.type == 'thumb' ) {
            return (
                <ThumbViewPane display={ this.props.display }
                               view={ this.props.view }
                               gen={ this.props.gen }/>
            );
        } else {
            return (
                <MiscViewPane display={ this.props.display }
                              view={ this.props.view }
                              gen={ this.props.gen }/>
            );
        }
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
            var display = this.props.data.provider.next();
            if( display ) {
                this.setDisplay( display );
            }
        } else if( e.type == 'key' && e.charCode == 107 /* k */
                || e.type == 'navigate' && e.direction == 'prev' )
        {
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
            disp_gen: this.state.disp_gen ? this.state.disp_gen + 1 : 1,
            info_gen: this.state.info_gen ? this.state.info_gen + 1 : 1,
            view_gen: this.state.view_gen ? this.state.view_gen + 1 : 1
        } );
    }

    onInitComplete( display )
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
            load_sync( request );

            src.val( '' );
            tgt.val( '' );
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
            load_sync( request );

            src.val( '' );
            tgt.val( '' );
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
            load_sync( request );

            src.val( '' );
            tgt.val( '' );
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

        var response = load_sync( request );
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
            var tags = this.state.tags.map( it => {
                        var m = it.match( /(.*):(.*)/ );
                        return (m == null) ? [ null, it ] : [ m[1], it ];
                    } );
            var groups = [];
            while( tags.length > 0 ) {
                var group = tags[0][0];
                var gtags = tags.filter( it => it[0] == group ).map( it => it[1] );
                tags = tags.filter( it => it[0] != group );
                groups.push( [ group, gtags ] );
            }
            var rendered_tags = groups.map( ( it ) => (
                <div key={ it[0] } className='taggroup'>
                  { it[0] != null && <h1>{ it[0] }</h1> }
                  <ul className='taglist'>
                    { it[1].map( jt => ( <li key={ jt }><TagLink tag={ jt }/></li> ) ) }
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

window.Tabs = {
    ContentTab: ContentTab
};
