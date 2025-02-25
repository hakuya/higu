#!/usr/bin/python

import sys
import os

ver = None
hdbfs = None

BASE_TIMESTAMP = 1740448453

def set_timestamp( offset ):

    if( ver[0] < 15 ):
        return

    from hdbfs.model import debug_set_timestamp
    debug_set_timestamp( BASE_TIMESTAMP + offset )

def make_db( h ):

    set_timestamp( 0 )

    mo = h.register_file( 'magenta_sq.png' )
    ro = h.register_file( 'red_sq.png' )
    yo = h.register_file( 'yellow_sq.png' )
    go = h.register_file( 'green_sq.png' )
    co = h.register_file( 'cyan_sq.png' )

    set_timestamp( 5 )

    if( ver == ( 1, 0, ) ):
        wo = h.register_file( 'white_sq.png' )
    elif( ver[0] < 10 ):
        wo = h.register_file( 'white_sq.png', add_name = False )
    else:
        wo = h.register_file( 'white_sq.png', name_policy = hdbfs.NAME_POLICY_DONT_REGISTER )
    lo = h.register_file( 'grey_sq.png' )
    lo = h.register_file( 'grey_sq2.png' )
    ko = h.register_file( 'black_sq.png' )

    set_timestamp( 10 )

    if( ver[0] >= 10 ):
        # Force a thumb to be generated so that info is initalized
        wo.get_thumb_stream( 4 )
        wo.rotate_cw()
    elif( ver[0] > 7 ):
        wo.read_thumb( 4 )
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

        mo.tag( 'warm' )
        ro.tag( 'warm' )
        yo.tag( 'warm' )
        go.tag( 'cool' )
        co.tag( 'cool' )

        wo.tag( 'greyscale' )
        lo.tag( 'greyscale' )
        ko.tag( 'greyscale' )

        ro.tag( 'red' )
        wo.tag( 'white' )
        lo.tag( 'grey' )
        ko.tag( 'black' )
    else:
        set_timestamp( 15 )

        cl = h.make_tag( 'colour' )

        wc = h.make_tag( 'warm' )
        cc = h.make_tag( 'cool' )
        bw = h.make_tag( 'greyscale' )

        set_timestamp( 20 )

        mo.assign( cl )
        ro.assign( cl )
        yo.assign( cl )
        go.assign( cl )
        co.assign( cl )

        mo.assign( wc )
        ro.assign( wc )
        yo.assign( wc )

        go.assign( cc )
        co.assign( cc )

        wo.assign( bw )
        lo.assign( bw )
        ko.assign( bw )

        set_timestamp( 25 )

        ro.assign( h.make_tag( 'red' ) )
        wo.assign( h.make_tag( 'white' ) )
        lo.assign( h.make_tag( 'grey' ) )
        ko.assign( h.make_tag( 'black' ) )

    if( ver[0] < 2 ):
        ro.set_parent( mo )
        yo.set_parent( mo )
        go.set_parent( mo )
        co.set_parent( mo )
    elif( ver[0] < 4 ):
        al1 = h.create_album()
        al1.add_file( mo, 5 )
        al1.add_file( ro, 4 )
        al1.add_file( yo, 3 )
        al1.add_file( go, 2 )
        al1.add_file( co, 1 )

        al1.register_name( 'colours' )
        al1.tag( 'colour_album' )

        al2 = h.create_album()
        al2.add_file( wo )

        al2.register_name( 'white_and_blue' )
        al2.tag( 'white_blue_album' )
    elif( ver[0] < 5 ):
        al1 = h.create_album()
        mo.assign( al1 )
        ro.assign( al1 )
        yo.assign( al1 )
        go.assign( al1 )
        co.assign( al1 )

        al1.register_name( 'colours' )
        al1.assign( h.make_tag( 'colour_album' ) )

        al2 = h.create_album()
        wo.assign( al2 )

        al2.register_name( 'white_and_blue' )
        al2.assign( h.make_tag( 'white_blue_album' ) )
    else:
        set_timestamp( 30 )
        al1 = h.create_album()
        mo.assign( al1, 5 )
        ro.assign( al1, 4 )
        yo.assign( al1, 3 )

        set_timestamp( 35 )
        go.assign( al1, 2 )
        co.assign( al1, 1 )

        if( ver[0] >= 10 ):
            al1.set_name( 'colours' )
        else:
            al1.add_name( 'colours' )

        set_timestamp( 40 )
        al1.assign( h.make_tag( 'colour_album' ) )

        set_timestamp( 45 )
        al2 = h.create_album()
        wo.assign( al2 )

        if( ver[0] >= 10 ):
            al2.set_name( 'white_and_blue' )
        else:
            al2.add_name( 'white_and_blue' )

        al2.assign( h.make_tag( 'white_blue_album' ) )
        al2.set_text( 'White & Blue' )

    set_timestamp( 50 )
    bo = h.register_file( 'blue_sq.png' )

    set_timestamp( 55 )

    if( ver[0] < 4 ):
        bo.tag( 'colour' )
        bo.tag( 'cool' )
    else:
        bo.assign( cl )
        bo.assign( cc )

    if( ver[0] < 2 ):
        bo.set_parent( mo )
    elif( ver[0] < 4 ):
        al1.add_file( bo, 0 )
        al2.add_file( bo )
    elif( ver[0] < 5 ):
        bo.assign( al1 )
        bo.assign( al2 )
    else:
        bo.assign( al1, 0 )
        bo.assign( al2 )

    if( ver[0] >= 12 ):
        lo.assign( wo )
        bo.assign( ko )
    elif( ver[0] > 8 or ver[0] == 8 and ver[1] > 0 ):
        lo.set_variant_of( wo )
        bo.set_variant_of( ko )
    else:
        lo.set_varient_of( wo )
        bo.set_varient_of( ko )

    if( ver[0] >= 12 ):
        ko.assign( lo, is_duplicate = True )
    elif( ver[0] >= 10 ):
        h.merge_objects( lo, ko )
    else:
        ko.set_duplicate_of( lo )

    if( ver[0] >= 14 ):
        h.process_thumb_requests()

if( __name__ == '__main__' ):

    ver = tuple( map( int, sys.argv[1].split( '.' ) ) )

    if( ver[0] > 8 or ver[0] == 8 and ver[1] > 0 ):
        import hdbfs as higu
    else:
        import higu

    hdbfs = higu

    if( ver[0] >= 14 or (ver[0] == 13 and ver[1] >= 1) ):
        hdbfs.imgdb.cache.MIN_THUMB_EXP = 2
    elif( ver[0] >= 10 ):
        hdbfs.imgdb.MIN_THUMB_EXP = 2
    elif( ver[0] >= 5 ):
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

    if( ver[0] >= 11 ):
        with h.transaction():
            make_db( h )
    elif( ver[0] >= 8 ):
        make_db( h )
    else:
        make_db( h )
        h.commit()

# vim:sts=4:et:sw=4
