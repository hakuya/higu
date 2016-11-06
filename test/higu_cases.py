import unittest
import testutil
import shutil
import os
import higu
import time
import datetime

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
        h.enable_write_access()

        obj = h.register_file( red, False )

        self.assertFalse( os.path.exists( red ),
                'Old image was not removed' )
        self.assertTrue( os.path.isdir(
                    os.path.join( self.db_path, 'imgdat' ) ),
                'Image data directory not created' )

        red_fd = obj.read()
        self.assertTrue( self._diff_data( red_fd, self.red ),
                'Image not read from library' )

    def test_thumb( self ):

        pass
# TODO
#        
#        blue = self._load_data( self.blue )
#
#        h = higu.Database()
#        h.enable_write_access()
#
#        obj = h.register_file( blue, False )
#
#        orig_fd = obj.read()
#        big_fd = obj.read_thumb( 10 )
#        small_fd = obj.read_thumb( 4 )
#
#        self.assertFalse( big_fd is None,
#                'Invalid image returned for bigger thumb' )
#        self.assertFalse( small_fd is None,
#                'Invalid image returned for smaller thumb' )
#
#        self.assertTrue( self._diff( orig_fd, big_fd ),
#                'Bigger thumb created' )
#        orig_fd = obj.read()
#        self.assertFalse( self._diff( orig_fd, small_fd ),
#                'Smaller thumb not created' )

    def test_delete( self ):

        yellow = self._load_data( self.yellow )

        h = higu.Database()
        h.enable_write_access()

        obj = h.register_file( yellow, False )

        img_fd = obj.read()
        tb_fd = obj.read_thumb( 4 )
        self.assertFalse( img_fd is None,
                'Invalid image returned' )
        self.assertFalse( tb_fd is None,
                'Invalid thumb returned' )

        img_fd.close()
        tb_fd.close()

        h.delete_object( obj )

        img_fd = obj.read()
        tb_fd = obj.read_thumb( 4 )
        self.assertTrue( img_fd is None,
                'Image returned after delete' )
        self.assertTrue( tb_fd is None,
                'Thumb returned after delete' )

    def test_timestamp( self ):

        blue = self._load_data( self.blue )

        h = higu.Database()
        h.enable_write_access()

        obj_id = h.register_file( blue, False ).get_id()

        time.sleep( 5 )
        obj = h.get_object_by_id( obj_id )

        now = datetime.datetime.utcnow()
        d_5sec = datetime.timedelta( seconds = 5 )
        d_10sec = datetime.timedelta( seconds = 10 )

        self.assertTrue( now - obj.get_creation_time_utc() < d_10sec,
                'Unexpected timestamp > 10secs away' )
        self.assertTrue( now - obj.get_creation_time_utc() > d_5sec,
                'Unexpected timestamp < 5secs away' )

    def test_double_add( self ):

        green = self._load_data( self.green )

        h = higu.Database()
        h.enable_write_access()

        obj = h.register_file( green, False )

        self.assertFalse( os.path.exists( green ),
                'Old image was not removed' )

        img_fd = obj.read()
        self.assertFalse( img_fd is None,
                'Failed opening image' )
        img_fd.close()

        green = self._load_data( self.green )

        h = higu.Database()
        h.enable_write_access()

        obj = h.register_file( green, False )

        self.assertTrue( os.path.exists( green ),
                'Double image was removed' )

        img_fd = obj.read()
        self.assertFalse( img_fd is None,
                'Invalid image returned after double-add' )
        img_fd.close()

    def test_recover_missing( self ):

        cyan = self._load_data( self.cyan )

        h = higu.Database()
        h.enable_write_access()

        obj = h.register_file( cyan, False )
        
        img_fd = obj.read()
        self.assertFalse( img_fd is None,
                'Failed opening image' )
        img_fd.close()

        h.imgdb.delete( obj.get_id() )
        h.imgdb.commit()

        img_fd = obj.read()
        self.assertFalse( img_fd is not None,
                'Remove failed' )

        cyan = self._load_data( self.cyan )

        h = higu.Database()
        h.enable_write_access()

        obj = h.register_file( cyan, False )
        
        img_fd = obj.read()
        self.assertTrue( self._diff_data( img_fd, self.cyan ),
                'Image not recovered' )

    def test_recover_corrupted( self ):

        magenta = self._load_data( self.magenta )

        h = higu.Database()
        h.enable_write_access()

        obj = h.register_file( magenta, False )
        
        img_fd = obj.read()
        self.assertFalse( img_fd is None,
                'Failed opening image' )
        img_fd.close()

        img_fd = h.imgdb._debug_write( obj.get_id() )

        try:
            img_fd.write( 'this is junk' )
        finally:
            img_fd.close()

        self.assertFalse( self._diff_data( obj.read(), self.magenta ),
                'Corruption failed' )

        magenta = self._load_data( self.magenta )

        h = higu.Database()
        h.enable_write_access()

        obj = h.register_file( magenta, False )
        
        self.assertTrue( self._diff_data( obj.read(), self.magenta ),
                'Image not recovered' )

    def test_name( self ):

        white = self._load_data( self.white )

        h = higu.Database()
        h.enable_write_access()

        obj = h.register_file( white, True )

        self.assertEqual( obj.get_name(), self.white,
                'Name not loaded' )
        self.assertEqual( len( obj.get_names() ), 1,
                'Name count does not match' )

    def test_duplicate_name( self ):

        grey = self._load_data( self.grey )

        h = higu.Database()
        h.enable_write_access()

        obj = h.register_file( grey, True )

        grey2 = self._load_data( self.grey )

        h = higu.Database()
        h.enable_write_access()

        obj = h.register_file( grey2, True )

        names = obj.get_names()
        self.assertTrue( self.grey in names,
                'Name not loaded' )
        self.assertEqual( len( names ), 1,
                'Name count does not match' )

    def test_different_names( self ):

        grey = self._load_data( self.grey )

        h = higu.Database()
        h.enable_write_access()

        obj = h.register_file( grey, True )

        grey2 = self._load_data( self.grey, 'altname.png' )

        h = higu.Database()
        h.enable_write_access()

        obj = h.register_file( grey2, True )

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
        h.enable_write_access()

        obj = h.register_file( black, False )

        self.assertNotEqual( obj.get_name(), self.black,
                'Name loaded when it shouldn\'t have been' )

        black = self._load_data( self.black )

        h = higu.Database()
        h.enable_write_access()

        obj = h.register_file( black, True )

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
        h.enable_write_access()

        tag = h.make_tag( 'a_tag' )
        tag2 = h.get_tag( 'a_tag' )

        self.assertEqual( tag.get_id(), tag2.get_id(),
                'Tag ID mismatch' )

    def test_tag_file( self ):

        black = self._load_data( self.black )

        h = higu.Database()
        h.enable_write_access()

        obj = h.register_file( black, False )
        tag = h.make_tag( 'black' )
        obj.assign( tag )

        files = tag.get_files()
        self.assertEqual( len( files ), 1,
                'Unexpected number of files' )
        self.assertEqual( files[0].get_id(), obj.get_id(),
                'Incorrect file returned' )

    def test_file_has_tag( self ):

        black = self._load_data( self.black )

        h = higu.Database()
        h.enable_write_access()

        obj = h.register_file( black, False )
        tag = h.make_tag( 'black' )
        obj.assign( tag )

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
        h.enable_write_access()

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

    def test_create_album( self ):

        h = higu.Database()
        h.enable_write_access()

        obj_id = h.create_album().get_id()

        album = h.get_object_by_id( obj_id )
        self.assertTrue( album is not None,
                'Unable to get album after creation' )
        self.assertTrue( isinstance( album, higu.Group ),
                'Created album is not a group' )

    def test_create_album_with_text( self ):

        h = higu.Database()
        h.enable_write_access()

        obj_id = h.create_album( text = 'This is some test text' ).get_id()

        album = h.get_object_by_id( obj_id )
        self.assertEqual( album.get_text(), 'This is some test text',
                'Album text not properly returned' )

    def test_album_set_text( self ):

        h = higu.Database()
        h.enable_write_access()

        album = h.create_album()
        album.set_text( 'This is some test text' )
        obj_id = album.get_id()

        h = higu.Database()
        album = h.get_object_by_id( obj_id )

        self.assertEqual( album.get_text(), 'This is some test text',
                'Album text not properly returned' )

    def test_add_files_to_album( self ):

        red = self._load_data( self.red )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        h = higu.Database()
        h.enable_write_access()

        album = h.create_album()

        ro = h.register_file( red, False )
        go = h.register_file( green, False )
        bo = h.register_file( blue, False )

        ro.assign( album )
        go.assign( album )
        bo.assign( album )

        files = album.get_files()

        self.assertTrue( ro in files, 'Red not in album' )
        self.assertTrue( go in files, 'Green not in album' )
        self.assertTrue( bo in files, 'Blue not in album' )

    def test_order_then_reorder( self ):

        red = self._load_data( self.red )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        h = higu.Database()
        h.enable_write_access()

        album = h.create_album()

        ro = h.register_file( red, False )
        go = h.register_file( green, False )
        bo = h.register_file( blue, False )

        ro.assign( album, 2 )
        go.assign( album, 0 )
        bo.assign( album, 1 )

        files = album.get_files()

        self.assertEqual( files[0], go, 'Green not in first position after add with order' )
        self.assertEqual( files[1], bo, 'Blue not in second position after add with order' )
        self.assertEqual( files[2], ro, 'Red not in third position after add with order' )

        ro.reorder( album, 2 )
        go.reorder( album, 1 )
        bo.reorder( album, 0 )

        files = album.get_files()

        self.assertEqual( files[0], bo, 'Blue not in first position after reorder' )
        self.assertEqual( files[1], go, 'Green not in second position after reorder' )
        self.assertEqual( files[2], ro, 'Red not in third position after reorder' )

    def test_set_order_in_album( self ):

        red = self._load_data( self.red )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        h = higu.Database()
        h.enable_write_access()

        album = h.create_album()

        ro = h.register_file( red, False )
        go = h.register_file( green, False )
        bo = h.register_file( blue, False )

        ro.assign( album, 2 )
        go.assign( album, 0 )
        bo.assign( album, 1 )

        files = album.get_files()

        self.assertEqual( files[0], go, 'Green not in first position after add with order' )
        self.assertEqual( files[1], bo, 'Blue not in second position after add with order' )
        self.assertEqual( files[2], ro, 'Red not in third position after add with order' )

        album.set_order( [ bo, go, ro, ] )
        files = album.get_files()

        self.assertEqual( files[0], bo, 'Blue not in first position after reorder' )
        self.assertEqual( files[1], go, 'Green not in second position after reorder' )
        self.assertEqual( files[2], ro, 'Red not in third position after reorder' )

    def test_set_duplicate( self ):

        white = self._load_data( self.white )
        black = self._load_data( self.black )

        h = higu.Database()
        h.enable_write_access()

        wo = h.register_file( white, False )
        ko = h.register_file( black, False )

        ko.set_duplicate_of( wo )

        self.assertFalse( wo.is_duplicate(), 'White is a duplicate' )
        self.assertTrue( ko.is_duplicate(), 'Black is not a duplicate' )
        self.assertTrue( ko in wo.get_duplicates(), 'Black not in duplicate list of white' )

    def test_set_duplicate_of_variant( self ):

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        h = higu.Database()
        h.enable_write_access()

        ro = h.register_file( red, False )
        yo = h.register_file( yellow, False )
        go = h.register_file( green, False )
        bo = h.register_file( blue, False )

        go.set_variant_of( ro )
        yo.set_duplicate_of( ro )
        bo.set_duplicate_of( go )

        self.assertTrue( yo.get_similar_to() == ro, 'Yellow not child of red' )
        self.assertTrue( bo.get_similar_to() == go, 'Blue not child of green' )
        self.assertTrue( go.get_similar_to() == ro, 'Green not child of red' )

        self.assertFalse( ro.is_duplicate(), 'Red is a duplicate' )
        self.assertTrue( yo.is_duplicate(), 'Yellow is not a duplicate' )
        self.assertFalse( go.is_duplicate(), 'Green is a duplicate' )
        self.assertTrue( bo.is_duplicate(), 'Blue is not a duplicate' )

        self.assertEqual( len( ro.get_duplicates() ), 1, 'Red duplicate list mismatch' )
        self.assertEqual( len( yo.get_duplicates() ), 0, 'Yellow duplicate list mismatch' )
        self.assertEqual( len( go.get_duplicates() ), 1, 'Green duplicate list mismatch' )
        self.assertEqual( len( bo.get_duplicates() ), 0, 'Blue duplicate list mismatch' )

        self.assertFalse( ro.is_variant(), 'Red is a variant' )
        self.assertTrue( go.is_variant(), 'Green is not a variant' )

        self.assertEqual( len( ro.get_variants() ), 1, 'Red variant list mismatch' )
        self.assertEqual( len( go.get_variants() ), 0, 'Green variant list mismatch' )

    def test_duplicate_duplicate_circle( self ):

        white = self._load_data( self.white )
        black = self._load_data( self.black )

        h = higu.Database()
        h.enable_write_access()

        wo = h.register_file( white, False )
        ko = h.register_file( black, False )

        ko.set_duplicate_of( wo )
        wo.set_duplicate_of( ko )

        self.assertTrue( wo.is_duplicate(), 'White is not a duplicate' )
        self.assertFalse( ko.is_duplicate(), 'Black is a duplicate' )
        self.assertTrue( wo in ko.get_duplicates(), 'White not in duplicate list of black' )
        self.assertFalse( ko in wo.get_duplicates(), 'Black in duplicate list of black' )

    def test_duplicate_variant_circle( self ):

        white = self._load_data( self.white )
        black = self._load_data( self.black )

        h = higu.Database()
        h.enable_write_access()

        wo = h.register_file( white, False )
        ko = h.register_file( black, False )

        ko.set_duplicate_of( wo )
        wo.set_variant_of( ko )

        self.assertTrue( wo.is_variant(), 'White is not a variant' )
        self.assertFalse( ko.is_duplicate(), 'Black is a duplicate' )
        self.assertTrue( wo in ko.get_variants(), 'White not in variant list of black' )
        self.assertFalse( ko in wo.get_duplicates(), 'Black in duplicate list of black' )

    def test_variant_duplicate_circle( self ):

        white = self._load_data( self.white )
        black = self._load_data( self.black )

        h = higu.Database()
        h.enable_write_access()

        wo = h.register_file( white, False )
        ko = h.register_file( black, False )

        ko.set_variant_of( wo )
        wo.set_duplicate_of( ko )

        self.assertTrue( wo.is_duplicate(), 'White is not a duplicate' )
        self.assertFalse( ko.is_variant(), 'Black is a variant' )
        self.assertTrue( wo in ko.get_duplicates(), 'White not in duplicate list of black' )
        self.assertFalse( ko in wo.get_variants(), 'Black in variant list of black' )

    def test_variant_variant_circle( self ):

        white = self._load_data( self.white )
        black = self._load_data( self.black )

        h = higu.Database()
        h.enable_write_access()

        wo = h.register_file( white, False )
        ko = h.register_file( black, False )

        ko.set_variant_of( wo )
        wo.set_variant_of( ko )

        self.assertTrue( wo.is_variant(), 'White is not a variant' )
        self.assertFalse( ko.is_variant(), 'Black is a variant' )
        self.assertTrue( wo in ko.get_variants(), 'White not in variant list of black' )
        self.assertFalse( ko in wo.get_variants(), 'Black in variant list of black' )

    def test_duplicates_moved( self ):

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        h = higu.Database()
        h.enable_write_access()

        ro = h.register_file( red, False )
        yo = h.register_file( yellow, False )
        go = h.register_file( green, False )
        bo = h.register_file( blue, False )

        yo.set_duplicate_of( ro )
        bo.set_duplicate_of( go )
        go.set_duplicate_of( ro )

        self.assertFalse( ro.is_duplicate(), 'Red is a duplicate' )
        self.assertTrue( yo.is_duplicate(), 'Yellow is not a duplicate' )
        self.assertTrue( go.is_duplicate(), 'Green is not a duplicate' )
        self.assertTrue( bo.is_duplicate(), 'Blue is not a duplicate' )

        self.assertEqual( len( ro.get_duplicates() ), 3, 'Red duplicate list mismatch' )
        self.assertEqual( len( yo.get_duplicates() ), 0, 'Yellow duplicate list mismatch' )
        self.assertEqual( len( go.get_duplicates() ), 0, 'Green duplicate list mismatch' )
        self.assertEqual( len( bo.get_duplicates() ), 0, 'Blue duplicate list mismatch' )

        dups = ro.get_duplicates()
        self.assertTrue( yo in dups, 'Yellow not in dup list' )
        self.assertTrue( go in dups, 'Green not in dup list' )
        self.assertTrue( bo in dups, 'Blue not in dup list' )

    def test_variants_moved( self ):

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        h = higu.Database()
        h.enable_write_access()

        ro = h.register_file( red, False )
        yo = h.register_file( yellow, False )
        go = h.register_file( green, False )
        bo = h.register_file( blue, False )

        yo.set_variant_of( ro )
        bo.set_variant_of( go )
        go.set_duplicate_of( ro )

        self.assertFalse( ro.is_duplicate(), 'Red is a duplicate' )
        self.assertFalse( ro.is_variant(), 'Red is a variant' )
        self.assertTrue( yo.is_variant(), 'Yellow is not a variant' )
        self.assertTrue( go.is_duplicate(), 'Green is not a duplicate' )
        self.assertTrue( bo.is_variant(), 'Blue is not a variant' )

        self.assertEqual( len( ro.get_duplicates() ), 1, 'Red duplicate list mismatch' )
        self.assertEqual( len( ro.get_variants() ), 2, 'Red variant list mismatch' )
        self.assertEqual( len( go.get_variants() ), 0, 'Green variant list mismatch' )

        dups = ro.get_duplicates()
        variants = ro.get_variants()
        self.assertTrue( yo in variants, 'Yellow not in variant list' )
        self.assertTrue( go in dups, 'Green not in dup list' )
        self.assertTrue( bo in variants, 'Blue not in variant list' )

    def test_albums_moved( self ):

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        h = higu.Database()
        h.enable_write_access()

        album = h.create_album()

        ro = h.register_file( red, False )
        yo = h.register_file( yellow, False )
        go = h.register_file( green, False )
        bo = h.register_file( blue, False )

        yo.assign( album, 2 )
        bo.assign( album, 3 )
        ro.assign( album, 1 )

        yo.set_duplicate_of( go )

        files = album.get_files()
        self.assertEqual( len( files ), 3, 'Album size mismatch' )
        self.assertEqual( files[0], ro, 'Red not first in album' )
        self.assertEqual( files[1], go, 'Green not second in album' )
        self.assertEqual( files[2], bo, 'Blue not third in album' )

    def test_tags_moved( self ):

        red = self._load_data( self.red )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        h = higu.Database()
        h.enable_write_access()

        tag1 = h.make_tag( 'a_tag' )
        tag2 = h.make_tag( 'b_tag' )
        tag3 = h.make_tag( 'c_tag' )

        ro = h.register_file( red, False )
        go = h.register_file( green, False )
        bo = h.register_file( blue, False )

        ro.assign( tag1 )
        
        go.assign( tag1 )
        go.assign( tag2 )

        bo.assign( tag3 )

        go.set_duplicate_of( ro )
        bo.set_duplicate_of( ro )

        self.assertEqual( len( ro.get_tags() ), 3, 'Red tag list mismatch' )
        self.assertEqual( len( go.get_tags() ), 0, 'Green tag list mismatch' )
        self.assertEqual( len( bo.get_tags() ), 0, 'Blue tag list mismatch' )

        tags = ro.get_tags()
        self.assertTrue( tag1 in tags, 'tag1 not in dup list' )
        self.assertTrue( tag2 in tags, 'tag2 not in dup list' )
        self.assertTrue( tag3 in tags, 'tag3 not in dup list' )

    def test_assign_on_duplicate( self ):

        white = self._load_data( self.white )
        black = self._load_data( self.black )

        h = higu.Database()
        h.enable_write_access()

        tag = h.make_tag( 'a_tag' )

        wo = h.register_file( white, False )
        ko = h.register_file( black, False )

        ko.set_duplicate_of( wo )

        try:
            ko.assign( tag )
            self.fail( 'Did not except on assign to duplicate' )
        except ValueError:
            pass

if( __name__ == '__main__' ):
    unittest.main()
