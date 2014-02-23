import zlib
import os

from hashlib import md5
from hashlib import sha1

FBUFF = 4096

def str2hex( str ):
    xstr = ""
    for c in str:
        if( isinstance( c, int ) ):
            # Python 3 compatibility
            xstr += "%02x" % ( c )
        else:
            xstr += "%02x" % ( ord( c ) )
    return xstr.lower()

class crc32:
    def __init__( self ):
        self.__value = zlib.crc32( "" )

    def update( self, str ):
        self.__value = zlib.crc32( str, self.__value )

    def digest( self ):
        return chr( (self.__value >> 24) & 0xFF ) \
             + chr( (self.__value >> 16) & 0xFF ) \
             + chr( (self.__value >>  8) & 0xFF ) \
             + chr( (self.__value >>  0) & 0xFF )

class length:

    def __init__( self ):

        self.__value = 0

    def update( self, str ):

        self.__value += len( str )

    def digest( self ):

        return self.__value

def calculate_details( f ):

    algs = [ sha1(), md5(), crc32(), length() ]

    if( isinstance( f, str ) ):
        f = open( f, 'rb' )

    while( True ):
        b = f.read( FBUFF )
        if( len( b ) == 0 ):
            break
        for alg in algs:
            alg.update( b )

    f.close()

    return  algs[3].digest(), \
            str2hex( algs[2].digest() ), \
            str2hex( algs[1].digest() ), \
            str2hex( algs[0].digest() )

# vim:sts=4:et:sw=4
