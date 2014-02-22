#!/usr/bin/python

import higu
import sys
import os

import logging
log = logging.getLogger( __name__ )
logging.basicConfig()

MAX_TEXT_LEN = 2**18

def create_album( name, text, tags, files, order ):

    if( order ):
        order = 0
    else:
        order = None

    album = h.create_album()

    if( name is not None ):
        album.add_name( name )

    if( text is not None ):
        album.set_text( text )

    for t in tags:
        album.assign( t )

    for f in files:
        f[1].assign( album )
        #album.add_file( f[1], order )
        #if( order != None ):
        #    order += 1

if( __name__ == '__main__' ):

    argv = sys.argv[1:]

    if( len( argv ) < 1 ):
        print 'Usage: insertfile.py [-c config] [-r] [-a album] [-x textfile] [-t taglist] [-n|-N] [-o|-O] [-s|-S] file...'

    if( argv[0] == '-c' ):
        higu.init( argv[1] )
        argv = argv[2:]
    else:
        higu.init()

    h = higu.Database()

    album = None
    add_name = True
    taglist = []
    text_data = None
    order = False
    sort = False
    recovery = False
    pretend = False

    files = []

    def sortfn( a, b ):
        if( a[0] < b[0] ):
            return -1
        elif( a[0] > b[0] ):
            return 1
        else:
            return 0

    while( len( argv ) > 0 ):
        if( argv[0] == '-r' ):
            recovery = True
        elif( argv[0] == '-a' ):
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
        elif( argv[0] == '-x' ):
            textfile = open( argv[1], 'r' )
            text_data = unicode( textfile.read( MAX_TEXT_LEN ), 'utf-8' )
            assert textfile.read( 1 ) == '', 'Text file too long'
            argv = argv[2:]
            continue
        elif( argv[0] == '-t' ):
            taglist = map( h.get_tag, argv[1].split( ',' ) )
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
        elif( not os.path.isfile( argv[0] ) ):
            log.warn( '%s is a directory and was skipped', argv[0] )
        elif( pretend ):
            pass
        elif( recovery ):
            if( not h.recover_file( argv[0] ) ):
                log.warn( '%s was not found in the db and was ignored', argv[0] )
        else:
            x = h.register_file( argv[0], add_name )

            if( album == None ):
                for t in taglist:
                    x.assign( t )

            files.append( ( argv[0], x, ) )

        argv = argv[1:]

    if( recovery or pretend ):
        h.commit()
        sys.exit( 0 )

    if( sort ):
        files.sort( sortfn )
    if( album != None ):
        if( album == '-' ):
            create_album( None, text_data, taglist, files, order )
        else:
            create_album( album, text_data, taglist, files, order )

    log.info( 'Committing changes' )
    h.commit()

# vim:sts=4:et:sw=4
