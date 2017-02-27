import unittest
import testutil
import shutil
import os

import hdbfs.ark

PRI_THUMB = 1000
PRI_DATA = 2000

class ImgDbCases( testutil.TestCase ):

    def setUp( self ):

        self.init_env()

        data_config = hdbfs.ark.ImageDbDataConfig( self.db_path )
        self.idb = hdbfs.ark.StreamDatabase( data_config )

    def tearDown( self ):

        self.uninit_env()

    def test_imgdat_structure( self ):

        red = self._load_data( self.red )

        self.idb.load_data( red, 0x123, PRI_DATA )

        # Should not be moved before commit
        self.assertTrue( os.path.exists( red ),
                'Image moved before commit' )
        self.idb.commit()

        self.assertFalse( os.path.exists( red ),
                'Old image was not removed' )
        self.assertTrue( os.path.isdir(
                    os.path.join( self.db_path, 'imgdat/000/000' ) ),
                'Image data directory not created' )

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/000/0000000000000123.png' ) ),
                'Image file moved to incorrect location' )

        red_fd = self.idb.read( 0x123, PRI_DATA )
        self.assertTrue( self._diff_data( red_fd, self.red ),
                'Image not read properly from library' )

        uk_fd = self.idb.read( 0xabc, PRI_DATA )
        self.assertTrue( uk_fd is None,
                'Missing file somehow read from library' )

    def test_tbdat_structure( self ):

        red = self._load_data( self.red )

        self.idb.load_data( red, 0x123, PRI_THUMB )

        # Should not be moved before commit
        self.assertTrue( os.path.exists( red ),
                'Image moved before commit' )
        self.idb.commit()

        self.assertFalse( os.path.exists( red ),
                'Old image was not removed' )
        self.assertTrue( os.path.isdir(
                    os.path.join( self.db_path, 'tbdat/000/000' ) ),
                'Image data directory not created' )

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'tbdat/000/000/0000000000000123.png' ) ),
                'Image file moved to incorrect location' )

        red_fd = self.idb.read( 0x123, PRI_THUMB )
        self.assertTrue( self._diff_data( red_fd, self.red ),
                'Image not read properly from library' )

        uk_fd = self.idb.read( 0xabc, PRI_THUMB )
        self.assertTrue( uk_fd is None,
                'Missing file somehow read from library' )

    def test_multiple_folders( self ):

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )
        cyan = self._load_data( self.cyan )
        blue = self._load_data( self.blue )
        magenta = self._load_data( self.magenta )

        self.idb.load_data( red, 0x123, PRI_DATA )
        self.idb.load_data( yellow, 0xabc, PRI_THUMB )
        self.idb.load_data( green, 0xdef, PRI_DATA )
        self.idb.load_data( cyan, 0x123abc, PRI_DATA )
        self.idb.load_data( blue, 0xabc123abc, PRI_THUMB )
        self.idb.load_data( magenta, 0xabc123def, PRI_DATA )
        self.idb.commit()

        self.assertTrue( os.path.isdir(
                    os.path.join( self.db_path, 'imgdat/000/000' ) ),
                'Image data directory 000 not created' )
        self.assertTrue( os.path.isdir(
                    os.path.join( self.db_path, 'tbdat/000/000' ) ),
                'Thumb data directory 000 not created' )
        self.assertTrue( os.path.isdir(
                    os.path.join( self.db_path, 'imgdat/000/123' ) ),
                'Image data directory 123 not created' )
        self.assertTrue( os.path.isdir(
                    os.path.join( self.db_path, 'imgdat/abc/123' ) ),
                'Image data directory abc/123 not created' )
        self.assertTrue( os.path.isdir(
                    os.path.join( self.db_path, 'tbdat/abc/123' ) ),
                'Thumb data directory abc/123 not created' )

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/000/0000000000000123.png' ) ),
                'Image file 123 moved to incorrect location' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'tbdat/000/000/0000000000000abc.png' ) ),
                'Image file abc moved to incorrect location' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/000/0000000000000def.png' ) ),
                'Image file def moved to incorrect location' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/123/0000000000123abc.png' ) ),
                'Image file 123abc moved to incorrect location' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'tbdat/abc/123/0000000abc123abc.png' ) ),
                'Image file abc123abc moved to incorrect location' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/abc/123/0000000abc123def.png' ) ),
                'Image file abc123def moved to incorrect location' )

        red_fd = self.idb.read( 0x123, PRI_DATA )
        self.assertTrue( self._diff_data( red_fd, self.red ),
                'Image 123 not read properly from library' )
        yellow_fd = self.idb.read( 0xabc, PRI_THUMB )
        self.assertTrue( self._diff_data( yellow_fd, self.yellow ),
                'Image not read properly from library' )
        green_fd = self.idb.read( 0xdef, PRI_DATA )
        self.assertTrue( self._diff_data( green_fd, self.green ),
                'Image not read properly from library' )
        cyan_fd = self.idb.read( 0x123abc, PRI_DATA )
        self.assertTrue( self._diff_data( cyan_fd, self.cyan ),
                'Image not read properly from library' )
        blue_fd = self.idb.read( 0xabc123abc, PRI_THUMB )
        self.assertTrue( self._diff_data( blue_fd, self.blue ),
                'Image not read properly from library' )
        magenta_fd = self.idb.read( 0xabc123def, PRI_DATA )
        self.assertTrue( self._diff_data( magenta_fd, self.magenta ),
                'Image not read properly from library' )

    def test_commit_and_rollback( self ):

        # State should be clean on start-up
        self.assertEquals( self.idb.get_state(), 'clean',
                'Database not clean on start-up' )

        red = self._load_data( self.red )
        self.idb.load_data( red, 0x123, PRI_DATA )

        self.assertEquals( self.idb.get_state(), 'dirty',
                'Database not dirty after load' )

        # Should not be moved before commit
        self.assertTrue( os.path.exists( red ),
                'Image moved before commit' )
        
        self.idb.prepare_commit()

        self.assertFalse( os.path.exists( red ),
                'Image not moved after prepare' )
        
        self.assertEquals( self.idb.get_state(), 'prepared',
                'Database not prepared after prepare' )

        self.idb.unprepare_commit()

        self.assertTrue( os.path.exists( red ),
                'Image not returned after unprepare' )

        self.assertEquals( self.idb.get_state(), 'dirty',
                'Database not clean after unprepare' )

        self.idb.prepare_commit()

        self.assertFalse( os.path.exists( red ),
                'Image not moved after prepare/unprepare/prepare' )
        
        self.assertEquals( self.idb.get_state(), 'prepared',
                'Database not prepared after prepare/unprepare/prepare' )

    def test_hard_single_vol( self ):

        # State should be clean on start-up
        self.assertEquals( self.idb.get_state(), 'clean',
                'Database not clean on start-up' )

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )

        self.idb.load_data( red, 0x1, PRI_DATA )
        self.idb.commit()

        self.idb.load_data( yellow, 0x2, PRI_THUMB )
        self.idb.prepare_commit()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/000/0000000000000001.png' ) ),
                'File 0x1 missing' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'tbdat/000/000/0000000000000002.png' ) ),
                'File 0x2 missing' )

        self.idb.unprepare_commit()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/000/0000000000000001.png' ) ),
                'File 0x1 missing after rollback' )
        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    'tbdat/000/000/0000000000000002.png' ) ),
                'File 0x2 present when should have been removed' )

        self.idb.load_data( green, 0x3, PRI_DATA )
        self.idb.prepare_commit()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/000/0000000000000001.png' ) ),
                'File 0x1 missing after 3rd commit' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'tbdat/000/000/0000000000000002.png' ) ),
                'File 0x2 not re-instated after 3rd commit' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/000/0000000000000003.png' ) ),
                'File 0x3 added by 3rd commit' )

        self.idb.rollback()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/000/0000000000000001.png' ) ),
                'File 0x1 missing after 2nd rollback' )
        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    'tbdat/000/000/0000000000000002.png' ) ),
                'File 0x2 not removed by 2nd rollback' )
        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/000/0000000000000003.png' ) ),
                'File 0x3 not removed by 2nd rollback' )

        self.assertEqual( self.idb.get_state(), 'clean',
                'Reset state did not reset state to clean' )

        self.idb.load_data( green, 0x3, PRI_DATA )
        self.idb.commit()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/000/0000000000000001.png' ) ),
                'File 0x1 missing after 4th commit' )
        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    'tbdat/000/000/0000000000000002.png' ) ),
                'File 0x2 brought back after reset and commit' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/000/0000000000000003.png' ) ),
                'File 0x3 not re-added by 4th commit' )

    def test_hard_multi_vol( self ):

        # State should be clean on start-up
        self.assertEquals( self.idb.get_state(), 'clean',
                'Database not clean on start-up' )

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )

        self.idb.load_data( red, 0x1001, PRI_DATA )
        self.idb.commit()
        self.idb.load_data( yellow, 0x2001, PRI_DATA )
        self.idb.prepare_commit()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/001/0000000000001001.png' ) ),
                'File 0x1001 missing' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/002/0000000000002001.png' ) ),
                'File 0x2001 missing' )

        self.idb.unprepare_commit()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/001/0000000000001001.png' ) ),
                'File 0x1001 missing after rollback' )
        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/002/0000000000002001.png' ) ),
                'File 0x2001 present when should have been removed' )

        self.idb.load_data( green, 0x3001, PRI_DATA )
        self.idb.prepare_commit()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/001/0000000000001001.png' ) ),
                'File 0x1001 missing after 3rd commit' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/002/0000000000002001.png' ) ),
                'File 0x2001 not re-instated after 3rd commit' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/003/0000000000003001.png' ) ),
                'File 0x3001 added by 3rd commit' )

        self.idb.rollback()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/001/0000000000001001.png' ) ),
                'File 0x1001 missing after 2nd rollback' )
        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/002/0000000000002001.png' ) ),
                'File 0x2001 not removed by 2nd rollback' )
        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/003/0000000000003001.png' ) ),
                'File 0x3001 not removed by 2nd rollback' )

        self.assertEqual( self.idb.get_state(), 'clean',
                'Reset state did not reset state to clean' )

        self.idb.load_data( green, 0x3001, PRI_DATA )
        self.idb.commit()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/001/0000000000001001.png' ) ),
                'File 0x1001 missing after 4th commit' )
        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/002/0000000000002001.png' ) ),
                'File 0x2001 brought back after reset and commit' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/003/0000000000003001.png' ) ),
                'File 0x3001 not re-added by 4th commit' )

    def test_hard_multi_pri( self ):

        # State should be clean on start-up
        self.assertEquals( self.idb.get_state(), 'clean',
                'Database not clean on start-up' )

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )

        self.idb.load_data( red, 0x1001, PRI_DATA )
        self.idb.commit()
        self.idb.load_data( yellow, 0x1002, PRI_THUMB )
        self.idb.prepare_commit()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/001/0000000000001001.png' ) ),
                'File 0x1001 missing' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'tbdat/000/001/0000000000001002.png' ) ),
                'File 0x1002 missing' )

        self.idb.unprepare_commit()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/001/0000000000001001.png' ) ),
                'File 0x1001 missing after rollback' )
        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    'tbdat/000/001/0000000000001002.png' ) ),
                'File 0x1002 present when should have been removed' )

        self.idb.load_data( green, 0x3001, PRI_DATA )
        self.idb.prepare_commit()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/001/0000000000001001.png' ) ),
                'File 0x1001 missing after 3rd commit' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'tbdat/000/001/0000000000001002.png' ) ),
                'File 0x2001 not re-instated after 3rd commit' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/003/0000000000003001.png' ) ),
                'File 0x3001 added by 3rd commit' )

        self.idb.rollback()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/001/0000000000001001.png' ) ),
                'File 0x1001 missing after 2nd rollback' )
        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    'tbdat/000/001/0000000000001002.png' ) ),
                'File 0x2001 not removed by 2nd rollback' )
        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/003/0000000000003001.png' ) ),
                'File 0x3001 not removed by 2nd rollback' )

        self.assertEqual( self.idb.get_state(), 'clean',
                'Reset state did not reset state to clean' )

        self.idb.load_data( green, 0x3001, PRI_DATA )
        self.idb.commit()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/001/0000000000001001.png' ) ),
                'File 0x1001 missing after 4th commit' )
        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    'tbdat/000/001/0000000000001002.png' ) ),
                'File 0x2001 brought back after reset and commit' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/003/0000000000003001.png' ) ),
                'File 0x3001 not re-added by 4th commit' )

    def test_rollback_then_commit( self ):

        self.assertEquals( self.idb.get_state(), 'clean',
                'Database not clean on start-up' )

        red = self._load_data( self.red )
        self.idb.load_data( red, 0x123, PRI_DATA )

        self.assertEquals( self.idb.get_state(), 'dirty',
                'Database not dirty after load' )

        self.assertTrue( os.path.exists( red ),
                'Image moved before commit' )
        
        self.idb.rollback()

        self.assertTrue( os.path.exists( red ),
                'Image moved after no-commit-rollback' )
        
        self.assertEquals( self.idb.get_state(), 'clean',
                'Database not clean after rollback' )

        self.idb.commit()

        self.assertTrue( os.path.exists( red ),
                'Image moved after rollback before commit' )

        self.assertEquals( self.idb.get_state(), 'clean',
                'Database not clean after rollback then commit' )

    def test_commit_failure( self ):

        self.assertEquals( self.idb.get_state(), 'clean',
                'Database not clean on start-up' )

        red = self._load_data( self.red )
        self.idb.load_data( red, 0x123, PRI_DATA )

        os.remove( red )
        
        try:
            self.idb.commit()
            self.fail( 'Commit succeeded on missing file' )
        except:
            pass

        self.assertEquals( self.idb.get_state(), 'dirty',
                'Database not dirty after failed commit' )

    def test_commit_failure_rollback_single_volume( self ):

        self.assertEquals( self.idb.get_state(), 'clean',
                'Database not clean on start-up' )

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )

        self.idb.load_data( red, 0x1, PRI_DATA )
        self.idb.load_data( yellow, 0x2, PRI_DATA )
        self.idb.load_data( green, 0x3, PRI_DATA )

        os.remove( yellow )

        try:
            self.idb.commit()
            self.fail( 'Commit succeeded on missing file' )
        except:
            pass

        self.assertTrue( os.path.exists( red ),
                'File 0x1 not rolled back on failed commit' )
        self.assertTrue( os.path.exists( green ),
                'File 0x3 not rolled back on failed commit' )

    def test_commit_failure_rollback_multi_volume( self ):

        self.assertEquals( self.idb.get_state(), 'clean',
                'Database not clean on start-up' )

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )

        self.idb.load_data( red, 0x1001, PRI_DATA )
        self.idb.load_data( yellow, 0x2001, PRI_DATA )
        self.idb.load_data( green, 0x3001, PRI_DATA )

        os.remove( yellow )

        try:
            self.idb.commit()
            self.fail( 'Commit succeeded on missing file' )
        except:
            pass

        self.assertTrue( os.path.exists( red ),
                'File 0x1001 not rolled back on failed commit' )
        self.assertTrue( os.path.exists( green ),
                'File 0x3001 not rolled back on failed commit' )

    def test_delete( self ):

        # State should be clean on start-up
        self.assertEquals( self.idb.get_state(), 'clean',
                'Database not clean on start-up' )

        red = self._load_data( self.red )
        green = self._load_data( self.green )
        self.idb.load_data( red, 0x123, PRI_DATA )
        self.idb.load_data( green, 0xabc, PRI_THUMB )

        self.idb.commit()

        self.idb.delete( 0x123, PRI_DATA )
        self.idb.delete( 0xabc, PRI_THUMB )

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/000/0000000000000123.png' ) ),
                'Image file removed before commit' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'tbdat/000/000/0000000000000abc.png' ) ),
                'Thumb file removed before commit' )

        self.idb.prepare_commit()

        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/000/0000000000000123.png' ) ),
                'Image file delete failed' )
        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    'tbdat/000/000/0000000000000abc.png' ) ),
                'Image file delete failed' )

        self.idb.rollback()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'imgdat/000/000/0000000000000123.png' ) ),
                'Image file rollback from delete failed' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'tbdat/000/000/0000000000000abc.png' ) ),
                'Image file rollback from delete failed' )

if( __name__ == '__main__' ):
    unittest.main()
