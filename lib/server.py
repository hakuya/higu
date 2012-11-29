import higu
import cherrypy
import os
import time
import json

from html import TextFormatter, HtmlGenerator

import dialog

CONFIG={
    'global' : {
        'server.socket_host'    : '0.0.0.0',
        'server.socket_port'    : 8080,
        'tools.encode.on'       : True,
        'tools.encode.encoding' : 'utf-8',
    },
    '/static' : {
        'tools.staticdir.on' : True,
        'tools.staticdir.dir' : os.path.join( os.getcwd(), 'static' ),
    },
}


INDEX="""
<html><head><title>NextGen UI</title></head>
<body onload="init()">
<script src="static/image.js" type="text/javascript"></script>
<script src="static/script.js" type="text/javascript"></script>
<link rel="stylesheet" href="static/style.css" type="text/css"/>
<div id='header'>
    <form name='search' onsubmit="load( '/search?mode=tags&tags=' + document.forms[0].tags.value ); return false;">
    <a href="javascript:load( '/search?mode=all' )">all</a> /
    <a href="javascript:load( '/search?mode=untagged' )">untagged</a> /
    <a href="javascript:load( '/search?mode=albums' )">albums</a> /
    <a href="javascript:load( '/taglist?' )">taglist</a> /
    <a href="javascript:load( '/admin?' )">admin</a> /
    <input type="text" name="tags"/></form>
</div>
<div id='sidebar'>
    <div id='info'></div>
    <div id='list'></div>
</div>
<div id='main'>
</div>
<div id='overlay'>
 <div id='grey'></div>
 <div id='dialogbox'>
  <div id='dialoghead'>
   <div id='dialogtitle'></div>
   <div id='dialogcontrols'><a href='javascript:dismiss_dialog()'>x</a></div>
  </div><div id='dialog'></div>
 </div>
</div>
"""

