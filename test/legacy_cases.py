import unittest
import testutil
import shutil
import os
import higu
import types
import datetime

class LegacyCases( testutil.TestCase ):

    def setUp( self ):

        self.init_env( False )

    def tearDown( self ):

        self.uninit_env()

    def _create_library_structure( self, ver ):

        os.makedirs( self.db_path )
        src = os.path.join( self.data_dir, 'hfdb_%d.%d.dat' % ver )
        tgt = os.path.join( self.db_path, 'hfdb.dat' )

        shutil.copy( src, tgt )

    def _lookup( self, h, tags = [], type = None ):

        tags = map( lambda x: h.get_tag( x ), tags )

        return [ obj for obj in
                h.lookup_objects( tags, type = type ) ]

    def subtest_ensure_files_present( self, ver ):

        h = higu.Database()

        files = self._lookup( h, type = higu.TYPE_FILE )
        files.extend( self._lookup( h, type = higu.TYPE_FILE_DUP ) )
        files.extend( self._lookup( h, type = higu.TYPE_FILE_VAR ) )

        self.assertEqual( len( files ), 9,
                'Unexpected number of files in DB' )

        for f in files:
            self.assertTrue( isinstance( f, higu.File ),
                    'Unexpected file type found %s' % (
                        str( type( f ) ) ) )

        fnames = map( lambda x: x.get_name(), files )
        self.assertTrue( self.magenta in fnames,
                'Magenta not found' )
        self.assertTrue( self.red in fnames,
                'Red not found' )
        self.assertTrue( self.yellow in fnames,
                'Yellow not found' )
        self.assertTrue( self.green in fnames,
                'Green not found' )
        self.assertTrue( self.cyan in fnames,
                'Cyan not found' )
        self.assertTrue( self.blue in fnames,
                'Blue not found' )
        if( ver == ( 1, 0, ) ):
            self.assertTrue( self.white in fnames,
                    'White not found' )
        else:
            self.assertTrue( None in fnames,
                    'White not found' )
        self.assertTrue( self.grey in fnames,
                'Grey not found' )
        self.assertTrue( self.black in fnames,
                'Black not found: ' + str( fnames ) )

    def subtest_ensure_files_have_timestamp( self, ver ):

        h = higu.Database()

        files = self._lookup( h, type = higu.TYPE_FILE )
        files.extend( self._lookup( h, type = higu.TYPE_FILE_DUP ) )
        files.extend( self._lookup( h, type = higu.TYPE_FILE_VAR ) )

        now = datetime.datetime.utcnow()
        for f in files:
            self.assertTrue( now - f.get_creation_time_utc()
                           < datetime.timedelta( minutes = 5 ),
                    'Unexpected timestamp in file, %r' % (
                        f.get_creation_time_utc(), ) )

    def subtest_check_tagging( self, ver ):

        h = higu.Database()

        colour = self._lookup( h, [ 'colour'] )
        warm = self._lookup( h, [ 'warm'] )
        cool = self._lookup( h, [ 'cool'] )
        greyscale = self._lookup( h, [ 'greyscale'] )
        white = self._lookup( h, [ 'white'] )
        grey = self._lookup( h, [ 'grey'] )
        black = self._lookup( h, [ 'black'] )

        self.assertEqual( len( colour ), 6,
                'Unexpected number of files in colour' )
        self.assertEqual( len( warm ), 3,
                'Unexpected number of files in warm' )
        self.assertEqual( len( cool ), 3,
                'Unexpected number of files in cool' )
        self.assertEqual( len( greyscale ), 2,
                'Unexpected number of files in greyscale' )
        self.assertEqual( len( white ), 1,
                'Unexpected number of files in white' )
        self.assertEqual( len( grey ), 1,
                'Unexpected number of files in grey' )
        self.assertEqual( len( black ), 1,
                'Unexpected number of files in black' )

    def subtest_check_dup_and_var( self, ver ):

        h = higu.Database()

        white = self._lookup( h, [ 'white' ] )[0]
        grey = self._lookup( h, [ 'grey' ] )[0]

        self.assertTrue( grey.is_variant()
                    and grey.get_similar_to() == white,
                'Grey should be variant of white' )
        self.assertEqual( len( grey.get_duplicates() ), 1,
                'Grey duplicate list len mismatch' )

        black = grey.get_duplicates()[0]
        self.assertEqual( black.get_name(), self.black,
                'Black is not the duplicate of grey' )

    def subtest_check_dup_moved( self, ver ):

        h = higu.Database()
        
        grey = self._lookup( h, [ 'grey' ] )[0]
        grey2 = self._lookup( h, [ 'black' ] )[0]

        self.assertEqual( grey, grey2,
                'Black tag not moved' )
        self.assertEqual( len( grey.get_variants() ), 1,
                'Unexpected variant count' )
        self.assertEqual( grey.get_variants()[0].get_name(), self.blue,
                'Blue not moved as black\'s variant' )

    def subtest_check_multi_names( self, ver ):

        h = higu.Database()

        grey = self._lookup( h, [ 'grey' ] )[0]
        names = grey.get_names()

        self.assertTrue( self.grey in names,
                'Primary name not found' )
        self.assertTrue( 'grey_sq2.png' in names,
                'Secondary name not found' )

    def subtest_check_album( self, ver ):

        h = higu.Database()

        if( ver[0] < 2 ):
            cl_al = self._lookup( h, type = higu.TYPE_ALBUM )[0]

            self.assertTrue( isinstance( cl_al, higu.Album ),
                    'Unexpected type found %s' % (
                        str( type( cl_al ) ) ) )

            cl_files = cl_al.get_files()

            self.assertEqual( len( cl_files ), 5,
                    'Unexpected number of files in colour album' )

        else:
            cl_al = self._lookup( h, [ 'colour_album'] )[0]
            bw_al = self._lookup( h, [ 'white_blue_album'] )[0]

            self.assertTrue( isinstance( cl_al, higu.Album ),
                    'Unexpected type found %s' % (
                        str( type( cl_al ) ) ) )
            self.assertTrue( isinstance( cl_al, higu.Album ),
                    'Unexpected type found %s' % (
                        str( type( bw_al ) ) ) )

            cl_files = cl_al.get_files()
            bw_files = bw_al.get_files()

            self.assertEqual( len( cl_files ), 6,
                    'Unexpected number of files in colour album' )
            self.assertEqual( len( bw_files ), 2,
                    'Unexpected number of files in white/blue album' )

    def subtest_check_album_order( self, ver ):

        if( ver[0] < 2 or ver[0] == 4 ):
            return

        h = higu.Database()

        album = self._lookup( h, [ 'colour_album'] )[0]
        colours = album.get_files()

        self.assertEqual( colours[0].get_name(), self.blue,
                'Expected blue in pos 0' )
        self.assertEqual( colours[1].get_name(), self.cyan,
                'Expected cyan in pos 1' )
        self.assertEqual( colours[2].get_name(), self.green,
                'Expected green in pos 2' )
        self.assertEqual( colours[3].get_name(), self.yellow,
                'Expected yellow in pos 3' )
        self.assertEqual( colours[4].get_name(), self.red,
                'Expected red in pos 4' )
        self.assertEqual( colours[5].get_name(), self.magenta,
                'Expected magenta in pos 5' )

    def subtest_check_album_text( self, ver ):

        if( ver[0] < 5 ):
            return

        h = higu.Database()

        album = self._lookup( h, [ 'white_blue_album'] )[0]

        self.assertEqual( album.get_text(), 'White & Blue',
                'Text mismatch in album' )

class BoundSubtest:

    def __init__( self, fn, ver ):

        self.fn = fn
        self.ver = ver

    def __call__( self, lself ):

        lself._create_library_structure( self.ver )
        lself._init_higu()
        self.fn( lself, self.ver )

def build_cases():

    cls = LegacyCases

    VERSIONS = [ ( 1, 0, ), ( 1, 1, ), ( 2, 0, ), ( 3, 0, ),
                 ( 4, 0, ), ( 5, 0, ), ( 6, 0, ), ( 7, 0, ),
                 ( 8, 0, ), ( 8, 1, ) ]

    for ver in VERSIONS:

        items = dir( cls )
        for item in items:
            if( not item.startswith( 'subtest_' ) ):
                continue

            # For each version and sub-test, create a test
            fn = getattr( cls, item )
            bound_fn = BoundSubtest( fn, ver ).__call__
            setattr( cls, 'test_%d_%d_%s' % (
                        ver[0], ver[1], item[8:] ),
                    types.MethodType( bound_fn, None, cls ) )

build_cases()

if( __name__ == '__main__' ):
    unittest.main()
