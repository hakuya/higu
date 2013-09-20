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

        print 'yyy'
        print result
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

init = json_interface.init
init_default = json_interface.init_default
