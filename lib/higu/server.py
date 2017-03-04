import cherrypy
import os
import uuid
import time
import config
import json


from genshi.template import TemplateLoader

import hdbfs
import json_interface
import model
import thumb_generator
import web_session

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

    def __get_session_id( self, access ):

        if( 'session_id' in cherrypy.request.cookie ):
            session_id = cherrypy.request.cookie['session_id'].value
        else:
            session_id = None

        new_session_id = access.renew_session( session_id )

        if( session_id != new_session_id ):
            cherrypy.response.cookie['session_id'] = new_session_id

        return new_session_id

    def __get_session( self ):

        access = web_session.WebSessionAccess()
        session_id = self.__get_session_id( access )

        access_level, user_name = access.get_session_info( session_id )
        if( access_level == model.ACCESS_LEVEL_NONE ):
            return None, user_name, False, session_id

        db = hdbfs.Database()
        if( access_level >= model.ACCESS_LEVEL_EDIT ):
            db.enable_write_access()

        return db, user_name, (access_level >= model.ACCESS_LEVEL_ADMIN), session_id

    def get_host( self ):

        return self.cfg['host']

    def get_port( self ):

        return int( self.cfg['port'] )

    @cherrypy.expose
    def index( self ):

        db, username, is_admin, session_id = self.__get_session()

        if( db is not None ):
            all_tags = db.all_tags()
        else:
            all_tags = None

        tmpl = loader.load( 'index.html' )
        stream = tmpl.generate( taglist = all_tags,
                                username = username,
                                is_admin = is_admin )
        return stream.render( 'html', doctype = 'html' )    

    @cherrypy.expose
    def login( self ):

        tmpl = loader.load( 'tabs/login.html' )
        stream = tmpl.generate()
        return stream.render( 'html', doctype = 'html' )    

    @cherrypy.expose
    def do_login( self, username, password ):

        access = web_session.WebSessionAccess()
        session_id = self.__get_session_id( access )

        success = access.login( session_id, username, password )

        tmpl = loader.load( 'login.html' )
        stream = tmpl.generate( username = username,
                                success = success )
        return stream.render( 'html', doctype = 'html' )    

    @cherrypy.expose
    def do_logout( self ):

        access = web_session.WebSessionAccess()
        session_id = self.__get_session_id( access )

        access.logout( session_id )

        tmpl = loader.load( 'logout.html' )
        stream = tmpl.generate()
        return stream.render( 'html', doctype = 'html' )    

    @cherrypy.expose
    def admin( self ):

        tmpl = loader.load( 'tabs/admin.html' )
        stream = tmpl.generate()
        return stream.render( 'html', doctype = 'html' )    

    @cherrypy.expose
    def taglist( self ):

        db = self.__get_session()[0]
        all_tags = db.all_tags()

        tmpl = loader.load( 'tabs/taglist.html' )
        stream = tmpl.generate( taglist = all_tags )
        return stream.render( 'html', doctype = 'html' )    

    @cherrypy.expose
    def callback_new( self ):
        cherrypy.response.headers['Content-Type'] = 'application/json'

        db, username, is_admin, session_id = self.__get_session()

        cl = cherrypy.request.headers['Content-Length']
        data = cherrypy.request.body.read( int( cl ) )
        data = json.loads( data )

        jsif = json_interface.JsonInterface( db, session_id )
        result = jsif.execute( data )

        jsif.close()

        return json.dumps( result )

    @cherrypy.expose
    def img( self, id = None, exp = None, gen = None, stream = None ):

        db = self.__get_session()[0]

        try:
            if( stream is not None ):
                stream = db.get_stream_by_id( stream )
                rep = stream
            else:
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
                    stream = f.get_root_stream()
                else:
                    stream = f.get_thumb_stream( exp )

                if( stream is None ):
                    raise cherrypy.HTTPError( 404 )

                rep = f

            p = stream.read()
            mime = stream.get_mime()
            name = rep.get_repr()
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
