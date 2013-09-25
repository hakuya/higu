import higu
import cherrypy
import os
import uuid
import time
import json

from view import JsonWebView
from html import TextFormatter, HtmlGenerator

import dialog

CONFIG={
    'global' : {
        'server.socket_host'    : '0.0.0.0',
        'server.socket_port'    : 8080,
        'tools.encode.on'       : True,
        'tools.encode.encoding' : 'utf-8',
    },
    '/index' : {
        'tools.staticfile.on' : True,
        'tools.staticfile.filename' : os.path.join( os.getcwd(), 'static/index.html' ),
        },
    '/static' : {
        'tools.staticdir.on' : True,
        'tools.staticdir.dir' : os.path.join( os.getcwd(), 'static' ),
    },
}

class Server:

    def __init__( self, database_path = None ):

        self.dialogs = {
            'rename' : dialog.RenameDialog(),
        }
        self.searches = {}

        if( database_path is None ):
            higu.init_default()
        else:
            higu.init( database_path )

    def open_db( self ):

        return higu.Database()

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

    def generate_album_pane( self, album ):

        files = album.get_files()

        html = HtmlGenerator()
        html.list( '<a class="albumlink" href="#%d-%d"><img src="/img?id=%d&exp=7"/></a>',
                enumerate( files ), lambda x: ( album.get_id(), x[0], x[1].get_id() ), cls = 'thumbslist' )
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

    @cherrypy.expose
    def callback_new( self ):
        cherrypy.response.headers['Content-Type'] = 'application/json'

        cl = cherrypy.request.headers['Content-Length']
        data = cherrypy.request.body.read( int( cl ) )
        print '111'
        print data
        data = json.loads( data )

        print '***'
        print data

        view = JsonWebView()
        result = view.execute( data )

        print '==='
        print result

        view.close()

        return json.dumps( result )

    def img( self, id = None, exp = None ):

        db = self.open_db()

        if( id == None ):
            raise cherrypy.HTTPError( 404 )

        try:
            id = int( id )
        except:
            raise cherrypy.HTTPError( 400 )

        if( exp is None ):
            exp = 10
        else:
            exp = int( exp )

        f = db.get_object_by_id( id )
        p = f.get_thumb( exp )

        if( p == None ):
            raise cherrypy.HTTPError( 404 )

        name = os.path.split( p )[-1]
        ext = name[name.rindex( '.' )+1:]

        name = f.get_repr()

        db.close()

        return cherrypy.lib.static.serve_file( p, 'image/' + ext, 'inline', name )

    img.exposed = True
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
