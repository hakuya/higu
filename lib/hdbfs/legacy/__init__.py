import os

import logging
log = logging.getLogger( __name__ )

import pre8
import ver8rules
import imgdb_rules

from hdbfs.db import SqlLiteDatabase
from hdbfs.hash import calculate_details

class HDBFSMigrator:

    def __init__( self, init_schema_callback ):

        self.__init_schema_callback = init_schema_callback

    def determine_schema_info( self, session ):

        try:
            result = session.execute( 'SELECT ver, rev, uuid FROM dbi' ).first()
            return result['ver'], result['rev'], result['uuid']
        except:
            return None, None, None

    def init_schema( self, engine, ver, rev ):

        self.__init_schema_callback( engine, ver, rev )

    def upgrade_schema( self, session, ver, rev ):

        if( ver == 0 ): 
            return pre8.upgrade_from_0_to_1( log, session )
        elif( ver == 1 ):
            return pre8.upgrade_from_1_to_2( log, session )
        elif( ver == 2 ):
            return pre8.upgrade_from_2_to_3( log, session )
        elif( ver == 3 ):
            return pre8.upgrade_from_3_to_4( log, session )
        elif( ver == 4 ):
            return pre8.upgrade_from_4_to_5( log, session )
        elif( ver == 5 ):
            return pre8.upgrade_from_5_to_6( log, session )
        elif( ver == 6 ):
            return pre8.upgrade_from_6_to_7( log, session )
        elif( ver == 7 ):
            return pre8.upgrade_from_7_to_8( log, session )
        elif( ver == 8 and rev == 0 ):
            return ver8rules.upgrade_from_8_to_8_1( log, session )
        elif( ver == 8 ):
            return ver8rules.upgrade_from_8_1_to_9( log, session )
        elif( ver == 9 ):
            return ver8rules.upgrade_from_9_to_10( log, session )
        else:
            raise RuntimeError( 'Incompatible database version for upgrade' )

class ImgDBMigrator:

    def __init__( self, dbpath ):

        self.dbpath = dbpath

    def determine_schema_info( self, session ):

        try:
            result = session.execute( 'SELECT imgdb_ver FROM dbi' ).first()
            if( result is None ):
                return None, None, None

            # Due to a bug in initialization, sometimes version is left
            # NULL
            ver = result['imgdb_ver']
            if( ver is None ):
                ver = 0;

            return ver, 0, None
        except:
            return None, None, None

    def init_schema( self, engine, ver, rev ):

        pass

    def upgrade_schema( self, session, ver, rev ):

        if( ver == 0 ): 
            return imgdb_rules.upgrade_from_0_to_1( log, session, self.dbpath )

# vim:sts=4:et
