import unittest

class RequirementCases( unittest.TestCase ):

    def setUp( self ):

        pass

    def tearDown( self ):

        pass

    def test_python( self ):

        import sys

        ver = sys.version_info
        self.assertEqual( ver[0], 3,
                'Only Python 3.x series is supported' )

    def test_cherrypy( self ):

        try:
            import cherrypy
        except ImportError:
            self.fail( 'CherryPy is not installed' )

        ver = list( map( lambda x: int( x ), cherrypy.__version__.split( '.' ) ) )

        self.assertTrue( ver[0] > 3 or (ver[0] == 3 and ver[1] >= 1),
                'CherryPy must be at least version 3.1' )

    def test_sqlalchemy( self ):

        try:
            import sqlalchemy
        except ImportError:
            self.fail( 'SqlAlchemy is not installed' )

        ver = list( map( lambda x: int( x ), sqlalchemy.__version__.split( '.' ) ) )

        self.assertTrue( ver[0] > 0 or ver[1] >= 5,
                'SqlAlchemy must be at least version 0.5' )

    def test_pil( self ):

        try:
            import PIL
        except ImportError:
            self.fail( 'PIL is not installed' )

        ver = list( map( lambda x: int( x ), PIL.__version__.split( '.' ) ) )

        self.assertTrue( ver[0] >= 1,
                'PIL must be at least version 2.0' )

    def test_bcrypt( self ):

        try:
            import bcrypt
        except ImportError:
            self.fail( 'bcrypt is not installed' )

if( __name__ == '__main__' ):
    unittest.main()
