""" Hash calculation utilities for file integrity verification.

This module provides utilities for calculating various hash types (SHA-1, MD5,
CRC32) and file lengths. Used primarily for content-addressable storage and
verifying file integrity.
"""

import zlib
import os

from hashlib import md5
from hashlib import sha1
from typing import Union, BinaryIO, Tuple

FBUFF = 4096

def str2hex( str: bytes ) -> str:
    """ Convert bytes to lowercase hexadecimal string.

    Args:
        str: Bytes object to convert (despite parameter name)

    Returns:
        Lowercase hexadecimal string representation

    Example:
        >>> str2hex(b'\\x01\\x02\\xab')
        '0102ab'
    """
    xstr = ""
    for c in str:
        if( isinstance( c, int ) ):
            # Python 3 compatibility
            xstr += "{:02x}".format( c )
        else:
            xstr += "{:02x}".format( ord( c ) )
    return xstr.lower()

class crc32:
    """ CRC32 hash calculator with hashlib-compatible interface.

    Provides an interface similar to hashlib hash objects for calculating
    CRC32 checksums incrementally.
    """

    def __init__( self ) -> None:
        self.__value = zlib.crc32( bytearray() )

    def update( self, str: bytes ) -> None:
        """ Update the hash with new data.

        Args:
            str: Bytes to add to the hash calculation
        """
        self.__value = zlib.crc32( str, self.__value )

    def digest( self ) -> str:
        """ Get the digest as a 4-byte string.

        Returns:
            4-character string containing the CRC32 value as bytes
        """
        return chr( (self.__value >> 24) & 0xFF ) \
             + chr( (self.__value >> 16) & 0xFF ) \
             + chr( (self.__value >>  8) & 0xFF ) \
             + chr( (self.__value >>  0) & 0xFF )

class length:
    """ Length calculator with hashlib-compatible interface.

    Provides an interface similar to hashlib hash objects for calculating
    the total length of data incrementally.
    """

    def __init__( self ) -> None:

        self.__value = 0

    def update( self, str: bytes ) -> None:
        """ Update the length with new data.

        Args:
            str: Bytes to add to the length calculation
        """

        self.__value += len( str )

    def digest( self ) -> int:
        """ Get the total length.

        Returns:
            Total number of bytes processed
        """

        return self.__value

def calculate_details( f: Union[str, BinaryIO] ) -> Tuple[int, str, str, str]:
    """ Calculate file length and hashes (SHA-1, MD5, CRC32).

    Reads a file and calculates all hash types used for file integrity
    verification and content-addressable storage.

    Args:
        f: File path string or binary file-like object. If a path is provided,
           the file will be opened and closed automatically.

    Returns:
        Tuple of (length, crc32_hex, md5_hex, sha1_hex):
        - length: File size in bytes
        - crc32_hex: CRC32 checksum as lowercase hex string
        - md5_hex: MD5 hash as lowercase hex string
        - sha1_hex: SHA-1 hash as lowercase hex string

    Example:
        >>> calculate_details('myfile.txt')
        (1024, '9ae0ea9e', 'a3b2c1...', 'd4e5f6...')
    """

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
