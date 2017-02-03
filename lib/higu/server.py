import cherrypy
import os
import uuid
import time
import config
import json

import hdbfs

from genshi.template import TemplateLoader

import json_interface
import thumb_generator

from html import TextFormatter, HtmlGenerator

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

loader = TemplateLoader(
    os.path.join( os.getcwd(), 'templates' ),
    auto_reload = True )

class Server:

    def __init__( self ):

        self.cfg = config.config().subsection( 'www' )

    def get_host( self ):

        return self.cfg['host']

    def get_port( self ):

        return int( self.cfg['port'] )

    @cherrypy.expose
    def index( self ):

        db = hdbfs.Database()
        all_tags = db.all_tags()

        tmpl = loader.load( 'index.html' )
        stream = tmpl.generate( taglist = all_tags,
                                logged_in = True,
                                is_admin = True )
        return stream.render( 'html', doctype = 'html' )    

    @cherrypy.expose
    def admin( self ):

        tmpl = loader.load( 'tabs/admin.html' )
        stream = tmpl.generate()
        return stream.render( 'html', doctype = 'html' )    

    @cherrypy.expose
    def taglist( self ):

        db = hdbfs.Database()
        all_tags = db.all_tags()

        tmpl = loader.load( 'tabs/taglist.html' )
        stream = tmpl.generate( taglist = all_tags )
        return stream.render( 'html', doctype = 'html' )    

    @cherrypy.expose
    def callback_new( self ):
        cherrypy.response.headers['Content-Type'] = 'application/json'

        cl = cherrypy.request.headers['Content-Length']
        data = cherrypy.request.body.read( int( cl ) )
        data = json.loads( data )

        jsif = json_interface.JsonInterface()
        result = jsif.execute( data )

        jsif.close()

        return json.dumps( result )

    @cherrypy.expose
    def img( self, id = None, exp = None, gen = None ):

        db = hdbfs.Database()

        try:
            # The thumb cache requires the ability to write to the database
            db.enable_write_access()

            if( id == None ):
                raise cherrypy.HTTPError( 404 )

            try:
                id = int( id )
                if( exp is not None ):
                    exp = int( exp )
            except:
                raise cherrypy.HTTPError( 400 )

            f = db.get_object_by_id( id )
            if( exp is None ):
                p = f.read()
                mime = f.get_mime()
            else:
                p = f.read_thumb( exp )
                mime = 'image/jpeg'

            if( p == None ):
                raise cherrypy.HTTPError( 404 )

            name = f.get_repr()
        finally:
            db.close()

        cherrypy.response.headers["Content-Type"] = mime
        cherrypy.response.headers["Content-Disposition"] = 'filename="%s"' % name

        def stream():

            with p:
                while( 1 ):
                    data = p.read( 4096 )
                    if( len( data ) == 0 ):
                        break
                    yield data

        return stream()

def _background_thumb_generator():

    print 'Running thumb generator'
    gen = thumb_generator.ThumbGenerator()

    while( True ):
        try:
            gen.run( 9, False, 2 )
        except:
            cherrypy.log( 'Exception while generating thumbs', traceback=True )
            
        time.sleep( 2 )

def start():

    tbgen = cherrypy.process.plugins.BackgroundTask( 2, _background_thumb_generator )
    tbgen.start()

    server = Server()
    CONFIG['global']['server.socket_host'] = server.get_host()
    CONFIG['global']['server.socket_port'] = server.get_port()

    print 'Starting server'
    cherrypy.quickstart( server, config=CONFIG )

# vim:sts=4:et:sw=4
