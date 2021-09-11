package ca._4haven.higu.hdbfs

import ca._4haven.higu.hdbfs.imgdb.*
import kotlin.test.*

class ThumbCases {
    val utils = TestUtils()

    @BeforeTest
    fun setUp() {
        this.utils.init_env()
    }

    @AfterTest
    fun tearDown() {
        this.utils.uninit_env()
    }

    @Test
    fun test_create_thumb() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val blue = this.utils._load_data( TestUtils.blue )
            val obj = (h.register_file( blue.toString(), NAME_POLICY_DONT_SET ).file as ImageFile)

            val root_stream = obj.get_root_stream()!!
            val thumb_stream = obj.get_thumb_stream( 4 )!!

            assertNotEquals( root_stream.get_stream_id(), thumb_stream.get_stream_id(),
                            "Root returned for small thumb" )
            assertFalse( this.utils._diff( root_stream.read()!!, thumb_stream.read()!! ),
                            "Smaller thumb stream identical" )
            assertEquals( SP_EXPENDABLE, thumb_stream.get_priority(),
                            "Thumb priority not set correctly" )
        }
    }

    @Test
    fun test_return_orig() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val blue = this.utils._load_data( TestUtils.blue )
            val obj = (h.register_file( blue.toString(), NAME_POLICY_DONT_SET ).file as ImageFile)

            val root_stream = obj.get_root_stream()!!
            val thumb_stream = obj.get_thumb_stream( 10 )!!

            assertEquals( root_stream.get_stream_id(), thumb_stream.get_stream_id(),
                            "Root not returned large small thumb" )
            assertEquals( root_stream.get_priority(), thumb_stream.get_priority(),
                            "Oddity in return root for large priority" )
        }
    }

    @Test
    fun test_rot_does_not_return_orig() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val blue = this.utils._load_data( TestUtils.blue )
            val obj = (h.register_file( blue.toString(), NAME_POLICY_DONT_SET ).file as ImageFile)

            obj.rotate_cw()

            val root_stream = obj.get_root_stream()!!
            val thumb_stream = obj.get_thumb_stream( 10 )!!

            assertNotEquals( root_stream.get_stream_id(), thumb_stream.get_stream_id(),
                          "Root returned on rotated image" )
        }
    }

    @Test
    fun test_thumb_points_to_root() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val blue = this.utils._load_data( TestUtils.blue )
            val obj = (h.register_file( blue.toString(), NAME_POLICY_DONT_SET ).file as ImageFile)

            val root_stream = obj.get_root_stream()!!
            val thumb_stream = obj.get_thumb_stream( 4 )!!
            val origin_stream = thumb_stream.get_origin_stream()

            assertNotNull( origin_stream, "Thumb has no origin" )
            assertEquals( root_stream.get_stream_id(), origin_stream.get_stream_id(),
                            "Origin stream is not root stream" )
        }
    }

    @Test
    fun test_create_very_small() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val blue = this.utils._load_data( TestUtils.blue )
            val obj = (h.register_file( blue.toString(), NAME_POLICY_DONT_SET ).file as ImageFile)

            val thumb_stream = obj.get_thumb_stream( 4 )!!
            val small_stream = obj.get_thumb_stream( 3 )!!

            assertEquals( thumb_stream.get_stream_id(), small_stream.get_stream_id(),
                            "Very small does not match small" )
            assertEquals( SP_EXPENDABLE, small_stream.get_priority(),
                            "Very small priority not set correctly" )
        }
    }

    @Test
    fun test_thumbs_not_moved() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val red = this.utils._load_data( TestUtils.red )
            val blue = this.utils._load_data( TestUtils.blue )

            val o1 = (h.register_file( blue.toString(), NAME_POLICY_DONT_SET ).file as ImageFile)
            val o2 = (h.register_file( red.toString(), NAME_POLICY_DONT_SET ).file as ImageFile)

            val t2_4_hash = o2.get_thumb_stream( 4 )!!.get_hash()
            val t2_5_hash = o2.get_thumb_stream( 5 )!!.get_hash()

            h.merge_objects( o1, o2 )

            val t1_4_hash = o1.get_thumb_stream( 4 )!!.get_hash()
            val t1_5_hash = o1.get_thumb_stream( 5 )!!.get_hash()

            assertNotEquals( t2_4_hash, t1_4_hash, "New thumb matches moved from o2" )
            assertNotEquals( t2_5_hash, t1_5_hash, "New thumb matches moved from o2" )
        }
    }

    @Test
    fun test_thumbs_not_moved_with_existing() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val red = this.utils._load_data( TestUtils.red )
            val blue = this.utils._load_data( TestUtils.blue )

            val o1 = (h.register_file( blue.toString(), NAME_POLICY_DONT_SET ).file as ImageFile)
            val o2 = (h.register_file( red.toString(), NAME_POLICY_DONT_SET ).file as ImageFile)

            val t1_4_hash = o1.get_thumb_stream( 4 )!!.get_hash()
            val t1_5_hash = o1.get_thumb_stream( 5 )!!.get_hash()
            val t2_4_hash = o2.get_thumb_stream( 4 )!!.get_hash()
            val t2_5_hash = o2.get_thumb_stream( 5 )!!.get_hash()

            h.merge_objects( o1, o2 )

            val tx_4_hash = o1.get_thumb_stream( 4 )!!.get_hash()
            val tx_5_hash = o1.get_thumb_stream( 5 )!!.get_hash()

            assertEquals( t1_4_hash, tx_4_hash, "New thumb not matching from o1" )
            assertEquals( t1_5_hash, tx_5_hash, "New thumb not matching from o1" )
            assertNotEquals( t2_4_hash, tx_4_hash, "New thumb matches moved from o2" )
            assertNotEquals( t2_5_hash, tx_5_hash, "New thumb matches moved from o2" )
        }
    }
}