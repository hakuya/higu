#!/usr/bin/python

import higu
import sys
import os

import logging
log = logging.getLogger( __name__ )
logging.basicConfig()

MAX_TEXT_LEN = 2**18

def create_album( name, text, tags ):

    album = h.create_album()

    if( name is not None ):
        album.add_name( name )

    if( text is not None ):
        album.set_text( text )

    for t in tags:
        album.assign( t )

    return album

if( __name__ == '__main__' ):

    import optparse

    parser = optparse.OptionParser( usage = 'Usage: %prog [options] files...' )

    parser.add_option( '-c', '--config',
        dest = 'config',
        help = 'Configuration File' )
    parser.add_option( '-p', '--pretend',
        dest = 'pretend', action = 'store_true', default = False,
        help = 'Pretend, don\'t actually do anything' )
    parser.add_option( '-r', '--recovery',
        dest = 'recovery', action = 'store_true', default = False,
        help = 'Recovery mode' )
    parser.add_option( '-a', '--album',
        dest = 'album',
        help = 'Create album and add files to album' )
    parser.add_option( '-x', '--text',
        dest = 'text_data',
        help = 'Add text description to album (txt file)' )
    parser.add_option( '-t', '--tags',
        dest = 'taglist',
        help = 'List of tags (\',\' separated) to apply' )
    parser.add_option( '-T', '--newtags',
        dest = 'taglist_new',
        help = 'Same as -t, but creates tags if they don\'t exist' )
    parser.add_option( '-n', '--nosavename',
        dest = 'save_name', action = 'store_false',
        help = 'Don\'t save the original file name in the metadata' )
    parser.add_option( '-N', '--savename',
        dest = 'save_name', action = 'store_true', default = True,
        help = 'Save the original file name in the metadata' )

    opts, files = parser.parse_args()

    if( len( files ) < 1 ):
        parser.print_help()
        sys.exit( 0 )

    if( opts.config is not None ):
        higu.init( opts.config )
    else:
        higu.init()

    h = higu.Database()

    if( opts.recovery ):
        # Recovery mode, all we do is reload file data

        for f in files:
            if( not h.recover_file( f ) ):
                log.warn( '%s was not found in the db and was ignored', f )

        h.commit()
        sys.exit( 0 )

    # Load tags
    taglist = []
    if( opts.taglist is not None ):
        taglist += map( h.get_tag, opts.taglist.split( ',' ) )
    if( opts.taglist_new is not None ):
        taglist += map( h.make_tag, opts.taglist_new.split( ',' ) )

    if( opts.album is not None ):
        # Create album
        if( opts.text_data is not None ):
            textfile = open( opts.text_data, 'r' )
            text_data = unicode( textfile.read( MAX_TEXT_LEN ), 'utf-8' )
            assert textfile.read( 1 ) == '', 'Text file too long'
        else:
            text_data = None

        if( opts.album == '-' ):
            album = create_album( None, text_data, taglist )
        else:
            album = create_album( opts.album, text_data, taglist )
    else:
        album = None

    for f in files:
        x = h.register_file( f, opts.save_name )

        if( album is not None ):
            x.assign( album )
        else:
            for t in taglist:
                x.assign( t )

    if( not opts.pretend ):
        log.info( 'Committing changes' )
        h.commit()

# vim:sts=4:et:sw=4
