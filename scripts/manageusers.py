import sys

import higu.model
import higu.web_session

LEVEL_MAP = {
    'none' : higu.model.ACCESS_LEVEL_NONE,
    'read' : higu.model.ACCESS_LEVEL_READ,
    'edit' : higu.model.ACCESS_LEVEL_EDIT,
    'admin' : higu.model.ACCESS_LEVEL_ADMIN,
}

if( __name__ == '__main__' ):

    import optparse

    parser = optparse.OptionParser( usage = 'Usage: %prog [options] user' )

    parser.add_option( '-c', '--config',
        dest = 'config',
        help = 'Configuration File' )
    parser.add_option( '-r', '--remove',
        dest = 'remove', action = 'store_true', default = False,
        help = 'Remove user' )
    parser.add_option( '-a', '--add',
        dest = 'add', action = 'store_true', default = False,
        help = 'Add user' )
    parser.add_option( '-p', '--password',
        dest = 'password', default = None,
        help = 'Set / Change user password' )
    parser.add_option( '-l', '--level',
        dest = 'level', default = None,
        help = 'Set / Change user access level (none, read, edit, admin)' )

    opts, args = parser.parse_args()

    if( len( args ) < 1 ):
        parser.print_help()
        sys.exit( 0 )

    user = args[0]

    if( len( sys.argv ) > 1 ):
        cfg = higu.config.init( opts.config )
    else:
        cfg = higu.config.init()

    higu.web_session.init( cfg.get_path( 'library' ) )
    access = higu.web_session.WebSessionAccess()

    if( opts.remove ):
        access.drop_user( user )
        sys.exit( 0 )

    elif( opts.add ):
        if( opts.password is None ):
            parser.print_help()
            sys.exit( 0 )

        if( opts.level is None ):
            access_level = higu.model.ACCESS_LEVEL_NONE
        else:
            access_level = LEVEL_MAP[opts.level]

        access.create_user( user, opts.password, access_level )

    else:
        if( opts.password is not None ):
            access.set_password( user, opts.password )

        if( opts.level is not None ):
            access_level = LEVEL_MAP[opts.level]
            access.promote( user, access_level )
