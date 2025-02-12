import unittest
import testutil
import shutil
import os
import time
import datetime

import hdbfs
import hdbfs.ark

from hdbfs.imgdb.objects import ThumbRequestPrio

class HiguLibCases( testutil.TestCase ):

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

    def test_basic_structure( self ):

        self.assertTrue( os.path.isdir( self.db_path ),
                'Library not created' )
        self.assertTrue( os.path.isfile(
                    os.path.join( self.db_path, 'hfdb.dat' ) ),
                'Sqlite database not created' )

    def test_imgdat_structure( self ):

        red = self._load_data( self.red )

        with hdbfs.Database() as h:
            h.enable_write_access()

            obj = h.register_file( red, False )

            self.assertFalse( os.path.exists( red ),
                    'Old image was not removed' )
            self.assertTrue( os.path.isdir(
                        os.path.join( self.db_path, 'imgdat' ) ),
                    'Image data directory not created' )

            with obj.get_root_stream().open() as red_fd:
                self.assertTrue( self._diff_data( red_fd, self.red ),
                        'Image not read from library' )

    def test_delete( self ):

        yellow = self._load_data( self.yellow )

        with hdbfs.Database() as h:
            h.enable_write_access()

            obj = h.register_file( yellow, False )

            # Ensure these work
            with obj.get_root_stream().open() as fd:
                pass
            with obj.get_thumb_stream( 4, ThumbRequestPrio.IMMEDIATE ).open() as fd:
                pass

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

            try:
                h.imgdb.open( s_id, s_prio, s_ext )
                self.fail( 'Image returned after delete' )
            except hdbfs.ark.FileUnavailableError:
                pass

            try:
                h.imgdb.open( t_id, t_prio, t_ext )
                self.fail( 'Thumb returned after delete' )
            except hdbfs.ark.FileUnavailableError:
                pass

    def test_drop_streams( self ):

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )

        with hdbfs.Database() as h:
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

        with hdbfs.Database() as h:
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

            self.assertIsNotNone(
                    red.get_thumb_stream( 4, ThumbRequestPrio.IMMEDIATE ),
                    'Red: Thumb not created' )
            self.assertIsNotNone(
                    yellow.get_thumb_stream( 4, ThumbRequestPrio.IMMEDIATE ),
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

        with hdbfs.Database() as h:
            h.enable_write_access()

            obj_id = h.register_file( blue, False ).get_id()

            time.sleep( 5 )
            obj = h.get_object_by_id( obj_id )

            now = datetime.datetime.now( datetime.timezone.utc )
            d_5sec = datetime.timedelta( seconds = 5 )
            d_10sec = datetime.timedelta( seconds = 10 )

            self.assertTrue( now - obj.get_creation_time_utc() < d_10sec,
                    'Unexpected timestamp > 10secs away' )
            self.assertTrue( now - obj.get_creation_time_utc() > d_5sec,
                    'Unexpected timestamp < 5secs away' )

    def test_double_add( self ):

        green = self._load_data( self.green )

        with hdbfs.Database() as h:
            h.enable_write_access()

            obj = h.register_file( green, False )

            self.assertFalse( os.path.exists( green ),
                    'Old image was not removed' )

            with obj.get_root_stream().open() as fd:
                pass

            green = self._load_data( self.green )

        with hdbfs.Database() as h:
            h.enable_write_access()

            obj = h.register_file( green, False )

            self.assertTrue( os.path.exists( green ),
                    'Double image was removed' )

            with obj.get_root_stream().open() as fd:
                pass

    def test_recover_missing( self ):

        cyan = self._load_data( self.cyan )

        with hdbfs.Database() as h:
            h.enable_write_access()

            obj = h.register_file( cyan, False )

            with obj.get_root_stream().open() as fd:
                pass

            s = obj.get_root_stream()
            h.imgdb.delete( s.get_stream_id(),
                            s.get_priority(),
                            s.get_extension() )
            h.imgdb.commit()

            try:
                obj.get_root_stream().open()
                self.fail( 'Remove failed' )
            except hdbfs.ark.FileUnavailableError:
                pass

        cyan = self._load_data( self.cyan )

        with hdbfs.Database() as h:
            h.enable_write_access()

            obj = h.register_file( cyan, False )

            with obj.get_root_stream().open() as fd:
                pass

    def test_recover_corrupted( self ):

        magenta = self._load_data( self.magenta )

        with hdbfs.Database() as h:
            h.enable_write_access()

            obj = h.register_file( magenta, False )

            with obj.get_root_stream().open() as fd:
                pass

            s = obj.get_root_stream()
            with h.imgdb._debug_write( s.get_stream_id(),
                                       s.get_priority(),
                                       s.get_extension() ) as fd:

                fd.write( 'this is junk'.encode() )

            with obj.get_root_stream().open() as fd:
                self.assertFalse( self._diff_data( fd, self.magenta ),
                        'Corruption failed' )

            magenta = self._load_data( self.magenta )

        with hdbfs.Database() as h:
            h.enable_write_access()

            obj = h.register_file( magenta, False )

            with obj.get_root_stream().open() as fd:
                self.assertTrue( self._diff_data( fd, self.magenta ),
                        'Image not recovered' )

    def test_name( self ):

        white = self._load_data( self.white )

        with hdbfs.Database() as h:
            h.enable_write_access()

            obj = h.register_file( white )

            self.assertEqual( obj.get_name(), self.white,
                    'Name not loaded' )

            origin_names = obj.get_origin_names()
            self.assertEqual( len( origin_names ), 1,
                    'Name count does not match' )
            self.assertEqual( origin_names[0], self.white,
                    'Unexpected name in origin list' )

    def test_group_name( self ):

        white = self._load_data( self.white )

        with hdbfs.Database() as h:
            h.enable_write_access()

            obj = h.register_file( white )
            alb_named = h.create_album()
            alb_noname = h.create_album()

            obj.assign( alb_named, name = 'not_white.png' )
            obj.assign( alb_noname )

            self.assertEqual( obj.get_name(), self.white,
                    'White name not read' )
            self.assertEqual( obj.get_name( alb_named ), 'not_white.png',
                    'Album name not read' )
            self.assertEqual( obj.get_name( alb_noname ), self.white,
                    'White name not read from noname album' )

            obj.set_name( 'maybe_blue.png', alb_noname )

            self.assertEqual( obj.get_name(), self.white,
                    'White name not read' )
            self.assertEqual( obj.get_name( alb_named ), 'not_white.png',
                    'Album name not read' )
            self.assertEqual( obj.get_name( alb_noname ), 'maybe_blue.png',
                    'Album 2 name not read' )

    def test_repr( self ):

        white = self._load_data( self.white )
        black = self._load_data( self.black )

        with hdbfs.Database() as h:
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

        with hdbfs.Database() as h:
            h.enable_write_access()

            w_f = h.register_file( white )
            k_f = h.register_file( black, hdbfs.NAME_POLICY_DONT_REGISTER )

            self.assertTrue( self.white in w_f.get_origin_names(),
                    'Name list on white did not return single name' )
            self.assertTrue( len( k_f.get_origin_names() ) == 0,
                    'Name list on black did not return empty' )

    def test_duplicate_name( self ):

        grey = self._load_data( self.grey )

        with hdbfs.Database() as h:
            h.enable_write_access()

            obj = h.register_file( grey )

            grey2 = self._load_data( self.grey )

        with hdbfs.Database() as h:
            h.enable_write_access()

            obj = h.register_file( grey2 )

            names = obj.get_origin_names()
            self.assertTrue( self.grey in names,
                    'Name not loaded' )
            self.assertEqual( len( names ), 1,
                    'Name count does not match' )

    def test_different_names( self ):

        grey = self._load_data( self.grey )

        with hdbfs.Database() as h:
            h.enable_write_access()

            obj = h.register_file( grey )

            grey2 = self._load_data( self.grey, 'altname.png' )

        with hdbfs.Database() as h:
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

        with hdbfs.Database() as h:
            h.enable_write_access()

            obj = h.register_file( black, hdbfs.NAME_POLICY_DONT_REGISTER )

            self.assertIsNone( obj.get_name(),
                    'Name set when it shouldn\'t have been' )
            self.assertEqual( len( obj.get_origin_names() ), 0,
                    'Name registered when it shouldn\'t have been' )

            black = self._load_data( self.black )

        with hdbfs.Database() as h:
            h.enable_write_access()

            obj = h.register_file( black, hdbfs.NAME_POLICY_DONT_SET )

            self.assertIsNone( obj.get_name(),
                    'Name set when it shouldn\'t have been' )
            self.assertEqual( len( obj.get_origin_names() ), 1,
                    'Name not registered when it should\'ve been' )
            self.assertEqual( obj.get_origin_names()[0], self.black,
                    'Name not registered when it should\'ve been' )

            black = self._load_data( self.black )

        with hdbfs.Database() as h:
            h.enable_write_access()

            obj = h.register_file( black )

            self.assertEqual( obj.get_name(), self.black,
                'Name not set when it should\'ve been' )

    def test_fetch_missing_tag( self ):

        with hdbfs.Database() as h:

            try:
                h.get_tag( 'tag_that_doesnt_exist' )
                self.fail( 'Did not except on missing tag' )
            except KeyError:
                pass

    def test_create_tag( self ):

        with hdbfs.Database() as h:
            h.enable_write_access()

            tag = h.make_tag( 'a_tag' )
            tag2 = h.get_tag( 'a_tag' )

            self.assertEqual( tag.get_id(), tag2.get_id(),
                    'Tag ID mismatch' )

    def test_tag_file( self ):

        black = self._load_data( self.black )

        with hdbfs.Database() as h:
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

        with hdbfs.Database() as h:
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

        with hdbfs.Database() as h:
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

        with hdbfs.Database() as h:
            h.enable_write_access()

            obj_id = h.create_album().get_id()

            album = h.get_object_by_id( obj_id )
            self.assertIsNotNone( album,
                    'Unable to get album after creation' )
            self.assertTrue( isinstance( album, hdbfs.Album ),
                    'Created album is not a group' )

    def test_create_album_with_text( self ):

        with hdbfs.Database() as h:
            h.enable_write_access()

            obj_id = h.create_album( text = 'This is some test text' ).get_id()

            album = h.get_object_by_id( obj_id )
            self.assertEqual( album.get_text(), 'This is some test text',
                    'Album text not properly returned' )

    def test_album_set_text( self ):

        with hdbfs.Database() as h:
            h.enable_write_access()

            album = h.create_album()
            album.set_text( 'This is some test text' )
            obj_id = album.get_id()

        with hdbfs.Database() as h:
            album = h.get_object_by_id( obj_id )

            self.assertEqual( album.get_text(), 'This is some test text',
                    'Album text not properly returned' )

    def test_add_files_to_album( self ):

        red = self._load_data( self.red )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        with hdbfs.Database() as h:
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

    def test_add_album_to_album( self ):

        red = self._load_data( self.red )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        with hdbfs.Database() as h:
            h.enable_write_access()

            parent = h.create_album()
            child = h.create_album()

            ro = h.register_file( red, False )
            go = h.register_file( green, False )
            bo = h.register_file( blue, False )

            ro.assign( child )
            go.assign( child )
            bo.assign( parent )
            child.assign( parent )

            child_files = child.get_files()

            self.assertTrue( ro in child_files, 'Red not in album' )
            self.assertTrue( go in child_files, 'Green not in album' )

            par_files = parent.get_files()
            par_albums = parent.get_albums()
            par_items = parent.get_items()

            self.assertTrue( bo in par_files, 'Blue not in album' )
            self.assertTrue( bo in par_items, 'Blue not in album' )
            self.assertTrue( child in par_albums, 'Blue not in album' )
            self.assertTrue( child in par_items, 'Blue not in album' )

    def test_order_then_reorder( self ):

        red = self._load_data( self.red )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        with hdbfs.Database() as h:
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

        with hdbfs.Database() as h:
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

    def test_set_variant( self ):

        white = self._load_data( self.white )
        black = self._load_data( self.black )

        with hdbfs.Database() as h:
            h.enable_write_access()

            wo = h.register_file( white, False )
            ko = h.register_file( black, False )

            ko.assign( wo )

            self.assertTrue( ko in wo.get_variants(), 'Black not variant of white' )
            self.assertTrue( len( wo.get_variants_of() ) == 0, 'White is a variant' )

            self.assertTrue( wo in ko.get_variants_of(), 'White is not a parent of black' )
            self.assertTrue( len( ko.get_variants() ) == 0, 'Black has variants' )

            self.assertTrue( len( wo.get_duplicates() ) == 0, 'White has duplicates' )
            self.assertTrue( len( ko.get_duplicates() ) == 0, 'Black has duplicates' )
            self.assertTrue( wo.get_original_file() is None, 'White is a duplicate' )
            self.assertTrue( ko.get_original_file() is None, 'Black is a duplicate' )

            # Reverse the relationship
            wo.assign( ko )

            self.assertTrue( wo in ko.get_variants(), 'White not variant of black' )
            self.assertTrue( len( ko.get_variants_of() ) == 0, 'Black is a variant' )

            self.assertTrue( ko in wo.get_variants_of(), 'Black is not a parent of white' )
            self.assertTrue( len( wo.get_variants() ) == 0, 'White has variants' )

    def test_set_duplicate( self ):

        red = self._load_data( self.red )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        with hdbfs.Database() as h:
            h.enable_write_access()

            ro = h.register_file( red, False )
            go = h.register_file( green, False )
            bo = h.register_file( blue, False )

            bo.assign( ro, is_duplicate = True )

            self.assertTrue( bo in ro.get_duplicates(), 'Blue not duplicate of red' )
            self.assertTrue( len( bo.get_duplicates() ) == 0, 'Blue has duplicates' )

            self.assertTrue( bo.get_original_file() == ro, 'Red is not a parent of blue' )
            self.assertTrue( ro.get_original_file() == None, 'Red is a duplicate' )

            self.assertTrue( len( ro.get_variants() ) == 0, 'Red has variants' )
            self.assertTrue( len( bo.get_variants() ) == 0, 'Blue has variants' )
            self.assertTrue( len( ro.get_variants_of() ) == 0, 'Red has variant parents' )
            self.assertTrue( len( bo.get_variants_of() ) == 0, 'Blue has variant parents' )

            go.assign( ro, is_duplicate = True )

            self.assertTrue( go in ro.get_duplicates(), 'Green not duplicate of red' )
            self.assertTrue( bo in ro.get_duplicates(), 'Blue not duplicate of red' )
            self.assertTrue( len( bo.get_duplicates() ) == 0, 'Blue has duplicates' )

    def test_promote_duplicate( self ):

        white = self._load_data( self.white )
        black = self._load_data( self.black )

        with hdbfs.Database() as h:
            h.enable_write_access()

            wo = h.register_file( white, False )
            ko = h.register_file( black, False )

            ko.assign( wo )

            self.assertTrue( wo in ko.get_variants_of(), 'White is not a parent of Black' )
            self.assertTrue( ko.get_original_file() is None, 'Black is a dup' )

            ko.assign( wo, is_duplicate = True )

            self.assertEqual( len( ko.get_variants_of() ), 0, 'White has variants' )
            self.assertEqual( ko.get_original_file(), wo, 'Black not a dup' )

    def test_duplicates_moved( self ):

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        with hdbfs.Database() as h:
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

            yo.assign( ro, is_duplicate = True )
            bo.assign( go, is_duplicate = True )
            go.assign( ro, is_duplicate = True )

            dups = ro.get_duplicates()
            self.assertFalse( ro in dups, 'Red in dup list' )
            self.assertTrue( yo in dups, 'Yellow not in dup list' )
            self.assertTrue( go in dups, 'Green not in dup list' )
            self.assertTrue( bo in dups, 'Blue not in dup list' )

            self.assertEqual( len( dups ), 3, 'Unexpected no. of dups' )
            self.assertEqual( len( yo.get_duplicates() ), 0, 'Yellow has duplicates' )
            self.assertEqual( len( go.get_duplicates() ), 0, 'Green has duplicates' )
            self.assertEqual( len( bo.get_duplicates() ), 0, 'Blue has duplicates' )

    def test_variants_moved( self ):

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        with hdbfs.Database() as h:
            h.enable_write_access()

            ro = h.register_file( red, False )
            yo = h.register_file( yellow, False )
            go = h.register_file( green, False )
            bo = h.register_file( blue, False )

            yo.assign( ro )
            bo.assign( go )
            go.assign( ro, is_duplicate = True )

            self.assertEqual( len( ro.get_variants_of() ), 0, 'Red is a variant' )
            self.assertEqual( len( yo.get_variants_of() ), 1, 'Yellow is not a variant' )
            self.assertEqual( len( bo.get_variants_of() ), 1, 'Blue is not a variant' )

            self.assertEqual( len( ro.get_duplicates() ), 1, 'Red duplicate list mismatch' )
            self.assertEqual( len( ro.get_variants() ), 2, 'Red variant list mismatch' )

            variants = ro.get_variants()
            self.assertTrue( yo in variants, 'Yellow not in variant list' )
            self.assertTrue( bo in variants, 'Blue not in variant list' )

    def test_albums_moved( self ):

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        with hdbfs.Database() as h:
            h.enable_write_access()

            album = h.create_album()
            pub = h.create_album()

            ro = h.register_file( red, False )
            yo = h.register_file( yellow, False )
            go = h.register_file( green, False )
            bo = h.register_file( blue, False )

            yo.assign( album, 2 )
            bo.assign( album, 3 )
            ro.assign( album, 1 )

            yo.assign( pub )
            pub.publish()

            yo.assign( go, is_duplicate = True )

            files = album.get_files()
            self.assertEqual( len( files ), 3, 'Album size mismatch' )
            self.assertEqual( files[0], ro, 'Red not first in album' )
            self.assertEqual( files[1], go, 'Green not second in album' )
            self.assertEqual( files[2], bo, 'Blue not third in album' )

            files = pub.get_files()
            self.assertEqual( len( files ), 1, 'Publish size mismatch' )
            self.assertEqual( files[0], yo, 'Red not in published album' )

    def test_tags_moved( self ):

        red = self._load_data( self.red )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        with hdbfs.Database() as h:
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

            go.assign( ro, is_duplicate = True )
            bo.assign( ro, is_duplicate = True )

            self.assertEqual( len( ro.get_tags() ), 3, 'Red tag list mismatch' )

            tags = ro.get_tags()
            self.assertTrue( tag1 in tags, 'tag1 not in dup list' )
            self.assertTrue( tag2 in tags, 'tag2 not in dup list' )
            self.assertTrue( tag3 in tags, 'tag3 not in dup list' )

    def test_check_register_requests_thumbs( self ):

        red = self._load_data( self.red )

        with hdbfs.Database() as h:
            h.enable_write_access()

            h.register_file( red, False )

            r = h.get_next_thumb_request()
            self.assertIsNotNone( r, 'No thumb request was marked' )
            self.assertEqual( r.prio, hdbfs.ImageRequestPriority.BACKGROUND,
                              'Thumb request priority is not background' )

    def test_check_process_thumb_requests( self ):

        red = self._load_data( self.red )

        with hdbfs.Database() as h:
            h.enable_write_access()

            ro = h.register_file( red, False )

            self.assertTrue( h.process_thumb_requests(),
                             'No thumb requests to process.' )

            self.assertIsNotNone( ro.get_thumb_stream( 4 ),
                                  'Thumb stream not generated' )

            self.assertFalse( h.process_thumb_requests(),
                              'Thumb request not cleared.' )

    def test_get_thumb_requests( self ):

        red = self._load_data( self.red )

        with hdbfs.Database() as h:
            h.enable_write_access()

            ro = h.register_file( red, False )
            ro.get_thumb_stream( 4, ThumbRequestPrio.MARK_REQUESTED )

            r = h.get_next_thumb_request()
            self.assertIsNotNone( r, 'No thumb request was marked' )
            self.assertEqual( r.prio, hdbfs.ImageRequestPriority.IMMEDIATE,
                              'Thumb request priority is not immedate' )
            self.assertIn( 4, r.exps, 'Request for exp 4 is missing' )


if( __name__ == '__main__' ):
    unittest.main()
