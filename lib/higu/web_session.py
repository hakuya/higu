import bcrypt
import calendar
import os
import time

import model

WEB_SESSION_DB_NAME = 'websdb.dat'

DEFAULT_EXPIRY_SECS = 60 * 60

class WebSessionAccess:

    def __init__( self ):

        self.__db_session = model.DBSession()

    def __update_sessions( self ):

        now = calendar.timegm( time.gmtime() )
        self.__db_session.query( model.Session ) \
                .filter( model.Session.expires_time <= now ) \
                .delete()

        return now + DEFAULT_EXPIRY_SECS

    def begin_session( self ):

        return self.renew_session( None )

    def renew_session( self, session_id ):

        self.__db_session.execute( 'BEGIN EXCLUSIVE' )

        try:
            expires = self.__update_sessions()
            if( session_id is not None ):
                session = self.__db_session.query( model.Session ) \
                        .filter( model.Session.session_id == session_id ) \
                        .first()
            else:
                session = None

            if( session is None ):
                session = model.Session( expires )
                self.__db_session.add( session )

            session_id = session.session_id

            self.__db_session.commit()
            return session_id
        except:
            self.__db_session.rollback()
            raise

    def get_session_info( self, session_id ):

        self.__db_session.execute( 'BEGIN EXCLUSIVE' )

        try:
            expires = self.__update_sessions()
            session = self.__db_session.query( model.Session ) \
                    .filter( model.Session.session_id == session_id ) \
                    .first()

            if( session is not None ):
                session.expires_time = expires
                access_level = session.access_level
                if( session.user is not None ):
                    user_name = session.user.user_name
                else:
                    user_name = None
            else:
                access_level = model.ACCESS_LEVEL_NONE
                user_name = None

            self.__db_session.commit()
            return access_level, user_name
        except:
            self.__db_session.rollback()
            raise

    def login( self, session_id, user_name, password ):

        self.__db_session.execute( 'BEGIN EXCLUSIVE' )

        try:
            expires = self.__update_sessions()
            session = self.__db_session.query( model.Session ) \
                    .filter( model.Session.session_id == session_id ) \
                    .first()

            user_info = self.__db_session.query( model.User ) \
                    .filter( model.User.user_name == user_name ) \
                    .first()

            if( session is None or user_info is None ):
                self.__db_session.commit()
                return False

            if( bcrypt.hashpw( password, user_info.password_hash ) == user_info.password_hash ):
                session.user_id = user_info.user_id
                session.access_level = user_info.access_level
                session.expires_time = expires
                self.__db_session.commit()
                return True
            else:
                self.__db_session.commit()
                return False

        except:
            self.__db_session.rollback()
            raise

    def logout( self, session_id ):

        self.__db_session.execute( 'BEGIN EXCLUSIVE' )

        try:
            expires = self.__update_sessions()
            session = self.__db_session.query( model.Session ) \
                    .filter( model.Session.session_id == session_id ) \
                    .first()

            if( session is None ):
                self.__db_session.commit()
                return

            session.user_id = None
            session.access_level = model.ACCESS_LEVEL_NONE
            session.expires_time = expires
            self.__db_session.commit()

        except:
            self.__db_session.rollback()
            raise


    def create_user( self, user_name, password, access_level = model.ACCESS_LEVEL_NONE ):

        self.__db_session.execute( 'BEGIN EXCLUSIVE' )

        try:
            user_info = self.__db_session.query( model.User ) \
                    .filter( model.User.user_name == user_name ) \
                    .first()

            if( user_info is not None ):
                self.__db_session.commit()
                return False

            password_hash = bcrypt.hashpw( password, bcrypt.gensalt( 14 ) )
            user_info = model.User( user_name, password_hash )
            user_info.access_level = access_level

            self.__db_session.add( user_info )
            self.__db_session.commit()
            return True

        except:
            self.__db_session.rollback()
            raise

    def drop_user( self, user_name ):

        self.__db_session.execute( 'BEGIN EXCLUSIVE' )

        try:
            user_info = self.__db_session.query( model.User ) \
                    .filter( model.User.user_name == user_name ) \
                    .first()

            if( user_info is None ):
                self.__db_session.commit()
                return

            self.__db_session.query( model.Session ) \
                    .filter( model.Session.user_id == user_info.user_id ) \
                    .update( { model.Session.access_level : model.ACCESS_LEVEL_NONE,
                               model.Session.user_id : None } )

            self.__db_session.delete( user_info )

            self.__db_session.commit()

        except:
            self.__db_session.rollback()
            raise

    def set_password( self, user_name, password ):

        self.__db_session.execute( 'BEGIN EXCLUSIVE' )

        try:
            user_info = self.__db_session.query( model.User ) \
                    .filter( model.User.user_name == user_name ) \
                    .first()

            if( user_info is None ):
                self.__db_session.commit()
                return False

            user_info.password_hash = bcrypt.hashpw( password, bcrypt.gensalt( 14 ) )

            self.__db_session.commit()
            return True

        except:
            self.__db_session.rollback()
            raise

    def promote( self, user_name, access_level ):

        self.__db_session.execute( 'BEGIN EXCLUSIVE' )

        try:
            user_info = self.__db_session.query( model.User ) \
                    .filter( model.User.user_name == user_name ) \
                    .first()

            if( user_info is None ):
                self.__db_session.commit()
                return False

            user_info.access_level = access_level

            self.__db_session.query( model.Session ) \
                    .filter( model.Session.user_id == user_info.user_id ) \
                    .update( { model.Session.access_level : access_level } )

            self.__db_session.commit()
            return True

        except:
            self.__db_session.rollback()
            raise

def init( library_path ):

    model.init( os.path.join( library_path, WEB_SESSION_DB_NAME ) )

def dispose():

    model.dispose()
