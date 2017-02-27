import unittest
import testutil
import shutil
import os
import types
import datetime

import hdbfs

class LegacyCases( testutil.TestCase ):

    def setUp( self ):

        self.init_env( False )

    def tearDown( self ):

        self.uninit_env()

    def _create_library_structure( self, ver ):

        shutil.copytree( os.path.join( self.data_dir,
                                       'ver_%d.%d.db' % ver ),
                         self.db_path )

    def _lookup( self, h, tags = [], type = None ):

        tags = map( lambda x: hdbfs.query.TagConstraint( x ), tags )

        query = hdbfs.query.Query()
        query.set_constraints( tags )
        
        if( type is not None ):
            query.set_type( type )
        
        return [ obj for obj in query.execute( h ) ]

    def _single( self, h, tags = [], type = None ):

        r = self._lookup( h, tags, type )
        if( len( r ) == 0 ):
            self.fail( 'Result expected' )
        return r[0]

    def subtest_ensure_files_present( self, ver ):

        h = hdbfs.Database()

        files = self._lookup( h, type = hdbfs.TYPE_FILE )

        self.assertEqual( len( files ), 8,
                'Unexpected number of files in DB' )

        for f in files:
            self.assertTrue( isinstance( f, hdbfs.File ),
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

    def subtest_ensure_streams_present( self, ver ):

        h = hdbfs.Database()

        files = self._lookup( h, type = hdbfs.TYPE_FILE )
        streams = []

        for f in files:
            streams.append( f.get_root_stream() )
            streams.extend( f.get_duplicates() )

        self.assertEqual( len( streams ), 9,
                'Unexpected number of streams in DB' )

        hashs = map( lambda x: x.get_hash(), streams )
        self.assertTrue( self.magenta_hash in hashs,
                'Magenta not found' )
        self.assertTrue( self.red_hash in hashs,
                'Red not found' )
        self.assertTrue( self.yellow_hash in hashs,
                'Yellow not found' )
        self.assertTrue( self.green_hash in hashs,
                'Green not found' )
        self.assertTrue( self.cyan_hash in hashs,
                'Cyan not found' )
        self.assertTrue( self.blue_hash in hashs,
                'Blue not found' )
        self.assertTrue( self.white_hash in hashs,
                'White not found' )
        self.assertTrue( self.grey_hash in hashs,
                'Grey not found' )
        self.assertTrue( self.black_hash in hashs,
                'Black not found' )

    def subtest_ensure_files_have_timestamp( self, ver ):

        h = hdbfs.Database()

        files = self._lookup( h, type = hdbfs.TYPE_FILE )

        now = datetime.datetime.utcnow()
        for f in files:
            self.assertTrue( now - f.get_creation_time_utc()
                           < datetime.timedelta( minutes = 5 ),
                    'Unexpected timestamp in file, %r' % (
                        f.get_creation_time_utc(), ) )

    def subtest_ensure_streams_have_timestamp( self, ver ):

        h = hdbfs.Database()

        files = self._lookup( h, type = hdbfs.TYPE_FILE )

        now = datetime.datetime.utcnow()
        for f in files:
            for s in f.get_streams():
                self.assertTrue( now - s.get_creation_time_utc()
                               < datetime.timedelta( minutes = 5 ),
                        'Unexpected timestamp in file, %r' % (
                            s.get_creation_time_utc(), ) )

    def subtest_check_tagging( self, ver ):

        h = hdbfs.Database()

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

        h = hdbfs.Database()

        white = self._single( h, [ 'white' ] )
        grey = self._single( h, [ 'grey' ] )

        vo_list = grey.get_variant_of()
        self.assertEqual( len( vo_list ), 1,
                'Grey variant of list len mismatch' )
        self.assertTrue( white in grey.get_variant_of(),
                'Grey should be variant of white' )

        dup_list = grey.get_duplicates()
        self.assertEqual( len( dup_list ), 1,
                'Grey duplicate list len mismatch' )
        self.assertEqual( dup_list[0].get_hash(), self.black_hash,
                'Black is not the duplicate of grey' )

    def subtest_check_dup_moved( self, ver ):

        h = hdbfs.Database()
        
        grey = self._single( h, [ 'grey' ] )
        grey2 = self._single( h, [ 'black' ] )

        self.assertEqual( grey, grey2,
                'Black tag not moved' )
        self.assertEqual( len( grey.get_variants() ), 1,
                'Unexpected variant count' )
        self.assertEqual( grey.get_variants()[0].get_name(), self.blue,
                'Blue not moved as black\'s variant' )

    def subtest_check_multi_names( self, ver ):

        h = hdbfs.Database()

        grey = self._single( h, [ 'grey' ] )
        names = grey.get_names()

        self.assertTrue( self.grey in names,
                'Primary name not found' )
        self.assertTrue( 'grey_sq2.png' in names,
                'Secondary name not found' )

    def subtest_check_album( self, ver ):

        h = hdbfs.Database()

        if( ver[0] < 2 ):
            cl_al = self._single( h, type = hdbfs.TYPE_ALBUM )

            self.assertTrue( isinstance( cl_al, hdbfs.Album ),
                    'Unexpected type found %s' % (
                        str( type( cl_al ) ) ) )

            cl_files = cl_al.get_files()

            self.assertEqual( len( cl_files ), 5,
                    'Unexpected number of files in colour album' )

        else:
            cl_al = self._single( h, [ 'colour_album'] )
            bw_al = self._single( h, [ 'white_blue_album'] )

            self.assertTrue( isinstance( cl_al, hdbfs.Album ),
                    'Unexpected type found %s' % (
                        str( type( cl_al ) ) ) )
            self.assertTrue( isinstance( cl_al, hdbfs.Album ),
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

        h = hdbfs.Database()

        album = self._single( h, [ 'colour_album'] )
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

        h = hdbfs.Database()

        album = self._single( h, [ 'white_blue_album'] )

        self.assertEqual( album.get_text(), 'White & Blue',
                'Text mismatch in album' )

    def subtest_check_thumb_streams( self, ver ):

        if( ver[0] < 5 ):
            return

        h = hdbfs.Database()

        white = self._single( h, [ 'white' ] )
        grey = self._single( h, [ 'grey' ] )
        
        white_s = white.get_streams()
        grey_s = grey.get_streams()

        if( ver[0] < 8 ):
            self.assertEqual( len( white_s ), 1,
                    'Unexpected number of streams in white obj' )
        else:
            self.assertEqual( len( white_s ), 2,
                    'Unexpected number of streams in white obj' )

        self.assertEqual( len( grey_s ), 4,
                'Unexpected number of streams in grey obj' )

class BoundSubtest:

    def __init__( self, fn, ver ):

        self.fn = fn
        self.ver = ver

    def __call__( self, lself ):

        lself._create_library_structure( self.ver )
        lself._init_hdbfs()
        self.fn( lself, self.ver )

def build_cases():

    cls = LegacyCases

    VERSIONS = [ ( 1, 0, ), ( 1, 1, ), ( 2, 0, ), ( 3, 0, ),
                 ( 4, 0, ), ( 5, 0, ), ( 6, 0, ), ( 7, 0, ),
                 ( 8, 0, ), ( 8, 1, ), ( 9, 0, ) ]

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
