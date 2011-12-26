import higu
import cherrypy
import os

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

    def admin( self, action = None, **args ):
        cherrypy.response.headers['Content-Type'] = "text/html; charset=utf-8" 

        s = ''

        if( action == 'rename' ):
            if( args['rntag'] != '' and args['rnnew'] != '' ):
                db = self.open_db()
                db.rename_tag( args['rntag'], args['rnnew'] )
                db.commit()

        s += '<h2>Rename tag</h2>'
        s += '<form>'
        s += """Tag: <input type="text" name="rntag"/> New: <input type="text" name="rnnew"/> <input type="button" value="Update" onclick="load( 'main', '/admin?action=rename&rntag=' + this.form.rntag.value + '&rnnew=' + this.form.rnnew.value )"/>"""
        s += '</form>'

        return s

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
            return '<img src="/img?id=%d" class="picture" onload="resize_image( this )" onclick="nextfile( %d, 1 )"/><br/>' % ( f.get_id(), f.get_id() )

    def info( self, id = None, action = None ):

        if( id == None ):
            raise cherrypy.HTTPError( 404 )
        try:
            ids = id.split( ' ' )
            ids = map( lambda x: int( x ), ids )
        except:
            raise cherrypy.HTTPError( 400 )

        db = self.open_db()
        obj = db.get_object_by_id( ids[-1] )

        s = ''

        # Process an action
        if( action != None ):
            try:
                action.index( '|' )
                cmd, parm = action.split( '|' )
            except ValueError:
                cmd = action
                parm = ''

            parms = parm.split( ' ' )
            if( cmd == 'tag' ):
                files = map( lambda x: higu.File( obj.db, x ), ids )

                for fx in files:
                    for t in parms:
                        fx.tag( t )
            elif( cmd == 'untag' ):
                obj.untag( parm )
            elif( cmd == 'rempar' ):
                obj.set_parent( None )
            elif( cmd == 'rm' ):
                db.delete_object( obj )
            elif( cmd == 'album' ):
                files = map( lambda x: higu.File( obj.db, x ), ids )
                album = db.get_object_by_id( int( parm ) )

                for fx in files:
                    album.add_file( fx )
            elif( cmd == 'group' ):
                files = map( lambda x: higu.File( obj.db, x ), ids )
                fn = int( parm )

                if( fn == 0 ):
                    c = db.create_album()
                    for fx in files:
                        c.add_file( fx )
                elif( fn == 1 ):
                    for fx in files[:-1]:
                        fx.set_varient_of( files[-1] )
                elif( fn == 2 ):
                    for fx in files[:-1]:
                        fx.set_duplicate_of( files[-1] )

            db.commit()

        if( isinstance( obj, higu.Album ) ):
            s += '<h2>Files</h2>'

            fs = obj.get_files()

            s += '<ul>'
            for g in fs:
                s += '<li><a href="javascript:selectfromalbum( %d, %d )">%s</a></li>' \
                        % ( obj.get_id(), g.get_id(), g.get_name(), )
            s += '</ul>'

        s += '<h2>Tags</h2>'

        tags = obj.get_tags()

        s += '<ul>'
        for t in tags:
            s += """<li>%s (<a href="javascript:load( 'info', '/info?id=%d&action=untag|%s' )">del</a>)</li>""" \
                    % ( t, obj.get_id(), t )
        s += '</ul>'

        s += '<h2>Names</h2>'

        names = obj.get_names()

        s += '<ul>'
        for n in names:
            s += '<li>%s</li>' % ( n )
        s += '</ul>'

        if( isinstance( obj, higu.File ) ):
            variants = obj.get_variants_of()
            if( len( variants ) > 0 ):
                links = map( lambda x:
                        """<a href="javascript:load( 'viewer', '/view?id=%d' )">%s</a>""" % (
                            x.get_id(), x.get_name() ), variants )
                links = ', '.join( links )

                s += 'Varient of: ' + links + '<br/>'

            duplicates = obj.get_duplicates_of()
            if( len( duplicates ) > 0 ):
                links = map( lambda x:
                        """<a href="javascript:load( 'viewer', '/view?id=%d' )">%s</a>""" % (
                            x.get_id(), x.get_name() ), duplicates )
                links = ', '.join( links )

                s += 'Duplicate of: ' + links + '<br/>'

            variants = obj.get_variants()
            if( len( variants ) > 0 ):
                links = map( lambda x:
                        """<a href="javascript:load( 'viewer', '/view?id=%d' )">%s</a>""" % (
                            x.get_id(), x.get_name() ), variants )
                links = ', '.join( links )

                s += 'Varients: ' + links + '<br/>'

            duplicates = obj.get_duplicates()
            if( len( duplicates ) > 0 ):
                links = map( lambda x:
                        """<a href="javascript:load( 'viewer', '/view?id=%d' )">%s</a>""" % (
                            x.get_id(), x.get_name() ), duplicates )
                links = ', '.join( links )

                s += 'Duplicates: ' + links + '<br/>'

            albums = obj.get_albums()

            if( len( albums ) == 1 ):
                s += '<h2>Album: %s</h2>' % ( albums[0].get_name() )

                fs = albums[0].get_files()

                s += '<ul>'
                for g in fs:
                    s += '<li><a href="javascript:selectfromalbum( %d, %d )">%s</a></li>' \
                            % ( albums[0].get_id(), g.get_id(), g.get_name(), )
                s += '</ul>'

            elif( len( albums ) > 1 ):
                s += '<ul>'
                for c in albums:
                    s += '<li>%s</li>' % ( c.get_name() )
                s += '</ul>'

        s += '<h2>Tools</h2>'
        s += '<ul>'
        s += """<li>Tag: <form onsubmit="load( 'info', '/info?id=%s&action=tag|' + this.tag.value ); return false;"><input type="text" name="tag"/></form></li>""" \
                    % ( id )
        s += '<li><a href="javascript:rm()">Delete</a></li>'

        if( isinstance( obj, higu.File ) and len( ids ) > 1 ):
            albums = []

            objs = map( lambda x: db.get_object_by_id( x ), ids )

            for i in objs:
                if( isinstance( i, higu.File ) ):
                    fas = i.get_albums()
                    for a in fas:
                        if( not a in albums ):
                            albums.append( a )

            s += '<li><a href="javascript:group( 0 )">Create Album</a></li>'
            for i in albums:
                s += """<li><a href="javascript:load( 'info', '/info?id=%s&action=album|%d' )">Add to %s</a></li>""" % (
                        id, i.get_id(), i.get_name() )
            s += '<li><a href="javascript:group( 1 )">Varient</a></li>'
            s += '<li><a href="javascript:group( 2 )">Duplicate</a></li>'
        s += '</ul>'

        db.close()

        return s

    def list( self, mode = None, tags = None, id = None, selected = None ):

        db = self.open_db()
        s = []

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
            for tag in ls:
                if( len( tag ) == 0 ):
                    continue
                elif( tag[0] == '?' ):
                    add.append( tag[1:] )
                elif( tag[0] == '!' ):
                    sub.append( tag[1:] )
                else:
                    require.append( tag )

            objects = db.lookup_objects_by_tags_with_names( require, add, sub, strict )
        elif( mode == 'album' ):
            c = higu.Album( db, int( id ) )
            objects = map( lambda x: ( x, x.get_name(), ), c.get_files() )
        else:
            objects = db.lookup_objects_by_tags_with_names( [], type = higu.TYPE_FILE )

        totidx = len( s )
        s.append( 'Total: %d objects<br/>' )
        s.append( '<form name="list">' )

        c = 0
        for o in objects:
            c += 1

            name = o[1]
            o = o[0]

            id = o.get_id()
            if( o.id == selected ):
                if( isinstance( o, higu.File ) ):
                    s.append( ("""<div style="background:yellow" id="list_div%d"><input """
                            + """type="checkbox" name="list_check%d" checked """
                            + """value="%d" onclick="javascript:clickfile( %d, false )"/>"""
                            + """<a href="javascript:clickfile( %d, true )">%s</a></div>""")
                            % ( id, id, id, id, id, name, ) )
                else:
                    s.append( ("""<div style="background:yellow" id="list_div%d"><input """
                            + """type="checkbox" name="list_check%d" checked """
                            + """value="%d" onclick="javascript:clickalbum( %d )"/>"""
                            + """<a href="javascript:clickalbum( %d )"><i>%s</i></a></div>""")
                            % ( id, id, id, id, id, name, ) )
            else:
                if( isinstance( o, higu.File ) ):
                    s.append( ("""<div id="list_div%d"><input type="checkbox" name="list_check%d" """
                            + """value="%d" onclick="javascript:clickfile( %d, false )"/>"""
                            + """<a href="javascript:clickfile( %d, true )">%s</a></div>""")
                            % ( id, id, id, id, id, name, ) )
                else:
                    s.append( ("""<div id="list_div%d"><input type="checkbox" name="list_check%d" """
                            + """value="%d" onclick="javascript:clickalbum( %d )"/>"""
                            + """<a href="javascript:clickalbum( %d )"><i>%s</i></a></div>""")
                            % ( id, id, id, id, id, name, ) )
        s.append( '</ul>' )

        s[totidx] = s[totidx] % ( c )

        return ''.join( s )

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
