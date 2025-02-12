import unittest
import testutil
import shutil
import os
import types
import datetime

import hdbfs

from typing import Optional

class LegacyCases( testutil.TestCase ):

    def setUp( self ):

        self.init_env( False )

    def tearDown( self ):

        self.uninit_env()

    def _create_library_structure( self, ver ):

        shutil.copytree( os.path.join( self.data_dir,
                                       'ver_%d.%d.db' % ver ),
                         self.db_path )

    def _lookup( self, h, tags = [], type: Optional[hdbfs.ObjectType] = None ):

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

        files = self._lookup( h, type = hdbfs.ObjectType.FILE )

        self.assertEqual( len( files ), 8,
                'Unexpected number of files in DB' )

        for f in files:
            self.assertTrue( isinstance( f, hdbfs.File ),
                    'Unexpected file type found %s' % (
                        str( type( f ) ) ) )

        fnames = list( map( lambda x: x.get_name(), files ) )
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

        files = self._lookup( h, type = hdbfs.ObjectType.FILE )
        streams = []

        for f in files:
            streams.append( f.get_root_stream() )

        self.assertEqual( len( streams ), 8,
                'Unexpected number of streams in DB' )

        hashs = list( map( lambda x: x.get_hash(), streams ) )
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

    def subtest_ensure_files_have_timestamp( self, ver ):

        h = hdbfs.Database()

        files = self._lookup( h, type = hdbfs.ObjectType.FILE )

        now = datetime.datetime.now( datetime.timezone.utc )
        for f in files:
            self.assertTrue( now - f.get_creation_time_utc()
                           < datetime.timedelta( minutes = 10 ),
                    'Unexpected timestamp in file, %r' % (
                        f.get_creation_time_utc(), ) )

    def subtest_ensure_streams_have_timestamp( self, ver ):

        h = hdbfs.Database()

        files = self._lookup( h, type = hdbfs.ObjectType.FILE )

        now = datetime.datetime.now( datetime.timezone.utc )
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

        vo_list = grey.get_variants_of()
        self.assertEqual( len( vo_list ), 1,
                'Grey variant of list len mismatch' )
        self.assertTrue( white in grey.get_variants_of(),
                'Grey should be variant of white' )

        dup_list = grey.get_duplicates()
        self.assertEqual( len( dup_list ), 1,
                'Grey duplicate list len mismatch' )
        self.assertEqual( dup_list[0].get_name(), self.black,
                'Black is not the duplicate of grey' )
        self.assertEqual( dup_list[0].get_root_stream().get_hash(), self.black_hash,
                'Black is missing its stream' )

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

    def subtest_check_single_names( self, ver ):

        h = hdbfs.Database()

        red = self._single( h, [ 'red' ] )

        names = red.get_origin_names()
        self.assertEqual( red.get_name(), self.red,
                'Unexpected name' )
        self.assertTrue( self.red in names,
                'Name not found' )

    def subtest_check_multi_names( self, ver ):

        h = hdbfs.Database()

        grey = self._single( h, [ 'grey' ] )
        names = grey.get_origin_names()

        self.assertTrue( self.grey in names,
                'Primary name not found' )
        self.assertTrue( 'grey_sq2.png' in names,
                'Secondary name not found' )

    def subtest_check_album( self, ver ):

        h = hdbfs.Database()

        if( ver[0] < 2 ):
            cl_al = self._single( h, type = hdbfs.ObjectType.ALBUM_FREE )

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

        if( ver[0] >= 14 ):
            self.assertEqual( len( white_s ), 5,
                    'Unexpected number of streams in white obj' )
        elif( ver[0] >= 8 ):
            self.assertEqual( len( white_s ), 2,
                    'Unexpected number of streams in white obj' )
        else:
            self.assertEqual( len( white_s ), 1,
                    'Unexpected number of streams in white obj' )

        if( ver[0] >= 14 ):
                self.assertEqual( len( grey_s ), 4,
                        'Unexpected number of streams in grey obj' )
        else:
                self.assertEqual( len( grey_s ), 3,
                        'Unexpected number of streams in grey obj' )

    def subtest_check_stream_origin( self, ver ):

        h = hdbfs.Database()

        files = self._lookup( h, type = hdbfs.ObjectType.FILE )

        now = datetime.datetime.now( datetime.timezone.utc )
        for f in files:
            for s in f.get_streams():

                if( s.get_name() == '.' ):
                    if( ver[0] >= 10 ):
                        self.assertEqual( s.get_origin_method(),
                                          'hdbfs:register',
                                          'unexpected origin method for root' )
                    else:
                        self.assertEqual( s.get_origin_method(),
                                          'hdbfs:legacy_create',
                                          'unexpected origin method for root' )
                    self.assertIsNone( s.get_origin_stream(),
                                     'Unexpected origin stream for root' )
                    self.assertEqual( s, f.get_root_stream(),
                                      'Unexpected mapping for root' )
                    self.assertEqual( s.get_extension(), 'png',
                                      'Unexpected extension for root' )
                    self.assertEqual( s.get_mime(), 'image/png',
                                      'Unexpected mime for root' )
                elif( s.get_name().startswith( 'dup:' ) ):
                    if( ver[0] >= 10 ):
                        self.assertEqual( s.get_origin_method(),
                                          'hdbfs:register',
                                          'Unexpected origin method for dup' )
                    else:
                        self.assertEqual( s.get_origin_method(),
                                          'hdbfs:legacy_create',
                                          'Unexpected origin method for dup' )
                    self.assertIsNone( s.get_origin_stream(),
                                     'Unexpected origin stream for dup' )
                    self.assertEqual( s.get_extension(), 'png',
                                      'Unexpected extension for dup' )
                    self.assertEqual( s.get_mime(), 'image/png',
                                      'Unexpected mime for dup' )
                elif( s.get_name().startswith( 'tb:' ) ):
                    if( ver[0] >= 10 ):
                        self.assertTrue( s.get_origin_method().startswith(
                                            'imgdb:tb:' ),
                                          'Unexpected origin method for thumb' )
                    else:
                        self.assertTrue( s.get_origin_method().startswith(
                                            'imgdb:legacy_tb:' ),
                                          'Unexpected origin method for thumb' )
                    self.assertEqual( s.get_origin_stream(),
                                      f.get_root_stream(),
                                     'Unexpected origin stream for thumb' )
                    self.assertEqual( s.get_extension(), 'jpg',
                                      'Unexpected extension for thumb' )
                    self.assertEqual( s.get_mime(), 'image/jpeg',
                                      'Unexpected mime for jpg' )
                else:
                    self.fail( 'Unexpected stream name' )

    def subtest_check_orientation( self, ver ):

        h = hdbfs.Database()
        white = self._single( h, [ 'white' ] )

        if( ver[0] > 7 ):
            self.assertEqual( white.get_orientation(), 6, 'Unexpected orientation' )

    def subtest_check_generation( self, ver ):

        h = hdbfs.Database()
        white = self._single( h, [ 'white' ] )
        grey = self._single( h, [ 'grey' ] )

        if( ver[0] > 9 ):
            # White has a generation bump because it has been rotated
            self.assertEqual( white.get_generation(), 1, 'Unexpected gen for white' )
            self.assertEqual( grey.get_generation(), 0, 'Unexpected gen for grey' )

