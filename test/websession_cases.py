import unittest
import testutil
import shutil
import os

import higu

class WebSessionCases( testutil.TestCase ):

    def setUp( self ):

        self.init_env( do_init = False, web_init = True )

    def tearDown( self ):

        self.uninit_env()

    def test_add_session( self ):

        access = higu.web_session.WebSessionAccess()

        session_id = access.begin_session()
        level, user_name = access.get_session_info( session_id )

        self.assertEqual( level, higu.model.ACCESS_LEVEL_NONE,
                          'Unexpected access level' )
        self.assertEqual( user_name, None,
                          'Unexpected user name' )

    def test_create_user( self ):

        access = higu.web_session.WebSessionAccess()

        self.assertTrue( access.create_user(
                            'testuser', 'passwd', higu.model.ACCESS_LEVEL_READ ),
                         'Failed adding user' )

        session_id = access.begin_session()
        self.assertTrue( access.login( session_id, 'testuser', 'passwd' ),
                         'Failed loging in' )

        level, user_name = access.get_session_info( session_id )
        self.assertEqual( level, higu.model.ACCESS_LEVEL_READ,
                          'Unexpected access level' )
        self.assertEqual( user_name, 'testuser',
                          'Unexpected user name' )

        access.logout( session_id )

        level, user_name = access.get_session_info( session_id )
        self.assertEqual( level, higu.model.ACCESS_LEVEL_NONE,
                          'Unexpected access level' )
        self.assertEqual( user_name, None,
                          'Unexpected user name' )

    def test_drop_user( self ):

        access = higu.web_session.WebSessionAccess()

        self.assertTrue( access.create_user(
                            'testuser', 'passwd', higu.model.ACCESS_LEVEL_READ ),
                         'Failed adding user' )

        session_id = access.begin_session()
        self.assertTrue( access.login( session_id, 'testuser', 'passwd' ),
                         'Failed loging in' )

        level, user_name = access.get_session_info( session_id )
        self.assertEqual( level, higu.model.ACCESS_LEVEL_READ,
                          'Unexpected access level' )
        self.assertEqual( user_name, 'testuser',
                          'Unexpected user name' )

        access.drop_user( 'testuser' )

        level, user_name = access.get_session_info( session_id )
        self.assertEqual( level, higu.model.ACCESS_LEVEL_NONE,
                          'Unexpected access level' )
        self.assertEqual( user_name, None,
                          'Unexpected user name' )

        session_id = access.begin_session()
        self.assertFalse( access.login( session_id, 'testuser', 'passwd' ),
                         'Shouldn\'t have logged in' )

    def test_set_password( self ):

        access = higu.web_session.WebSessionAccess()

        self.assertTrue( access.create_user(
                            'testuser', 'passwd', higu.model.ACCESS_LEVEL_READ ),
                         'Failed adding user' )

        session_id = access.begin_session()
        self.assertTrue( access.login( session_id, 'testuser', 'passwd' ),
                         'Failed loging in' )

        level, user_name = access.get_session_info( session_id )
        self.assertEqual( level, higu.model.ACCESS_LEVEL_READ,
                          'Unexpected access level' )
        self.assertEqual( user_name, 'testuser',
                          'Unexpected user name' )

        access.set_password( 'testuser', 'newpasswd' )

        level, user_name = access.get_session_info( session_id )
        self.assertEqual( level, higu.model.ACCESS_LEVEL_READ,
                          'Unexpected access level' )
        self.assertEqual( user_name, 'testuser',
                          'Unexpected user name' )

        session_id2 = access.begin_session()

        self.assertFalse( access.login( session_id2, 'testuser', 'passwd' ),
                         'Shouldn\'t have logged in' )
        self.assertTrue( access.login( session_id2, 'testuser', 'newpasswd' ),
                         'Failed loging in' )

    def test_fail_login( self ):

        access = higu.web_session.WebSessionAccess()

        self.assertTrue( access.create_user( 'testuser', 'passwd' ),
                         'Failed adding user' )

        session_id = access.begin_session()
        self.assertFalse( access.login( session_id, 'testuser', 'wrong' ),
                         'Login should have failed' )

        level, user_name = access.get_session_info( session_id )
        self.assertEqual( level, higu.model.ACCESS_LEVEL_NONE,
                          'Unexpected access level' )
        self.assertEqual( user_name, None,
                          'Unexpected user name' )

    def test_prompote( self ):

        access = higu.web_session.WebSessionAccess()

        self.assertTrue( access.create_user(
                            'testuser', 'passwd', higu.model.ACCESS_LEVEL_READ ),
                         'Failed adding user' )

        self.assertTrue( access.promote( 'testuser', higu.model.ACCESS_LEVEL_EDIT ),
                         'Unexpected promote failure' )

        session_id = access.begin_session()
        self.assertTrue( access.login( session_id, 'testuser', 'passwd' ),
                         'Failed loging in' )

        level, user_name = access.get_session_info( session_id )
        self.assertEqual( level, higu.model.ACCESS_LEVEL_EDIT,
                          'Unexpected access level' )
        self.assertEqual( user_name, 'testuser',
                          'Unexpected user name' )

    def test_promote_live( self ):

        access = higu.web_session.WebSessionAccess()

        self.assertTrue( access.create_user(
                            'testuser', 'passwd', higu.model.ACCESS_LEVEL_READ ),
                         'Failed adding user' )

        session_id = access.begin_session()

        self.assertTrue( access.login( session_id, 'testuser', 'passwd' ),
                         'Failed loging in' )

        level, user_name = access.get_session_info( session_id )
        self.assertEqual( level, higu.model.ACCESS_LEVEL_READ,
                          'Unexpected access level' )
        self.assertEqual( user_name, 'testuser',
                          'Unexpected user name' )

        self.assertTrue( access.promote( 'testuser', higu.model.ACCESS_LEVEL_EDIT ),
                         'Unexpected promote failure' )

        level, user_name = access.get_session_info( session_id )
        self.assertEqual( level, higu.model.ACCESS_LEVEL_EDIT,
                          'Unexpected access level' )
        self.assertEqual( user_name, 'testuser',
                          'Unexpected user name' )

if( __name__ == '__main__' ):
    unittest.main()
