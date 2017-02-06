from sqlalchemy import *
from sqlalchemy import event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, backref, sessionmaker, scoped_session
from sqlalchemy.ext.associationproxy import association_proxy

import calendar
import numbers
import re
import time
import threading
import uuid

Base = declarative_base()

ACCESS_LEVEL_NONE = 0
ACCESS_LEVEL_READ = 1
ACCESS_LEVEL_EDIT = 2
ACCESS_LEVEL_ADMIN = 3

class User( Base ):
    __tablename__ = 'users'

    user_id = Column( Integer, primary_key = True )
    user_name = Column( Text, nullable = False )
    password_hash = Column( Text, nullable = False )
    access_level = Column( Integer, nullable = False, default = ACCESS_LEVEL_NONE )
    can_logon = Column( Integer )

    def __init__( self, user_name, password_hash ):

        self.user_name = user_name
        self.password_hash = password_hash

    def __repr__( self ):

        return 'User( %r, %r, %r, %r, %r, %r )' % (
                self.user_id, self.user_name,
                self.can_admin, self.can_logon,
                self.child, self.parent, self.sort )

class Session( Base ):
    __tablename__ = 'sessions'

    session_id = Column( Text, primary_key = True )
    user_id = Column( Integer, ForeignKey( 'users.user_id' ) )
    expires_time = Column( Integer, nullable = False )
    access_level = Column( Integer, nullable = False, default = ACCESS_LEVEL_NONE )

    user = relation( 'User', backref = backref( 'sessions', lazy = 'dynamic' ) )

    def __init__( self, expires_time ):

        self.session_id = str( uuid.uuid1() )
        self.user_id = None
        self.expires_time = expires_time
        self.access_level = ACCESS_LEVEL_NONE

    def __repr__( self ):

        return 'Session( %r, %r, %r, %r )' % (
            self.session_id, self.user_id,
            self.expires_time, self.access_level )

DBSession = None
dbfile = None

class WebMigrator:

    def __init__( self ):

        pass

    def determine_schema_info( self, session ):

        return None, None, None

    def init_schema( self, engine, ver, rev ):

        Base.metadata.create_all( engine )

    def upgrade_schema( self, session, ver, rev ):

        assert False

def init( database_file ):
    global dbfile
    global DBSession

    import hdbfs.db_utils

    migrators = {
        'higu_web' : WebMigrator(),
    }

    dbfile = hdbfs.db_utils.DatabaseFile( database_file, migrators )
    dbfile.init()
    dbfile.init_schema( 'higu_web', 1, 0 )

    DBSession = dbfile.get_session

def dispose():
    global dbfile
    global DBSession

    if( dbfile is not None ):
        DBSession = None
        dbfile.dispose()
        dbfile = None
