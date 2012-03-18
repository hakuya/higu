
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

    def make_tag( self, tag, kind = 0, **args ):

        sarg = ''

        for arg in args:
            if( arg == 'cls' ):
                sarg += ' class'
            else:
                sarg += ' ' + arg

            if( args[arg] is not None ):
                s = args[arg]
                try:
                    s.index( "'" )
                    try:
                        s.index( '"' )
                        assert False
                    except ValueError:
                        sarg += '="%s"' % ( s )
                except ValueError:
                    sarg += "='%s'" % ( s )

        if( kind == 1 ):
            return '<' + tag + sarg + '>'
        elif( kind == 0 ):
            return '<' + tag + sarg + '/>'
        elif( kind == -1 ):
            return '</' + tag + sarg + '>'

    def tag( self, tag, kind = 0, **args ):

        self.content.append( self.make_tag( tag, kind, **args ) )

    def header( self, text, level = 2 ):

        self.content.append( '<h%d>%s</h%d>' % ( level, text, level, ) )

    def br( self ):

        self.tag( 'br' )

    def hr( self ):

        self.tag( 'hr' )

    def begin_form( self, **args ):

        self.tag( 'form', 1, **args )

    def end_form( self ):
    
        self.tag( 'form', -1 )

    def input( self, **args ):

        self.tag( 'input', 0, **args )

    def begin_ul( self, **args ):

        self.tag( 'ul', 1, **args )

    def end_ul( self ):

        self.tag( 'ul', -1 )

    def item( self, text, *fmt, **args ):

        self.content.append( self.make_tag( 'li', 1, **args )
                           + text % fmt
                           + self.make_tag( 'li', -1 ) )

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

    def span( self, text, *fmt, **args ):

        self.content.append( self.make_tag( 'span', 1, **args )
                           + text % fmt
                           + self.make_tag( 'span', -1 ) )

    def text( self, text, *fmt ):

        self.content.append( text % fmt )

    def generator( self, generator ):

        self.content.append( generator )

    def format( self ):

        def stringify( x ):

            if( not isinstance( x, str ) and not isinstance( x, unicode ) ):
                return str( x )
            else:
                return x

        return ''.join( map( stringify, self.content ) )

# vim:sts=4:et:sw=4
