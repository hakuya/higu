import unittest

class RequirementCases( unittest.TestCase ):

    def setUp( self ):

        pass

    def tearDown( self ):

        pass

    def test_python( self ):

        import sys

        ver = sys.version_info
        self.assertEqual( ver[0], 2,
                'Only Python 2.x series is supported' )
        self.assertTrue( ver[1] >= 6,
                'Python must be at least version 2.6' )

    def test_cherrypy( self ):

        try:
            import cherrypy
        except ImportError:
            self.fail( 'CherryPy is not installed' )

        ver = map( lambda x: int( x ), cherrypy.__version__.split( '.' ) )

        self.assertEqual( ver[0], 3,
                'Only CherryPy 3.x series is supported' )
        self.assertTrue( ver[1] >= 1,
                'CherryPy must be at least version 3.1' )

    def test_sqlalchemy( self ):

        try:
            import sqlalchemy
        except ImportError:
            self.fail( 'SqlAlchemy is not installed' )

        ver = map( lambda x: int( x ), sqlalchemy.__version__.split( '.' ) )

        self.assertTrue( ver[0] > 0 or ver[1] >= 5,
                'SqlAlchemy must be at least version 0.5' )

    def test_pil( self ):

        try:
            from PIL import Image
        except ImportError:
            self.fail( 'PIL is not installed' )

        ver = map( lambda x: int( x ), Image.VERSION.split( '.' ) )

        self.assertTrue( ver[0] >= 1,
                'PIL must be at least version 1.0' )

    def test_bcrypt( self ):

        try:
            import bcrypt
        except ImportError:
            self.fail( 'bcrypt is not installed' )

if( __name__ == '__main__' ):
    unittest.main()
