#!/usr/bin/python

import sys
import os

import logging
log = logging.getLogger( __name__ )
logging.basicConfig()

import hdbfs
import higu.config

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
    parser.add_option( '-n', '--name-policy',
        dest = 'name_policy',
        help = 'Policy for persisting names ("noreg", "noset", "setundef", "setall")' )

    opts, files = parser.parse_args()

    if( len( files ) < 1 ):
        parser.print_help()
        sys.exit( 0 )

    if( opts.config is not None ):
        cfg = higu.config.init( opts.config )
        hdbfs.init( cfg.get_path( 'library' ) )
    else:
        hdbfs.init()

    h = hdbfs.Database()
    h.enable_write_access()

    if( opts.recovery ):
        h.recover_files( files )
        sys.exit( 0 )

    tags = opts.taglist.split( ',' ) if( opts.taglist is not None ) else []
    tags_new = opts.taglist_new.split( ',' ) if( opts.taglist_new is not None ) else []

    create_album = opts.album is not None
    album_name = opts.album if( opts.album != '-' ) else None

    if( create_album and opts.text_data is not None ):
        textfile = open( opts.text_data, 'r' )
        text_data = unicode( textfile.read( MAX_TEXT_LEN ), 'utf-8' )
        assert textfile.read( 1 ) == '', 'Text file too long'
    else:
        text_data = None

    name_policy = hdbfs.NAME_POLICY_SET_IF_UNDEF
    if( opts.name_policy == "noreg" ):
        name_policy = hdbfs.NAME_POLICY_DONT_REGISTER
    elif( opts.name_policy == "noset" ):
        name_policy = hdbfs.NAME_POLICY_DONT_SET
    elif( opts.name_policy == "setundef" ):
        name_policy = hdbfs.NAME_POLICY_SET_IF_UNDEF
    elif( opts.name_policy == "setall" ):
        name_policy = hdbfs.NAME_POLICY_SET_ALWAYS

    h.batch_add_files( files, tags, tags_new, name_policy,
                       create_album, album_name, text_data )

# vim:sts=4:et:sw=4
