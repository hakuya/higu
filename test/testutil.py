import unittest
import tempfile
import shutil
import os

import hdbfs
import higu

class TestCase( unittest.TestCase ):

    def init_env( self, do_init = True, web_init = False ):

        self.data_dir = 'test/data'
        self.work_dir = tempfile.mkdtemp()
        self.cfg_file_path = os.path.join( self.work_dir, 'test.cfg' )
        self.db_path = os.path.join( self.work_dir, 'test.db' )
        self.web_db = os.path.join( self.work_dir, 'web.db' )

        self.red = 'red_sq.png'
        self.yellow = 'yellow_sq.png'
        self.green = 'green_sq.png'
        self.cyan = 'cyan_sq.png'
        self.blue = 'blue_sq.png'
        self.magenta = 'magenta_sq.png'
        self.white = 'white_sq.png'
        self.grey = 'grey_sq.png'
        self.black = 'black_sq.png'
        self.cl_desc = 'cl_sq_desc.txt'
        self.bw_desc = 'bw_sq_desc.txt'

        self.red_hash = '92a5cf2c69d16d57c5dde8e0c0d4bdb9d76bc316'
        self.yellow_hash = 'ca90c86d1621d000f1de2071f766615417298537'
        self.green_hash = '2cc964f5c885bde996b38a6f0fd8a3b907d038c9'
        self.cyan_hash = 'ef0495c17ef137143fb3ca403bef657e77d411ae'
        self.blue_hash = '0ca527049c4e8f2b145e15afbf3d6393473e0178'
        self.magenta_hash = 'ab8d44c936e2ccfe1c73cde3d7ace31750530442'
        self.white_hash = 'f5a7cebc04fdd67e746b14b9492eb0cf56d815cf'
        self.grey_hash = '5c75230de43a5617f7e85f32602ce3866a430e19'
        self.black_hash = 'c2d1060c9ea2949e327d412778ccda8d31cdb538'

        cfg_file = open( self.cfg_file_path, 'w' )
        cfg_file.write( '[main]\n' )
        cfg_file.write( 'library = %s\n' % ( self.db_path ) )
        cfg_file.write( '\n' )
        cfg_file.write( '[www]\n' )
        cfg_file.write( 'host = localhost\n' )
        cfg_file.write( 'port = 60080\n' )
        cfg_file.close()


        if( do_init ):
            self._init_hdbfs()

        if( web_init ):
            higu.model.init( self.web_db )

    def uninit_env( self ):

        hdbfs.dispose()
        higu.model.dispose()
        shutil.rmtree( self.work_dir )

    def _init_hdbfs( self ):

        hdbfs.init( self.db_path )

    def _data_path( self, fname ):

        return os.path.join( self.data_dir, fname )

    def _load_data( self, fname, tname = None ):

        src = self._data_path( fname )
        if( tname is None ):
            tgt = os.path.join( self.work_dir, fname )
        else:
            tgt = os.path.join( self.work_dir, tname )

        shutil.copy( src, tgt )

        return tgt

    def _diff_data( self, f, data ):

        return self._diff( f, self._data_path( data ) )

    def _diff( self, f1, f2 ):

        if( isinstance( f1, str ) ):
            if( not os.path.isfile( f1 ) ):
                return False

            f1 = open( f1, 'rb' )

        if( isinstance( f2, str ) ):
            if( not os.path.isfile( f2 ) ):
                return False

            f2 = open( f2, 'rb' )

        try:
            while True:
                d1 = f1.read( 4096 )
                d2 = f2.read( 4096 )

                if( d1 != d2 ):
                    return False

                if( len( d1 ) == 0 ):
                    return True
        finally:
            f1.close()
            f2.close()

