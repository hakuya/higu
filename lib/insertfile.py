#!/usr/bin/python

import higu
import sys

def create_album( name, tags, files, order ):

    if( order ):
        order = 0
    else:
        order = None

    album = h.create_album()

    if( name != None ):
        album.register_name( name )

    for t in tags:
        album.tag( t )

    for f in files:
        album.add_file( f[1], order )
        if( order != None ):
            order += 1

if( __name__ == '__main__' ):

    argv = sys.argv[1:]

    if( len( argv ) < 1 ):
        print 'Usage: insertfile.py [-d database] [-a album] [-t taglist] [-n|-N] [-o|-O] [-s|-S] file...'

    if( argv[0] == '-d' ):
        h = higu.Database( argv[1] )
        argv = argv[2:]
    else:
        h = higu.init_default()

    album = None
    add_name = True
    taglist = []
    order = False
    sort = False

    files = []

    def sortfn( a, b ):
        if( a[0] < b[0] ):
            return -1
        elif( a[0] > b[0] ):
            return 1
        else:
            return 0

    while( len( argv ) > 0 ):
        if( argv[0] == '-a' ):
            if( album != None ):
                if( sort ):
                    files.sort( sortfn )
                if( album == '-' ):
                    create_album( None, taglist, files, order )
                else:
                    create_album( album, taglist, files, order )
            files = []

            album = argv[1]
            argv = argv[2:]
            continue
        elif( argv[0] == '-t' ):
            taglist = argv[1].split( ',' )
            argv = argv[2:]
            continue
        elif( argv[0] == '-n' ):
            add_name = False
        elif( argv[0] == '-N' ):
            add_name = True
        elif( argv[0] == '-o' ):
            order = False
        elif( argv[0] == '-O' ):
            order = True
        elif( argv[0] == '-s' ):
            sort = False
        elif( argv[0] == '-S' ):
            sort = True
        else:
            x = h.register_file( argv[0], add_name )

            if( album == None ):
                for t in taglist:
                    x.tag( t )

            files.append( ( argv[0], x, ) )

        argv = argv[1:]

    if( sort ):
        files.sort( sortfn )
    if( album != None ):
        if( album == '-' ):
            create_album( None, taglist, files, order )
        else:
            create_album( album, taglist, files, order )

    h.commit()

# vim:sts=4:et:sw=4