fun check_len( length: Long ): Long {
    if( length < 0 ) throw RuntimeException()
    return length
}

fun check_crc32( hash: String ): String {
    /* TODO
    hash = hash.lower()
    assert re.match( '^[0-9a-f]{8}$', hash )*/
    return hash
}

fun check_md5( hash: String ): String {
    /* TODO
    hash = hash.lower()
    assert re.match( '^[0-9a-f]{32}$', hash )*/
    return hash
}

fun check_sha1( hash: String ): String {
    /* TODO
    hash = hash.lower()
    assert re.match( '^[0-9a-f]{40}$', hash )*/
    return hash
}