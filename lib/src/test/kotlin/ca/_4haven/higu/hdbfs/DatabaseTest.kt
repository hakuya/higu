package ca._4haven.higu.hdbfs

import ca._4haven.higu.hdbfs.basic_objects.*
import ca._4haven.higu.hdbfs.imgdb.*
import ca._4haven.higu.hdbfs.model.*
import kotlin.test.*
import kotlin.test.assertTrue
import kotlin.io.path.isRegularFile
import kotlin.io.path.isDirectory
import java.lang.Thread
import java.time.Instant

class DatabaseTest {
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
    fun test_basic_structure() {
        assertTrue( this.utils.db_path.toFile().isDirectory(),
                "Library not created" )
        assertTrue( this.utils.db_path.resolve( "hfdb.dat" )
                        .toFile().isFile(),
                "Sqlite database not created" )
    }

    @Test
    fun test_imgdat_structure() {
        val red = this.utils._load_data( TestUtils.red )

        val h = Database()
        h.enable_write_access()

        val result = h.register_file( red.toString(), NAME_POLICY_DONT_REGISTER )

        assertFalse( red.isFile(), "Old image was not removed" )

        assertTrue( this.utils.db_path.resolve( "imgdat" ).toFile().isDirectory(),
                    "Image data directory not created" )

        val red_istm = result.file.get_root_stream()?.read()
        assertNotNull( red_istm )
        assertTrue( this.utils._diff_data( red_istm, TestUtils.red ),
                    "Image not read from library" )
    }

    @Test
    fun test_delete() {
        val yellow = this.utils._load_data( TestUtils.yellow )

        val h = Database()
        h.enable_write_access()

        val y_reg = h.register_file( yellow.toString(), NAME_POLICY_DONT_REGISTER )
        val obj = y_reg.file as ImageFile

        val img_s = obj.get_root_stream()
        val tb_s = obj.get_thumb_stream( 4 )

        var img_istm = img_s?.read()
        var tb_istm = tb_s?.read()

        assertNotNull( img_istm, "Invalid image returned" )
        assertNotNull( tb_istm, "Invalid thumb returned" )

        img_istm.close()
        tb_istm.close()

        val obj_id = obj.get_id()

        val s_id = img_s?.get_stream_id()
        val s_prio = img_s?.get_priority()
        val s_ext = img_s?.get_extension()

        val t_id = tb_s?.get_stream_id()
        val t_prio = tb_s?.get_priority()
        val t_ext = tb_s?.get_extension()

        h.delete_object( obj )

        assertNull( h.get_object_by_id( obj_id ),
                    "Object returned by id after delete" )

        img_istm = h.imgdb.read( s_id!!, s_prio!!, s_ext )
        assertNull( img_istm, "Image returned after delete" )

        tb_istm = h.imgdb.read( t_id!!, t_prio!!, t_ext )
        assertNull( tb_istm, "Thumb returned after delete" )
    }

    @Test
    fun test_drop_streams() {

        val red = this.utils._load_data( TestUtils.red )
        val yellow = this.utils._load_data( TestUtils.yellow )

        val h = Database()
        h.enable_write_access()

        val red_f = h.register_file( red.toString() ).file
        val yellow_f = h.register_file( yellow.toString() ).file

        assertNotNull( red_f.get_root_stream(), "Red: No root stream" )
        assertNotNull( yellow_f.get_root_stream(), "Yellow: No root stream" )

        red_f.get_root_stream()?.setItem( "test_meta", 5 )
        yellow_f.get_root_stream()?.setItem( "test_meta", 5 )

        yellow_f.drop_expendable_streams()
        h.delete_object( yellow_f )

        assertNotNull( red_f.get_root_stream(), "Red: No root stream" )
        assertEquals( 5, red_f.get_root_stream()?.getItem( "test_meta" ),
                "Red: test_meta lost" )
    }

