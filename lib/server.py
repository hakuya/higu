import higu
import cherrypy
import os

CONFIG={
    'global' : {
        'server.socket_host' : '0.0.0.0',
        'server.socket_port' : 8080,
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
        s += '<input type="hidden" name="action" value="rename"/>Tag: <input type="text" name="rntag"/> New: <input type="text" name="rnnew"/> <input type="submit">'
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
        f = db.get_file_by_id( id )
        p = f.get_path()
        db.close()

        if( p == None ):
            return 'Image not available<br/>'
        else:
            return '<img src="/img?id=%d" class="picture" onload="resize_image( this )" onclick="nextfile( %d, 1 )"/><br/>' % ( id, id )

    def info( self, id = None, action = None, multi = None ):

        if( id == None ):
            raise cherrypy.HTTPError( 404 )
        try:
            id = int( id )
        except:
            raise cherrypy.HTTPError( 400 )

        db = self.open_db()
        f = db.get_file_by_id( id )

        s = ''

        # Process an action
        if( action != None ):
            cmd, parm = action.split( '|' )
            parms = parm.split( ' ' )
            if( cmd == 'tag' ):
                for t in parms:
                    f.tag( t )
            elif( cmd == 'untag' ):
                f.untag( parm )
            elif( cmd == 'rempar' ):
                f.set_parent( None )
            elif( cmd == 'group' ):
                files = map( lambda x: higu.File( f.db, int( x ) ), parms[1:] )
                fn = int( parms[0] )

                if( fn == 0 ):
                    for fx in files[:-1]:
                        fx.set_parent( files[-1] )
                elif( fn == 1 ):
                    for fx in files[:-1]:
                        fx.set_varient_of( files[-1] )
                elif( fn == 2 ):
                    for fx in files[:-1]:
                        fx.set_duplicate_of( files[-1] )

            db.commit()

        varient = f.is_varient()
        duplicate = f.is_duplicate()
        parent = f.get_parent()

        if( varient ):
            name = parent.get_name()

            s += """Varient of: <a href="javascript:load( 'viewer', '/view?id=%d' )">%s</a>""" \
                    % ( parent.get_id(), name )
        elif( duplicate ):
            name = parent.get_name()

            s += """Duplicate of: <a href="javascript:clickfile( %d, true )">%s</a>""" \
                    % ( parent.get_id(), name )
        elif( parent != None ):
            name = parent.get_name()

            s += """Duplicate of: <a href="javascript:load( 'viewer', '/view?id=%d' )">%s</a>""" \
                    % ( parent.get_id(), name )
        s += '<h2>Tags</h2>'

        tags = f.get_tags()

        s += '<ul>'
        for t in tags:
            s += """<li>%s (<a href="javascript:load( 'info', '/info?id=%d&action=untag|%s' )">del</a>)</li>""" \
                    % ( t, f.get_id(), t )
        s += '</ul>'

        s += '<h2>Names</h2>'

        names = f.get_names()

        s += '<ul>'
        for n in names:
            s += '<li>%s</li>' % ( n )
        s += '</ul>'

        dups = []
        vars = []
        coll = []

        for c in f.child_iterator():

            if( c.is_duplicate() ):
                dups.append( c )
            elif( c.is_varient() ):
                vars.append( c )
            else:
                coll.append( c )

        if( len( dups ) > 0 ):
            s += '<h2>Duplicates</h2>'

            s += '<ul>'
            for g in dups:
                name = g.get_name()
                s += '<li><a href="/view?id=%d" target="viewer">%s</a></li>' \
                % ( g.get_id(), name, )
            s += '</ul>'

        if( len( vars ) > 0 ):
            s += '<h2>Varients</h2>'

            s += '<ul>'
            for g in vars:
                name = g.get_name()
                s += '<li><a href="/view?id=%d" target="viewer">%s</a></li>' \
                % ( g.get_id(), name, )
            s += '</ul>'

        if( len( coll ) > 0 ):
            s += '<h2>Collection</h2>'

            s += '<ul>'
            s += '<li><a href="javascript:selectfromcol( %d, %d )">%s</a></li>' \
                    % ( f.get_id(), f.get_id(), f.get_name(), )
            for g in coll:
                s += '<li><a href="javascript:selectfromcol( %d, %d )">%s</a></li>' \
                        % ( f.get_id(), g.get_id(), g.get_name(), )
            s += '</ul>'

        if( parent != None and not duplicate and not varient ):
            coll = []

            for c in parent.child_iterator():

                if( not c.is_duplicate() and not c.is_varient() ):
                    coll.append( c )

            s += '<h2>Collection</h2>'

            s += '<ul>'
            s += '<li><a href="javascript:selectfromcol( %d, %d )">%s</a></li>' \
                    % ( parent.get_id(), parent.get_id(), parent.get_name(), )
            for g in coll:
                s += '<li><a href="javascript:selectfromcol( %d, %d )">%s</a></li>' \
                        % ( parent.get_id(), g.get_id(), parent.get_name(), )
            s += '</ul>'

        db.close()

        s += '<h2>Tools</h2>'
        s += '<ul>'
        s += """<li>Tag: <form onsubmit="load( 'info', '/info?id=%d&action=tag|' + this.tag.value ); return false;"><input type="text" name="tag"/></form></li>""" \
                    % ( f.get_id() )
        if( multi == '1' ):
            s += '<li><a href="javascript:group( 0 )">Collection</a></li>'
            s += '<li><a href="javascript:group( 1 )">Varient</a></li>'
            s += '<li><a href="javascript:group( 2 )">Duplicate</a></li>'
        s += '</ul>'

        return s

    def list( self, mode = None, tags = None, id = None, selected = None ):

        db = self.open_db()
        s = []

        if( selected != None ):
            selected = int( selected )

        if( mode == 'untagged' ):
            files = db.lookup_files_by_tags_with_names( [], strict = True )
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

            files = db.lookup_files_by_tags_with_names( require, add, sub, strict )
        elif( mode == 'collection' ):
            f = higu.File( db, int( id ) )

            files = [ ( f, f.get_name(), ) ]

            for c in f.child_iterator():

                if( not c.is_duplicate() and not c.is_varient() ):
                    files.append( ( c, c.get_name(), ) )
        else:
            files = db.lookup_files_by_tags_with_names( [] )

        totidx = len( s )
        s.append( 'Total: %d files<br/>' )
        s.append( '<form name="list">' )

        c = 0
        for f in files:
            c += 1

            name = f[1]
            f = f[0]

            id = f.get_id()
            if( f.id == selected ):
                s.append( ("""<div style="background:yellow" id="list_div%d"><input """
                        + """type="checkbox" name="list_check%d" checked """
                        + """value="%d" onclick="javascript:clickfile( %d, false )"/>"""
                        + """<a href="javascript:clickfile( %d, true )">%s</a></div>""")
                        % ( id, id, id, id, id, name, ) )
            else:
                s.append( ("""<div id="list_div%d"><input type="checkbox" name="list_check%d" """
                        + """value="%d" onclick="javascript:clickfile( %d, false )"/>"""
                        + """<a href="javascript:clickfile( %d, true )">%s</a></div>""")
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

        f = db.get_file_by_id( id )
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
