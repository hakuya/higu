package ca._4haven.higu.hdbfs.imgdb

data class Dimensions( val width: Int, val height: Int )

data class ThumbInfo( val gen: Int, val max_e: Int, val use_root: Boolean )

enum class Orientation( val value: Int ) {
    NORMAL( 1 ),
    MIRROR( 2 ),
    R180( 3 ),
    R180_MIRROR( 4 ),
    R90_MIRROR( 5 ),
    R90( 6 ),
    R270_MIRROR( 7 ),
    R270( 8 );

    companion object {
        fun fromInt( value: Int ): Orientation? {
            return values().firstOrNull { it.value == value }
        }
    }
}