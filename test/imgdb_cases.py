import unittest
import testutil
import shutil
import os
import ark

class ImgDbCases( testutil.TestCase ):

    def setUp( self ):

        self.init_env()

    def tearDown( self ):

        self.uninit_env()

    def test_imgdat_structure( self ):

        red = self._load_data( self.red )
        idb = ark.ImageDatabase( self.db_path )

        idb.load_data( red, 0x123 )

        # Should not be moved before commit
        self.assertTrue( os.path.exists( red ),
                'Image moved before commit' )
        idb.commit()

        self.assertFalse( os.path.exists( red ),
                'Old image was not removed' )
        self.assertTrue( os.path.isdir(
                    os.path.join( self.db_path, '000/000' ) ),
                'Image data directory not created' )

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/000/0000000000000123.png' ) ),
                'Image file moved to incorrect location' )

        red_fd = idb.read( 0x123 )
        self.assertTrue( self._diff_data( red_fd, self.red ),
                'Image not read properly from library' )

        uk_fd = idb.read( 0xabc )
        self.assertTrue( uk_fd is None,
                'Missing file somehow read from library' )

    def test_multiple_folders( self ):

        idb = ark.ImageDatabase( self.db_path )

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        idb.load_data( red, 0x123 )
        idb.load_data( yellow, 0xabc )
        idb.load_data( green, 0x123abc )
        idb.load_data( blue, 0xabc123abc )
        idb.commit()

        self.assertTrue( os.path.isdir(
                    os.path.join( self.db_path, '000/000' ) ),
                'Image data directory 000 not created' )
        self.assertTrue( os.path.isdir(
                    os.path.join( self.db_path, '000/123' ) ),
                'Image data directory 123 not created' )
        self.assertTrue( os.path.isdir(
                    os.path.join( self.db_path, 'abc/123' ) ),
                'Image data directory abc/123 not created' )

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/000/0000000000000123.png' ) ),
                'Image file 123 moved to incorrect location' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/000/0000000000000abc.png' ) ),
                'Image file abc moved to incorrect location' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/123/0000000000123abc.png' ) ),
                'Image file 123abc moved to incorrect location' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    'abc/123/0000000abc123abc.png' ) ),
                'Image file abc123abc moved to incorrect location' )

        red_fd = idb.read( 0x123 )
        self.assertTrue( self._diff_data( red_fd, self.red ),
                'Image 123 not read properly from library' )
        yellow_fd = idb.read( 0xabc )
        self.assertTrue( self._diff_data( yellow_fd, self.yellow ),
                'Image not read properly from library' )
        green_fd = idb.read( 0x123abc )
        self.assertTrue( self._diff_data( green_fd, self.green ),
                'Image not read properly from library' )
        blue_fd = idb.read( 0xabc123abc )
        self.assertTrue( self._diff_data( blue_fd, self.blue ),
                'Image not read properly from library' )

    def test_commit_and_rollback( self ):

        idb = ark.ImageDatabase( self.db_path )

        # State should be clean on start-up
        self.assertEquals( idb.get_state(), 'clean',
                'Database not clean on start-up' )

        red = self._load_data( self.red )
        idb.load_data( red, 0x123 )

        self.assertEquals( idb.get_state(), 'dirty',
                'Database not dirty after load' )

        # Should not be moved before commit
        self.assertTrue( os.path.exists( red ),
                'Image moved before commit' )
        
        idb.commit()

        self.assertFalse( os.path.exists( red ),
                'Image not moved after commit' )
        
        self.assertEquals( idb.get_state(), 'committed',
                'Database not committed after commit' )

        idb.rollback()

        self.assertTrue( os.path.exists( red ),
                'Image not returned after rollback' )

        self.assertEquals( idb.get_state(), 'dirty',
                'Database not clean after rollback from commit' )

        idb.commit()

        self.assertFalse( os.path.exists( red ),
                'Image not moved after commit/rollback/commit' )
        
        self.assertEquals( idb.get_state(), 'committed',
                'Database not committed after commit/rollback/commit' )

    def test_hard_single_vol( self ):

        idb = ark.ImageDatabase( self.db_path )

        # State should be clean on start-up
        self.assertEquals( idb.get_state(), 'clean',
                'Database not clean on start-up' )

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )

        idb.load_data( red, 0x1 )
        idb.commit()
        idb.load_data( yellow, 0x2 )
        idb.commit()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/000/0000000000000001.png' ) ),
                'File 0x1 missing' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/000/0000000000000002.png' ) ),
                'File 0x2 missing' )

        idb.rollback()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/000/0000000000000001.png' ) ),
                'File 0x1 missing after rollback' )
        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/000/0000000000000002.png' ) ),
                'File 0x2 present when should have been removed' )

        idb.load_data( green, 0x3 )
        idb.commit()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/000/0000000000000001.png' ) ),
                'File 0x1 missing after 3rd commit' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/000/0000000000000002.png' ) ),
                'File 0x2 not re-instated after 3rd commit' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/000/0000000000000003.png' ) ),
                'File 0x3 added by 3rd commit' )

        idb.rollback()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/000/0000000000000001.png' ) ),
                'File 0x1 missing after 2nd rollback' )
        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/000/0000000000000002.png' ) ),
                'File 0x2 not removed by 2nd rollback' )
        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/000/0000000000000003.png' ) ),
                'File 0x3 not removed by 2nd rollback' )

        idb.reset_state()

        self.assertEqual( idb.get_state(), 'clean',
                'Reset state did not reset state to clean' )

        idb.load_data( green, 0x3 )
        idb.commit()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/000/0000000000000001.png' ) ),
                'File 0x1 missing after 4th commit' )
        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/000/0000000000000002.png' ) ),
                'File 0x2 brought back after reset and commit' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/000/0000000000000003.png' ) ),
                'File 0x3 not re-added by 4th commit' )

    def test_hard_multi_vol( self ):

        idb = ark.ImageDatabase( self.db_path )

        # State should be clean on start-up
        self.assertEquals( idb.get_state(), 'clean',
                'Database not clean on start-up' )

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )

        idb.load_data( red, 0x1001 )
        idb.commit()
        idb.load_data( yellow, 0x2001 )
        idb.commit()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/001/0000000000001001.png' ) ),
                'File 0x1001 missing' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/002/0000000000002001.png' ) ),
                'File 0x2001 missing' )

        idb.rollback()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/001/0000000000001001.png' ) ),
                'File 0x1001 missing after rollback' )
        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/002/0000000000002001.png' ) ),
                'File 0x2001 present when should have been removed' )

        idb.load_data( green, 0x3001 )
        idb.commit()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/001/0000000000001001.png' ) ),
                'File 0x1001 missing after 3rd commit' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/002/0000000000002001.png' ) ),
                'File 0x2001 not re-instated after 3rd commit' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/003/0000000000003001.png' ) ),
                'File 0x3001 added by 3rd commit' )

        idb.rollback()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/001/0000000000001001.png' ) ),
                'File 0x1001 missing after 2nd rollback' )
        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/002/0000000000002001.png' ) ),
                'File 0x2001 not removed by 2nd rollback' )
        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/003/0000000000003001.png' ) ),
                'File 0x3001 not removed by 2nd rollback' )

        idb.reset_state()

        self.assertEqual( idb.get_state(), 'clean',
                'Reset state did not reset state to clean' )

        idb.load_data( green, 0x3001 )
        idb.commit()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/001/0000000000001001.png' ) ),
                'File 0x1001 missing after 4th commit' )
        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/002/0000000000002001.png' ) ),
                'File 0x2001 brought back after reset and commit' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/003/0000000000003001.png' ) ),
                'File 0x3001 not re-added by 4th commit' )

    def test_rollback_then_commit( self ):

        idb = ark.ImageDatabase( self.db_path )

        self.assertEquals( idb.get_state(), 'clean',
                'Database not clean on start-up' )

        red = self._load_data( self.red )
        idb.load_data( red, 0x123 )

        self.assertEquals( idb.get_state(), 'dirty',
                'Database not dirty after load' )

        self.assertTrue( os.path.exists( red ),
                'Image moved before commit' )
        
        idb.rollback()

        self.assertTrue( os.path.exists( red ),
                'Image moved after no-commit-rollback' )
        
        self.assertEquals( idb.get_state(), 'clean',
                'Database not clean after rollback' )

        idb.commit()

        self.assertTrue( os.path.exists( red ),
                'Image moved after rollback before commit' )

        self.assertEquals( idb.get_state(), 'clean',
                'Database not clean after rollback then commit' )

    def test_commit_failure( self ):

        idb = ark.ImageDatabase( self.db_path )

        self.assertEquals( idb.get_state(), 'clean',
                'Database not clean on start-up' )

        red = self._load_data( self.red )
        idb.load_data( red, 0x123 )

        os.remove( red )
        
        try:
            idb.commit()
            self.fail( 'Commit succeeded on missing file' )
        except:
            pass

        self.assertEquals( idb.get_state(), 'dirty',
                'Database not dirty after failed commit' )

    def test_commit_failure_rollback_single_volume( self ):

        idb = ark.ImageDatabase( self.db_path )

        self.assertEquals( idb.get_state(), 'clean',
                'Database not clean on start-up' )

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )

        idb.load_data( red, 0x1 )
        idb.load_data( yellow, 0x2 )
        idb.load_data( green, 0x3 )

        os.remove( yellow )

        try:
            idb.commit()
            self.fail( 'Commit succeeded on missing file' )
        except:
            pass

        self.assertTrue( os.path.exists( red ),
                'File 0x1 not rolled back on failed commit' )
        self.assertTrue( os.path.exists( green ),
                'File 0x3 not rolled back on failed commit' )

    def test_commit_failure_rollback_multi_volume( self ):

        idb = ark.ImageDatabase( self.db_path )

        self.assertEquals( idb.get_state(), 'clean',
                'Database not clean on start-up' )

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )

        idb.load_data( red, 0x1001 )
        idb.load_data( yellow, 0x2001 )
        idb.load_data( green, 0x3001 )

        os.remove( yellow )

        try:
            idb.commit()
            self.fail( 'Commit succeeded on missing file' )
        except:
            pass

        self.assertTrue( os.path.exists( red ),
                'File 0x1001 not rolled back on failed commit' )
        self.assertTrue( os.path.exists( green ),
                'File 0x3001 not rolled back on failed commit' )

    def test_delete( self ):

        idb = ark.ImageDatabase( self.db_path )

        # State should be clean on start-up
        self.assertEquals( idb.get_state(), 'clean',
                'Database not clean on start-up' )

        red = self._load_data( self.red )
        idb.load_data( red, 0x123 )

        idb.commit()

        idb.delete( 0x123 )

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/000/0000000000000123.png' ) ),
                'Image file removed before commit' )

        idb.commit()

        self.assertFalse( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/000/0000000000000123.png' ) ),
                'Image file delete failed' )

        idb.rollback()

        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path,
                    '000/000/0000000000000123.png' ) ),
                'Image file rollback from delete failed' )

if( __name__ == '__main__' ):
    unittest.main()
