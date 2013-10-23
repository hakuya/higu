import unittest
import testutil
import shutil
import os
import higu

class HiguLibCases( testutil.TestCase ):

    def setUp( self ):

        self.init_env()

    def tearDown( self ):

        self.uninit_env()

    def test_basic_structure( self ):

        self.assertTrue( os.path.isdir( self.db_path ),
                'Library not created' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path, 'hfdb.dat' ) ),
                'Sqlite database not created' )

    def test_imgdat_structure( self ):

        red = self._load_data( self.red )

        h = higu.Database()
        obj = h.register_file( red, False )
        # Should not be moved before commit
        self.assertTrue( os.path.exists( red ),
                'Image moved before commit' )
        h.commit()

        self.assertFalse( os.path.exists( red ),
                'Old image was not removed' )
        self.assertTrue( os.path.isdir(
                    os.path.join( self.db_path, 'imgdat' ) ),
                'Image data directory not created' )

        red_path = obj.get_path()
        self.assertTrue( os.path.isfile( red_path ),
                'Image not moved into library' )

    def test_thumb( self ):

        blue = self._load_data( self.blue )

        h = higu.Database()
        obj = h.register_file( blue, False )
        h.commit()

        original = obj.get_path()
        big_thumb = obj.get_thumb( 10 )
        small_thumb = obj.get_thumb( 4 )

        self.assertEqual( original, big_thumb,
                'Bigger thumb created' )
        self.assertTrue( os.path.isfile( big_thumb ),
                'Invalid image returned for bigger thumb' )
        self.assertTrue( os.path.isfile( small_thumb ),
                'Invalid image returned for smaller thumb' )

    def test_delete( self ):

        yellow = self._load_data( self.yellow )

        h = higu.Database()
        obj = h.register_file( yellow, False )
        h.commit()

        path = obj.get_path()
        thumb = obj.get_thumb( 4 )
        self.assertTrue( os.path.isfile( path ),
                'Invalid image returned' )
        self.assertTrue( os.path.isfile( thumb ),
                'Invalid thumb returned' )

        h.delete_object( obj )
        self.assertTrue( os.path.isfile( path ),
                'Image removed before commit' )
        self.assertTrue( os.path.isfile( thumb ),
                'Thumb removed before commit' )
        h.commit()
        self.assertFalse( os.path.isfile( path ),
                'Image not removed' )
        self.assertFalse( os.path.isfile( thumb ),
                'Thumb not removed' )

    def test_double_add( self ):

        green = self._load_data( self.green )

        h = higu.Database()
        obj = h.register_file( green, False )
        h.commit()

        self.assertFalse( os.path.exists( green ),
                'Old image was not removed' )

        path = obj.get_path()
        self.assertTrue( os.path.isfile( path ),
                'Invalid image returned' )

        green = self._load_data( self.green )

        h = higu.Database()
        obj = h.register_file( green, False )
        h.commit()

        self.assertTrue( os.path.exists( green ),
                'Double image was removed' )

        path = obj.get_path()
        self.assertTrue( self._diff_files( green, path ),
                'Invalid image returned after double-add' )

    def test_recover_missing( self ):

        cyan = self._load_data( self.cyan )

        h = higu.Database()
        obj = h.register_file( cyan, False )
        h.commit()
        
        path = obj.get_path()
        self.assertTrue( os.path.isfile( path ),
                'Invalid image returned' )

        os.remove( path )

        self.assertFalse( os.path.isfile( path ),
                'Remove failed' )

        cyan = self._load_data( self.cyan )

        h = higu.Database()
        obj = h.register_file( cyan, False )
        h.commit()
        
        cyan_src = os.path.join( self.data_dir, self.cyan )
        self.assertTrue( self._diff_files( cyan_src, path ),
                'Image not recovered' )

    def test_recover_corrupted( self ):

        magenta = self._load_data( self.magenta )

        h = higu.Database()
        obj = h.register_file( magenta, False )
        h.commit()
        
        path = obj.get_path()
        self.assertTrue( os.path.isfile( path ),
                'Invalid image returned' )

        f = open( path, 'wb' )

        try:
            f.write( 'this is junk' )
        finally:
            f.close()

        magenta_src = os.path.join( self.data_dir, self.magenta )
        self.assertFalse( self._diff_files( magenta_src, path ),
                'Corruption failed' )

        magenta = self._load_data( self.magenta )

        h = higu.Database()
        obj = h.register_file( magenta, False )
        h.commit()
        
        self.assertTrue( self._diff_files( magenta_src, path ),
                'Image not recovered' )

    def test_name( self ):

        white = self._load_data( self.white )

        h = higu.Database()
        obj = h.register_file( white, True )
        h.commit()

        self.assertEqual( obj.get_name(), self.white,
                'Name not loaded' )
        self.assertEqual( len( obj.get_names() ), 1,
                'Name count does not match' )

    def test_different_names( self ):

        grey = self._load_data( self.grey )

        h = higu.Database()
        obj = h.register_file( grey, True )
        h.commit()

        grey2 = self._load_data( self.grey, 'altname.png' )

        h = higu.Database()
        obj = h.register_file( grey2, True )
        h.commit()

        names = obj.get_names()
        self.assertTrue( self.grey in names,
                'First name not loaded' )
        self.assertTrue( 'altname.png' in names,
                'Second name not loaded' )
        self.assertEqual( len( obj.get_names() ), 2,
                'Name count does not match' )

    def test_load_name( self ):

        black = self._load_data( self.black )

        h = higu.Database()
        obj = h.register_file( black, False )
        h.commit()

        self.assertNotEqual( obj.get_name(), self.black,
                'Name loaded when it shouldn\'t have been' )

        black = self._load_data( self.black )

        h = higu.Database()
        obj = h.register_file( black, True )
        h.commit()

        self.assertEqual( obj.get_name(), self.black,
                'name not loaded' )
        self.assertEqual( len( obj.get_names() ), 1,
                'Name count does not match' )

    def test_fetch_missing_tag( self ):

        h = higu.Database()

        try:
            h.get_tag( 'tag_that_doesnt_exist' )
            self.fail( 'Did not except on missing tag' )
        except KeyError:
            pass

    def test_create_tag( self ):

        h = higu.Database()
        tag = h.make_tag( 'a_tag' )
        h.commit()

        tag2 = h.get_tag( 'a_tag' )

        self.assertEqual( tag.get_id(), tag2.get_id(),
                'Tag ID mismatch' )

    def test_tag_file( self ):

        black = self._load_data( self.black )

        h = higu.Database()
        obj = h.register_file( black, False )
        tag = h.make_tag( 'black' )
        obj.assign( tag )
        h.commit()

        files = tag.get_files()
        self.assertEqual( len( files ), 1,
                'Unexpected number of files' )
        self.assertEqual( files[0].get_id(), obj.get_id(),
                'Incorrect file returned' )

    def test_file_has_tag( self ):

        black = self._load_data( self.black )

        h = higu.Database()
        obj = h.register_file( black, False )
        tag = h.make_tag( 'black' )
        obj.assign( tag )
        h.commit()

        tags = obj.get_tags()
        self.assertEqual( len( tags ), 1,
                'Unexpected number of tags' )
        self.assertEqual( tags[0].get_id(), tag.get_id(),
                'Incorrect tag returned' )

    def test_tag_multi_file( self ):

        red = self._load_data( self.red )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        h = higu.Database()

        ro = h.register_file( red, False )
        go = h.register_file( green, False )
        bo = h.register_file( blue, False )

        mt = h.make_tag( 'magenta' )
        yt = h.make_tag( 'yellow' )
        ct = h.make_tag( 'cyan' )

        ro.assign( mt )
        bo.assign( mt )

        ro.assign( yt )
        go.assign( yt )

        go.assign( ct )
        bo.assign( ct )

        h.commit()

        magenta = mt.get_files()
        yellow = yt.get_files()
        cyan = ct.get_files()

        self.assertEqual( len( magenta ), 2,
                'Unexpected number of files (magenta)' )
        self.assertEqual( len( yellow ), 2,
                'Unexpected number of files (yellow)' )
        self.assertEqual( len( cyan ), 2,
                'Unexpected number of files (cyan)' )

        self.assertTrue( ro in magenta, 
                'Red not in magenta' )
        self.assertTrue( bo in magenta, 
                'Blue not in magenta' )

        self.assertTrue( ro in yellow, 
                'Red not in yellow' )
        self.assertTrue( go in yellow, 
                'Green not in yellow' )

        self.assertTrue( go in cyan, 
                'Green not in cyan' )
        self.assertTrue( bo in cyan, 
                'Blue not in cyan' )

        red_in = ro.get_tags()
        green_in = go.get_tags()
        blue_in = bo.get_tags()

        self.assertEqual( len( red_in ), 2,
                'Unexpected number of tags (red)' )
        self.assertEqual( len( green_in ), 2,
                'Unexpected number of tags (green)' )
        self.assertEqual( len( blue_in ), 2,
                'Unexpected number of tags (blue)' )

        self.assertTrue( mt in red_in, 
                'Red does not have magenta' )
        self.assertTrue( yt in red_in, 
                'Red does not have yellow' )

        self.assertTrue( yt in green_in, 
                'Green does not have yellow' )
        self.assertTrue( ct in green_in, 
                'Green does not have cyan' )

        self.assertTrue( mt in blue_in, 
                'Blue does not have magenta' )
        self.assertTrue( ct in blue_in, 
                'Blue does not have cyan' )

if( __name__ == '__main__' ):
    unittest.main()
