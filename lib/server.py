import higu
import cherrypy
import os
import uuid
import time
import config
import json

import json_interface

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
            p = f.get_path()
        else:
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

    if( len( sys.argv ) > 1 ):
        higu.init( sys.argv[1] )
    else:
        higu.init()

    server = Server()
    CONFIG['global']['server.socket_host'] = server.get_host()
    CONFIG['global']['server.socket_port'] = server.get_port()

    cherrypy.quickstart( server, config=CONFIG )

# vim:sts=4:et:sw=4
