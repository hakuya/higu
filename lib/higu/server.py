import cherrypy
import os
import uuid
import time
import json

import higu.config as config

import higu.model as model
import higu.thumb_generator as thumb_generator
import higu.web_session as web_session

from higu.html import TextFormatter, HtmlGenerator

import hdbfs
import json_interface

_json = json

CONFIG={
    'global' : {
        'server.socket_host'    : '0.0.0.0',
        'server.socket_port'    : 8080,
        'tools.encode.on'       : True,
        'tools.encode.encoding' : 'utf-8',
    },
    '/index' : {
        'tools.staticfile.on' : True,
        'tools.staticfile.filename' : os.path.join( os.getcwd(), 'html/index.html' ),
    },
    '/static' : {
        'tools.staticdir.on' : True,
        'tools.staticdir.dir' : os.path.join( os.getcwd(), 'static' ),
    },
}

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
    def do_login( self, username, password, json = 0 ):

        access = web_session.WebSessionAccess()
        session_id = self.__get_session_id( access )

        success = access.login( session_id, username, password )

        cherrypy.response.headers['Content-Type'] = 'application/json'
        return _json.dumps( {
                    'username' : username,
                    'session_id' : session_id if( success ) else None,
                    'success' : success
                } ).encode( 'utf8' )

    @cherrypy.expose
    def do_logout( self ):

        from cherrypy.lib.static import serve_file

        access = web_session.WebSessionAccess()
        session_id = self.__get_session_id( access )

        access.logout( session_id )

        return serve_file( os.path.join( os.getcwd(), 'html/logout.html' ),
                           content_type = 'text/html' )

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

        return json.dumps( result ).encode( 'utf8' )

    @cherrypy.expose
    def img( self, id = None, exp = None, gen = None, stream = None ):

        with self.__get_session()[0] as db:

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

            mime = stream.get_mime()
            name = rep.get_repr()

            p = stream.open()

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

    print( 'Running thumb generator' )
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

    print( 'Starting server' )
    cherrypy.quickstart( server, config=CONFIG )

# vim:sts=4:et:sw=4
