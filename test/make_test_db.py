#!/usr/bin/python

import sys
import os

if( __name__ == '__main__' ):

    ver = tuple( map( int, sys.argv[1].split( '.' ) ) )

    hdbfs = None
    if( ver[0] > 8 or ver[0] == 8 and ver[1] > 0 ):
        import hdbfs
    else:
        import higu
        hdbfs = higu

    if( ver[0] >= 5 ):
        hdbfs.ark.MIN_THUMB_EXP = 2

    if( ver[0] < 5 ):
        hdbfs.DEFAULT_ENVIRON = os.environ['MKDB_LIB_PATH']
        h = hdbfs.init_default()
    elif( ver[0] < 8 or ver[0] == 8 and ver[1] == 0 ):
        hdbfs.init( 'build_dbs.cfg' )
        h = hdbfs.Database()
    else:
        hdbfs.init( os.environ['MKDB_LIB_PATH'] )
        h = hdbfs.Database()

    if( ver[0] >= 8 ):
        h.enable_write_access()

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
    lo = h.register_file( 'grey_sq2.png' )
    ko = h.register_file( 'black_sq.png' )

    if( ver[0] > 7 ):
        wo.rotate( 1 )

    if( ver[0] < 5 ):
        pass
    elif( ver[0] < 10 ):
        if( ver[0] < 8 ):
            # Old versions of the database don't move the image files until
            # commit is called. This causes read_thumb() to fail
            h.commit()

        wo.read_thumb( 10 )
        lo.read_thumb( 3 )
        lo.read_thumb( 4 )
        ko.read_thumb( 3 )
        ko.read_thumb( 4 )
    else:
        wo.get_thumb_stream( 10 )
        lo.get_thumb_stream( 3 )
        lo.get_thumb_stream( 4 )
        ko.get_thumb_stream( 3 )
        ko.get_thumb_stream( 4 )

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

        ro.tag( 'red' )
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

        ro.assign( h.make_tag( 'red' ) )
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

    if( ver[0] > 8 or ver[0] == 8 and ver[1] > 0 ):
        lo.set_variant_of( wo )
        bo.set_variant_of( ko )
    else:
        lo.set_varient_of( wo )
        bo.set_varient_of( ko )

    ko.set_duplicate_of( lo )

    if( ver[0] < 8 ):
        h.commit()

# vim:sts=4:et:sw=4
