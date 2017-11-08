import unittest
import testutil
import shutil
import os
import time
import datetime

import hdbfs

hdbfs.imgdb.MIN_THUMB_EXP = 4

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

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( red, False )

        self.assertFalse( os.path.exists( red ),
                'Old image was not removed' )
        self.assertTrue( os.path.isdir(
                    os.path.join( self.db_path, 'imgdat' ) ),
                'Image data directory not created' )

        red_fd = obj.get_root_stream().read()
        self.assertTrue( self._diff_data( red_fd, self.red ),
                'Image not read from library' )

    def test_delete( self ):

        yellow = self._load_data( self.yellow )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( yellow, False )

        img_fd = obj.get_root_stream().read()
        tb_fd = obj.get_thumb_stream( 4 ).read()
        self.assertIsNotNone( img_fd, 'Invalid image returned' )
        self.assertIsNotNone( tb_fd, 'Invalid thumb returned' )

        img_fd.close()
        tb_fd.close()

        obj_id = obj.get_id()

        s_id = obj.get_root_stream().get_stream_id()
        s_prio = obj.get_root_stream().get_priority()
        s_ext = obj.get_root_stream().get_extension()

        t_id = obj.get_thumb_stream( 4 ).get_stream_id()
        t_prio = obj.get_thumb_stream( 4 ).get_priority()
        t_ext = obj.get_thumb_stream( 4 ).get_extension()

        h.delete_object( obj )

        self.assertEqual( h.get_object_by_id( obj_id ), None,
                          'Object returned by id after delete' )

        img_fd = h.imgdb.read( s_id, s_prio, s_ext )
        self.assertIsNone( img_fd, 'Image returned after delete' )

        tb_fd = h.imgdb.read( t_id, t_prio, t_ext )
        self.assertIsNone( tb_fd, 'Thumb returned after delete' )

    def test_drop_streams( self ):

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )

        h = hdbfs.Database()
        h.enable_write_access()

        red = h.register_file( red )
        yellow = h.register_file( yellow )

        self.assertIsNotNone( red.get_root_stream(),
                'Red: No root stream' )
        self.assertIsNotNone( yellow.get_root_stream(),
                'Yellow: No root stream' )

        red.get_root_stream()['test_meta'] = 5
        yellow.get_root_stream()['test_meta'] = 5

        yellow.drop_expendable_streams()
        h.delete_object( yellow )

        self.assertIsNotNone( red.get_root_stream(),
                'Red: No root stream' )
        self.assertEqual( red.get_root_stream()['test_meta'], 5,
                'Red: test_meta lost' )

    def test_drop_expendible( self ):

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )

        h = hdbfs.Database()
        h.enable_write_access()

        red = h.register_file( red )
        yellow = h.register_file( yellow )

        self.assertIsNotNone( red.get_root_stream(),
                'Red: No root stream' )
        self.assertIsNotNone( yellow.get_root_stream(),
                'Yellow: No root stream' )
        self.assertIsNone( red.get_stream( 'tb:4' ),
                'Red: Thumb exists before created' )
        self.assertIsNone( yellow.get_stream( 'tb:4' ),
                'Yellow: Thumb exists before created' )

        self.assertIsNotNone( red.get_thumb_stream( 4 ),
                'Red: Thumb not created' )
        self.assertIsNotNone( yellow.get_thumb_stream( 4 ),
                'Yellow: Thumb not created' )

        self.assertIsNotNone( red.get_stream( 'tb:4' ),
                'Red: Thumb name lookup fail' )
        self.assertIsNotNone( yellow.get_stream( 'tb:4' ),
                'Yellow: Thumb name lookup fail' )

        red.get_thumb_stream( 4 )['test_meta'] = 5
        yellow.get_thumb_stream( 4 )['test_meta'] = 5

        self.assertEqual( red.get_thumb_stream( 4 )['test_meta'], 5,
                'Red: Thumb test_meta not set' )
        self.assertEqual( yellow.get_thumb_stream( 4 )['test_meta'], 5,
                'Yellow: Thumb test_meta not set' )

        yellow.drop_expendable_streams()

        self.assertIsNotNone( red.get_root_stream(),
                'Red: No root stream' )
        self.assertIsNotNone( yellow.get_root_stream(),
                'Yellow: No root stream' )
        self.assertIsNotNone( red.get_stream( 'tb:4' ),
                'Red: Thumb was lost' )
        self.assertIsNone( yellow.get_stream( 'tb:4' ),
                'Yellow: Thumb was not dropped' )
        self.assertEqual( red.get_thumb_stream( 4 )['test_meta'], 5,
                'Red: Thumb test_meta lost' )

    def test_timestamp( self ):

        blue = self._load_data( self.blue )

        h = hdbfs.Database()
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

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( green, False )

        self.assertFalse( os.path.exists( green ),
                'Old image was not removed' )

        img_fd = obj.get_root_stream().read()
        self.assertIsNotNone( img_fd, 'Failed opening image' )
        img_fd.close()

        green = self._load_data( self.green )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( green, False )

        self.assertTrue( os.path.exists( green ),
                'Double image was removed' )

        img_fd = obj.get_root_stream().read()
        self.assertIsNotNone( img_fd, 'Invalid image returned after double-add' )
        img_fd.close()

    def test_recover_missing( self ):

        cyan = self._load_data( self.cyan )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( cyan, False )
        
        img_fd = obj.get_root_stream().read()
        self.assertIsNotNone( img_fd, 'Failed opening image' )
        img_fd.close()

        s = obj.get_root_stream()
        h.imgdb.delete( s.get_stream_id(),
                        s.get_priority(),
                        s.get_extension() )
        h.imgdb.commit()

        img_fd = obj.get_root_stream().read()
        self.assertIsNone( img_fd, 'Remove failed' )

        cyan = self._load_data( self.cyan )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( cyan, False )
        
        img_fd = obj.get_root_stream().read()
        self.assertTrue( self._diff_data( img_fd, self.cyan ),
                'Image not recovered' )

    def test_recover_corrupted( self ):

        magenta = self._load_data( self.magenta )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( magenta, False )
        
        img_fd = obj.get_root_stream().read()
        self.assertIsNotNone( img_fd, 'Failed opening image' )
        img_fd.close()

        s = obj.get_root_stream()
        img_fd = h.imgdb._debug_write( s.get_stream_id(),
                                       s.get_priority(),
                                       s.get_extension() )

        try:
            img_fd.write( 'this is junk' )
        finally:
            img_fd.close()

        self.assertFalse( self._diff_data( obj.get_root_stream().read(),
                                           self.magenta ),
                'Corruption failed' )

        magenta = self._load_data( self.magenta )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( magenta, False )
        
        self.assertTrue( self._diff_data( obj.get_root_stream().read(),
                                          self.magenta ),
                'Image not recovered' )

    def test_name( self ):

        white = self._load_data( self.white )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( white )

        self.assertEqual( obj.get_name(), self.white,
                'Name not loaded' )

        origin_names = obj.get_origin_names()
        self.assertEqual( len( origin_names ), 1,
                'Name count does not match' )
        self.assertEqual( origin_names[0], self.white,
                'Unexpected name in origin list' )

    def test_repr( self ):

        white = self._load_data( self.white )
        black = self._load_data( self.black )

        h = hdbfs.Database()
        h.enable_write_access()

        w_f = h.register_file( white )
        k_f = h.register_file( black, hdbfs.NAME_POLICY_DONT_SET )

        self.assertEqual( w_f.get_repr(), self.white,
                'Repr on white did not return name' )
        self.assertEqual( k_f.get_repr(),
                '%016x.%s' % ( k_f.get_id(),
                               k_f.get_root_stream().get_extension() ),
                'Repr on black did not return default name' )

    def test_log_names_single( self ):

        white = self._load_data( self.white )
        black = self._load_data( self.black )

        h = hdbfs.Database()
        h.enable_write_access()

        w_f = h.register_file( white )
        k_f = h.register_file( black, hdbfs.NAME_POLICY_DONT_REGISTER )

        self.assertTrue( self.white in w_f.get_origin_names(),
                'Name list on white did not return single name' )
        self.assertTrue( len( k_f.get_origin_names() ) == 0,
                'Name list on black did not return empty' )

    def test_log_all_names( self ):

        white = self._load_data( self.white )
        black = self._load_data( self.black )

        h = hdbfs.Database()
        h.enable_write_access()

        w_f = h.register_file( white )
        k_f = h.register_file( black )

        h.merge_objects( w_f, k_f )

        names = w_f.get_origin_names( True )
        self.assertTrue( self.white in names,
                'Name list did not return white' )
        self.assertTrue( self.black in names,
                'Name list did not return black' )
        self.assertEqual( len( names ), 2,
                'Name list had an unexpected number of names' )

    def test_duplicate_name( self ):

        grey = self._load_data( self.grey )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( grey )

        grey2 = self._load_data( self.grey )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( grey2 )

        names = obj.get_origin_names()
        self.assertTrue( self.grey in names,
                'Name not loaded' )
        self.assertEqual( len( names ), 1,
                'Name count does not match' )

    def test_different_names( self ):

        grey = self._load_data( self.grey )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( grey )

        grey2 = self._load_data( self.grey, 'altname.png' )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( grey2 )

        names = obj.get_origin_names()
        self.assertTrue( self.grey in names,
                'First name not loaded' )
        self.assertTrue( 'altname.png' in names,
                'Second name not loaded' )
        self.assertEqual( len( names ), 2,
                'Name count does not match' )

    def test_load_name( self ):

        black = self._load_data( self.black )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( black, hdbfs.NAME_POLICY_DONT_REGISTER )

        self.assertIsNone( obj.get_name(),
                'Name set when it shouldn\'t have been' )
        self.assertEqual( len( obj.get_origin_names() ), 0,
                'Name registered when it shouldn\'t have been' )

        black = self._load_data( self.black )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( black, hdbfs.NAME_POLICY_DONT_SET )

        self.assertIsNone( obj.get_name(),
                'Name set when it shouldn\'t have been' )
        self.assertEqual( len( obj.get_origin_names() ), 1,
                'Name not registered when it should\'ve been' )
        self.assertEqual( obj.get_origin_names()[0], self.black,
                'Name not registered when it should\'ve been' )

        black = self._load_data( self.black )

        h = hdbfs.Database()
        h.enable_write_access()

        obj = h.register_file( black )

        self.assertEqual( obj.get_name(), self.black,
                'Name not set when it should\'ve been' )

    def test_fetch_missing_tag( self ):

        h = hdbfs.Database()

        try:
            h.get_tag( 'tag_that_doesnt_exist' )
            self.fail( 'Did not except on missing tag' )
        except KeyError:
            pass

    def test_create_tag( self ):

        h = hdbfs.Database()
        h.enable_write_access()

        tag = h.make_tag( 'a_tag' )
        tag2 = h.get_tag( 'a_tag' )

        self.assertEqual( tag.get_id(), tag2.get_id(),
                'Tag ID mismatch' )

    def test_tag_file( self ):

        black = self._load_data( self.black )

        h = hdbfs.Database()
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

        h = hdbfs.Database()
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

        h = hdbfs.Database()
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

        h = hdbfs.Database()
        h.enable_write_access()

        obj_id = h.create_album().get_id()

        album = h.get_object_by_id( obj_id )
        self.assertIsNotNone( album,
                'Unable to get album after creation' )
        self.assertTrue( isinstance( album, hdbfs.Group ),
                'Created album is not a group' )

    def test_create_album_with_text( self ):

        h = hdbfs.Database()
        h.enable_write_access()

        obj_id = h.create_album( text = 'This is some test text' ).get_id()

        album = h.get_object_by_id( obj_id )
        self.assertEqual( album.get_text(), 'This is some test text',
                'Album text not properly returned' )

    def test_album_set_text( self ):

        h = hdbfs.Database()
        h.enable_write_access()

        album = h.create_album()
        album.set_text( 'This is some test text' )
        obj_id = album.get_id()

        h = hdbfs.Database()
        album = h.get_object_by_id( obj_id )

        self.assertEqual( album.get_text(), 'This is some test text',
                'Album text not properly returned' )

    def test_add_files_to_album( self ):

        red = self._load_data( self.red )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        h = hdbfs.Database()
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

        h = hdbfs.Database()
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

        h = hdbfs.Database()
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

        h = hdbfs.Database()
        h.enable_write_access()

        wo = h.register_file( white, False )
        ko = h.register_file( black, False )

        ko_id = ko.get_id()
        ko_hash = ko.get_root_stream().get_hash()

        h.merge_objects( wo, ko )

        self.assertEqual( wo, ko, 'White and black are not duplicates' )
        self.assertEqual( h.get_object_by_id( ko_id ), None, 'Blacks ID still exists' )

        dups = wo.get_duplicate_streams()
        self.assertEqual( len( dups ), 1, 'Unexpected number of dups on white' )
        self.assertEqual( dups[0].get_hash(),
                          ko_hash, 'Black not in duplicate list of white' )

    def test_set_root( self ):

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )
        black = self._load_data( self.black )

        h = hdbfs.Database()
        h.enable_write_access()

        ro = h.register_file( red, False )
        yo = h.register_file( yellow, False )
        go = h.register_file( green, False )
        bo = h.register_file( blue, False )
        ko = h.register_file( black, False )

        ro_hash = ro.get_root_stream().get_hash()
        yo_hash = yo.get_root_stream().get_hash()
        go_hash = go.get_root_stream().get_hash()
        bo_hash = bo.get_root_stream().get_hash()

        h.merge_objects( ro, yo )
        h.merge_objects( ro, go )
        h.merge_objects( ro, bo )

        dups = map( lambda x: x.get_hash(), ro.get_duplicate_streams() )
        self.assertEqual( len( dups ), 3, 'Unexpected number of dups on red' )
        self.assertEqual( ro.get_root_stream().get_hash(),
                          ro_hash, 'Red not primary stream after merge' )
        self.assertTrue( yo_hash in dups,
                         'Yellow not in duplicate list of red' )
        self.assertTrue( go_hash in dups,
                         'Green not in duplicate list of red' )
        self.assertTrue( bo_hash in dups,
                         'Blue not in duplicate list of red' )

        try:
            ro.set_root_stream( wo.get_root_stream() )
            self.fail( 'Attempt to set white as root stream succeeded' )
        except:
            pass

        try:
            ro.set_root_stream( ro.get_root_stream() )
            self.fail( 'Attempt to set root to root succeeded' )
        except:
            pass

        ro.set_root_stream( ro.get_stream( 'dup:' + go_hash ) )

        dups = map( lambda x: x.get_hash(), ro.get_duplicate_streams() )
        self.assertEqual( len( dups ), 3, 'Unexpected number of dups on red after set' )
        self.assertEqual( ro.get_root_stream().get_hash(),
                          go_hash, 'Green not primary stream after set' )
        self.assertTrue( ro_hash in dups,
                         'Red not in duplicate list of red after set' )
        self.assertTrue( yo_hash in dups,
                         'Yellow not in duplicate list of red after set' )
        self.assertTrue( bo_hash in dups,
                         'Blue not in duplicate list of red after set' )

        dups = map( lambda x: x.get_name(), ro.get_duplicate_streams() )
        self.assertEqual( ro.get_root_stream().get_name(),
                          '.', 'Incorrect name for primary stream after set' )
        self.assertFalse( '.' in dups,
                          'Root name in duplicate list after set' )

    def test_set_duplicate_of_variant( self ):

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        h = hdbfs.Database()
        h.enable_write_access()

        ro = h.register_file( red, False )
        yo = h.register_file( yellow, False )
        go = h.register_file( green, False )
        bo = h.register_file( blue, False )

        go.set_variant_of( ro )
        h.merge_objects( ro, yo )
        h.merge_objects( go, bo )

        self.assertEqual( ro, yo, 'Yellow not equal to red' )
        self.assertEqual( go, bo, 'Blue not equal to green' )
        self.assertTrue( go in ro.get_variants(), 'Green not variant of red' )

        self.assertEqual( len( ro.get_duplicate_streams() ),
                          1, 'Red duplicate list mismatch' )
        self.assertEqual( len( go.get_duplicate_streams() ),
                          1, 'Green duplicate list mismatch' )

        self.assertEqual( len( ro.get_variants_of() ), 0, 'Red is a variant' )
        self.assertEqual( len( go.get_variants_of() ), 1, 'Green is not a variant' )

        self.assertEqual( len( ro.get_variants() ), 1, 'Red variant list mismatch' )
        self.assertEqual( len( go.get_variants() ), 0, 'Green variant list mismatch' )

    def test_duplicates_moved( self ):

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        h = hdbfs.Database()
        h.enable_write_access()

        ro = h.register_file( red, False )
        yo = h.register_file( yellow, False )
        go = h.register_file( green, False )
        bo = h.register_file( blue, False )

        ro_id = ro.get_id()
        yo_id = yo.get_id()
        go_id = go.get_id()
        bo_id = bo.get_id()

        ro_s_id = ro.get_root_stream().get_stream_id()
        yo_s_id = yo.get_root_stream().get_stream_id()
        go_s_id = go.get_root_stream().get_stream_id()
        bo_s_id = go.get_root_stream().get_stream_id()

        h.merge_objects( ro, yo )
        h.merge_objects( go, bo )
        h.merge_objects( ro, go )

        self.assertEqual( ro.get_id(), ro_id, 'Red was removed' )
        self.assertEqual( h.get_object_by_id( yo_id ), None, 'Yellow was not removed' )
        self.assertEqual( h.get_object_by_id( go_id ), None, 'Green was not removed' )
        self.assertEqual( h.get_object_by_id( bo_id ), None, 'Blue was not removed' )

        dups = map( lambda x: x.get_stream_id(), ro.get_duplicate_streams() )
        self.assertFalse( ro_s_id in dups, 'Red in dup list' )
        self.assertTrue( yo_s_id in dups, 'Yellow not in dup list' )
        self.assertTrue( go_s_id in dups, 'Green not in dup list' )
        self.assertTrue( bo_s_id in dups, 'Blue not in dup list' )

    def test_variants_moved( self ):

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        h = hdbfs.Database()
        h.enable_write_access()

        ro = h.register_file( red, False )
        yo = h.register_file( yellow, False )
        go = h.register_file( green, False )
        bo = h.register_file( blue, False )

        yo.set_variant_of( ro )
        bo.set_variant_of( go )
        h.merge_objects( ro, go )

        self.assertEqual( len( ro.get_variants_of() ), 0, 'Red is a variant' )
        self.assertEqual( len( yo.get_variants_of() ), 1, 'Yellow is not a variant' )
        self.assertEqual( len( bo.get_variants_of() ), 1, 'Blue is not a variant' )

        self.assertEqual( len( ro.get_duplicate_streams() ), 1, 'Red duplicate list mismatch' )
        self.assertEqual( len( ro.get_variants() ), 2, 'Red variant list mismatch' )

        variants = ro.get_variants()
        self.assertTrue( yo in variants, 'Yellow not in variant list' )
        self.assertTrue( bo in variants, 'Blue not in variant list' )

    def test_albums_moved( self ):

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        h = hdbfs.Database()
        h.enable_write_access()

        album = h.create_album()

        ro = h.register_file( red, False )
        yo = h.register_file( yellow, False )
        go = h.register_file( green, False )
        bo = h.register_file( blue, False )

        yo.assign( album, 2 )
        bo.assign( album, 3 )
        ro.assign( album, 1 )

        h.merge_objects( go, yo )

        files = album.get_files()
        self.assertEqual( len( files ), 3, 'Album size mismatch' )
        self.assertEqual( files[0], ro, 'Red not first in album' )
        self.assertEqual( files[1], go, 'Green not second in album' )
        self.assertEqual( files[2], bo, 'Blue not third in album' )

    def test_tags_moved( self ):

        red = self._load_data( self.red )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        h = hdbfs.Database()
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

        h.merge_objects( ro, go )
        h.merge_objects( ro, bo )

        self.assertEqual( len( ro.get_tags() ), 3, 'Red tag list mismatch' )

        tags = ro.get_tags()
        self.assertTrue( tag1 in tags, 'tag1 not in dup list' )
        self.assertTrue( tag2 in tags, 'tag2 not in dup list' )
        self.assertTrue( tag3 in tags, 'tag3 not in dup list' )

if( __name__ == '__main__' ):
    unittest.main()
