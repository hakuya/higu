import unittest
import testutil
import shutil
import os
import time
import datetime

import hdbfs
import hdbfs.ark
import hdbfs.model

from hdbfs.imgdb.objects import ThumbRequestPrio

class ThumbCases( testutil.TestCase ):

    @classmethod
    def setUpClass( cls ):

        cls.init_cache()

    @classmethod
    def tearDownClass( cls ):

        cls.uninit_cache()

    def setUp( self ):

        hdbfs.imgdb.cache.MIN_THUMB_EXP = 4
        self.init_env()

    def tearDown( self ):

        self.uninit_env()

    def test_create_thumb( self ):

        blue = self._load_data( self.blue )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( blue, False )

        root_stream = obj.get_root_stream()
        thumb_stream = obj.get_thumb_stream( 4, ThumbRequestPrio.IMMEDIATE )

        self.assertFalse( thumb_stream.get_stream_id()
                       == root_stream.get_stream_id(),
                          'Root returned for small thumb' )
        with root_stream.open() as fd_root:
            with thumb_stream.open() as fd_thumb:
                self.assertFalse( self._diff( fd_root, fd_thumb ),
                        'Smaller thumb stream identical' )
        self.assertTrue( thumb_stream.get_priority()
                      == hdbfs.model.StreamPriority.EXPENDABLE.value,
                         'Thumb priority not set correctly' )

    def test_return_orig( self ):

        blue = self._load_data( self.blue )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( blue, False )

        root_stream = obj.get_root_stream()
        thumb_stream = obj.get_thumb_stream( 10, ThumbRequestPrio.IMMEDIATE )

        self.assertTrue( thumb_stream.get_stream_id()
                      == root_stream.get_stream_id(),
                          'Root not returned large small thumb' )
        self.assertTrue( thumb_stream.get_priority()
                      == root_stream.get_priority(),
                          'Oddity in return root for large priority' )

    def test_rot_does_not_return_orig( self ):

        blue = self._load_data( self.blue )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( blue, False )

        obj.rotate_cw()

        root_stream = obj.get_root_stream()
        thumb_stream = obj.get_thumb_stream( 10, ThumbRequestPrio.IMMEDIATE )

        self.assertFalse( thumb_stream.get_stream_id()
                      == root_stream.get_stream_id(),
                          'Root returned on rotated image' )

    def test_thumb_points_to_root( self ):

        blue = self._load_data( self.blue )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( blue, False )

        root_stream = obj.get_root_stream()
        thumb_stream = obj.get_thumb_stream( 4, ThumbRequestPrio.IMMEDIATE )
        origin_stream = thumb_stream.get_origin_stream()

        self.assertTrue( origin_stream is not None,
                         'Thumb has not origin' )
        self.assertTrue( origin_stream.get_stream_id()
                      == root_stream.get_stream_id(),
                         'Origin stream is not root stream' )

    def test_create_very_small( self ):

        blue = self._load_data( self.blue )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( blue, False )

        thumb_stream = obj.get_thumb_stream( 4, ThumbRequestPrio.IMMEDIATE )
        small_stream = obj.get_thumb_stream( 3, ThumbRequestPrio.IMMEDIATE )

        self.assertTrue( thumb_stream.get_stream_id()
                      == small_stream.get_stream_id(),
                         'Very small does not match small' )
        self.assertTrue( small_stream.get_priority()
                      == hdbfs.model.StreamPriority.EXPENDABLE.value,
                         'Very small priority not set correctly' )

if( __name__ == '__main__' ):
    unittest.main()
