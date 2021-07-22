import unittest
import testutil

import hdbfs

class HiguQueryCases( testutil.TestCase ):

    def setUp( self ):

        import time

        self.init_env()

        h = hdbfs.Database()
        h.enable_write_access()

        with h.transaction():

            red_obj = h.register_file( self._load_data( self.red ) )
            yellow_obj = h.register_file( self._load_data( self.yellow ) )
            green_obj = h.register_file( self._load_data( self.green ) )
            cyan_obj = h.register_file( self._load_data( self.cyan ) )
            blue_obj = h.register_file( self._load_data( self.blue ) )
            magenta_obj = h.register_file( self._load_data( self.magenta ) )
            white_obj = h.register_file( self._load_data( self.white ) )
            grey_obj = h.register_file( self._load_data( self.grey ) )
            black_obj = h.register_file( self._load_data( self.black ) )

            red_obj['test'] = 1
            yellow_obj['test'] = 2
            green_obj['test'] = 3
            blue_obj['test'] = 4

            rwb_alb = h.create_album( name = 'rwb' )
            bgy_alb = h.create_album( name = 'bgy' )

            warm_tag = h.make_tag( 'warm' )
            cool_tag = h.make_tag( 'cool' )
            rgb_tag = h.make_tag( 'rgb' )
            cmyk_tag = h.make_tag( 'cmyk' )
            paint_tag = h.make_tag( 'paint' )
            themes_tag = h.make_tag( 'themes' )

            red_obj.assign( rwb_alb )
            white_obj.assign( rwb_alb )
            blue_obj.assign( rwb_alb )

            blue_obj.assign( bgy_alb )
            green_obj.assign( bgy_alb )
            yellow_obj.assign( bgy_alb )

            rwb_alb.assign( themes_tag )
            bgy_alb.assign( themes_tag )
            black_obj.assign( themes_tag )

            red_obj.assign( warm_tag )
            yellow_obj.assign( warm_tag )
            magenta_obj.assign( warm_tag )

            green_obj.assign( cool_tag )
            cyan_obj.assign( cool_tag )
            blue_obj.assign( cool_tag )

            red_obj.assign( rgb_tag )
            green_obj.assign( rgb_tag )
            blue_obj.assign( rgb_tag )

            cyan_obj.assign( cmyk_tag )
            magenta_obj.assign( cmyk_tag )
            yellow_obj.assign( cmyk_tag )
            black_obj.assign( cmyk_tag )

            red_obj.assign( paint_tag )
            yellow_obj.assign( paint_tag )
            blue_obj.assign( paint_tag )

            self.h = hdbfs.Database()

            self.red_obj = self.h.get_object_by_id( red_obj.get_id() )
            self.yellow_obj = self.h.get_object_by_id( yellow_obj.get_id() )
            self.green_obj = self.h.get_object_by_id( green_obj.get_id() )
            self.cyan_obj = self.h.get_object_by_id( cyan_obj.get_id() )
            self.blue_obj = self.h.get_object_by_id( blue_obj.get_id() )
            self.magenta_obj = self.h.get_object_by_id( magenta_obj.get_id() )
            self.white_obj = self.h.get_object_by_id( white_obj.get_id() )
            self.grey_obj = self.h.get_object_by_id( grey_obj.get_id() )
            self.black_obj = self.h.get_object_by_id( black_obj.get_id() )

            self.rwb_alb = self.h.get_object_by_id( rwb_alb.get_id() )
            self.bgy_alb = self.h.get_object_by_id( bgy_alb.get_id() )

            self.warm_tag = self.h.get_object_by_id( warm_tag.get_id() )
            self.cool_tag = self.h.get_object_by_id( cool_tag.get_id() )
            self.rgb_tag = self.h.get_object_by_id( rgb_tag.get_id() )
            self.cmyk_tag = self.h.get_object_by_id( cmyk_tag.get_id() )
            self.paint_tag = self.h.get_object_by_id( paint_tag.get_id() )
            self.themes_tag = self.h.get_object_by_id( themes_tag.get_id() )

    def tearDown( self ):

        self.uninit_env()

    def test_query_all( self ):

        rs = [ r for r in self.h.all_albums_or_free_files() ]

        self.assertTrue( self.cyan_obj in rs, 'Cyan not in result' )
        self.assertTrue( self.magenta_obj in rs, 'Magenta not in result' )
        self.assertTrue( self.grey_obj in rs, 'Grey not in result' )
        self.assertTrue( self.black_obj in rs, 'Black not in result' )

        self.assertTrue( self.rwb_alb in rs, 'RWB not in result' )
        self.assertTrue( self.bgy_alb in rs, 'BGY not in result' )

        self.assertTrue( self.red_obj not in rs, 'Red not in result' )
        self.assertTrue( self.white_obj not in rs, 'White not in result' )
        self.assertTrue( self.blue_obj not in rs, 'Blue not in result' )
        self.assertTrue( self.green_obj not in rs, 'Green not in result' )
        self.assertTrue( self.yellow_obj not in rs, 'Yellow not in result' )

        self.assertEqual( len( rs ), 6, 'Result size mismatch' )

    def test_query_unowned( self ):

        rs = [ r for r in self.h.unowned_files() ]

        self.assertTrue( self.grey_obj in rs, 'Grey not in result' )

        self.assertEqual( len( rs ), 1, 'Result size mismatch' )

    def test_query_require( self ):

        query = hdbfs.query.Query()
        query.add_require_constraint( hdbfs.query.TagConstraint( self.warm_tag ) )
        query.add_require_constraint( hdbfs.query.TagConstraint( self.paint_tag ) )

        rs = [ r for r in query.execute( self.h ) ]

        self.assertTrue( self.red_obj in rs, 'Red not in result' )
        self.assertTrue( self.yellow_obj in rs, 'Yellow not in result' )

        self.assertEqual( len( rs ), 2, 'Result size mismatch' )

    def test_query_add( self ):

        query = hdbfs.query.Query()
        query.add_or_constraint( hdbfs.query.TagConstraint( self.warm_tag ) )
        query.add_or_constraint( hdbfs.query.TagConstraint( self.paint_tag ) )

        rs = [ r for r in query.execute( self.h ) ]

        self.assertTrue( self.red_obj in rs, 'Red not in result' )
        self.assertTrue( self.yellow_obj in rs, 'Yellow not in result' )
        self.assertTrue( self.blue_obj in rs, 'Blue not in result' )
        self.assertTrue( self.magenta_obj in rs, 'Magenta not in result' )

        self.assertEqual( len( rs ), 4, 'Result size mismatch' )

    def test_query_sub( self ):

        query = hdbfs.query.Query()
        query.add_not_constraint( hdbfs.query.TagConstraint( self.warm_tag ) )
        query.add_not_constraint( hdbfs.query.TagConstraint( self.paint_tag ) )

        rs = [ r for r in query.execute( self.h ) ]

        self.assertTrue( self.cyan_obj in rs, 'Cyan not in result' )
        self.assertTrue( self.grey_obj in rs, 'Grey not in result' )
        self.assertTrue( self.black_obj in rs, 'Black not in result' )

        self.assertTrue( self.rwb_alb in rs, 'RWB not in result' )
        self.assertTrue( self.bgy_alb in rs, 'BGY not in result' )

        self.assertEqual( len( rs ), 5, 'Result size mismatch' )

    def test_query_add_sub( self ):

        query = hdbfs.query.Query()
        query.add_or_constraint( hdbfs.query.TagConstraint( self.rgb_tag ) )
        query.add_or_constraint( hdbfs.query.TagConstraint( self.cmyk_tag ) )
        query.add_not_constraint( hdbfs.query.TagConstraint( self.cool_tag ) )

        rs = [ r for r in query.execute( self.h ) ]

        self.assertTrue( self.red_obj in rs, 'Red not in result' )
        self.assertTrue( self.yellow_obj in rs, 'Yellow not in result' )
        self.assertTrue( self.magenta_obj in rs, 'Magenta not in result' )
        self.assertTrue( self.black_obj in rs, 'Black not in result' )

        self.assertEqual( len( rs ), 4, 'Result size mismatch' )

    def test_query_require_add( self ):

        query = hdbfs.query.Query()
        query.add_require_constraint( hdbfs.query.TagConstraint( self.warm_tag ) )
        query.add_require_constraint( hdbfs.query.TagConstraint( self.paint_tag ) )
        query.add_or_constraint( hdbfs.query.TagConstraint( self.cool_tag ) )

        rs = [ r for r in query.execute( self.h ) ]

        self.assertTrue( self.red_obj in rs, 'Red not in result' )
        self.assertTrue( self.yellow_obj in rs, 'Yellow not in result' )
        self.assertTrue( self.green_obj in rs, 'Green not in result' )
        self.assertTrue( self.cyan_obj in rs, 'Cyan not in result' )
        self.assertTrue( self.blue_obj in rs, 'Blue not in result' )

        self.assertEqual( len( rs ), 5, 'Result size mismatch' )

    def test_query_require_add_sub( self ):

        query = hdbfs.query.Query()
        query.add_require_constraint( hdbfs.query.TagConstraint( self.warm_tag ) )
        query.add_require_constraint( hdbfs.query.TagConstraint( self.paint_tag ) )
        query.add_or_constraint( hdbfs.query.TagConstraint( self.cool_tag ) )
        query.add_not_constraint( hdbfs.query.TagConstraint( self.cmyk_tag ) )

        rs = [ r for r in query.execute( self.h ) ]

        self.assertTrue( self.red_obj in rs, 'Red not in result' )
        self.assertTrue( self.green_obj in rs, 'Green not in result' )
        self.assertTrue( self.blue_obj in rs, 'Blue not in result' )

        self.assertEqual( len( rs ), 3, 'Result size mismatch' )

    def test_query_order_add( self ):

        query = hdbfs.query.Query()
        query.add_require_constraint( hdbfs.query.TagConstraint( self.rgb_tag ) )
        query.set_order( 'add' )

        rs = [ r for r in query.execute( self.h ) ]

        self.assertTrue( self.red_obj == rs[0], 'Red not in pos 0' )
        self.assertTrue( self.green_obj == rs[1], 'Green not in pos 1' )
        self.assertTrue( self.blue_obj == rs[2], 'Blue not in pos 2' )

        self.assertEqual( len( rs ), 3, 'Result size mismatch' )

    def test_query_order_radd( self ):

        query = hdbfs.query.Query()
        query.add_require_constraint( hdbfs.query.TagConstraint( self.rgb_tag ) )
        query.set_order( 'add', True )

        rs = [ r for r in query.execute( self.h ) ]

        self.assertTrue( self.red_obj == rs[2], 'Red not in pos 2' )
        self.assertTrue( self.green_obj == rs[1], 'Green not in pos 1' )
        self.assertTrue( self.blue_obj == rs[0], 'Blue not in pos 0' )

        self.assertEqual( len( rs ), 3, 'Result size mismatch' )

    def test_query_mixed_tag( self ):

        query = hdbfs.query.Query()
        query.add_require_constraint( hdbfs.query.TagConstraint( self.themes_tag ) )

        rs = [ r for r in query.execute( self.h ) ]

        self.assertTrue( self.rwb_alb in rs, 'RWB not in result' )
        self.assertTrue( self.bgy_alb in rs, 'BGY not in result' )
        self.assertTrue( self.black_obj in rs, 'Black not in result' )

        self.assertEqual( len( rs ), 3, 'Result size mismatch' )

    def test_expand_mixed_tag( self ):

        query = hdbfs.query.Query()
        query.add_require_constraint( hdbfs.query.TagConstraint( self.themes_tag ) )
        query.set_expand()

        rs = [ r for r in query.execute( self.h ) ]

        self.assertTrue( self.rwb_alb not in rs, 'RWB in result' )
        self.assertTrue( self.bgy_alb not in rs, 'BGY in result' )
        self.assertTrue( self.red_obj in rs, 'Red not in result' )
        self.assertTrue( self.yellow_obj in rs, 'Yellow not in result' )
        self.assertTrue( self.black_obj in rs, 'Black not in result' )

        self.assertEqual( len( rs ), 6, 'Result size mismatch' )

    def test_query_fuzzy_tag( self ):

        query = hdbfs.query.Query()
        query.add_require_constraint( hdbfs.query.TagConstraint( 'c*', fuzzy = True ) )

        rs = [ r for r in query.execute( self.h ) ]

        self.assertTrue( self.cyan_obj in rs, 'Cyan not in result' )
        self.assertTrue( self.blue_obj in rs, 'Blue not in result' )
        self.assertTrue( self.red_obj not in rs, 'Red in result' )

    def test_query_by_name( self ):

        query = hdbfs.query.Query()
        query.add_require_constraint( hdbfs.query.UnboundConstraint( self.red ) )

        rs = [ r for r in query.execute( self.h ) ]

        self.assertTrue( self.red_obj in rs, 'Red not in result' )
        self.assertEqual( len( rs ), 1, 'Result size mismatch' )

    def test_query_by_name_subset( self ):

        query = hdbfs.query.Query()
        query.add_require_constraint( hdbfs.query.UnboundConstraint( 'e_sq.' ) )

        rs = [ r for r in query.execute( self.h ) ]

        self.assertTrue( self.blue_obj in rs, 'Blue not in result' )
        self.assertTrue( self.white_obj in rs, 'White not in result' )
        self.assertEqual( len( rs ), 2, 'Result size mismatch' )

    def test_query_by_name_wildcard( self ):

        query = hdbfs.query.Query()
        query.add_require_constraint( hdbfs.query.NameConstraint( '=', '*gr*sq*' ) )

        rs = [ r for r in query.execute( self.h ) ]

        self.assertTrue( self.green_obj in rs, 'Green not in result' )
        self.assertTrue( self.grey_obj in rs, 'Grey not in result' )
        self.assertEqual( len( rs ), 2, 'Result size mismatch' )

    def test_query_by_name_wildcard_neg( self ):

        query = hdbfs.query.Query()
        query.add_require_constraint( hdbfs.query.NameConstraint( '!=', '*gr*sq*' ) )

        rs = [ r for r in query.execute( self.h ) ]

        self.assertTrue( self.blue_obj in rs, 'Blue not in result' )
        self.assertTrue( self.green_obj not in rs, 'Green in result' )
        self.assertTrue( self.grey_obj not in rs, 'Grey in result' )

    def test_query_by_parameters( self ):

        query = hdbfs.query.Query()
        query.add_require_constraint( hdbfs.query.ParameterConstraint( 'test', '>=', 2 ) )
        query.add_require_constraint( hdbfs.query.ParameterConstraint( 'test', '<=', 3 ) )

        rs = [ r for r in query.execute( self.h ) ]

        self.assertTrue( self.yellow_obj in rs, 'Yellow not in result' )
        self.assertTrue( self.green_obj in rs, 'Green not in result' )
        self.assertEqual( len( rs ), 2, 'Result size mismatch' )

    def test_query_id_sorted( self ):

        query = hdbfs.query.Query()
        query.add_require_constraint( hdbfs.query.ObjIdConstraint( '>=', 0 ) )

        rs = [ r for r in query.execute( self.h ) ]

        self.assertEqual( rs[0], self.red_obj )
        self.assertEqual( rs[1], self.yellow_obj )
        self.assertEqual( rs[2], self.green_obj )
        self.assertEqual( rs[3], self.cyan_obj )
        self.assertEqual( rs[4], self.blue_obj )
        self.assertEqual( rs[5], self.magenta_obj )
        self.assertEqual( rs[6], self.white_obj )
        self.assertEqual( rs[7], self.grey_obj )
        self.assertEqual( rs[8], self.black_obj )

if( __name__ == '__main__' ):
    unittest.main()
