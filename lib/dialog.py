def interpret_bool( b ):

    b = b.lower()

    if( b == 't' or b == 'true' ):
        return True

    try:
        if( int( b ) != 0 ):
            return True
    except ValueError:
        pass

    return False

class TagDialog:

    def get_title( self ):

        return 'Tag'

    def get_dimensions( self ):

        return 300, 70

    def get_parameters( self ):

        return [ ( 'tags', 'value', ) ]

    def format_dialog( self, html, db, selection ):

        html.span( 'Enter a series of tags separated by spaces. Prefix a tag'
                 + ' with a dash to remove it', cls = 'description' )
        html.br()
        html.input( type = 'text', name = 'tags' )
        html.input( type = 'submit', value = 'Apply' )

    def process_input( self, server, db, selection, **args ):

        tags = args['tags'].split( ' ' )

        add = [t for t in tags if t[0] != '-' and t[0] != '!']
        new = [t[1:] for t in tags if t[0] == '!']
        sub = [t[1:] for t in tags if t[0] == '-']

        add = map( db.get_tag, add )
        sub = map( db.get_tag, sub )
        add += map( db.make_tag, new )

        for obj in selection:
            for t in sub:
                obj.unassign( t )
            for t in add:
                obj.assign( t )

        return [ ( 'info', server.generate_info_pane( selection ) ) ]

class RenameDialog:

    def get_title( self ):

        return 'Rename'

    def get_dimensions( self ):

        return 300, 80

    def get_parameters( self ):

        return [ ( 'fname', 'value', ), ( 'saveold', 'checked', ) ]

    def format_dialog( self, html, db, selection ):

        obj = db.get_object_by_id( selection[0] )

        html.span( 'Enter a new filename:', cls = 'description' )
        html.br()
        html.input( type = 'text', name = 'fname', value = obj.get_repr() )
        html.br()
        if( obj.get_name() is None ):
            html.input( type = 'checkbox', name = 'saveold', disabled = None )
        else:
            html.input( type = 'checkbox', name = 'saveold' )
        html.text( 'Save old name ' )
        html.input( type = 'submit', value = 'Apply' )

    def process_input( self, server, db, selection, **args ):

        item = selection[0]

        newname = args['fname']
        oldname = item.get_name()
        if( len( newname ) == 0 or newname == item.get_repr() ):
            return

        item.set_name( newname )
        if( interpret_bool( args['saveold'] ) and oldname is not None ):
            item.register_name( oldname )

        return [ ( 'info', server.generate_info_pane( selection ) ) ]

# vim:sts=4:et:sw=4
