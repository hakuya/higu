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

    def view_admin( self ):

        html = HtmlGenerator()

        html.header( 'Rename tag' )
        html.begin_form()
        html.text( """Tag: <input type="text" name="rntag"/> New: <input type="text" name="rnnew"/> <input type="button" value="Update" onclick="load( '/admin?action=rename_tag&rntag=' + this.form.rntag.value + '&rnnew=' + this.form.rnnew.value )"/>""" )
        html.end_form()

        return html.format()

    def cmd_info( self, data ):

        return self.json.execute( data )

    def cmd_tag( self, data ):

        tags = data['tags'].split( ' ' )

        add = [t for t in tags if t[0] != '-' and t[0] != '!']
        new = [t[1:] for t in tags if t[0] == '!']
        sub = [t[1:] for t in tags if t[0] == '-']

        if( data.has_key( 'targets' ) ):
            targets = data['targets']
        else:
            targets = [ data['target'] ]

        request = {
            'action'    : 'tag',
            'targets'   : targets,
            'add_tags'  : add,
            'sub_tags'  : sub,
            'new_tags'  : new,
        }
        result = self.json.execute( request )

        return result

    def cmd_admin( self, data ):

        return {
            'result'    : 'ok',
            'action'    : 'show-html',
            'data'      : self.view_admin()
        }

    def cmd_taglist( self, data ):

        return self.json.execute( data )

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
                    add.append( tag[1:] )
                elif( tag[0] == '!' ):
                    sub.append( tag[1:] )
                else:
                    req.append( tag )

            request['req'] = req
            request['add'] = add
            request['sub'] = sub

        result = self.json.execute( request )

        return {
            'result'    : 'ok',
            'action'    : 'begin-display',
            'selection' : result['selection'],
            'index'     : result['index'],
            'object_id' : result['first'],
        }

    def cmd_selection_fetch( self, data ):

        print data
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
            'object_id' : result['object_id'],
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

    def cmd_set_duplication( self, data ):

        return self.json.execute( data )

    def cmd_clear_duplication( self, data ):

        return self.json.execute( data )

    def cmd_group_append( self, data ):

        return self.json.execute( data )

    def cmd_group_remove( self, data ):

        return self.json.execute( data )


init = json_interface.init
init_default = json_interface.init_default
