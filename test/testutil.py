import unittest
import tempfile
import shutil
import os

import hdbfs

class TestCase( unittest.TestCase ):

    def init_env( self, do_init = True ):

        self.data_dir = 'test/data'
        self.work_dir = tempfile.mkdtemp()
        self.cfg_file_path = os.path.join( self.work_dir, 'test.cfg' )
        self.db_path = os.path.join( self.work_dir, 'test.db' )

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

    def uninit_env( self ):

        hdbfs.dispose()
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

