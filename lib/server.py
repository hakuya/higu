import higu
import cherrypy
import os
import time

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
    <form name='search' onsubmit="load( 'list', '/list?mode=tags&tags=' + document.forms[0].tags.value ); return false;">
    <a href="javascript:load( 'list', '/list?mode=all' )">all</a> /
    <a href="javascript:load( 'list', '/list?mode=untagged' )">untagged</a> /
    <a href="javascript:load( 'list', '/list?mode=albums' )">albums</a> /
    <a href="javascript:load( 'main', '/taglist' )">taglist</a> /
    <a href="javascript:load( 'main', '/admin' )">admin</a> /
    <input type="text" name="tags"/></form>
</div>
<div id='sidebar'>
    <div id='info'></div>
    <div id='list'></div>
</div>
<div id='main'>
</div>
<div id='right'>
</div>
"""

class TextFormatter:

    def __init__( self, text ):

        self.text = text
        self.data = None

    def set_data( self, *args ):

        self.data = args

    def __str__( self ):

        if( self.data == None ):
            return self.text
        else:
            return self.text % self.data

class HtmlGenerator:

    def __init__( self ):

        self.content = []

    def header( self, text, level = 2 ):

        self.content.append( '<h%d>%s</h%d>' % ( level, text, level, ) )

    def begin_form( self, name = None ):

        args = ''

        if( name is not None ):
            args += ' name="' + name + '"'

        self.content.append( '<form' + args + '>' )

    def end_form( self ):
    
        self.content.append( '</form>' )

    def begin_ul( self ):

        self.content.append( '<ul>' )

    def end_ul( self ):

        self.content.append( '</ul>' )

    def item( self, text, *args ):

        self.content.append( ('<li>' + text + '</li>') % args )

    def list( self, text, iterable, argfn = None ):

        self.begin_ul()
        if( argfn is None ):
            for i in iterable:
                if( not isinstance( i, tuple ) ):
                    i = ( i, )
                self.item( text, *i )
        else:
            for i in iterable:
                self.item( text, *argfn( i ) )
        self.end_ul()

    def text( self, text, *args ):

        self.content.append( text % args )

    def generator( self, generator ):

        self.content.append( generator )

    def format( self ):

        def stringify( x ):

            if( not isinstance( x, str ) and not isinstance( x, unicode ) ):
                return str( x )
            else:
                return x

        return ''.join( map( stringify, self.content ) )

class Server:

    def __init__( self, database_path = None ):

        self.db_path = database_path

    def open_db( self ):

        if( self.db_path == None ):
            return higu.init_default()
        else:
            return higu.Database( self.db_path )

    def index( self ):

        return INDEX

    def process_action( self, db, objs, action, **args ):

        if( action is None ):
            return

        elif( action == 'rename' ):
            if( args['rntag'] != '' and args['rnnew'] != '' ):
                db.rename_tag( args['rntag'], args['rnnew'] )
        elif( action == 'tag' ):
            tags = args['tags'].split( ' ' )

            for obj in objs:
                for t in tags:
                    obj.tag( t )
        elif( action == 'untag' ):
            if( len( objs ) > 1 ):
                return
            objs[0].untag( args['tag'] )
        elif( action == 'rempar' ):
            for obj in objs:
                obj.set_parent( None )
        elif( action == 'rm' ):
            for obj in objs:
                db.delete_object( obj )
        elif( action == 'album_append' ):
            album = db.get_object_by_id( args['album'] )

            for obj in objs:
                album.add_file( obj )
        elif( action == 'create_album' ):
            c = db.create_album()
            for obj in objs:
                c.add_file( obj )
        elif( action == 'group' ):
            if( args['create'] == 'varient' ):
                for obj in objs[:-1]:
                    obj.set_varient_of( objs[-1] )
            elif( args['create'] == 'duplicate' ):
                for obj in objs[:-1]:
                    obj.set_duplicate_of( objs[-1] )

        db.commit()

    def admin( self, action = None, **args ):

        cherrypy.response.headers['Content-Type'] = "text/html; charset=utf-8" 

        html = HtmlGenerator()

        process_action( self, db, [], action, **args )

        html.header( 'Rename tag' )
        html.begin_form()
        html.text( """Tag: <input type="text" name="rntag"/> New: <input type="text" name="rnnew"/> <input type="button" value="Update" onclick="load( 'main', '/admin?action=rename&rntag=' + this.form.rntag.value + '&rnnew=' + this.form.rnnew.value )"/>""" )
        html.end_form()

        return html.format()

    def view( self, id = None ):

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
            return 'Image not available<br/>'
        else:
            return '<img src="/img?id=%d" class="picture" onload="register_image( this )" onclick="nextfile( 1 )"/><br/>' % ( f.get_id(), )

    def link_load( self, text, pane, target, action = None, **args ):

        if( action is None ):
            return """<a href="javascript:load( '%s', '/info?id=%d' )">%s</a>""" % (
                    pane, target, text )
        else:
            extra = ''
            for arg in args:
                extra += '&%s=%s' % ( arg, args[arg], )
            return """<a href="javascript:load( '%s', '/info?id=%d&action=%s%s' )">%s</a>""" % (
                    pane, target, action, extra, text )

    def info( self, id = None, action = None, **args ):

        if( id == None ):
            raise cherrypy.HTTPError( 404 )
        try:
            ids = id.split( ' ' )
            ids = map( lambda x: int( x ), ids )
        except:
            raise cherrypy.HTTPError( 400 )

        db = self.open_db()
        obj = db.get_object_by_id( ids[-1] )

        self.process_action( db, map( lambda x: db.get_object_by_id( x ), ids ), action, **args )

        html = HtmlGenerator()

        html.text( obj.get_name() + '<br/>' )

        if( isinstance( obj, higu.Album ) ):

            html.header( 'Files' )
            fs = obj.get_files()
            html.list( '<a href="javascript:selectfromalbum( %d, %d )">%s</a>', fs,
                    lambda x: ( obj.get_id(), x.get_id(), x.get_name(), ) )

        html.header( 'Tags' )
        tags = obj.get_tags()
        html.list( """%s (%s)""",
                tags, lambda x: ( x, self.link_load( 'del', 'info', obj.get_id(), 'untag', tag = x ), ) )

        html.header( 'Names' )
        names = obj.get_names()
        html.list( '%s', names )

        if( isinstance( obj, higu.File ) ):

            variants = obj.get_variants_of()
            if( len( variants ) > 0 ):
                links = map( lambda x:
                        self.link_load( x.get_name(), 'viewer', x.get_id() ), variants )
                links = ', '.join( links )

                html.text( 'Varient of: ' + links + '<br/>' )

            duplicates = obj.get_duplicates_of()
            if( len( duplicates ) > 0 ):
                links = map( lambda x:
                        self.link_load( x.get_name(), 'viewer', x.get_id() ), duplicates )
                links = ', '.join( links )

                html.text( 'Duplicate of: ' + links + '<br/>' )

            variants = obj.get_variants()
            if( len( variants ) > 0 ):
                links = map( lambda x:
                        self.link_load( x.get_name(), 'viewer', x.get_id() ), variants )
                links = ', '.join( links )

                html.text( 'Varients: ' + links + '<br/>' )

            duplicates = obj.get_duplicates()
            if( len( duplicates ) > 0 ):
                links = map( lambda x:
                        self.link_load( x.get_name(), 'viewer', x.get_id() ), duplicates )
                links = ', '.join( links )

                html.text( 'Duplicates: ' + links + '<br/>' )

            albums = obj.get_albums()

            if( len( albums ) == 1 ):

                html.header( 'Album: %s' % ( albums[0].get_name() ) )
                fs = albums[0].get_files()
                html.list( '<a href="javascript:selectfromalbum( %d, %d )">%s</a>', fs,
                        lambda x: ( albums[0].get_id(), x.get_id(), x.get_name(), ) )

            elif( len( albums ) > 1 ):

                html.header( 'Albums:' )
                html.list( '%s', map( lambda x: x.get_name(), albums ) )

        html.header( 'Tools' )
        html.begin_ul()
        html.item( """Tag: <form onsubmit="load( 'info', '/info?id=%s&action=tag&tags=' + this.tag.value ); return false;"><input type="text" name="tag"/></form></li>""", id )
        html.item( '<a href="javascript:rm()">Delete</a>' )

        if( isinstance( obj, higu.File ) and len( ids ) > 1 ):
            albums = []

            objs = map( lambda x: db.get_object_by_id( x ), ids )

            for i in objs:
                if( isinstance( i, higu.File ) ):
                    fas = i.get_albums()
                    for a in fas:
                        if( not a in albums ):
                            albums.append( a )

            html.item( """<a href="javascript:group( 'create_album' )">Create Album</a>""" )
            for i in albums:
                html.item( """<a href="javascript:load( 'info', '/info?id=%s&action=album_append&album=%d' )">Add to %s</a>""",
                        id, i.get_id(), i.get_name() )
            html.item( '<a href="javascript:group( 1 )">Varient</a>' )
            html.item( '<a href="javascript:group( 2 )">Duplicate</a>' )
        html.end_ul()

        db.close()

        return html.format()

    def list( self, mode = None, tags = None, id = None, selected = None ):

        db = self.open_db()
        html = HtmlGenerator()

        if( selected != None ):
            selected = int( selected )

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
                    add.append( tag[1:] )
                elif( tag[0] == '!' ):
                    sub.append( tag[1:] )
                else:
                    require.append( tag )

            if( t == None ):
                objects = db.lookup_objects_by_tags_with_names( require, add, sub, strict, type = higu.TYPE_FILE )
            else:
                objects = db.lookup_objects_by_tags_with_names( require, add, sub, strict, type = t )
        elif( mode == 'album' ):
            c = higu.Album( db, int( id ) )
            objects = map( lambda x: ( x, x.get_name(), ), c.get_files() )
        else:
            objects = db.lookup_objects_by_tags_with_names( [], type = higu.TYPE_FILE )

        total_count = TextFormatter( 'Total: %d objects<br/>' )
        html.generator( total_count )
        html.begin_form( 'list' )

        FILE_SELECTED_ITEM = [  '<div style="background:yellow" id="list_div',
                                '"><input type="checkbox" name="list_check',
                                '" checked value="',
                                '" onclick="javascript:clickfile( ',
                                ', false )"/><a href="javascript:clickfile( ',
                                ', true )">' ]

        ALBUM_SELECTED_ITEM = [ '<div style="background:yellow" id="list_div',
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

        c = 0
        for o in objects:
            c += 1

            name = o[1]
            o = o[0]

            id = o.get_id()
            id_str = str( id )
            if( o.id == selected ):

                if( isinstance( o, higu.File ) ):
                    html.text( id_str.join( FILE_SELECTED_ITEM ) + (name + FILE_ITEM_CLOSE) )
                else:
                    html.text( id_str.join( ALBUM_SELECTED_ITEM ) + (name + ALBUM_ITEM_CLOSE) )
            else:
                if( isinstance( o, higu.File ) ):
                    html.text( id_str.join( FILE_ITEM ) + (name + FILE_ITEM_CLOSE) )
                else:
                    html.text( id_str.join( ALBUM_ITEM ) + (name + ALBUM_ITEM_CLOSE) )

        html.end_form()

        total_count.set_data( c )

        return html.format()

    def taglist( self ):

        db = self.open_db()
        s = ''

        tags = db.all_tags()

        s += '<ul>'
        for t in tags:
            s += """<li><a href="javascript:load( 'list', '/list?mode=tags&tags=%s' )">%s</a></li>""" \
                    % ( t, t,)
        s += '</ul>'

        return s

    def img( self, id = None ):

        db = self.open_db()

        if( id == None ):
            raise cherrypy.HTTPError( 404 )

        try:
            id = int( id )
        except:
            raise cherrypy.HTTPError( 400 )

        f = db.get_object_by_id( id )
        p = f.get_path()

        if( p == None ):
            raise cherrypy.HTTPError( 404 )

        name = os.path.split( p )[-1]
        ext = name[name.rindex( '.' )+1:]

        name = f.get_name()

        db.close()

        return cherrypy.lib.static.serve_file( p, 'image/' + ext, \
                'filename=%s' % ( name )  )

    index.exposed = True
    view.exposed = True
    info.exposed = True
    list.exposed = True
    taglist.exposed = True
    img.exposed = True
    admin.exposed = True

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
