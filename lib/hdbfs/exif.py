import sys

from hdbfs.defs import *

from PIL import ExifTags

IGNORED_EXIF_TAGS = [ 0x927c, 0x8769, 0xc4a5 ]

def _decode_exif_unknown_inner( s ):

    if( isinstance( s, str ) ):
        # Already unicode, we're good to go
        return s

    if( not isinstance( s, bytes ) ):
        # Probably a number
        return str( s )

    try:
        if( len( s ) > 8 ):
            # The type is specified in the first 8 bytes of the buffer
            if( s[0:8] == b'UNICODE\0' ):
                return s[8:].decode( 'utf_16_le' )
            elif( s[0:8] == b'JIS\0\0\0\0\0' ):
                return s[8:].decode( 'iso2022_jp' )
            elif( s[0:8] == b'ASCII\0\0\0' ):
                # Theoretically ASCII, but sometimes utf8 gets pumped in
                for enc in [ 'ascii', 'utf_8' ]:
                    try:
                        return s[8:].decode( enc )
                    except:
                        pass
                return s[8:].decode( 'utf_8', 'replace' )
            elif( s[0:8] == b'\0\0\0\0\0\0\0\0' ):
                # Unspecified, drop the header and fall down for our
                # fallback processing
                s = s[8:]

        if( len( s ) > 2 and s[-2:] == b'\0\0' ):
            # If there are two NULL terminators, it's a utf16
            # null terminator
            return s.decode( 'utf_16_le' )
        else:
            # Try to take it as utf8
            return s.decode( 'utf_8' )

    except:
        pass

    # *shrugs*, power it into unicode
    return s.decode( 'utf_8', 'replace' )

def _decode_exif_unknown( s ):

    s = _decode_exif_unknown_inner( s )
    if( len( s ) > 0 and s[-1] == '\0' ):
        return s[:-1]
    else:
        return s

def _decode_exif_gps( gps_v ):

    def _dms( dms, axis ):

        if( dms[0][0] % dms[0][1] != 0 ):
            d = float( dms[0][0] / dms[0][1] )
            return f'{d}\u00b0 {axis!s}'

        elif( dms[1][0] % dms[1][1] != 0 ):
            d = int( dms[0][0] // dms[0][1] )
            m = float( dms[1][0] / dms[1][1] )
            return f'{d}\u00b0{m}\'{axis!s}'

        else:
            d = int( dms[0][0] // dms[0][1] )
            m = int( dms[1][0] // dms[1][1] )
            s = float( dms[2][0] / dms[2][1] )
            return f'{d}\u00b0{m}\'{s}"{axis!s}'

    return ' '.join( ( _dms( gps_v[0x0002], gps_v[0x0001] ),
                       _dms( gps_v[0x0004], gps_v[0x0003] ) ) )

def _decode_exif_shutter_speed( v ):

    f = 1.0 * v[0] / v[1]

    if( f > 0 ):
        return f'1/{int( round( 2 ** f ) )}s'
    else:
        return f'{2 ** f}s'

def _decode_exif_aperture_value( v ):

    import math

    f = 1.0 * v[0] / v[1]

    return f'f/{math.sqrt( 2 ** f ):.1f}'

def _decode_exif_focal_length( v ):

    v = float( v[0] / v[1] )
    return f'{v}mm'

def _decode_exif_rational( v ):

    n, d = v

    if( n == 1 and d > 1 ):
        return f'1/{d}'
    else:
        return f'{n/d}'

def _decode_exif_exposure_time( v ):

    return f'{_decode_exif_rational( v )}s'

def _decode_exif_lens_spec( v ):

    focal_len = [_decode_exif_focal_length( it )
                    for it in v[0:2]
                    if it != ( 0, 0 )]
    if( len( focal_len ) == 2 ):
        r = f'{focal_len[0]} - {focal_len[1]}'
    elif( len( focal_len ) == 1 ):
        r = f'{focal_len[0]}'
    else:
        return None

    ap = [_decode_exif_rational( it )
            for it in v[2:4]
            if it != ( 0, 0 )]
    if( len( ap ) == 2 ):
        return f'{r}, {ap[0]} - {ap[1]}'
    elif( len( ap ) == 1 ):
        return f'{r}, {ap[0]}'
    else:
        return r

def _decode_exposure_bias( v ):

    n, d = v

    if( n == 0 ):
        return '0'
    elif( n < 0 ):
        return f'-{-n}/{d}'.format( -n, d )
    else:
        return f'+{n}/{d}'

EXIF_DECODE_FN_MAP = {
    0x011a : _decode_exif_rational,
    0x011b : _decode_exif_rational,
    0x8825 : _decode_exif_gps,
    0x829a : _decode_exif_exposure_time,
    0x829d : _decode_exif_rational,
    0x9201 : _decode_exif_shutter_speed,
    0x9202 : _decode_exif_aperture_value,
    0x9204 : _decode_exposure_bias,
    0x920a : _decode_exif_focal_length,
    0xa432 : _decode_exif_lens_spec,
}

def _decode_exif( k, v ):

    if( k not in ExifTags.TAGS or k in IGNORED_EXIF_TAGS ):
        return None
    elif( k in EXIF_DECODE_FN_MAP ):
        try:
            return EXIF_DECODE_FN_MAP[k]( v )
        except:
            return None
    else:
        return _decode_exif_unknown( v )

def read_exif( img ):

    if( 'exif' in img.info ):
        try:
            exif = img._getexif()
            return {
                ExifTags.TAGS[k] : _decode_exif( k, v )
                for k, v in exif.items()
                if _decode_exif( k, v ) is not None
            }
        except:
            LOG.warning( f'Failed reading exif for "{img}": {sys.exc_info()[1]!s}' )

    return None