    @Test
    fun test_drop_expendible() {

        val red = this.utils._load_data( TestUtils.red )
        val yellow = this.utils._load_data( TestUtils.yellow )

        val h = Database()
        h.enable_write_access()

        val red_f = h.register_file( red.toString() ).file as ImageFile
        val yellow_f = h.register_file( yellow.toString() ).file as ImageFile

        assertNotNull( red_f.get_root_stream(), "Red: No root stream" )
        assertNotNull( yellow_f.get_root_stream(), "Yellow: No root stream" )
        assertNull( red_f.get_stream( "tb:4" ), "Red: Thumb exists before created" )
        assertNull( yellow_f.get_stream( "tb:4" ), "Yellow: Thumb exists before created" )

        assertNotNull( red_f.get_thumb_stream( 4 ), "Red: Thumb not created" )
        assertNotNull( yellow_f.get_thumb_stream( 4 ), "Yellow: Thumb not created" )

        assertNotNull( red_f.get_stream( "tb:4" ), "Red: Thumb name lookup fail" )
        assertNotNull( yellow_f.get_stream( "tb:4" ), "Yellow: Thumb name lookup fail" )

        red_f.get_thumb_stream( 4 )?.setItem( "test_meta", 5 )
        yellow_f.get_thumb_stream( 4 )?.setItem( "test_meta", 5 )

        assertEquals( 5, red_f.get_thumb_stream( 4 )?.getItem( "test_meta" ),
                "Red: Thumb test_meta not set" )
        assertEquals( 5, yellow_f.get_thumb_stream( 4 )?.getItem( "test_meta" ),
                "Yellow: Thumb test_meta not set" )

        yellow_f.drop_expendable_streams()

        assertNotNull( red_f.get_root_stream(), "Red: No root stream" )
        assertNotNull( yellow_f.get_root_stream(), "Yellow: No root stream" )
        assertNotNull( red_f.get_stream( "tb:4" ), "Red: Thumb was lost" )
        assertNull( yellow_f.get_stream( "tb:4" ), "Yellow: Thumb was not dropped" )
        assertEquals( 5, red_f.get_thumb_stream( 4 )?.getItem( "test_meta" ),
                "Red: Thumb test_meta lost" )
    }

    @Test
    fun test_timestamp() {

        val blue = this.utils._load_data( TestUtils.blue )

        val h = Database()
        h.enable_write_access()

        val obj_id = h.register_file( blue.toString(), NAME_POLICY_DONT_REGISTER ).file.get_id()

        Thread.sleep( 5_000 )
        val obj = h.get_object_by_id( obj_id )!!

        val now = Instant.now().getEpochSecond()

        assertTrue( now - obj.get_creation_time_utc() <= 10,
                "Unexpected timestamp > 10secs away" )
        assertTrue( now - obj.get_creation_time_utc() >= 5,
                "Unexpected timestamp < 5secs away" )
    }

    @Test
    fun test_double_add() {

        // Add the file
        Database().apply {
            enable_write_access()
        }.let { h ->
            val green = this.utils._load_data( TestUtils.green )

            val result = h.register_file( green.toString(), NAME_POLICY_DONT_REGISTER )
            assertFalse( result.was_known, "File known prior to first add" )

            assertFalse( green.isFile(), "Old image was not removed" )

            val img_fd = result.file.get_root_stream()?.read()
            assertNotNull( img_fd, "Failed opening image" )
            img_fd.close()
        }

        // Add it again
        Database().apply {
            enable_write_access()
        }.let { h ->
            val green = this.utils._load_data( TestUtils.green )

            val result = h.register_file( green.toString(), NAME_POLICY_DONT_REGISTER )
            assertTrue( result.was_known, "File not known on second add" )

            assertTrue( green.isFile(), "Double image was removed" )

            val img_fd = result.file.get_root_stream()?.read()
            assertNotNull( img_fd, "Invalid image returned after double-add" )
            img_fd.close()
        }
    }

