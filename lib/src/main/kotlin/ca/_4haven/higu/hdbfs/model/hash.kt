package ca._4haven.higu.hdbfs.model

import java.io.InputStream
import java.util.zip.Checksum
import java.util.zip.CRC32
import java.security.MessageDigest

val FBUFF = 4096

interface DigestAlgorithm {
    fun update( b: ByteArray, off: Int, len: Int )
    fun digest(): String
}

class LengthAlgorithm : DigestAlgorithm {
    private var len = 0.toLong()


    override fun update( b: ByteArray, off: Int, len: Int ) {
        this.len += len
    }

    override fun digest(): String {
        return len.toString()
    }
}

class CRC32Algorithm() : DigestAlgorithm {
    val inst = CRC32()

    override fun update( b: ByteArray, off: Int, len: Int ) {
        inst.update( b, off, len )
    }

    override fun digest(): String {
        return "%08x".format( inst.getValue() )
    }
}

class MessageDigestAlgorithm( val algorithm: String ) : DigestAlgorithm {
    val inst = MessageDigest.getInstance( algorithm )

    override fun update( b: ByteArray, off: Int, len: Int ) {
        inst.update( b, off, len )
    }

    override fun digest(): String {
        var result = ""
        inst.digest().forEach { b ->
            result += "%02x".format( b )
        }
        return result
    }
}

data class Details( val length: Long,
                    val crc32: String,
                    val md5: String,
                    val sha1: String )
{
    companion object {
        fun calculate( ins: InputStream ): Details {
            val algs = listOf( MessageDigestAlgorithm( "SHA-1" ),
                               MessageDigestAlgorithm( "MD5" ),
                               CRC32Algorithm(),
                               LengthAlgorithm() )

            val buff = ByteArray( FBUFF )
            ins.use {
                while( true ) {
                    val c = ins.read( buff )
                    if( c <= 0 ) break
                    algs.forEach {
                        it.update( buff, 0, c )
                    }
                }
            }

            return Details( algs[3].digest().toLong(),
                            algs[2].digest(),
                            algs[1].digest(),
                            algs[0].digest() )

        }
    }
}
