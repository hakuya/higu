import unittest
import testutil
import higu

class HiguQueryCases( testutil.TestCase ):

    def setUp( self ):

        self.init_env()

        h = higu.Database()
        h.enable_write_access()

        red_obj = h.register_file( self._load_data( self.red ), False )
        yellow_obj = h.register_file( self._load_data( self.yellow ), False )
        green_obj = h.register_file( self._load_data( self.green ), False )
        cyan_obj = h.register_file( self._load_data( self.cyan ), False )
        blue_obj = h.register_file( self._load_data( self.blue ), False )
        magenta_obj = h.register_file( self._load_data( self.magenta ), False )
        white_obj = h.register_file( self._load_data( self.white ), False )
        grey_obj = h.register_file( self._load_data( self.grey ), False )
        black_obj = h.register_file( self._load_data( self.black ), False )

        warm_tag = h.make_tag( 'warm' )
        cool_tag = h.make_tag( 'cool' )
        rgb_tag = h.make_tag( 'rgb' )
        cmyk_tag = h.make_tag( 'cmyk' )
        paint_tag = h.make_tag( 'paint' )

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

        self.h = higu.Database()

        self.red_obj = self.h.get_object_by_id( red_obj.get_id() )
        self.yellow_obj = self.h.get_object_by_id( yellow_obj.get_id() )
        self.green_obj = self.h.get_object_by_id( green_obj.get_id() )
        self.cyan_obj = self.h.get_object_by_id( cyan_obj.get_id() )
        self.blue_obj = self.h.get_object_by_id( blue_obj.get_id() )
        self.magenta_obj = self.h.get_object_by_id( magenta_obj.get_id() )
        self.white_obj = self.h.get_object_by_id( white_obj.get_id() )
        self.grey_obj = self.h.get_object_by_id( grey_obj.get_id() )
        self.black_obj = self.h.get_object_by_id( black_obj.get_id() )

        self.warm_tag = self.h.get_object_by_id( warm_tag.get_id() )
        self.cool_tag = self.h.get_object_by_id( cool_tag.get_id() )
        self.rgb_tag = self.h.get_object_by_id( rgb_tag.get_id() )
        self.cmyk_tag = self.h.get_object_by_id( cmyk_tag.get_id() )
        self.paint_tag = self.h.get_object_by_id( paint_tag.get_id() )

    def tearDown( self ):

        self.uninit_env()

    def test_query_all( self ):

        rs = [ r for r in self.h.all_albums_or_free_files() ]

        self.assertTrue( self.red_obj in rs, 'Red not in result' )
        self.assertTrue( self.yellow_obj in rs, 'Yellow not in result' )
        self.assertTrue( self.green_obj in rs, 'Green not in result' )
        self.assertTrue( self.cyan_obj in rs, 'Cyan not in result' )
        self.assertTrue( self.blue_obj in rs, 'Blue not in result' )
        self.assertTrue( self.magenta_obj in rs, 'Magenta not in result' )
        self.assertTrue( self.white_obj in rs, 'White not in result' )
        self.assertTrue( self.grey_obj in rs, 'Grey not in result' )
        self.assertTrue( self.black_obj in rs, 'Black not in result' )

        self.assertTrue( len( rs ) == 9, 'Result size mismatch' )

    def test_query_unowned( self ):

        rs = [ r for r in self.h.unowned_files() ]

        self.assertTrue( self.white_obj in rs, 'White not in result' )
        self.assertTrue( self.grey_obj in rs, 'Grey not in result' )

        self.assertTrue( len( rs ) == 2, 'Result size mismatch' )

    def test_query_require( self ):

        rs = [ r for r in self.h.lookup_objects(
            require = [ self.warm_tag, self.paint_tag ] ) ]

        self.assertTrue( self.red_obj in rs, 'Red not in result' )
        self.assertTrue( self.yellow_obj in rs, 'Yellow not in result' )

        self.assertTrue( len( rs ) == 2, 'Result size mismatch' )

    def test_query_add( self ):

        rs = [ r for r in self.h.lookup_objects(
            add = [ self.warm_tag, self.paint_tag ] ) ]

        self.assertTrue( self.red_obj in rs, 'Red not in result' )
        self.assertTrue( self.yellow_obj in rs, 'Yellow not in result' )
        self.assertTrue( self.blue_obj in rs, 'Blue not in result' )
        self.assertTrue( self.magenta_obj in rs, 'Magenta not in result' )

        self.assertTrue( len( rs ) == 4, 'Result size mismatch' )

    def test_query_sub( self ):

        rs = [ r for r in self.h.lookup_objects(
            sub = [ self.warm_tag, self.paint_tag ] ) ]

        self.assertTrue( self.green_obj in rs, 'Green not in result' )
        self.assertTrue( self.cyan_obj in rs, 'Cyan not in result' )
        self.assertTrue( self.white_obj in rs, 'White not in result' )
        self.assertTrue( self.grey_obj in rs, 'Grey not in result' )
        self.assertTrue( self.black_obj in rs, 'Black not in result' )

        self.assertTrue( len( rs ) == 5, 'Result size mismatch' )

    def test_query_add_sub( self ):

        rs = [ r for r in self.h.lookup_objects(
            add = [ self.rgb_tag, self.cmyk_tag ],
            sub = [ self.cool_tag ] ) ]

        self.assertTrue( self.red_obj in rs, 'Red not in result' )
        self.assertTrue( self.yellow_obj in rs, 'Yellow not in result' )
        self.assertTrue( self.magenta_obj in rs, 'Magenta not in result' )
        self.assertTrue( self.black_obj in rs, 'Black not in result' )

        self.assertTrue( len( rs ) == 4, 'Result size mismatch' )

    def test_query_require_add( self ):

        rs = [ r for r in self.h.lookup_objects(
            require = [ self.warm_tag, self.paint_tag ],
            add = [ self.cool_tag ] ) ]

        self.assertTrue( self.red_obj in rs, 'Red not in result' )
        self.assertTrue( self.yellow_obj in rs, 'Yellow not in result' )
        self.assertTrue( self.green_obj in rs, 'Green not in result' )
        self.assertTrue( self.cyan_obj in rs, 'Cyan not in result' )
        self.assertTrue( self.blue_obj in rs, 'Blue not in result' )

        self.assertTrue( len( rs ) == 5, 'Result size mismatch' )

    def test_query_require_add_sub( self ):

        rs = [ r for r in self.h.lookup_objects(
            require = [ self.warm_tag, self.paint_tag ],
            add = [ self.cool_tag ],
            sub = [ self.cmyk_tag ] ) ]

        self.assertTrue( self.red_obj in rs, 'Red not in result' )
        self.assertTrue( self.green_obj in rs, 'Green not in result' )
        self.assertTrue( self.blue_obj in rs, 'Blue not in result' )

        self.assertTrue( len( rs ) == 3, 'Result size mismatch' )

    def test_query_order_add( self ):

        rs = [ r for r in self.h.lookup_objects(
            require = [ self.rgb_tag ],
            order = 'add' ) ]

        self.assertTrue( self.red_obj == rs[0], 'Red not in pos 0' )
        self.assertTrue( self.green_obj == rs[1], 'Green not in pos 1' )
        self.assertTrue( self.blue_obj == rs[2], 'Blue not in pos 2' )

        self.assertTrue( len( rs ) == 3, 'Result size mismatch' )

    def test_query_order_radd( self ):

        rs = [ r for r in self.h.lookup_objects(
            require = [ self.rgb_tag ],
            order = 'add', rsort = True ) ]

        self.assertTrue( self.red_obj == rs[2], 'Red not in pos 2' )
        self.assertTrue( self.green_obj == rs[1], 'Green not in pos 1' )
        self.assertTrue( self.blue_obj == rs[0], 'Blue not in pos 0' )

        self.assertTrue( len( rs ) == 3, 'Result size mismatch' )

if( __name__ == '__main__' ):
    unittest.main()
