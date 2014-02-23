import higu
import cherrypy
import os
import uuid
import time
import config
import json

import json_interface

from html import TextFormatter, HtmlGenerator

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

    def __init__( self ):

        self.cfg = config.config().subsection( 'www' )

    def get_host( self ):

        return self.cfg['host']

    def get_port( self ):

        return int( self.cfg['port'] )

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

        jsif = json_interface.JsonInterface()
        result = jsif.execute( data )

        print '==='
        print result

        jsif.close()

        return json.dumps( result )

    @cherrypy.expose
    def img( self, id = None, exp = None ):

        db = higu.Database()

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

        cherrypy.response.headers["Content-Type"] = mime
        cherrypy.response.headers["Content-Disposition"] = 'attachment; filename="%s"' % name

        db.close()

        def stream():

            with p:
                while( 1 ):
                    data = p.read( 4096 )
                    if( len( data ) == 0 ):
                        break
                    yield data

        return stream()

if( __name__ == '__main__' ):

    import sys

    if( len( sys.argv ) > 1 ):
        higu.init( sys.argv[1] )
    else:
        higu.init()

    server = Server()
    CONFIG['global']['server.socket_host'] = server.get_host()
    CONFIG['global']['server.socket_port'] = server.get_port()

    cherrypy.quickstart( server, config=CONFIG )

# vim:sts=4:et:sw=4
