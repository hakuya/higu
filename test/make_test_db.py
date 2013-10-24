#!/usr/bin/python

import higu
import sys
import os

if( __name__ == '__main__' ):

    ver = tuple( map( int, sys.argv[1].split( '.' ) ) )

    if( ver[0] < 5 ):
        higu.DEFAULT_ENVIRON = os.environ['MKDB_LIB_PATH']
        h = higu.init_default()
    else:
        higu.init( 'build_dbs.cfg' )
        h = higu.Database()

    mo = h.register_file( 'magenta_sq.png' )
    ro = h.register_file( 'red_sq.png' )
    yo = h.register_file( 'yellow_sq.png' )
    go = h.register_file( 'green_sq.png' )
    co = h.register_file( 'cyan_sq.png' )
    bo = h.register_file( 'blue_sq.png' )
    if( ver == ( 1, 0, ) ):
        wo = h.register_file( 'white_sq.png' )
    else:
        wo = h.register_file( 'white_sq.png', add_name = False )
    lo = h.register_file( 'grey_sq.png' )
    ko = h.register_file( 'black_sq.png' )
    ko = h.register_file( 'black_sq2.png' )

    if( ver[0] < 4 ):
        mo.tag( 'colour' )
        ro.tag( 'colour' )
        yo.tag( 'colour' )
        go.tag( 'colour' )
        co.tag( 'colour' )
        bo.tag( 'colour' )

        mo.tag( 'warm' )
        ro.tag( 'warm' )
        yo.tag( 'warm' )
        go.tag( 'cool' )
        co.tag( 'cool' )
        bo.tag( 'cool' )

        wo.tag( 'greyscale' )
        lo.tag( 'greyscale' )
        ko.tag( 'greyscale' )

        wo.tag( 'white' )
        lo.tag( 'grey' )
        ko.tag( 'black' )
    else:
        cl = h.make_tag( 'colour' )
        mo.assign( cl )
        ro.assign( cl )
        yo.assign( cl )
        go.assign( cl )
        co.assign( cl )
        bo.assign( cl )

        wc = h.make_tag( 'warm' )
        mo.assign( wc )
        ro.assign( wc )
        yo.assign( wc )
        cc = h.make_tag( 'cool' )
        go.assign( cc )
        co.assign( cc )
        bo.assign( cc )

        bw = h.make_tag( 'greyscale' )
        wo.assign( bw )
        lo.assign( bw )
        ko.assign( bw )

        wo.assign( h.make_tag( 'white' ) )
        lo.assign( h.make_tag( 'grey' ) )
        ko.assign( h.make_tag( 'black' ) )

    if( ver[0] < 2 ):
        ro.set_parent( mo )
        yo.set_parent( mo )
        go.set_parent( mo )
        co.set_parent( mo )
        bo.set_parent( mo )
    elif( ver[0] < 4 ):
        al = h.create_album()
        al.add_file( mo, 5 )
        al.add_file( ro, 4 )
        al.add_file( yo, 3 )
        al.add_file( go, 2 )
        al.add_file( co, 1 )
        al.add_file( bo, 0 )

        al.register_name( 'colours' )
        al.tag( 'colour_album' )

        al = h.create_album()
        al.add_file( wo )
        al.add_file( bo )

        al.register_name( 'white_and_blue' )
        al.tag( 'white_blue_album' )
    elif( ver[0] < 5 ):
        al = h.create_album()
        mo.assign( al )
        ro.assign( al )
        yo.assign( al )
        go.assign( al )
        co.assign( al )
        bo.assign( al )

        al.register_name( 'colours' )
        al.assign( h.make_tag( 'colour_album' ) )

        al = h.create_album()
        wo.assign( al )
        bo.assign( al )

        al.register_name( 'white_and_blue' )
        al.assign( h.make_tag( 'white_blue_album' ) )
    else:
        al = h.create_album()
        mo.assign( al, 5 )
        ro.assign( al, 4 )
        yo.assign( al, 3 )
        go.assign( al, 2 )
        co.assign( al, 1 )
        bo.assign( al, 0 )

        al.add_name( 'colours' )
        al.assign( h.make_tag( 'colour_album' ) )

        al = h.create_album()
        wo.assign( al )
        bo.assign( al )

        al.add_name( 'white_and_blue' )
        al.assign( h.make_tag( 'white_blue_album' ) )
        al.set_text( 'White & Blue' )

    lo.set_varient_of( wo )
    ko.set_duplicate_of( lo )

    h.commit()

# vim:sts=4:et:sw=4
