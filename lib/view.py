import json_interface

from html import TextFormatter, HtmlGenerator

class JsonWebView:

    def __init__( self ):

        self.json = json_interface.JsonInterface()

    def close( self ):

        self.json.close()

    def execute( self, data ):

        #try:
        fn = getattr( self, 'cmd_' + data['action'] )
        return fn( data )
        #except:
        #    return { 'result' : 'error' }

    def view_object( self, target ):

        request = {
            'action'    : 'info',
            'targets'   : [ target ],
            'items'     : [ 'type' ],
        }
        result = self.json.execute( request )

        if( result['result'] != 'ok' ):
            return { 'result' : result['result'] }

        info = result['info'][0]

        html = HtmlGenerator()

        html.begin_div( cls = 'info' )
        html.text( self.view_info( target ) )
        html.end_div()

        if( info['type'] == 'file' ):
            html.begin_div( cls = 'img' )
            html.text( self.view_image( target ) )
            html.end_div()
        elif( info['type'] == 'album' ):
            html.begin_div( cls = 'thumbs' )
            html.text( self.view_album( target ) )
            html.end_div()

        return html.format()

    def view_image( self, target ):

        request = {
            'action'    : 'info',
            'targets'   : [ target ],
            'items'     : [ 'path' ],
        }
        result = self.json.execute( request )

        if( result['result'] != 'ok' ):
            return { 'result' : result['result'] }

        info = result['info'][0]
        if( info.has_key( 'path' ) ):
            return '<img src="/img?id=%d" class="picture" onload="register_image( this )" onclick="nextfile( 1 )"/><br/>' % ( target, )
        else:
            return 'Image not available<br/>'

    def view_album( self, target ):

        request = {
            'action'    : 'info',
            'targets'   : [ target ],
            'items'     : [ 'files' ],
        }
        result = self.json.execute( request )

        info = result['info'][0]
        files = info['files']

        html = HtmlGenerator()
        html.list( '<a class="albumlink" href="#%d-%d"><img src="/img?id=%d&exp=7"/></a>',
                enumerate( files ), lambda x: ( target, x[0], x[1][0] ), cls = 'thumbslist' )
        return html.format()

    def link_load( self, text, target, **args ):

        extra = ''
        for arg in args:
            extra += '&%s=%s' % ( arg, args[arg], )
        return """<a href="javascript:load( '/callback?id=%d%s' )">%s</a>""" % (
                target, extra, text )

    def view_info( self, target ):

        request = {
            'action'    : 'info',
            'targets'   : [ target ],
            'items'     : [ 'type', 'repr', 'tags', 'names', 'duplication',
                'similar_to', 'duplicates', 'variants', 'albums', 'files' ]
        }
        result = self.json.execute( request )

        if( result['result'] != 'ok' ):
            return { 'result' : result['result'] }

        info = result['info'][0]
        html = HtmlGenerator()

        html.text( info['repr'] + '<br/>' )

#        if( isinstance( obj, higu.Album ) ):
#
#            html.header( 'Files' )
#            fs = obj.get_files()
#            html.list( '<a href="javascript:selectfromalbum( %d, %d )">%s</a>', fs,
#                    lambda x: ( obj.get_id(), x.get_id(), x.get_repr(), ) )

        html.header( 'Tags' )
        html.list( """%s""", info['tags'] )

        html.header( 'Names' )
        html.list( '%s', info['names'] )

        if( info['type'] == 'file' ):

            if( info.has_key( 'similar_to' ) ):
                link = self.link_load( info['similar_to'][1], info['similar_to'][0], loadimg = '1' )

                if( info['duplication'] == 'duplicate' ):
                    html.text( 'Duplicate of: ' + link + '<br/>' )
                else:
                    html.text( 'Variant of: ' + link + '<br/>' )

            variants = info['variants']
            if( len( variants ) > 0 ):
                links = map( lambda x: self.link_load( x[1], x[0], loadimg = '1' ), variants )
                links = ', '.join( links )

                html.text( 'Varients: ' + links + '<br/>' )

            duplicates = info['duplicates']
            if( len( duplicates ) > 0 ):
                links = map( lambda x: self.link_load( x[1], x[0], loadimg = '1' ), duplicates )
                links = ', '.join( links )

                html.text( 'Duplicates: ' + links + '<br/>' )

            albums = info['albums']
            if( len( albums ) >= 1 ):

                html.header( 'Albums:' )
                html.list( '%s', map( lambda x: x[1], albums ) )

        return html.format()

    def cmd_info( self, data ):

        return {
            'result'    : 'ok',
            'action'    : 'show-html',
            'data'      : self.view_info( data['target'] )
        }

    def cmd_tag( self, data ):

        tags = data['tags'].split( ' ' )

        add = [t for t in tags if t[0] != '-' and t[0] != '!']
        new = [t[1:] for t in tags if t[0] == '!']
        sub = [t[1:] for t in tags if t[0] == '-']

        request = {
            'action'    : 'tag',
            'targets'   : [ data['target'] ],
            'add_tags'  : add,
            'sub_tags'  : sub,
            'new_tags'  : new,
        }
        result = self.json.execute( request )

        return self.cmd_info( data )

    def cmd_search( self, data ):

        request = {
            'action'    : 'search'
        }

        if( data.has_key( 'index' ) ):
            request['index'] = data['index']

        if( data.has_key( 'mode' ) ):
            request['mode'] = data['mode']
            if( request['mode'] == 'album' ):
                request['album'] = data['album']

        elif( data.has_key( 'tags' ) ):
            tags = data['tags']
            
            if( tags[0] == '$' ):
                request['strict'] = True
                tags = tags[1:]

            ls = tags.split( ' ' )
            req = []
            add = []
            sub = []

            for tag in ls:
                if( len( tag ) == 0 ):
                    continue
                elif( tag == '~a' ):
                    pass
                elif( tag == '~f' ):
                    pass
                elif( tag[0] == '?' ):
                    c = db.get_tag( tag[1:] )
                    add.append( c )
                elif( tag[0] == '!' ):
                    c = db.get_tag( tag[1:] )
                    sub.append( c )
                else:
                    c = db.get_tag( tag )
                    req.append( c )

            request['req'] = req
            request['add'] = add
            request['sub'] = sub

        result = self.json.execute( request )

        return {
            'result'    : 'ok',
            'action'    : 'begin-display',
            'selection' : result['selection'],
            'index'     : result['index'],
            'data'      : self.view_object( result['first'] )
        }

    def cmd_selection_fetch( self, data ):

        request = {
            'action'    : 'selection_fetch',
            'selection' : data['selection'],
            'index'     : data['index'],
        }

        result = self.json.execute( request )

        return {
            'result'    : 'ok',
            'action'    : 'step-display',
            'selection' : data['selection'],
            'index'     : data['index'],
            'data'      : self.view_object( result['object_id'] )
        }

    def cmd_selection_close( self, data ):

        request = {
            'action'    : 'selection_close',
            'selection' : data['selection'],
        }

        result = self.json.execute( request )

        return {
            'result'    : 'ok',
            'action'    : 'nop',
        }

init = json_interface.init
init_default = json_interface.init_default