    @Test
    fun test_recover_missing() {

        // Add the file, and delete it
        Database().apply {
            enable_write_access()
        }.let { h ->
            val cyan = this.utils._load_data( TestUtils.cyan )
            val obj = h.register_file( cyan.toString(), NAME_POLICY_DONT_REGISTER ).file

            var img_fd = obj.get_root_stream()?.read()
            assertNotNull( img_fd, "Failed opening image" )
            img_fd.close()

            // Hack delete
            val s = obj.get_root_stream()!!
            h.imgdb.delete( s.get_stream_id(),
                            s.get_priority(),
                            s.get_extension() )
            h.imgdb.commit()

            img_fd = obj.get_root_stream()?.read()
            assertNull( img_fd, "Remove failed" )
        }

        // Start a new session and recover the file
        Database().apply {
            enable_write_access()
        }.let { h ->
            val cyan = this.utils._load_data( TestUtils.cyan )
            val obj = h.register_file( cyan.toString(), NAME_POLICY_DONT_REGISTER ).file

            val img_fd = obj.get_root_stream()?.read()
            assertTrue( this.utils._diff_data( img_fd!!, TestUtils.cyan ),
                    "Image not recovered" )
        }
    }

    @Test
    fun test_recover_corrupted() {

        // Add the file, and corrupt it
        Database().apply {
            enable_write_access()
        }.let { h ->
            val magenta = this.utils._load_data( TestUtils.magenta )
            val obj = h.register_file( magenta.toString(), NAME_POLICY_DONT_REGISTER ).file

            val img_fd = obj.get_root_stream()?.read()
            assertNotNull( img_fd, "Failed opening image" )
            img_fd.close()

            val s = obj.get_root_stream()!!
            h.imgdb._debug_write( s.get_stream_id(),
                                  s.get_priority(),
                                  s.get_extension() )?.use {
                                        it.write( "this is junk".toByteArray() )
                                  }


            assertFalse( this.utils._diff_data( obj.get_root_stream()!!.read()!!,
                                                TestUtils.magenta ),
                "Corruption failed" )
        }

        // Add the file, and corrupt it
        Database().apply {
            enable_write_access()
        }.let { h ->
            val magenta = this.utils._load_data( TestUtils.magenta )

            val obj = h.register_file( magenta.toString(), NAME_POLICY_DONT_REGISTER ).file

            assertTrue( this.utils._diff_data( obj.get_root_stream()!!.read()!!,
                                               TestUtils.magenta ),
                "Image not recovered" )
        }
    }

    @Test
    fun test_name() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val white = this.utils._load_data( TestUtils.white )

            val obj = h.register_file( white.toString() ).file

            assertEquals( TestUtils.white, obj.get_name(), "Name not loaded" )

