import unittest
import tempfile
import shutil
import os

import hdbfs
import higu

class TestCase( unittest.TestCase ):

    data_dir = 'test/data'
    cache_dir = None
    db_cache = None

    red = 'red_sq.png'
    yellow = 'yellow_sq.png'
    green = 'green_sq.png'
    cyan = 'cyan_sq.png'
    blue = 'blue_sq.png'
    magenta = 'magenta_sq.png'
    white = 'white_sq.png'
    grey = 'grey_sq.png'
    black = 'black_sq.png'
    cl_desc = 'cl_sq_desc.txt'
    bw_desc = 'bw_sq_desc.txt'

    red_hash = '92a5cf2c69d16d57c5dde8e0c0d4bdb9d76bc316'
    yellow_hash = 'ca90c86d1621d000f1de2071f766615417298537'
    green_hash = '2cc964f5c885bde996b38a6f0fd8a3b907d038c9'
    cyan_hash = 'ef0495c17ef137143fb3ca403bef657e77d411ae'
    blue_hash = '0ca527049c4e8f2b145e15afbf3d6393473e0178'
    magenta_hash = 'ab8d44c936e2ccfe1c73cde3d7ace31750530442'
    white_hash = 'f5a7cebc04fdd67e746b14b9492eb0cf56d815cf'
    grey_hash = '5c75230de43a5617f7e85f32602ce3866a430e19'
    black_hash = 'c2d1060c9ea2949e327d412778ccda8d31cdb538'

    @classmethod
    def init_cache( cls, cache_init_fn = None ):

        cls.cache_dir = tempfile.mkdtemp()
        cls.db_cache = os.path.join( cls.cache_dir, 'test.db' )

        hdbfs.init( cls.db_cache )

        if( cache_init_fn is not None ):
            cache_init_fn()

        hdbfs.dispose()

    @classmethod
    def uninit_cache( cls ):

        if( cls.db_cache is not None ):
            shutil.rmtree( cls.cache_dir )
            cls.cache_dir = None

    def init_env( self, do_init = True, web_init = False ):

        self.work_dir = tempfile.mkdtemp()
        self.cfg_file_path = os.path.join( self.work_dir, 'test.cfg' )
        self.db_path = os.path.join( self.work_dir, 'test.db' )
        self.web_db = os.path.join( self.work_dir, 'web.db' )

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

        if( self.db_cache is not None ):
            shutil.copytree( self.db_cache, self.db_path )

        hdbfs.init( self.db_path )

    @classmethod
    def _data_path( cls, fname ):

        return os.path.join( cls.data_dir, fname )

    @classmethod
    def _load_cache( cls, fname, tname = None ):

        src = cls._data_path( fname )
        tgt = os.path.join( cls.cache_dir, tname if tname is not None else fname )

        shutil.copy( src, tgt )

        return tgt

    def _load_data( self, fname: str, tname: str = None ) -> str:
        '''Loads the file with name fname into the work directory. If tname
        is provided, then it will be named as tname in the work directory.

        The full path to the file in the work directory will be returned.
        '''

        src = self._data_path( fname )
        tgt = os.path.join( self.work_dir, tname if tname is not None else fname )

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

