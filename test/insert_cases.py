import unittest
import testutil
import subprocess
import shutil
import os
import higu

class InsertCases( testutil.TestCase ):

    def setUp( self ):

        self.init_env()

    def tearDown( self ):

        self.uninit_env()

    def _run( self, files, album = None, text = None, taglist = [],
            newtags = [], recover = None, name = None ):

        cmd = [ 'python', 'lib/insertfile.py', '-c', self.cfg_file_path ]

        if( album is not None ):
            cmd.append( '-a' )

            if( len( album ) == 0 ):
                cmd.append( '-' )
            else:
                cmd.append( album )

        if( text is not None ):
            cmd.append( '-x' )
            cmd.append( text )

        if( len( taglist ) > 0 ):
            tags = ','.join( taglist )

            cmd.append( '-t' )
            cmd.append( tags )

        if( len( newtags ) > 0 ):
            tags = ','.join( newtags )

            cmd.append( '-T' )
            cmd.append( tags )

        if( recover is not None ):
            cmd.append( '-r' )

        if( name is not None ):
            if( name ):
                cmd.append( '-N' )
            else:
                cmd.append( '-n' )

        if( isinstance( files, str ) ):
            cmd.append( files )
        else:
            cmd.extend( files )

        subprocess.check_call( cmd )

    def test_add( self ):

        black = self._load_data( self.black )
        self._run( black )

        self.assertFalse( os.path.exists( black ),
                'Old image was not removed' )

        h = higu.Database()
        obj = h.get_object_by_id( 1 )

        self.assertFalse( obj is None,
                'Image not in DB' )

    def test_double_add( self ):

        black = self._load_data( self.black )
        self._run( black )

        self.assertFalse( os.path.exists( black ),
                'Old image was not removed' )

        black = self._load_data( self.black )
        self._run( black )

        self.assertTrue( os.path.exists( black ),
                'Double image was removed' )

        h = higu.Database()
        obj = h.get_object_by_id( 1 )

        self.assertFalse( obj is None,
                'Image not in DB' )

    def test_recover_not_in_db( self ):

        black = self._load_data( self.black )
        self._run( black, recover = True )

        self.assertTrue( os.path.exists( black ),
                'Image was removed' )

        h = higu.Database()
        obj = h.get_object_by_id( 1 )

        self.assertTrue( obj is None,
                'Image in DB' )

    def test_recover_ok_file( self ):

        black = self._load_data( self.black )
        self._run( black )

        self.assertFalse( os.path.exists( black ),
                'Old image was not removed' )

        black = self._load_data( self.black )
        self._run( black, recover = True )

        self.assertTrue( os.path.exists( black ),
                'Recovery image was removed' )

    def test_recover_missing_file( self ):

        black = self._load_data( self.black )
        self._run( black )

        h = higu.Database()
        obj = h.get_object_by_id( 1 )

        self.assertFalse( obj is None,
                'Image not in DB' )

        h.imgdb.delete( obj.get_id() )
        h.imgdb.commit()

        img_fd = obj.read()
        self.assertFalse( img_fd is not None,
                'Remove failed' )

        black = self._load_data( self.black )
        self._run( black, recover = True )

        self.assertTrue( self._diff_data( obj.read(), self.black ),
                'Image not recovered' )

        self.assertFalse( os.path.exists( black ),
                'Recovery image was not removed' )

    def test_no_name( self ):

        black = self._load_data( self.black )
        self._run( black, name = False )

        h = higu.Database()
        obj = h.get_object_by_id( 1 )

        self.assertFalse( obj is None,
                'Image not in DB' )
        self.assertNotEqual( obj.get_name(), self.black,
                'Name loaded' )

    def test_name( self ):

        black = self._load_data( self.black )
        self._run( black )

        h = higu.Database()
        obj = h.get_object_by_id( 1 )

        self.assertFalse( obj is None,
                'Image not in DB' )
        self.assertEqual( obj.get_name(), self.black,
                'Name not loaded' )

    def test_name2( self ):

        black = self._load_data( self.black )
        self._run( black, name = True )

        h = higu.Database()
        obj = h.get_object_by_id( 1 )

        self.assertFalse( obj is None,
                'Image not in DB' )
        self.assertEqual( obj.get_name(), self.black,
                'Name not loaded' )

    def test_different_names( self ):

        black = self._load_data( self.black )
        self._run( black )

        black2 = self._load_data( self.black, 'altname.png' )
        self._run( black2 )

        h = higu.Database()
        obj = h.get_object_by_id( 1 )

        self.assertFalse( obj is None,
                'Image not in DB' )

        names = obj.get_names()
        self.assertTrue( self.black in names,
                'First name not loaded' )
        self.assertTrue( 'altname.png' in names,
                'Second name not loaded' )
        self.assertEqual( len( obj.get_names() ), 2,
                'Name count does not match' )

    def test_load_name( self ):

        black = self._load_data( self.black )
        self._run( black, name = False )

        h = higu.Database()
        obj = h.get_object_by_id( 1 )

        self.assertFalse( obj is None,
                'Image not in DB' )

        self.assertNotEqual( obj.get_name(), self.black,
                'Name loaded when it shouldn\'t have been' )

        h.close()

        black = self._load_data( self.black )
        self._run( black, name = True )

        h = higu.Database()
        obj = h.get_object_by_id( 1 )

        self.assertEqual( obj.get_name(), self.black,
                'name not loaded' )

    def test_tag_file( self ):

        h = higu.Database()
        h.enable_write_access()

        tag = h.make_tag( 'black' )

        files = tag.get_files()
        self.assertEqual( len( files ), 0,
                'Unexpected number of files' )

        h.close()

        black = self._load_data( self.black )
        self._run( black, taglist = [ 'black' ] )

        h = higu.Database()
        tag = h.get_tag( 'black' )

        files = tag.get_files()
        self.assertEqual( len( files ), 1,
                'Unexpected number of files' )

    def test_create_tag( self ):

        h = higu.Database()

        black = self._load_data( self.black )
        self._run( black, newtags = [ 'black' ] )

        h = higu.Database()
        try:
            tag = h.get_tag( 'black' )
        except KeyError:
            self.fail( 'Failed creating tag' )
        except StopIteration:
            pass

        files = tag.get_files()
        self.assertEqual( len( files ), 1,
                'Unexpected number of files' )

    def test_tag_multi_file( self ):

        h = higu.Database()
        h.enable_write_access()

        h.make_tag( 'magenta' )
        h.make_tag( 'yellow' )
        h.make_tag( 'cyan' )
        h.close()

        red = self._load_data( self.red )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        self._run( red, taglist = [ 'magenta', 'yellow' ] )
        self._run( green, taglist = [ 'yellow', 'cyan' ] )
        self._run( blue, taglist = [ 'magenta', 'cyan' ] )

        h = higu.Database()
        mt = h.get_tag( 'magenta' )
        yt = h.get_tag( 'yellow' )
        ct = h.get_tag( 'cyan' )

        ro = h.get_object_by_id( 4 )
        go = h.get_object_by_id( 5 )
        bo = h.get_object_by_id( 6 )

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

    def test_make_album( self ):

        white = self._load_data( self.white )
        grey = self._load_data( self.grey )
        black = self._load_data( self.black )

        self._run( [ white, grey, black ], album = 'bw' )

        h = higu.Database()
        al = h.get_object_by_id( 1 )
        wo = h.get_object_by_id( 2 )
        lo = h.get_object_by_id( 3 )
        ko = h.get_object_by_id( 4 )

        self.assertTrue( isinstance( al, higu.Album ),
                'Expected album' )

        files = al.get_files()
        self.assertTrue( wo in files, 
                'White not in album' )
        self.assertTrue( lo in files, 
                'Grey not in album' )
        self.assertTrue( ko in files, 
                'Black not in album' )

    def test_tag_album( self ):

        h = higu.Database()
        h.enable_write_access()
        tag = h.make_tag( 'bw' )
        h.close()

        white = self._load_data( self.white )
        grey = self._load_data( self.grey )
        black = self._load_data( self.black )

        self._run( [ white, grey, black ], album = 'bw', taglist = [ 'bw' ] )

        h = higu.Database()
        al = h.get_object_by_id( 2 )
        wo = h.get_object_by_id( 3 )
        lo = h.get_object_by_id( 4 )
        ko = h.get_object_by_id( 5 )

        self.assertTrue( isinstance( al, higu.Album ),
                'Expected album' )

        it = h.lookup_objects( [ h.get_tag( 'bw' ) ] ).__iter__()

        self.assertEqual( it.next(), al,
                'Unexpected tagged item' )

        try:
            it.next()
            self.fail( 'Unexpected tagged item' )
        except StopIteration:
            pass

    def test_album_text( self ):

        white = self._load_data( self.white )
        grey = self._load_data( self.grey )
        black = self._load_data( self.black )
        bw_desc = self._load_data( self.bw_desc )

        self._run( [ white, grey, black ], album = 'bw', text = bw_desc )

        h = higu.Database()
        al = h.lookup_objects( type = higu.TYPE_ALBUM ).__iter__().next()

        self.assertTrue( isinstance( al, higu.Album ),
                'Expected album' )

        textf = open( bw_desc, 'r' )
        text = textf.read( 256 )
        textf.close()

        self.assertEqual( text, al.get_text(),
                'Text not loaded' )

if( __name__ == '__main__' ):
    unittest.main()
