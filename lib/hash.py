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

def calculate_details( path ):

    algs = [ sha1(), md5(), crc32() ]
    f = open( path, 'rb' )

    while( True ):
        b = f.read( FBUFF )
        if( len( b ) == 0 ):
            break
        for alg in algs:
            alg.update( b )

    f.close()

    return  os.path.getsize( path ), \
            str2hex( algs[2].digest() ), \
            str2hex( algs[1].digest() ), \
            str2hex( algs[0].digest() )

# vim:sts=4:et:sw=4
