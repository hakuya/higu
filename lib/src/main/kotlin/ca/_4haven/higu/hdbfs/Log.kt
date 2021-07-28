object Log {
    fun debug( msg: String ) {
        if( enableDebug ) {
            println( "[d] ${msg}" )
        }
    }

    fun info( msg: String ) {
        println( "[i] ${msg}" )
    }

    fun warning( msg: String ) {
        println( "[w] ${msg}" )
    }

    fun error( msg: String ) {
        println( "[!] ${msg}" )
    }

    var enableDebug = false
}