            val origin_names = obj.get_origin_names()
            assertEquals( 1, origin_names.size, "Name count does not match" )
            assertEquals( TestUtils.white, origin_names[0],
                    "Unexpected name in origin list" )
        }
    }

    @Test
    fun test_repr() {
        Database().apply {
            enable_write_access()
        }.let { h ->

            val white = this.utils._load_data( TestUtils.white )
            val black = this.utils._load_data( TestUtils.black )

            val w_f = h.register_file( white.toString() ).file
            val k_f = h.register_file( black.toString(), NAME_POLICY_DONT_SET ).file

            assertEquals( TestUtils.white, w_f.get_repr(),
                    "Repr on white did not return name" )
            assertEquals( "%016x.%s".format( k_f.get_id(), k_f.get_root_stream()?.get_extension() ),
                    k_f.get_repr(), "Repr on black did not return default name" )
        }
    }

    @Test
    fun test_log_names_single() {
        Database().apply {
            enable_write_access()
        }.let { h ->

            val white = this.utils._load_data( TestUtils.white )
            val black = this.utils._load_data( TestUtils.black )

            val w_f = h.register_file( white.toString() ).file
            val k_f = h.register_file( black.toString(), NAME_POLICY_DONT_REGISTER ).file

            assertTrue( TestUtils.white in w_f.get_origin_names(),
                    "Name list on white did not return single name" )
            assertTrue( k_f.get_origin_names().isEmpty(),
                    "Name list on black did not return empty" )
        }
    }

    @Test
    fun test_log_all_names() {
        Database().apply {
            enable_write_access()
        }.let { h ->

            val white = this.utils._load_data( TestUtils.white )
            val black = this.utils._load_data( TestUtils.black )

            val w_f = h.register_file( white.toString() ).file
            val k_f = h.register_file( black.toString() ).file

            h.merge_objects( w_f, k_f )

            val names = w_f.get_origin_names( true )
            assertTrue( TestUtils.white in names,
                    "Name list did not return white" )
            assertTrue( TestUtils.black in names,
                    "Name list did not return black" )
            assertEquals( 2, names.size,
                    "Name list had an unexpected number of names" )
        }
    }

    @Test
    fun test_duplicate_name() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val grey = this.utils._load_data( TestUtils.grey )
            h.register_file( grey.toString() )
        }

        Database().apply {
            enable_write_access()
        }.let { h ->
            val grey2 = this.utils._load_data( TestUtils.grey )
            val obj = h.register_file( grey2.toString() ).file

            val names = obj.get_origin_names()
            assertTrue( TestUtils.grey in names, "Name not loaded" )
            assertEquals( 1, names.size, "Name count does not match" )
        }
    }

    @Test
    fun test_different_names() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val grey = this.utils._load_data( TestUtils.grey )
            h.register_file( grey.toString() )
        }

        Database().apply {
            enable_write_access()
        }.let { h ->
            val grey2 = this.utils._load_data( TestUtils.grey, "altname.png" )
            val obj = h.register_file( grey2.toString() ).file

            val names = obj.get_origin_names()
            assertTrue( TestUtils.grey in names, "First name not loaded" )
            assertTrue( "altname.png" in names, "Second name not loaded" )
            assertEquals( 2, names.size, "Name count does not match" )
        }
    }

    @Test
    fun test_load_name() {
        Database().apply {
            enable_write_access()
        }.let { h ->

            val black = this.utils._load_data( TestUtils.black )
            val obj = h.register_file( black.toString(), NAME_POLICY_DONT_REGISTER ).file

            assertNull( obj.get_name(),
                    "Name set when it shouldn\'t have been" )
            assertTrue( obj.get_origin_names().isEmpty(),
                    "Name registered when it shouldn\'t have been" )
        }

        Database().apply {
            enable_write_access()
        }.let { h ->

            val black = this.utils._load_data( TestUtils.black )
            val obj = h.register_file( black.toString(), NAME_POLICY_DONT_SET ).file

            assertNull( obj.get_name(),
                    "Name set when it shouldn\'t have been" )
            assertEquals( 1, obj.get_origin_names().size,
                    "Name not registered when it should\'ve been" )
            assertTrue( TestUtils.black in obj.get_origin_names(),
                    "Name not registered when it should\'ve been" )
        }

        Database().apply {
            enable_write_access()
        }.let { h ->

            val black = this.utils._load_data( TestUtils.black )
            val obj = h.register_file( black.toString() ).file

            assertEquals( TestUtils.black, obj.get_name(),
                    "Name not set when it should\'ve been" )
        }
    }

    @Test
    fun test_fetch_missing_tag() {
        Database().let { h ->
            assertFailsWith<NoSuchElementException>( "Did not except on missing tag" ) {
                h.get_tag( "tag_that_doesnt_exist" )
            }
        }
    }

    @Test
    fun test_create_bad_tag() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            assertFailsWith<IllegalArgumentException>( "Did not except on bad tag name" ) {
                h.make_tag( "a/tag" )
            }
        }
    }

    @Test
    fun test_create_tag() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val tag = h.make_tag( "a_tag" )
            val tag2 = h.get_tag( "a_tag" )

            assertEquals( tag.get_id(), tag2.get_id(),
                    "Tag ID mismatch" )
        }
    }

    @Test
    fun test_tag_file() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val black = this.utils._load_data( TestUtils.black )

            val obj = h.register_file( black.toString(), NAME_POLICY_DONT_SET ).file
            val tag = h.make_tag( "black" )
            obj.assign( tag )

            val files = tag.get_files()
            assertEquals( 1, files.size,
                    "Unexpected number of files" )
            assertEquals( obj.get_id(), files[0].get_id(),
                    "Incorrect file returned" )
        }
    }

    @Test
    fun test_file_has_tag() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val black = this.utils._load_data( TestUtils.black )

            val obj = h.register_file( black.toString(), NAME_POLICY_DONT_SET ).file
            val tag = h.make_tag( "black" )
            obj.assign( tag )

            val tags = obj.get_tags()
            assertEquals( 1, tags.size,
                    "Unexpected number of tags" )
            assertEquals( tag.get_id(), tags[0].get_id(),
                    "Incorrect tag returned" )
        }
    }

    @Test
    fun test_tag_multi_file() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val red = this.utils._load_data( TestUtils.red )
            val green = this.utils._load_data( TestUtils.green )
            val blue = this.utils._load_data( TestUtils.blue )

            val ro = h.register_file( red.toString(), NAME_POLICY_DONT_SET ).file
            val go = h.register_file( green.toString(), NAME_POLICY_DONT_SET ).file
            val bo = h.register_file( blue.toString(), NAME_POLICY_DONT_SET ).file

            val mt = h.make_tag( "magenta" )
            val yt = h.make_tag( "yellow" )
            val ct = h.make_tag( "cyan" )

            ro.assign( mt )
            bo.assign( mt )

            ro.assign( yt )
            go.assign( yt )

            go.assign( ct )
            bo.assign( ct )

            val magenta = mt.get_files()
            val yellow = yt.get_files()
            val cyan = ct.get_files()

            assertEquals( 2, magenta.size,
                    "Unexpected number of files (magenta)" )
            assertEquals( 2, yellow.size,
                    "Unexpected number of files (yellow)" )
            assertEquals( 2, cyan.size,
                    "Unexpected number of files (cyan)" )

            assertTrue( ro in magenta, "Red not in magenta" )
            assertTrue( bo in magenta, "Blue not in magenta" )

            assertTrue( ro in yellow, "Red not in yellow" )
            assertTrue( go in yellow, "Green not in yellow" )

            assertTrue( go in cyan, "Green not in cyan" )
            assertTrue( bo in cyan, "Blue not in cyan" )

            val red_in = ro.get_tags()
            val green_in = go.get_tags()
            val blue_in = bo.get_tags()

            assertEquals( 2, red_in.size,
                    "Unexpected number of tags (red)" )
            assertEquals( 2, green_in.size,
                    "Unexpected number of tags (green)" )
            assertEquals( 2, blue_in.size,
                    "Unexpected number of tags (blue)" )

            assertTrue( mt in red_in, "Red does not have magenta" )
            assertTrue( yt in red_in, "Red does not have yellow" )

            assertTrue( yt in green_in, "Green does not have yellow" )
            assertTrue( ct in green_in, "Green does not have cyan" )

            assertTrue( mt in blue_in, "Blue does not have magenta" )
            assertTrue( ct in blue_in, "Blue does not have cyan" )
        }
    }

    @Test
    fun test_create_album() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val obj_id = h.create_album().get_id()

            val album = h.get_object_by_id( obj_id )
            assertNotNull( album, "Unable to get album after creation" )
            assertTrue( album is Group, "Created album is not a group" )
        }
    }

    @Test
    fun test_create_album_with_text() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val obj_id = h.create_album( text = "This is some test text" ).get_id()

            val album = h.get_object_by_id( obj_id ) as? Album
            assertNotNull( album, "Unable to get album after creation" )
            assertEquals( "This is some test text", album.get_text(),
                    "Album text not properly returned" )
        }
    }

    @Test
    fun test_album_set_text() {
        var obj_id: Id = 0

        Database().apply {
            enable_write_access()
        }.let { h ->
            val album = h.create_album().apply {
                set_text( "This is some test text" )
            }
            obj_id = album.get_id()
        }

        Database().let { h ->
            val album = h.get_object_by_id( obj_id ) as? Album

            assertNotNull( album, "Unable to get album after creation" )
            assertEquals( "This is some test text", album.get_text(),
                    "Album text not properly returned" )
        }
    }

    @Test
    fun test_add_files_to_album() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val red = this.utils._load_data( TestUtils.red )
            val green = this.utils._load_data( TestUtils.green )
            val blue = this.utils._load_data( TestUtils.blue )

            val album = h.create_album()

            val ro = h.register_file( red.toString(), NAME_POLICY_DONT_SET ).file
            val go = h.register_file( green.toString(), NAME_POLICY_DONT_SET ).file
            val bo = h.register_file( blue.toString(), NAME_POLICY_DONT_SET ).file

            ro.assign( album )
            go.assign( album )
            bo.assign( album )

            val files = album.get_files()

            assertTrue( ro in files, "Red not in album" )
            assertTrue( go in files, "Green not in album" )
            assertTrue( bo in files, "Blue not in album" )
        }
    }

    @Test
    fun test_order_then_reorder() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val red = this.utils._load_data( TestUtils.red )
            val green = this.utils._load_data( TestUtils.green )
            val blue = this.utils._load_data( TestUtils.blue )

            val album = h.create_album()

            val ro = h.register_file( red.toString(), NAME_POLICY_DONT_SET ).file
            val go = h.register_file( green.toString(), NAME_POLICY_DONT_SET ).file
            val bo = h.register_file( blue.toString(), NAME_POLICY_DONT_SET ).file

            ro.assign( album, 2 )
            go.assign( album, 0 )
            bo.assign( album, 1 )

            var files = album.get_files()

            assertEquals( go, files[0], "Green not in first position after add with order" )
            assertEquals( bo, files[1], "Blue not in second position after add with order" )
            assertEquals( ro, files[2], "Red not in third position after add with order" )

            ro.reorder( album, 2 )
            go.reorder( album, 1 )
            bo.reorder( album, 0 )

            files = album.get_files()

            assertEquals( bo, files[0], "Blue not in first position after reorder" )
            assertEquals( go, files[1], "Green not in second position after reorder" )
            assertEquals( ro, files[2], "Red not in third position after reorder" )
        }
    }

    @Test
    fun test_set_order_in_album() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val red = this.utils._load_data( TestUtils.red )
            val green = this.utils._load_data( TestUtils.green )
            val blue = this.utils._load_data( TestUtils.blue )

            val album = h.create_album()

            val ro = h.register_file( red.toString(), NAME_POLICY_DONT_SET ).file
            val go = h.register_file( green.toString(), NAME_POLICY_DONT_SET ).file
            val bo = h.register_file( blue.toString(), NAME_POLICY_DONT_SET ).file

            ro.assign( album, 2 )
            go.assign( album, 0 )
            bo.assign( album, 1 )

            var files = album.get_files()

            assertEquals( go, files[0], "Green not in first position after add with order" )
            assertEquals( bo, files[1], "Blue not in second position after add with order" )
            assertEquals( ro, files[2], "Red not in third position after add with order" )

            album.set_order( listOf( bo, go, ro ) )
            files = album.get_files()

            assertEquals( bo, files[0], "Blue not in first position after reorder" )
            assertEquals( go, files[1], "Green not in second position after reorder" )
            assertEquals( ro, files[2], "Red not in third position after reorder" )
        }
    }

    @Test
    fun test_set_duplicate() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val white = this.utils._load_data( TestUtils.white )
            val black = this.utils._load_data( TestUtils.black )

            val wo = h.register_file( white.toString(), NAME_POLICY_DONT_SET ).file
            val ko = h.register_file( black.toString(), NAME_POLICY_DONT_SET ).file

            val ko_id = ko.get_id()
            val ko_hash = ko.get_root_stream()?.get_hash()

            h.merge_objects( wo, ko )

            assertNull( h.get_object_by_id( ko_id ), "Blacks ID still exists" )

            val dups = wo.get_duplicate_streams()
            assertEquals( 1, dups.size, "Unexpected number of dups on white" )
            assertEquals( ko_hash, dups[0].get_hash(),
                                "Black not in duplicate list of white" )
        }
    }

    @Test
    fun test_set_root() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val red = this.utils._load_data( TestUtils.red )
            val yellow = this.utils._load_data( TestUtils.yellow )
            val green = this.utils._load_data( TestUtils.green )
            val blue = this.utils._load_data( TestUtils.blue )
            val black = this.utils._load_data( TestUtils.black )

            val ro = h.register_file( red.toString(), NAME_POLICY_DONT_SET ).file
            val yo = h.register_file( yellow.toString(), NAME_POLICY_DONT_SET ).file
            val go = h.register_file( green.toString(), NAME_POLICY_DONT_SET ).file
            val bo = h.register_file( blue.toString(), NAME_POLICY_DONT_SET ).file
            val ko = h.register_file( black.toString(), NAME_POLICY_DONT_SET ).file

            val ro_hash = ro.get_root_stream()?.get_hash()
            val yo_hash = yo.get_root_stream()?.get_hash()
            val go_hash = go.get_root_stream()?.get_hash()
            val bo_hash = bo.get_root_stream()?.get_hash()

            h.merge_objects( ro, yo )
            h.merge_objects( ro, go )
            h.merge_objects( ro, bo )

            var dups = ro.get_duplicate_streams().map { it.get_hash() }
            assertEquals( 3, dups.size, "Unexpected number of dups on red" )
            assertEquals( ro_hash, ro.get_root_stream()?.get_hash(),
                                "Red not primary stream after merge" )
            assertTrue( yo_hash in dups, "Yellow not in duplicate list of red" )
            assertTrue( go_hash in dups, "Green not in duplicate list of red" )
            assertTrue( bo_hash in dups, "Blue not in duplicate list of red" )

            assertFailsWith<IllegalArgumentException>( "Attempt to set black as root stream succeeded" ) {
                ro.set_root_stream( ko.get_root_stream()!! )
            }

            assertFailsWith<IllegalArgumentException>( "Attempt to set root to root succeeded" ) {
                ro.set_root_stream( ro.get_root_stream()!! )
            }

            ro.set_root_stream( ro.get_stream( "dup:${go_hash}" )!! )

            dups = ro.get_duplicate_streams().map { it.get_hash() }
            assertEquals( 3, dups.size, "Unexpected number of dups on red after set" )
            assertEquals( go_hash, ro.get_root_stream()?.get_hash(),
                                "Green not primary stream after set" )
            assertTrue( ro_hash in dups, "Red not in duplicate list of red after set" )
            assertTrue( yo_hash in dups, "Yellow not in duplicate list of red after set" )
            assertTrue( bo_hash in dups, "Blue not in duplicate list of red after set" )

            dups = ro.get_duplicate_streams().map { it.get_name() }
            assertEquals( ".", ro.get_root_stream()?.get_name(), "Incorrect name for primary stream after set" )
            assertFalse( "." in dups, "Root name in duplicate list after set" )
        }
    }

    @Test
    fun test_set_duplicate_of_variant() {
        Database().apply {
            enable_write_access()
        }.let { h ->
            val red = this.utils._load_data( TestUtils.red )
            val yellow = this.utils._load_data( TestUtils.yellow )
            val green = this.utils._load_data( TestUtils.green )
            val blue = this.utils._load_data( TestUtils.blue )

            val ro = h.register_file( red.toString(), NAME_POLICY_DONT_SET ).file
            val yo = h.register_file( yellow.toString(), NAME_POLICY_DONT_SET ).file
            val go = h.register_file( green.toString(), NAME_POLICY_DONT_SET ).file
            val bo = h.register_file( blue.toString(), NAME_POLICY_DONT_SET ).file

            go.set_variant_of( ro )
            h.merge_objects( ro, yo )
            h.merge_objects( go, bo )

            assertTrue( go in ro.get_variants(), "Green not variant of red" )

            assertEquals( 1, ro.get_duplicate_streams().size, "Red duplicate list mismatch" )
            assertEquals( 1, go.get_duplicate_streams().size, "Green duplicate list mismatch" )

            assertEquals( 0, ro.get_variants_of().size, "Red is a variant" )
            assertEquals( 1, go.get_variants_of().size, "Green is not a variant" )

            assertEquals( 1, ro.get_variants().size, "Red variant list mismatch" )
            assertEquals( 0, go.get_variants().size, "Green variant list mismatch" )
        }
    }

    /* TODO
    def test_duplicates_moved( self ):

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        h = hdbfs.Database()
        h.enable_write_access()

        ro = h.register_file( red, False )
        yo = h.register_file( yellow, False )
        go = h.register_file( green, False )
        bo = h.register_file( blue, False )

        ro_id = ro.get_id()
        yo_id = yo.get_id()
        go_id = go.get_id()
        bo_id = bo.get_id()

        ro_s_id = ro.get_root_stream().get_stream_id()
        yo_s_id = yo.get_root_stream().get_stream_id()
        go_s_id = go.get_root_stream().get_stream_id()
        bo_s_id = go.get_root_stream().get_stream_id()

        h.merge_objects( ro, yo )
        h.merge_objects( go, bo )
        h.merge_objects( ro, go )

        assertEquals( ro.get_id(), ro_id, 'Red was removed' )
        assertEquals( h.get_object_by_id( yo_id ), None, 'Yellow was not removed' )
        assertEquals( h.get_object_by_id( go_id ), None, 'Green was not removed' )
        assertEquals( h.get_object_by_id( bo_id ), None, 'Blue was not removed' )

        dups = map( lambda x: x.get_stream_id(), ro.get_duplicate_streams() )
        self.assertFalse( ro_s_id in dups, 'Red in dup list' )
        self.assertTrue( yo_s_id in dups, 'Yellow not in dup list' )
        self.assertTrue( go_s_id in dups, 'Green not in dup list' )
        self.assertTrue( bo_s_id in dups, 'Blue not in dup list' )

    def test_variants_moved( self ):

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        h = hdbfs.Database()
        h.enable_write_access()

        ro = h.register_file( red, False )
        yo = h.register_file( yellow, False )
        go = h.register_file( green, False )
        bo = h.register_file( blue, False )

        yo.set_variant_of( ro )
        bo.set_variant_of( go )
        h.merge_objects( ro, go )

        assertEquals( len( ro.get_variants_of() ), 0, 'Red is a variant' )
        assertEquals( len( yo.get_variants_of() ), 1, 'Yellow is not a variant' )
        assertEquals( len( bo.get_variants_of() ), 1, 'Blue is not a variant' )

        assertEquals( len( ro.get_duplicate_streams() ), 1, 'Red duplicate list mismatch' )
        assertEquals( len( ro.get_variants() ), 2, 'Red variant list mismatch' )

        variants = ro.get_variants()
        self.assertTrue( yo in variants, 'Yellow not in variant list' )
        self.assertTrue( bo in variants, 'Blue not in variant list' )

    def test_albums_moved( self ):

        red = self._load_data( self.red )
        yellow = self._load_data( self.yellow )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        h = hdbfs.Database()
        h.enable_write_access()

        album = h.create_album()

        ro = h.register_file( red, False )
        yo = h.register_file( yellow, False )
        go = h.register_file( green, False )
        bo = h.register_file( blue, False )

        yo.assign( album, 2 )
        bo.assign( album, 3 )
        ro.assign( album, 1 )

        h.merge_objects( go, yo )

        files = album.get_files()
        assertEquals( len( files ), 3, 'Album size mismatch' )
        assertEquals( files[0], ro, 'Red not first in album' )
        assertEquals( files[1], go, 'Green not second in album' )
        assertEquals( files[2], bo, 'Blue not third in album' )

    def test_tags_moved( self ):

        red = self._load_data( self.red )
        green = self._load_data( self.green )
        blue = self._load_data( self.blue )

        h = hdbfs.Database()
        h.enable_write_access()

        tag1 = h.make_tag( 'a_tag' )
        tag2 = h.make_tag( 'b_tag' )
        tag3 = h.make_tag( 'c_tag' )

        ro = h.register_file( red, False )
        go = h.register_file( green, False )
        bo = h.register_file( blue, False )

        ro.assign( tag1 )
        
        go.assign( tag1 )
        go.assign( tag2 )

        bo.assign( tag3 )

        h.merge_objects( ro, go )
        h.merge_objects( ro, bo )

        assertEquals( len( ro.get_tags() ), 3, 'Red tag list mismatch' )

        tags = ro.get_tags()
        self.assertTrue( tag1 in tags, 'tag1 not in dup list' )
        self.assertTrue( tag2 in tags, 'tag2 not in dup list' )
        self.assertTrue( tag3 in tags, 'tag3 not in dup list' )*/
}
