from PIL import ExifTags


IGNORED_EXIF_TAGS = [ 0x927c, 0x8769, 0xc4a5 ]

def _decode_exif_unknown_inner( s ):

    if( isinstance( s, unicode ) ):
        # Already unicode, we're good to go
        return s

    if( not isinstance( s, str ) ):
        # Probably a number
        return str( s )

    try:
        if( len( s ) > 8 ):
            # The type is specified in the first 8 bytes of the buffer
            if( s[0:8] == 'UNICODE\0' ):
                return unicode( s[8:].decode( 'utf_16_le' ) )
            elif( s[0:8] == 'JIS\0\0\0\0\0' ):
                return unicode( s[8:].decode( 'iso2022_jp' ) )
            elif( s[0:8] == 'ASCII\0\0\0' ):
                # Theoretically ASCII, but sometimes utf8 gets pumped in
                for enc in [ 'ascii', 'utf_8' ]:
                    try:
                        return unicode( s[8:].decode( enc ) )
                    except:
                        pass
                return unicode( s[8:], errors='replace' )
            elif( s[0:8] == '\0\0\0\0\0\0\0\0' ):
                # Unspecified, drop the header and fall down for our
                # fallback processing
                s = s[8:]

        if( len( s ) > 2 and s[-2:] == '\0\0' ):
            # If there are two NULL terminators, it's a utf16
            # null terminator
            return unicode( s.decode( 'utf_16_le' ) )
        else:
            # Try to take it as utf8
            return unicode( s.decode( 'utf_8' ) )

    except:
        pass

    # *shrugs*, power it into unicode
    return unicode( s, errors='replace' )

def _decode_exif_unknown( s ):

    s = _decode_exif_unknown_inner( s )
    if( len( s ) > 0 and s[-1] == '\0' ):
        return s[:-1]
    else:
        return s

def _decode_exif_gps( gps_v ):

    def _dms( dms, axis ):

        if( dms[0][0] % dms[0][1] != 0 ):
            return u'{0}\u00b0 {1}'.format(
                        1.0 * dms[0][0] / dms[0][1],
                        str( axis ) )
        elif( dms[1][0] % dms[1][1] != 0 ):
            return u'{0}\u00b0{1}\'{2}'.format(
                        dms[0][0] / dms[0][1],
                        1.0 * dms[1][0] / dms[1][1],
                        str( axis ) )
        else:
            return u'{0}\u00b0{1}\'{2}"{3}'.format(
                        dms[0][0] / dms[0][1],
                        dms[1][0] / dms[1][1],
                        1.0 * dms[2][0] / dms[2][1],
                        str( axis ) )

    return u'{0} {1}'.format(
                _dms( gps_v[0x0002], gps_v[0x0001] ),
                _dms( gps_v[0x0004], gps_v[0x0003] ) )

def _decode_exif_shutter_speed( v ):

    f = 1.0 * v[0] / v[1]

    if( f > 0 ):
        return '1/{0}s'.format( int( round( 2 ** f ) ) )
    else:
        return '{0}s'.format( 2 ** f )

def _decode_exif_aperture_value( v ):

    import math

    f = 1.0 * v[0] / v[1]

    return 'f/{0:.1f}'.format( math.sqrt( 2 ** f ) )

def _decode_exif_focal_length( v ):

    return '{0}mm'.format( 1.0 * v[0] / v[1] )

def _decode_exif_rational( v ):

    n, d = v

    if( n == 1 and d > 1 ):
        return '1/{0}'.format( d )
    else:
        return '{0}'.format( 1.0 * n / d )

def _decode_exif_exposure_time( v ):

    return '{0}s'.format( _decode_exif_rational( v ) )

def _decode_exif_lens_spec( v ):

    if( v[0] != ( 0, 0 ) ):
        focal_len = _decode_exif_focal_length( v[0] )

        if( v[1] != ( 0, 0 ) and v[1] != v[0] ):
            focal_len = '{0} - {1}'.format( focal_len,
                            _decode_exif_focal_length( v[1] ) )
    else:
        return None

    if( v[2] != ( 0, 0 ) ):
        ap = _decode_exif_rational( v[2] )
        if( v[3] != ( 0, 0 ) and v[3] != v[2] ):
            ap = '{0} - {1}'.format( ap,
                        _decode_exif_rational( v[3] ) )

        return '{0}, {1}'.format( focal_len, ap )
    else:
        return focal_len

def _decode_exposure_bias( v ):

    n, d = v

    if( n == 0 ):
        return '0'
    elif( n < 0 ):
        return '-{0}/{1}'.format( -n, d )
    else:
        return '+{0}/{1}'.format( n, d )

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
            import traceback
            traceback.print_exc()
            print sys.exc_info()
            LOG.warning(
                    'Failed reading exif for "%s": %s',
                    self.stream.get_repr(), str( sys.exc_info()[1] ) )

    return None