class BoundSubtest:

    def __init__( self, fn, ver ):

        self.fn = fn
        self.ver = ver

    def __call__( self, lself = None ):

        print( self )
        print( lself )

        lself._create_library_structure( self.ver )
        lself._init_hdbfs()
        self.fn( lself, self.ver )

def build_cases():

    VERSIONS_FILE = 'test/data/versions.txt'

    import functools
    import sys

    cls = LegacyCases

    if( len( sys.argv ) > 1 ):
        versions_str = [ sys.argv[1] ]
        sys.argv = sys.argv[0:1] + sys.argv[2:]
    elif( os.path.isfile( VERSIONS_FILE ) ):
        with open( VERSIONS_FILE, 'r' ) as f:
            versions_str = [
                        v
                        for v in f.read().strip().split( ' ' )
                        if v != ''
                ]
    else:
        print( f'{VERSIONS_FILE} is missing!' )
        sys.exit( 1 )

    # Convert to list of tuples
    versions = [
            ( int( v[0] ), int( v[1] ) )
            for v in map( lambda it: it.split( '.' ), versions_str )
        ]

    for ver in versions:

        items = dir( cls )
        for item in items:
            if( not item.startswith( 'subtest_' ) ):
                continue

            def decorator( fn, ver ):

                def new_fn( self ):

                    self._create_library_structure( ver )
                    self._init_hdbfs()
                    fn( self, ver )

                return new_fn

            # For each version and sub-test, create a test
            fn = getattr( cls, item )
            setattr( cls,
                     f'test_{ver[0]}_{ver[1]}_{item[8:]}',
                     decorator( fn, ver ) )

build_cases()

if( __name__ == '__main__' ):
    unittest.main()
