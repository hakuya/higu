var make_display = function( obj_id )
{
    var request = {
        action:     'info',
        targets:    [ obj_id ],
        items:      [ 'type', 'repr', 'tags', 'names', 'duplication',
            'similar_to', 'duplicates', 'variants', 'albums', 'files',
            'path' ],
    };
    
    response = load_sync( request );
    info = response.info[0];

    if( info.type == 'file' ) {
        disp = new FileDisplay( obj_id, info );
    } else {
        disp = new GroupDisplay( obj_id, info );
    }

    return disp;
}

function make_link( repr, target )
{
    label = $( '<a href="#">' + repr + '</a>' );
    label.data( 'repr', repr );
    label.data( 'obj_id', target );

    label.click( function( e ) {
        obj_id = $( this ).data( 'obj_id' );
        repr = $( this ).data( 'repr' );

        provider = new SingleProvider( obj_id );
        new DisplayTab( repr, provider );
    });

    return label;
}

function make_link2( pair )
{
    return make_link( pair[1], pair[0] );
}

function make_link_list( list )
{
    if( list.length == 0 ) return;

    span = $( '<span></span>' );
    span.append( make_link2( list[0] ) );

    for( i = 1; i < list.length; i++ ) {
        span.append( ', ' );
        span.append( make_link2( list[i] ) );
    }

    return span;
}

var common_info_display = function( div )
{
    div.append( make_link( this.info.repr, this.obj_id ) );
    div.append( '<br/>' );

    /* Display album info?
#        if( isinstance( obj, higu.Album ) ):
#
#            html.header( 'Files' )
#            fs = obj.get_files()
#            html.list( '<a href="javascript:selectfromalbum( %d, %d )">%s</a>', fs,
#                    lambda x: ( obj.get_id(), x.get_id(), x.get_repr(), ) )
    */

    div.append( '<h1>Tags</h1>' );
    div.append( "<ul class='infotaglist'></ul>" );
    var ls = div.find( '.infotaglist' );

    for( i = 0; i < this.info.tags.length; i++ ) {
        var li = TAGLINK_TEMPLATE.replace( /#\{tag\}/g, this.info.tags[i]);
        ls.append( li );
    }

    div.append( '<h1>Names</h1>' );
    div.append( "<ul class='infonamlist'></ul>" );
    ls = div.find( '.infonamlist' );

    for( i = 0; i < this.info.names.length; i++ ) {
        var li = '<li>' + this.info.names[i] + '</li>'
        ls.append( li );
    }
};

var common_refresh_info = function()
{
    var request = {
        action:     'info',
        targets:    [ this.obj_id ],
        items:      [ 'type', 'repr', 'tags', 'names', 'duplication',
            'similar_to', 'duplicates', 'variants', 'albums', 'files',
            'path' ],
    };
    
    response = load_sync( request );
    this.info = response.info[0];

    this.on_display_info();
};

var common_tag = function( tags )
{
    var request = {
        'action' : 'tag',
        'target' : this.obj_id,
        'tags' : tags,
    };
    load_sync( request );
    this.refresh_info();
}

/**
 * class FileDisplay
 */
FileDisplay = function( obj_id, info )
{
    this.obj_id = obj_id;
    this.info = info;

    this.pane = null;

    this.common_info_display = common_info_display;
    this.refresh_info = common_refresh_info;
    this.tag = common_tag;

    this.attach = function( pane )
    {
        this.pane = pane;
        this.on_display();
    }

    this.on_display_info = function()
    {
        var div = this.pane.find( '.info' );
        div.html( '' );

        this.common_info_display( div );

        if( this.info.similar_to ) {
            if( this.info.duplication == 'duplicate' ) {
                div.append( 'Duplicate of: ' );
            } else {
                div.append( 'Variant of: ' );
            }

            div.append( make_link2( this.info.similar_to ) );
            div.append( '<br/>' );
        }

        if( this.info.variants && this.info.variants.length > 0 ) {
            div.append( 'Variants: ' );
            div.append( make_link_list( this.info.variants ) );
        }

        if( this.info.duplicates && this.info.duplicates.length > 0 ) {
            div.append( 'Duplicates: ' );
            div.append( make_link_list( this.info.duplicates ) );
        }

        if( this.info.albums && this.info.albums.length > 0 ) {
            div.append( 'Albums: ' );
            div.append( make_link_list( this.info.albums ) );
        }

        activate_links( div );
    };

    this.on_display_disp = function()
    {
        var div = this.pane.find( '.disp' );
        div.html( '' );

        if( this.info.path ) {
            div.append( '<img src="/img?id=' + this.obj_id
                + '" class="picture" onload="register_image( this )" onclick="nextfile( 1 )"/><br/>' );
        } else {
            div.append( 'Image not available<br/>' );
        }
    }

    this.on_display = function()
    {
        this.on_display_info();
        this.on_display_disp();
    }
};

/**
 * class FileDisplay
 */
GroupDisplay = function( obj_id, info )
{
    this.obj_id = obj_id;
    this.info = info

    this.pane = null;

    this.common_info_display = common_info_display;
    this.refresh_info = common_refresh_info;
    this.tag = common_tag;

    this.attach = function( pane )
    {
        this.pane = pane;
        this.on_display();
    }

    this.on_display_info = function()
    {
        var div = this.pane.find( '.info' );
        div.html( '' );

        this.common_info_display( div, this.info );
        activate_links( div );
    };

    this.on_display_disp = function()
    {
        var div = this.pane.find( '.disp' );
        div.html( '' );

        var request = {
            action:     'info',
            targets:    [ this.obj_id ],
            items:      [ 'files' ],
        }

        info_response = load_sync( request );
        files = info_response.info[0].files;

        div.append( '<ul class="thumbslist sortable"></ul>' );
        var ls = div.children().first();
        for( i = 0; i < files.length; i++ ) {
            var li = GROUPLINK_TEMPLATE
                    .replace( /#\{grp\}/g, this.obj_id )
                    .replace( /#\{idx\}/g, i )
                    .replace( /#\{obj\}/g, files[i][0] );
            ls.append( li );
        }
        activate_links( div );
    };

    this.on_display = function( response )
    {
        this.on_display_info( response );
        this.on_display_disp( response );
    }
};