class Server:

    def __init__( self, database_path = None ):

        self.db_path = database_path
        self.dialogs = {
            'tag' : dialog.TagDialog(),
            'rename' : dialog.RenameDialog(),
        }

    def open_db( self ):

        if( self.db_path == None ):
            return higu.init_default()
        else:
            return higu.Database( self.db_path )

    def index( self ):

        return INDEX

    def process_action( self, db, objs, action, **args ):

        result = []

        if( action is None ):
            return []

        elif( action == 'rename_tag' ):
            if( args['rntag'] != '' and args['rnnew'] != '' ):
                db.rename_tag( args['rntag'], args['rnnew'] )
            if( len( objs ) > 0 ):
                result = [ ( 'info', self.generate_info_pane( objs ) ) ]

        elif( action == 'rempar' ):
            for obj in objs:
                obj.set_parent( None )
            result = [ ( 'info', self.generate_info_pane( objs ) ) ]

        elif( action == 'rm' ):
            for obj in objs:
                db.delete_object( obj )

        elif( action == 'album_append' ):
            album = db.get_object_by_id( args['album'] )

            for obj in objs:
                obj.assign( album )
            result = [ ( 'info', self.generate_info_pane( objs ) ) ]

        elif( action == 'create_album' ):
            c = db.create_album()
            for obj in objs:
                obj.assign( c )
            result = [ ( 'info', self.generate_info_pane( objs ) ) ]

        elif( action == 'mark_varient' ):
            for obj in objs[:-1]:
                obj.set_varient_of( objs[-1] )
            result = [ ( 'info', self.generate_info_pane( objs ) ) ]

        elif( action == 'mark_duplicate' ):
            for obj in objs[:-1]:
                obj.set_duplicate_of( objs[-1] )
            result = [ ( 'info', self.generate_info_pane( objs ) ) ]

        elif( action == 'select' ):
            result = [ ( 'info', self.generate_info_pane( objs ) ),
                     ( 'main', self.generate_image_pane( objs[-1] ) ) ]
            return result

        elif( action == 'selalbum' ):
            f = higu.File( db, int( args['fid'] ) )
            c = higu.Album( db, int( args['cid'] ) )

            objects = map( lambda x: ( x, x.get_repr(), ), c.get_files() )

            return [ ( 'info', self.generate_info_pane( [ f ] ) ),
                     ( 'main', self.generate_image_pane( f ) ),
                     ( 'list', self.generate_search_pane( objects, [ f ] ) ) ]

        elif( self.dialogs.has_key( action ) ):
            result = self.dialogs[action].process_input( self, db, objs, **args )

        db.commit()
        return result

    def do_update_divs( self, divs ):

        data = map( lambda x: { 'id' : x[0], 'content' : x[1] }, divs )
        return json.dumps( { 'action' : 'update-divs', 'data' : data } )

    def do_show_dialog( self, title, content, width, height ):

        data = {
            'title' : title,
            'content' : content,
            'width' : width,
            'height' : height,
        }

        return json.dumps( { 'action' : 'display-dialog', 'data' : data } )

    def admin( self, action = None, **args ):

        cherrypy.response.headers['Content-Type'] = "text/html; charset=utf-8" 

        html = HtmlGenerator()

        self.process_action( self.open_db(), [], action, **args )

        html.header( 'Rename tag' )
        html.begin_form()
        html.text( """Tag: <input type="text" name="rntag"/> New: <input type="text" name="rnnew"/> <input type="button" value="Update" onclick="load( '/admin?action=rename_tag&rntag=' + this.form.rntag.value + '&rnnew=' + this.form.rnnew.value )"/>""" )
        html.end_form()

        return self.do_update_divs( [ ( 'main', html.format(), ) ] )

    def view( self, id = None, selection = None ):

        if( id == None ):
            raise cherrypy.HTTPError( 404 )
        try:
            id = int( id )
        except:
            raise cherrypy.HTTPError( 400 )

        db = self.open_db()
        f = db.get_object_by_id( id )

        if( isinstance( f, higu.Album ) ):
            f = f.get_files()
            
            if( len( f ) == 0 ):
                f = None
            else:
                f = f[0]
            
        if( f == None ):
            p = None
        else:
            p = f.get_path()

        db.close()

        if( p == None ):
            return self.do_update_divs( [ ( 'viewer', 'Image not available<br/>', ) ] )
        else:
            return self.do_update_divs( [ ( 'viewer', '<img src="/img?id=%d" class="picture" onload="register_image( this )" onclick="nextfile( 1 )"/><br/>' % ( f.get_id(), ), ) ] )

    def link_load( self, text, target, **args ):

        extra = ''
        for arg in args:
            extra += '&%s=%s' % ( arg, args[arg], )
        return """<a href="javascript:load( '/callback?id=%d%s' )">%s</a>""" % (
                target, extra, text )

    def generate_info_pane( self, objs ):

        html = HtmlGenerator()
        obj = objs[-1]

        html.text( obj.get_repr() + '<br/>' )

        if( isinstance( obj, higu.Album ) ):

            html.header( 'Files' )
            fs = obj.get_files()
            html.list( '<a href="javascript:selectfromalbum( %d, %d )">%s</a>', fs,
                    lambda x: ( obj.get_id(), x.get_id(), x.get_repr(), ) )

        html.header( 'Tags' )
        tags = obj.get_tags()
        html.list( """%s""", tags, lambda x: ( x.get_name(), ) )

        html.header( 'Names' )
        names = obj.get_names()
        html.list( '%s', names )

        if( isinstance( obj, higu.File ) ):

            variants = obj.get_variants_of()
            if( len( variants ) > 0 ):
                links = map( lambda x:
                        self.link_load( x.get_repr(), x.get_id(), loadimg = '1' ), variants )
                links = ', '.join( links )

                html.text( 'Varient of: ' + links + '<br/>' )

            duplicates = obj.get_duplicates_of()
            if( len( duplicates ) > 0 ):
                links = map( lambda x:
                        self.link_load( x.get_repr(), x.get_id(), loadimg = '1' ), duplicates )
                links = ', '.join( links )

                html.text( 'Duplicate of: ' + links + '<br/>' )

            variants = obj.get_variants()
            if( len( variants ) > 0 ):
                links = map( lambda x:
                        self.link_load( x.get_repr(), x.get_id(), loadimg = '1' ), variants )
                links = ', '.join( links )

                html.text( 'Varients: ' + links + '<br/>' )

            duplicates = obj.get_duplicates()
            if( len( duplicates ) > 0 ):
                links = map( lambda x:
                        self.link_load( x.get_repr(), x.get_id(), loadimg = '1' ), duplicates )
                links = ', '.join( links )

                html.text( 'Duplicates: ' + links + '<br/>' )

            albums = obj.get_albums()

            if( len( albums ) == 1 ):

                html.header( 'Album: %s' % ( albums[0].get_repr() ) )
                fs = albums[0].get_files()
                html.list( '<a href="javascript:selectfromalbum( %d, %d )">%s</a>', fs,
                        lambda x: ( albums[0].get_id(), x.get_id(), x.get_repr(), ) )

            elif( len( albums ) > 1 ):

                html.header( 'Albums:' )
                html.list( '%s', map( lambda x: x.get_repr(), albums ) )

        html.header( 'Tools' )
        html.begin_ul()
        html.item( '<a href="javascript:rm()">Delete</a>' )

        if( isinstance( obj, higu.File ) and len( objs ) > 1 ):
            albums = []

            for i in objs:
                if( isinstance( i, higu.File ) ):
                    fas = i.get_albums()
                    for a in fas:
                        if( not a in albums ):
                            albums.append( a )

            html.item( """<a href="javascript:group( 'create_album' )">Create Album</a>""" )
            for i in albums:
                html.item( """<a href="javascript:load( '/callback?id=%s&action=album_append&album=%d' )">Add to %s</a>""",
                        id, i.get_id(), i.get_repr() )
            html.item( """<a href="javascript:group( 'mark_varient' )">Varient</a>""" )
            html.item( """<a href="javascript:group( 'mark_duplicate' )">Duplicate</a>""" )
        html.end_ul()

        return html.format()

    def generate_image_pane( self, obj ):

        if( isinstance( obj, higu.Album ) ):
            f = obj.get_files()
            
            if( len( f ) == 0 ):
                f = None
            else:
                f = f[0]
        else:
            f = obj
            
        if( f == None ):
            p = None
        else:
            p = f.get_path()

        if( p == None ):
            return 'Image not available<br/>'
        else:
            return '<img src="/img?id=%d" class="picture" onload="register_image( this )" onclick="nextfile( 1 )"/><br/>' % ( f.get_id(), )

    def generate_search_pane( self, objs, selection ):

        html = HtmlGenerator()

        total_count = TextFormatter( 'Total: %d objects<br/>' )
        html.generator( total_count )
        html.begin_form( name = 'list' )

        FILE_PRIMARY_ITEM =  [  '<div style="background:yellow" id="list_div',
                                '"><input type="checkbox" name="list_check',
                                '" checked value="',
                                '" onclick="javascript:clickfile( ',
                                ', false )"/><a href="javascript:clickfile( ',
                                ', true )">' ]

        ALBUM_PRIMARY_ITEM  = [ '<div style="background:yellow" id="list_div',
                                '"><input type="checkbox" name="list_check',
                                '" checked value="',
                                '" onclick="javascript:clickalbum( ',
                                ' )"/><a href="javascript:clickalbum( ',
                                ' )"><i>' ]

        FILE_SELECTED_ITEM = [  '<div style="" id="list_div',
                                '"><input type="checkbox" name="list_check',
                                '" checked value="',
                                '" onclick="javascript:clickfile( ',
                                ', false )"/><a href="javascript:clickfile( ',
                                ', true )">' ]

        ALBUM_SELECTED_ITEM = [ '<div style="" id="list_div',
                                '"><input type="checkbox" name="list_check',
                                '" checked value="',
                                '" onclick="javascript:clickalbum( ',
                                ' )"/><a href="javascript:clickalbum( ',
                                ' )"><i>' ]

        FILE_ITEM = [           '<div id="list_div',
                                '"><input type="checkbox" name="list_check',
                                '" value="',
                                '" onclick="javascript:clickfile( ',
                                ', false )"/><a href="javascript:clickfile( ',
                                ', true )">' ]

        ALBUM_ITEM = [          '<div id="list_div',
                                '"><input type="checkbox" name="list_check',
                                '" value="',
                                '" onclick="javascript:clickalbum( ',
                                ' )"/><a href="javascript:clickalbum( ',
                                ' )"><i>' ]

        FILE_ITEM_CLOSE = '</a></div>'
        ALBUM_ITEM_CLOSE = '</i></a></div>'

        selection = list( selection )
        if( selection ):
            primary = selection[-1]
        else:
            primary = None

        c = 0
        for o in objs:
            c += 1

            name = o[1]
            o = o[0]

            id = o.get_id()
            id_str = str( id )

            try:
                selection.remove( o )
                if( isinstance( o, higu.File ) ):
                    if( o == primary ):
                        html.text( id_str.join( FILE_PRIMARY_ITEM ) + (name + FILE_ITEM_CLOSE) )
                    else:
                        html.text( id_str.join( FILE_SELECTED_ITEM ) + (name + FILE_ITEM_CLOSE) )
                else:
                    if( o == primary ):
                        html.text( id_str.join( ALBUM_PRIMARY_ITEM ) + (name + FILE_ITEM_CLOSE) )
                    else:
                        html.text( id_str.join( ALBUM_SELECTED_ITEM ) + (name + ALBUM_ITEM_CLOSE) )
            except ValueError:
                if( isinstance( o, higu.File ) ):
                    html.text( id_str.join( FILE_ITEM ) + (name + FILE_ITEM_CLOSE) )
                else:
                    html.text( id_str.join( ALBUM_ITEM ) + (name + ALBUM_ITEM_CLOSE) )

        if( len( selection ) > 0 ):
            html.hr()
            html.text( 'Also selected<br/>' )

            for o in selection:
                name = o.get_repr()
                id = o.get_id()
                id_str = str( id )

                if( isinstance( o, higu.File ) ):
                    if( o == primary ):
                        html.text( id_str.join( FILE_PRIMARY_ITEM ) + (name + FILE_ITEM_CLOSE) )
                    else:
                        html.text( id_str.join( FILE_SELECTED_ITEM ) + (name + FILE_ITEM_CLOSE) )
                else:
                    if( o == primary ):
                        html.text( id_str.join( ALBUM_PRIMARY_ITEM ) + (name + FILE_ITEM_CLOSE) )
                    else:
                        html.text( id_str.join( ALBUM_SELECTED_ITEM ) + (name + ALBUM_ITEM_CLOSE) )

        html.end_form()

        total_count.set_data( c )

        return html.format()

    def dialog( self, kind, selection = None ):
        cherrypy.response.headers['Content-Type'] = 'application/json'

        db = self.open_db()
        html = HtmlGenerator()

        if( not self.dialogs.has_key( kind ) ):
            html.span( 'Invalid dialog', cls = 'error' )
            return html.format()

        dialog = self.dialogs[kind]
        selection = map( lambda x: int( x ), selection.split( ' ' ) )

        url = "'/callback?id=%d&action=%s'"
        for parm in dialog.get_parameters():
            url += " + '&" + parm[0] + "=' + this." + parm[0] + "." + parm[1]

        url = url % ( selection[-1], kind )

        html.begin_form( onsubmit = "dismiss_and_load( " + url + " ); return false;" )
        dialog.format_dialog( html, db, selection )
        html.end_form()

        width, height = dialog.get_dimensions()
        return self.do_show_dialog( dialog.get_title(), html.format(), width, height )

    def callback( self, action = None, selection = None, **args ):
        cherrypy.response.headers['Content-Type'] = 'application/json'

        if( selection == None ):
            raise cherrypy.HTTPError( 404 )
        try:
            ids = selection.split( ' ' )
            ids = map( lambda x: int( x ), ids )
        except:
            raise cherrypy.HTTPError( 400 )

        db = self.open_db()

        return self.do_update_divs( self.process_action( db, map( lambda x: db.get_object_by_id( x ), ids ), action, **args ) )

    def search( self, mode = None, tags = None, id = None, selection = [] ):
        cherrypy.response.headers['Content-Type'] = 'application/json'

        db = self.open_db()

        try:
            ids = selection.split( ' ' )
            selection = map( lambda x: db.get_object_by_id( x ), map( lambda x: int( x ), ids ) )
        except:
            selection = []

        if( mode == 'untagged' ):
            objects = db.lookup_objects_by_tags_with_names( [], strict = True, type = higu.TYPE_FILE )
        elif( mode == 'albums' ):
            objects = db.lookup_objects_by_tags_with_names( [], type = higu.TYPE_ALBUM )
        elif( mode == 'tags' ):
            if( tags[0] == '$' ):
                strict = True
                tags = tags[1:]
            else:
                strict = False

            ls = tags.split( ' ' )
            require = []
            add = []
            sub = []
            t = None

            for tag in ls:
                if( len( tag ) == 0 ):
                    continue
                elif( tag == '~a' ):
                    t = higu.TYPE_ALBUM
                elif( tag == '~f' ):
                    t = higu.TYPE_FILE
                elif( tag[0] == '?' ):
                    c = db.get_tag( tag[1:] )
                    add.append( c )
                elif( tag[0] == '!' ):
                    c = db.get_tag( tag[1:] )
                    sub.append( c )
                else:
                    c = db.get_tag( tag )
                    require.append( c )

            if( t == None ):
                objects = db.lookup_objects_by_tags_with_names( require, add, sub, strict, type = higu.TYPE_FILE )
            else:
                objects = db.lookup_objects_by_tags_with_names( require, add, sub, strict, type = t )
        else:
            objects = db.lookup_objects_by_tags_with_names( [], type = higu.TYPE_FILE )

        return self.do_update_divs( [ ( 'list', self.generate_search_pane( objects, selection ), ) ] )

    def taglist( self, selection = None ):

        db = self.open_db()
        s = ''

        tags = db.all_tags()

        s += '<ul>'
        for t in tags:
            s += """<li><a href="javascript:load( '/search?mode=tags&tags=%s' )">%s</a></li>""" \
                    % ( t.get_name(), t.get_name(),)
        s += '</ul>'

        return self.do_update_divs( [ ( 'main', s, ) ] )

    def img( self, id = None ):

        from PIL import Image

        db = self.open_db()

        if( id == None ):
            raise cherrypy.HTTPError( 404 )

        try:
            id = int( id )
        except:
            raise cherrypy.HTTPError( 400 )

        f = db.get_object_by_id( id )
        p = f.get_thumb( 10 )

        if( p == None ):
            raise cherrypy.HTTPError( 404 )

        name = os.path.split( p )[-1]
        ext = name[name.rindex( '.' )+1:]

        name = f.get_repr()

        img_obj = Image.open( p )
        print img_obj.size

        db.close()

        return cherrypy.lib.static.serve_file( p, 'image/' + ext, 'inline', name )

    index.exposed = True
    callback.exposed = True
    search.exposed = True
    taglist.exposed = True
    img.exposed = True
    admin.exposed = True
    dialog.exposed = True

if( __name__ == '__main__' ):

    import sys

    if( os.environ.has_key( 'HIGU_BINDADDR' ) ):
        CONFIG['global']['server.socket_host'] = os.environ['HIGU_BINDADDR']
    if( os.environ.has_key( 'HIGU_BINDPORT' ) ):
        CONFIG['global']['server.socket_port'] = int( os.environ['HIGU_BINDPORT'] )

    if( len( sys.argv ) > 1 ):
        cherrypy.quickstart( Server( sys.argv[1] ), config=CONFIG )
    else:
        cherrypy.quickstart( Server(), config=CONFIG )

# vim:sts=4:et:sw=4
