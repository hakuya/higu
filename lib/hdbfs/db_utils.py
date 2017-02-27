import os
import uuid

import logging
log = logging.getLogger( __name__ )

from sqlalchemy import *
from sqlalchemy import event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, backref, sessionmaker, scoped_session
from sqlalchemy.exc import OperationalError

Base = declarative_base()

class Schema( Base ):
    __tablename__ = 'db_schema'

    uuid = Column( Text, primary_key = True )
    schema = Column( Text, nullable = False )
    ver = Column( Integer, nullable = False )
    rev = Column( Integer, nullable = False )

    def __init__( self, schema, ver, rev, _uuid = None ):

        if( _uuid is None ):
            self.uuid = str( uuid.uuid1() )
        else:
            self.uuid = _uuid

        self.schema = schema
        self.ver = ver
        self.rev = rev

    def __repr__( self ):

        return 'Schema( %r, %r, %r, %r )' % ( self.uuid, self.schema, self.ver, self.rev )

def _do_sqlite_connect( dbapi_conn, conn_record ):
    # Disable python's auto BEGIN/COMMIT
    dbapi_conn.isolation_level = None
    dbapi_conn.execute( 'PRAGMA busy_timeout = 10000' )

class DatabaseFile:

    def __init__( self, database_file, migrators = {} ):

        self.__file = database_file
        self.__engine = None
        self.__Session = None
        self.__migrators = migrators

    def __get_schema_version( self, session, schema ):

        info = session.query( Schema ).filter( Schema.schema == schema ).first()

        if( info is None ):
            ver, rev, uuid = self.__migrators[schema].determine_schema_info( session )

            if( ver is None ):
                return None, None

            info = Schema( schema, ver, rev, uuid )
            session.add( info )

        return info.ver, info.rev

    def get_schema_version( self, schema ):

        s = self.get_session()

        try:
            result = self.__get_schema_version( s, schema )
            s.commit()
            return result
        finally:
            s.close()

    def set_schema_version( self, schema, ver, rev ):

        s = self.get_session()

        try:
            s.execute( 'BEGIN EXCLUSIVE' )

            info = s.query( Schema ).filter( Schema.schema == schema ).first()
            if( info is not None ):
                info.ver = ver
                info.rev = rev
            else:
                info = Schema( schema, ver, rev )
                s.add( info )

            s.commit()
        finally:
            s.close()

    def backup( self ):

        with file( self.__file, 'rb' ) as f:
            n = 0
            while( 1 ):
                if( not os.path.isfile( self.__file + '.bak' + str( n ) ) ):
                    break
                n += 1
            with file( self.__file + '.bak' + str( n ), 'wb' ) as g:
                while( 1 ):
                    buff = f.read( 1024 )
                    if( len( buff ) == 0 ):
                        f.close()
                        g.close()
                        break
                    g.write( buff )

    def init( self ):

        self.__engine = create_engine( 'sqlite:///' + self.__file )
        event.listen( self.__engine, 'connect', _do_sqlite_connect )

        Base.metadata.create_all( self.__engine )

        self.__Session = scoped_session( sessionmaker( bind = self.__engine ) )

    def init_schema( self, schema, target_ver, target_rev ):

        ver, rev = self.get_schema_version( schema )

        if( ver is None ):
            self.__migrators[schema].init_schema( self.__engine, target_ver, target_rev )
            self.set_schema_version( schema, target_ver, target_rev )
        elif( ver > target_ver ):
            assert False, 'Unsupported schema version'
        elif( ver != target_ver or rev != target_rev ):
            self.backup()

            s = self.get_session()
            try:
                m = self.__migrators[schema]
                s.execute( 'BEGIN EXCLUSIVE' )

                while( ver != target_ver or rev != target_rev ):
                    new_ver, new_rev = m.upgrade_schema( s, ver, rev )
                    assert new_ver > ver or (new_ver == ver and new_rev > rev)
                    ver, rev = new_ver, new_rev

                info = s.query( Schema ).filter( Schema.schema == schema ).first()
                info.ver = ver
                info.rev = rev

                s.commit()
            finally:
                s.close()

    def dispose( self ):

        self.__Session = None
        self.__engine.dispose()
        self.__engine = None

    def get_engine( self ):

        return self.__engine

    def get_session( self ):

        return self.__Session()
