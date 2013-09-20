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

class ResultSet:

    def __init__( self, results ):

        if( isinstance( results, list ) ):
            self.loaded = results
        else:
            self.loaded = []
            self.preload( results.__iter__() )

    def preload( self, results ):

        i = 0

        try:
            self.loaded = [ 0 ] * 10000
            for i in range( 10000 ):
                self.loaded[i] = results.next().get_id()
        except StopIteration:
            self.loaded = self.loaded[:i]

    def fetch( self, idx ):

        if( idx < 0 or idx >= len( self.loaded ) ):
            raise StopIteration

        return self.loaded[idx]

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

    def flush_searches( self ):

        clear_list = []

        for search in self.searches:
            ot, rs = self.searches[search]
            if( time.time() > ot + 3600 ):
                clear_list.append( search )

        for search in clear_list:
            del self.searches[search]

    def close_search( self, search_id ):

        del self.searches[search_id]

    def register_search( self, rs ):

        self.flush_searches()
        search_id = uuid.uuid4().hex
        self.searches[search_id] = ( time.time(), rs, )
        return search_id

    def fetch_search( self, search_id ):

        self.flush_searches()
        ot, search = self.searches[search_id]
        self.searches[search_id] = ( time.time(), search, )

        return search

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

    def generate_content_for_object( self, obj ):

        html = HtmlGenerator()

        html.begin_div( cls = 'info' )
        html.text( self.generate_info_pane( [ obj ] ) )
        html.end_div()

        if( isinstance( obj, higu.File ) ):
            html.begin_div( cls = 'img' )
            html.text( self.generate_image_pane( obj ) )
            html.end_div()
        elif( isinstance( obj, higu.Album ) ):
            html.begin_div( cls = 'thumbs' )
            html.text( self.generate_album_pane( obj ) )
            html.end_div()

        return html.format()

    def do_content_by_new_search( self, db, rs, idx = 0 ):

        search_id = self.register_search( rs )
        oid = rs.fetch( idx )
        obj = db.get_object_by_id( oid )
        data = self.generate_content_for_object( obj )

        db.close()

        return json.dumps( {
            'action' : 'begin-display',
            'search_id' : search_id,
            'object_id' : oid,
            'index' : idx,
            'data' : data,
        } );

    def do_content_by_step_search( self, db, search_id, idx ):

        rs = self.fetch_search( search_id )
        oid = rs.fetch( idx )
        obj = db.get_object_by_id( oid )
        data = self.generate_content_for_object( obj )

        db.close()

        return json.dumps( {
            'action' : 'step-display',
            'search_id' : search_id,
            'object_id' : oid,
            'index' : idx,
            'data' : data,
        } );

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

        return json.dumps( {
            'action' : 'show-html',
            'data' : html.format(),
        } );

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

            similar = obj.get_similar_to()
            if( similar is not None ):
                link = self.link_load( similar.get_repr(), similar.get_id(), loadimg = '1' )

                if( obj.is_duplicate() ):
                    html.text( 'Duplicate of: ' + link + '<br/>' )
                else:
                    html.text( 'Variant of: ' + link + '<br/>' )

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

        if( isinstance( obj, higu.File ) and len( objs ) > 1 ):
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
        data = json.loads( data )

        print '***'
        print data

        view = JsonWebView()
        result = view.execute( data )

        print '==='
        print result

        view.close()

        return json.dumps( result )

    def perform_search( self, db, mode, tags = None ):

        if( mode == 'all' ):
            rs = db.all_albums_or_free_files()

        elif( mode == 'untagged' ):
            rs = db.unowned_files()

        elif( mode == 'albums' ):
            rs = db.all_albums()

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

            
            rs = db.lookup_ids_by_tags( require, add, sub, strict, random_order = True )

        return rs

    def search_new( self, mode, tags = None ):

        cherrypy.response.headers['Content-Type'] = 'application/json'
        db = self.open_db()

        rs = ResultSet( self.perform_search( db, mode, tags ) )
        return self.do_content_by_new_search( db, rs )

    def search_album( self, album, idx = None ):

        cherrypy.response.headers['Content-Type'] = 'application/json'
        db = self.open_db()

        obj = db.get_object_by_id( album )
        if( not isinstance( obj, higu.Album ) ):
            raise cherrypy.HTTPError( 404 )

        if( idx is None ):
            idx = 0
        else:
            idx = int( idx )

        rs = ResultSet( map( lambda x: x.get_id(), obj.get_files() ) ) 
        return self.do_content_by_new_search( db, rs, idx )

    def search_step( self, search_id, idx ):

        cherrypy.response.headers['Content-Type'] = 'application/json'
        db = self.open_db()

        idx = int( idx )
        return self.do_content_by_step_search( db, search_id, idx )

    def search_close( self, search_id ):

        self.close_search( search_id )
        return json.dumps( {
            'action' : 'nop',
        } );

    def taglist( self, selection = None ):

        db = self.open_db()
        tags = db.all_tags()

        print tags

        html = HtmlGenerator()
        html.list( """<a class='taglink' href='#%s'>%s</a></li>""",
                tags, lambda t: ( t.get_name(), t.get_name(), ),
                cls = 'taglist' )

        return json.dumps( {
            'action' : 'show-html',
            'data' : html.format(),
        } );

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

    callback.exposed = True
    search_new.exposed = True
    search_step.exposed = True
    search_album.exposed = True
    search_close.exposed = True
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
