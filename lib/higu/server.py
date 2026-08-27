import cherrypy
import os
import uuid
import time
import json

import hdbfs.imgdb
import higu.config as config

from hdbfs.imgdb.objects import ThumbRequestPrio

import higu.model as model
import higu.thumb_generator as thumb_generator
import higu.web_session as web_session

from higu.html import TextFormatter, HtmlGenerator

import hdbfs
import json_interface

from typing import Optional

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
        'tools.staticfile.filename' : os.path.join( os.getcwd(), 'webapp/html/index.html' ),
    },
    '/static' : {
        'tools.staticdir.on' : True,
        'tools.staticdir.dir' : os.path.join( os.getcwd(), 'webapp/static' ),
    },
    '/webapp.js' : {
        'tools.staticfile.on' : True,
        'tools.staticfile.filename' : os.path.join( os.getcwd(), 'webapp/build/_bundle.js' ),
    }
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

    def get_ssl_cert( self ):

        if( 'ssl_crt' not in self.cfg or 'ssl_key' not in self.cfg ):
            return None

        return self.cfg['ssl_crt'], self.cfg['ssl_key']

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

        return serve_file( os.path.join( os.getcwd(), 'webapp/html/logout.html' ),
                           content_type = 'text/html' )

    @cherrypy.expose
    def callback_new( self ):
        cherrypy.response.headers['Content-Type'] = 'application/json'

        higu_db, username, is_admin, session_id = self.__get_session()

        cl = cherrypy.request.headers['Content-Length']
        data = cherrypy.request.body.read( int( cl ) )
        data = json.loads( data )

        with higu_db as db:
            jsif = json_interface.JsonInterface( db, session_id )
            result = jsif.execute( data )

            jsif.close()

            return json.dumps( result ).encode( 'utf8' )

    @cherrypy.expose
    def img( self,
                id: Optional[str] = None,
                exp: Optional[str] = None,
                prio: Optional[str] = None,
                gen: Optional[str] = None,
                stream: Optional[str] = None
            ):

        try:
            # Convert arguments to int
            id_int = int( id ) if id is not None else None
            exp_int = int( exp ) if exp is not None else None
            prio_int = int( prio ) if prio is not None else None
            stream_int = int( stream ) if stream is not None else None
        except ValueError:
            raise cherrypy.HTTPError( 400 )

        with self.__get_session()[0] as db:

            sobj = None

            if( stream_int is not None ):
                sobj = db.get_stream_by_id( stream_int )
                rep = sobj
            else:
                # The thumb cache requires the ability to write to the database
                db.enable_write_access()

                if( id_int == None ):
                    raise cherrypy.HTTPError( 404 )

                f = db.get_object_by_id( id_int )

                # Try to resolve an album to a file
                while( isinstance( f, hdbfs.Album ) and f is not None ):
                    files = f.get_items()
                    f = files[0] if len( files ) > 0 else None

                if( isinstance( f, hdbfs.ImageFile ) ):
                    if( exp_int is None ):
                        sobj = f.get_root_stream()
                    elif( prio_int == 1 ):
                        sobj = f.get_thumb_stream( exp_int, ThumbRequestPrio.IMMEDIATE )
                    else:
                        sobj = f.get_thumb_stream( exp_int, ThumbRequestPrio.MARK_REQUESTED )

                rep = f

            if( sobj is not None ):
                mime = sobj.get_mime()
                name = rep.get_repr()
                p = sobj.open()
            else:
                mime = None
                name = None
                p = None

        if( p is None ):
            # This needs to be outside of the with,
            # so that we don't trigger a db rollback
            raise cherrypy.HTTPError( 404 )

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

    ssl_cert = server.get_ssl_cert()
    if( ssl_cert is not None ):
        CONFIG['global']['server.ssl_certificate'] = ssl_cert[0]
        CONFIG['global']['server.ssl_private_key'] = ssl_cert[1]

    print( 'Starting server' )
    cherrypy.quickstart( server, config=CONFIG )

# vim:sts=4:et:sw=4
