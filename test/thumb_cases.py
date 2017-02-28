import unittest
import testutil
import shutil
import os
import time
import datetime

import hdbfs
import hdbfs.ark
import hdbfs.model

hdbfs.ark.MIN_THUMB_EXP = 4

class ThumbCases( testutil.TestCase ):

    def setUp( self ):

        self.init_env()

    def tearDown( self ):

        self.uninit_env()

    def test_create_thumb( self ):

        blue = self._load_data( self.blue )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( blue, False )

        root_stream = obj.get_root_stream()
        thumb_stream = obj.get_thumb_stream( 4 )

        self.assertFalse( thumb_stream.get_stream_id()
                       == root_stream.get_stream_id(),
                          'Root returned for small thumb' )
        self.assertFalse( self._diff( root_stream.read(),
                                      thumb_stream.read() ),
                'Smaller thumb stream identical' )
        self.assertTrue( thumb_stream.get_priority()
                      == hdbfs.model.SP_EXPENDABLE,
                         'Thumb priority not set correctly' )

    def test_return_orig( self ):

        blue = self._load_data( self.blue )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( blue, False )

        root_stream = obj.get_root_stream()
        thumb_stream = obj.get_thumb_stream( 10 )

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

        obj.rotate( 1 )

        root_stream = obj.get_root_stream()
        thumb_stream = obj.get_thumb_stream( 10 )

        self.assertFalse( thumb_stream.get_stream_id()
                      == root_stream.get_stream_id(),
                          'Root returned on rotated image' )

    def test_thumb_points_to_root( self ):

        blue = self._load_data( self.blue )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( blue, False )

        root_stream = obj.get_root_stream()
        thumb_stream = obj.get_thumb_stream( 4 )
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

        thumb_stream = obj.get_thumb_stream( 4 )
        small_stream = obj.get_thumb_stream( 3 )

        self.assertTrue( thumb_stream.get_stream_id()
                      == small_stream.get_stream_id(),
                         'Very small does not match small' )
        self.assertTrue( small_stream.get_priority()
                      == hdbfs.model.SP_EXPENDABLE,
                         'Very small priority not set correctly' )

    def test_thumbs_not_moved( self ):

        red = self._load_data( self.red )
        blue = self._load_data( self.blue )

        h = hdbfs.Database()
        h.enable_write_access()

        o1 = h.register_file( blue, False )
        o2 = h.register_file( red, False )

        t2_4_hash = o2.get_thumb_stream( 4 ).get_hash()
        t2_5_hash = o2.get_thumb_stream( 5 ).get_hash()

        h.merge_objects( o1, o2 )

        t1_4_hash = o1.get_thumb_stream( 4 ).get_hash()
        t1_5_hash = o1.get_thumb_stream( 5 ).get_hash()

        self.assertFalse( t1_4_hash == t2_4_hash,
                         'New thumb matches moved from o2' )
        self.assertFalse( t1_5_hash == t2_5_hash,
                         'New thumb matches moved from o2' )

    def test_thumbs_not_moved_with_existing( self ):

        red = self._load_data( self.red )
        blue = self._load_data( self.blue )

        h = hdbfs.Database()
        h.enable_write_access()

        o1 = h.register_file( blue, False )
        o2 = h.register_file( red, False )

        t1_4_hash = o1.get_thumb_stream( 4 ).get_hash()
        t1_5_hash = o1.get_thumb_stream( 5 ).get_hash()
        t2_4_hash = o2.get_thumb_stream( 4 ).get_hash()
        t2_5_hash = o2.get_thumb_stream( 5 ).get_hash()

        h.merge_objects( o1, o2 )

        tx_4_hash = o1.get_thumb_stream( 4 ).get_hash()
        tx_5_hash = o1.get_thumb_stream( 5 ).get_hash()

        self.assertTrue( tx_4_hash == t1_4_hash,
                        'New thumb not matching from o1' )
        self.assertTrue( tx_5_hash == t1_5_hash,
                        'New thumb not matching from o1' )
        self.assertFalse( tx_4_hash == t2_4_hash,
                         'New thumb matches moved from o2' )
        self.assertFalse( tx_5_hash == t2_5_hash,
                         'New thumb matches moved from o2' )

if( __name__ == '__main__' ):
    unittest.main()
