package ca._4haven.higu.hdbfs

import ca._4haven.higu.hdbfs.ark.*
import ca._4haven.higu.hdbfs.imgdb.*
import kotlin.test.*
import kotlin.io.path.isDirectory
import java.nio.file.NoSuchFileException

val PRI_THUMB = 1000
val PRI_DATA = 2000

class ImgDbTest {
    val utils = TestUtils()
    lateinit var idb: StreamDatabase

    @BeforeTest
    fun setUp() {
        this.utils.init_env()

        val data_config = Config( this.utils.db_path.toString() )
        this.idb = StreamDatabase( data_config )
    }

    @AfterTest
    fun tearDown() {
        this.utils.uninit_env()
    }

    @Test
    fun test_imgdat_structure() {

        val red = this.utils._load_data( TestUtils.red )
        val green = this.utils._load_data( TestUtils.green )

        this.idb.load_data( red.toString(), 0x123, PRI_DATA, "png" )
        this.idb.load_data( green.toString(), 0xabc, PRI_DATA, "dat" )

        // Should not be moved before commit
        assertTrue( red.isFile(), "Image moved before commit" )
        this.idb.commit()

        assertFalse( red.isFile(), "Old image was not removed" )

        assertTrue( this.utils.db_path.resolve( "imgdat/000/000" )
                        .toFile().isDirectory(), "Image data directory not created" )

        assertTrue( this.utils.db_path.resolve( "imgdat/000/000/0000000000000123.png" )
                        .toFile().isFile(), "Image file moved to incorrect location" )

        assertTrue( this.utils.db_path.resolve( "imgdat/000/000/0000000000000abc.dat" )
                        .toFile().isFile(), "Image file moved to incorrect location" )

        val red_fd = this.idb.read( 0x123, PRI_DATA, "png" )
        assertTrue( this.utils._diff_data( red_fd!!, TestUtils.red ),
                "Image not read properly from library" )

        val uk_fd = this.idb.read( 0xabc, PRI_DATA, "png" )
        assertNull( uk_fd, "Missing file somehow read from library" )
    }

    @Test
    fun test_tbdat_structure() {

        val red = this.utils._load_data( TestUtils.red )

        this.idb.load_data( red.toString(), 0x123, PRI_THUMB, "png" )

        // Should not be moved before commit
        assertTrue( red.isFile(), "Image moved before commit" )
        this.idb.commit()

        assertFalse( red.isFile(), "Old image was not removed" )

        assertTrue( this.utils.db_path.resolve( "tbdat/000/000" )
                        .toFile().isDirectory(), "Image data directory not created" )

        assertTrue( this.utils.db_path.resolve( "tbdat/000/000/0000000000000123.png" )
                        .toFile().isFile(), "Image file moved to incorrect location" )

        val red_fd = this.idb.read( 0x123, PRI_THUMB, "png" )
        assertTrue( this.utils._diff_data( red_fd!!, TestUtils.red ),
                "Image not read properly from library" )

        val uk_fd = this.idb.read( 0xabc, PRI_THUMB, "png" )
        assertNull( uk_fd, "Missing file somehow read from library" )
    }

    @Test
    fun test_multiple_folders() {

        val red = this.utils._load_data( TestUtils.red )
        val yellow = this.utils._load_data( TestUtils.yellow )
        val green = this.utils._load_data( TestUtils.green )
        val cyan = this.utils._load_data( TestUtils.cyan )
        val blue = this.utils._load_data( TestUtils.blue )
        val magenta = this.utils._load_data( TestUtils.magenta )

        this.idb.load_data( red.toString(), 0x123, PRI_DATA, "png" )
        this.idb.load_data( yellow.toString(), 0xabc, PRI_THUMB, "png" )
        this.idb.load_data( green.toString(), 0xdef, PRI_DATA, "png" )
        this.idb.load_data( cyan.toString(), 0x123abc, PRI_DATA, "png" )
        this.idb.load_data( blue.toString(), 0xabc123abc, PRI_THUMB, "png" )
        this.idb.load_data( magenta.toString(), 0xabc123def, PRI_DATA, "png" )
        this.idb.commit()

        assertTrue( this.utils.db_path.resolve( "imgdat/000/000" )
                        .toFile().isDirectory(), "Image data directory 000 not created" )
        assertTrue( this.utils.db_path.resolve( "tbdat/000/000" )
                        .toFile().isDirectory(), "Thumb data directory 000 not created" )
        assertTrue( this.utils.db_path.resolve( "imgdat/000/123" )
                        .toFile().isDirectory(), "Image data directory 123 not created" )
        assertTrue( this.utils.db_path.resolve( "imgdat/abc/123" )
                        .toFile().isDirectory(), "Image data directory abc/123 not created" )
        assertTrue( this.utils.db_path.resolve( "tbdat/abc/123" )
                        .toFile().isDirectory(), "Thumb data directory abc/123 not created" )

        assertTrue( this.utils.db_path.resolve( "imgdat/000/000/0000000000000123.png" )
                        .toFile().isFile(), "Image file 123 moved to incorrect location" )
        assertTrue( this.utils.db_path.resolve( "tbdat/000/000/0000000000000abc.png" )
                        .toFile().isFile(), "Thumb file abc moved to incorrect location" )
        assertTrue( this.utils.db_path.resolve( "imgdat/000/000/0000000000000def.png" )
                        .toFile().isFile(), "Image file def moved to incorrect location" )
        assertTrue( this.utils.db_path.resolve( "imgdat/000/123/0000000000123abc.png" )
                        .toFile().isFile(), "Image file 123abc moved to incorrect location" )
        assertTrue( this.utils.db_path.resolve( "tbdat/abc/123/0000000abc123abc.png" )
                        .toFile().isFile(), "Thumb file abc123abc moved to incorrect location" )
        assertTrue( this.utils.db_path.resolve( "imgdat/abc/123/0000000abc123def.png" )
                        .toFile().isFile(), "Image file abc123def moved to incorrect location" )

        val red_fd = this.idb.read( 0x123, PRI_DATA, "png" )
        assertTrue( this.utils._diff_data( red_fd!!, TestUtils.red ),
                "Image 123 not read properly from library" )
        val yellow_fd = this.idb.read( 0xabc, PRI_THUMB, "png" )
        assertTrue( this.utils._diff_data( yellow_fd!!, TestUtils.yellow ),
                "Image not read properly from library" )
        val green_fd = this.idb.read( 0xdef, PRI_DATA, "png" )
        assertTrue( this.utils._diff_data( green_fd!!, TestUtils.green ),
                "Image not read properly from library" )
        val cyan_fd = this.idb.read( 0x123abc, PRI_DATA, "png" )
        assertTrue( this.utils._diff_data( cyan_fd!!, TestUtils.cyan ),
                "Image not read properly from library" )
        val blue_fd = this.idb.read( 0xabc123abc, PRI_THUMB, "png" )
        assertTrue( this.utils._diff_data( blue_fd!!, TestUtils.blue ),
                "Image not read properly from library" )
        val magenta_fd = this.idb.read( 0xabc123def, PRI_DATA, "png" )
        assertTrue( this.utils._diff_data( magenta_fd!!, TestUtils.magenta ),
                "Image not read properly from library" )
    }

    @Test
    fun test_commit_and_rollback() {

        // State should be clean on start-up
        assertEquals( StreamDatabase.State.CLEAN, this.idb.get_state(),
                        "Database not clean on start-up" )

        val red = this.utils._load_data( TestUtils.red )
        this.idb.load_data( red.toString(), 0x123, PRI_DATA, "png" )

        assertEquals( StreamDatabase.State.DIRTY, this.idb.get_state(),
                        "Database not dirty after load" )

        // Should not be moved before commit
        assertTrue( red.isFile(), "Image moved before commit" )
        
        this.idb.prepare_commit()

        assertFalse( red.isFile(), "Image not moved after prepare" )
        
        assertEquals( StreamDatabase.State.PREPARED, this.idb.get_state(),
                        "Database not prepared after prepare" )

        this.idb.unprepare_commit()

        assertTrue( red.isFile(), "Image not returned after unprepare" )

        assertEquals( StreamDatabase.State.DIRTY, this.idb.get_state(),
                        "Database not dirty after unprepare" )

        this.idb.prepare_commit()

        assertFalse( red.isFile(), "Image not moved after prepare/unprepare/prepare" )
        
        assertEquals( StreamDatabase.State.PREPARED, this.idb.get_state(),
                        "Database not prepared after prepare/unprepare/prepare" )
    }

    @Test
    fun test_hard_single_vol() {

        // State should be clean on start-up
        assertEquals( StreamDatabase.State.CLEAN, this.idb.get_state(),
                        "Database not clean on start-up" )

        val red = this.utils._load_data( TestUtils.red )
        val yellow = this.utils._load_data( TestUtils.yellow )
        val green = this.utils._load_data( TestUtils.green )

        this.idb.load_data( red.toString(), 0x1, PRI_DATA, "png" )
        this.idb.commit()

        this.idb.load_data( yellow.toString(), 0x2, PRI_THUMB, "png" )
        this.idb.prepare_commit()

        assertTrue( this.utils.db_path.resolve( "imgdat/000/000/0000000000000001.png" )
                        .toFile().isFile(), "File 0x1 missing" )
        assertTrue( this.utils.db_path.resolve( "tbdat/000/000/0000000000000002.png" )
                        .toFile().isFile(), "File 0x2 missing" )

        this.idb.unprepare_commit()

        assertTrue( this.utils.db_path.resolve( "imgdat/000/000/0000000000000001.png" )
                        .toFile().isFile(), "File 0x1 missing after rollback" )
        assertFalse( this.utils.db_path.resolve( "tbdat/000/000/0000000000000002.png" )
                        .toFile().isFile(), "File 0x2 present when should have been removed" )

        this.idb.load_data( green.toString(), 0x3, PRI_DATA, "png" )
        this.idb.prepare_commit()

        assertTrue( this.utils.db_path.resolve( "imgdat/000/000/0000000000000001.png" )
                        .toFile().isFile(), "File 0x1 missing after 3rd commit" )
        assertTrue( this.utils.db_path.resolve( "tbdat/000/000/0000000000000002.png" )
                        .toFile().isFile(), "File 0x2 not re-instated after 3rd commit" )
        assertTrue( this.utils.db_path.resolve( "imgdat/000/000/0000000000000003.png" )
                        .toFile().isFile(), "File 0x3 not added by 3rd commit" )

        this.idb.rollback()

        assertTrue( this.utils.db_path.resolve( "imgdat/000/000/0000000000000001.png" )
                        .toFile().isFile(), "File 0x1 missing after 2nd rollback" )
        assertFalse( this.utils.db_path.resolve( "tbdat/000/000/0000000000000002.png" )
                        .toFile().isFile(), "File 0x2 not removed by 2nd rollback" )
        assertFalse( this.utils.db_path.resolve( "imgdat/000/000/0000000000000003.png" )
                        .toFile().isFile(), "File 0x3 not removed by 2nd rollback" )

        assertEquals( StreamDatabase.State.CLEAN, this.idb.get_state(),
                        "Reset state did not reset state to clean" )

        this.idb.load_data( green.toString(), 0x3, PRI_DATA, "png" )
        this.idb.commit()

        assertTrue( this.utils.db_path.resolve( "imgdat/000/000/0000000000000001.png" )
                        .toFile().isFile(), "File 0x1 missing after 4th commit" )
        assertFalse( this.utils.db_path.resolve( "tbdat/000/000/0000000000000002.png" )
                        .toFile().isFile(), "File 0x2 brought back after reset and commit" )
        assertTrue( this.utils.db_path.resolve( "imgdat/000/000/0000000000000003.png" )
                        .toFile().isFile(), "File 0x3 not re-added by 4th commit" )
    }

    @Test
    fun test_hard_multi_vol() {

        // State should be clean on start-up
        assertEquals( StreamDatabase.State.CLEAN, this.idb.get_state(),
                        "Database not clean on start-up" )

        val red = this.utils._load_data( TestUtils.red )
        val yellow = this.utils._load_data( TestUtils.yellow )
        val green = this.utils._load_data( TestUtils.green )

        this.idb.load_data( red.toString(), 0x1001, PRI_DATA, "png" )
        this.idb.commit()
        this.idb.load_data( yellow.toString(), 0x2001, PRI_DATA, "png" )
        this.idb.prepare_commit()

        assertTrue( this.utils.db_path.resolve( "imgdat/000/001/0000000000001001.png" )
                        .toFile().isFile(), "File 0x1001 missing" )
        assertTrue( this.utils.db_path.resolve( "imgdat/000/002/0000000000002001.png" )
                        .toFile().isFile(), "File 0x2001 missing" )

        this.idb.unprepare_commit()

        assertTrue( this.utils.db_path.resolve( "imgdat/000/001/0000000000001001.png" )
                        .toFile().isFile(), "File 0x1001 missing after rollback" )
        assertFalse( this.utils.db_path.resolve( "imgdat/000/002/0000000000002001.png" )
                        .toFile().isFile(), "File 0x2001 present when should have been removed" )

        this.idb.load_data( green.toString(), 0x3001, PRI_DATA, "png" )
        this.idb.prepare_commit()

        assertTrue( this.utils.db_path.resolve( "imgdat/000/001/0000000000001001.png" )
                        .toFile().isFile(), "File 0x1001 missing after 3rd commit" )
        assertTrue( this.utils.db_path.resolve( "imgdat/000/002/0000000000002001.png" )
                        .toFile().isFile(), "File 0x2001 not re-instated after 3rd commit" )
        assertTrue( this.utils.db_path.resolve( "imgdat/000/003/0000000000003001.png" )
                        .toFile().isFile(), "File 0x3001 added by 3rd commit" )

        this.idb.rollback()

        assertTrue( this.utils.db_path.resolve( "imgdat/000/001/0000000000001001.png" )
                        .toFile().isFile(), "File 0x1001 missing after 2nd rollback" )
        assertFalse( this.utils.db_path.resolve( "imgdat/000/002/0000000000002001.png" )
                        .toFile().isFile(), "File 0x2001 not removed by 2nd rollback" )
        assertFalse( this.utils.db_path.resolve( "imgdat/000/003/0000000000003001.png" )
                        .toFile().isFile(), "File 0x3001 not removed by 2nd rollback" )

        assertEquals( StreamDatabase.State.CLEAN, this.idb.get_state(),
                        "Reset state did not reset state to clean" )

        this.idb.load_data( green.toString(), 0x3001, PRI_DATA, "png" )
        this.idb.commit()

        assertTrue( this.utils.db_path.resolve( "imgdat/000/001/0000000000001001.png" )
                        .toFile().isFile(), "File 0x1001 missing after 4th commit" )
        assertFalse( this.utils.db_path.resolve( "imgdat/000/002/0000000000002001.png" )
                        .toFile().isFile(), "File 0x2001 brought back after reset and commit" )
        assertTrue( this.utils.db_path.resolve( "imgdat/000/003/0000000000003001.png" )
                        .toFile().isFile(), "File 0x3001 not re-added by 4th commit" )
    }

    @Test
    fun test_hard_multi_pri() {

        // State should be clean on start-up
        assertEquals( StreamDatabase.State.CLEAN, this.idb.get_state(),
                        "Database not clean on start-up" )

        val red = this.utils._load_data( TestUtils.red )
        val yellow = this.utils._load_data( TestUtils.yellow )
        val green = this.utils._load_data( TestUtils.green )

        this.idb.load_data( red.toString(), 0x1001, PRI_DATA, "png" )
        this.idb.commit()
        this.idb.load_data( yellow.toString(), 0x1002, PRI_THUMB, "png" )
        this.idb.prepare_commit()

        assertTrue( this.utils.db_path.resolve( "imgdat/000/001/0000000000001001.png" )
                        .toFile().isFile(), "File 0x1001 missing" )
        assertTrue( this.utils.db_path.resolve( "tbdat/000/001/0000000000001002.png" )
                        .toFile().isFile(), "File 0x1002 missing" )

        this.idb.unprepare_commit()

        assertTrue( this.utils.db_path.resolve( "imgdat/000/001/0000000000001001.png" )
                        .toFile().isFile(), "File 0x1001 missing after rollback" )
        assertFalse( this.utils.db_path.resolve( "tbdat/000/001/0000000000001002.png" )
                        .toFile().isFile(), "File 0x1002 present when should have been removed" )

        this.idb.load_data( green.toString(), 0x3001, PRI_DATA, "png" )
        this.idb.prepare_commit()

        assertTrue( this.utils.db_path.resolve( "imgdat/000/001/0000000000001001.png" )
                        .toFile().isFile(), "File 0x1001 missing after 3rd commit" )
        assertTrue( this.utils.db_path.resolve( "tbdat/000/001/0000000000001002.png" )
                        .toFile().isFile(), "File 0x1002 not re-instated after 3rd commit" )
        assertTrue( this.utils.db_path.resolve( "imgdat/000/003/0000000000003001.png" )
                        .toFile().isFile(), "File 0x3001 added by 3rd commit" )

        this.idb.rollback()

        assertTrue( this.utils.db_path.resolve( "imgdat/000/001/0000000000001001.png" )
                        .toFile().isFile(), "File 0x1001 missing after 2nd rollback" )
        assertFalse( this.utils.db_path.resolve( "tbdat/000/001/0000000000001002.png" )
                        .toFile().isFile(), "File 0x1002 not removed by 2nd rollback" )
        assertFalse( this.utils.db_path.resolve( "imgdat/000/003/0000000000003001.png" )
                        .toFile().isFile(), "File 0x3001 not removed by 2nd rollback" )

        assertEquals( StreamDatabase.State.CLEAN, this.idb.get_state(),
                        "Reset state did not reset state to clean" )

        this.idb.load_data( green.toString(), 0x3001, PRI_DATA, "png" )
        this.idb.commit()

        assertTrue( this.utils.db_path.resolve( "imgdat/000/001/0000000000001001.png" )
                        .toFile().isFile(), "File 0x1001 missing after 4th commit" )
        assertFalse( this.utils.db_path.resolve( "tbdat/000/001/0000000000001002.png" )
                        .toFile().isFile(), "File 0x1002 brought back after reset and commit" )
        assertTrue( this.utils.db_path.resolve( "imgdat/000/003/0000000000003001.png" )
                        .toFile().isFile(), "File 0x3001 not re-added by 4th commit" )
    }

    @Test
    fun test_rollback_then_commit() {

        assertEquals( StreamDatabase.State.CLEAN, this.idb.get_state(),
                        "Database not clean on start-up" )

        val red = this.utils._load_data( TestUtils.red )
        this.idb.load_data( red.toString(), 0x123, PRI_DATA, "png" )

        assertEquals( StreamDatabase.State.DIRTY, this.idb.get_state(),
                        "Database not dirty after load" )

        assertTrue( red.isFile(), "Image moved before commit" )
        
        this.idb.rollback()

        assertTrue( red.isFile(), "Image moved after no-commit-rollback" )
        
        assertEquals( StreamDatabase.State.CLEAN, this.idb.get_state(),
                        "Database not clean after rollback" )

        this.idb.commit()

        assertTrue( red.isFile(), "Image moved after rollback, commit" )

        assertEquals( StreamDatabase.State.CLEAN, this.idb.get_state(),
                        "Database not clean after rollback then commit" )
    }

    @Test
    fun test_commit_failure() {

        assertEquals( StreamDatabase.State.CLEAN, this.idb.get_state(),
                        "Database not clean on start-up" )

        val red = this.utils._load_data( TestUtils.red )
        this.idb.load_data( red.toString(), 0x123, PRI_DATA, "png" )

        red.delete()
        
        assertFailsWith<NoSuchFileException>( "Commit succeeded on missing file" ) {
            this.idb.commit()
        }

        assertEquals( StreamDatabase.State.DIRTY, this.idb.get_state(),
                        "Database not dirty after failed commit" )
    }

    @Test
    fun test_commit_failure_rollback_single_volume() {

        assertEquals( StreamDatabase.State.CLEAN, this.idb.get_state(),
                        "Database not clean on start-up" )

        val red = this.utils._load_data( TestUtils.red )
        val yellow = this.utils._load_data( TestUtils.yellow )
        val green = this.utils._load_data( TestUtils.green )

        this.idb.load_data( red.toString(), 0x1, PRI_DATA, "png" )
        this.idb.load_data( yellow.toString(), 0x2, PRI_DATA, "png" )
        this.idb.load_data( green.toString(), 0x3, PRI_DATA, "png" )

        yellow.delete()

        assertFailsWith<NoSuchFileException>( "Commit succeeded on missing file" ) {
            this.idb.commit()
        }

        assertTrue( red.isFile(), "File 0x1 not rolled back on failed commit" )
        assertTrue( green.isFile(), "File 0x3 not rolled back on failed commit" )
    }

    @Test
    fun test_commit_failure_rollback_multi_volume() {

        assertEquals( StreamDatabase.State.CLEAN, this.idb.get_state(),
                        "Database not clean on start-up" )

        val red = this.utils._load_data( TestUtils.red )
        val yellow = this.utils._load_data( TestUtils.yellow )
        val green = this.utils._load_data( TestUtils.green )

        this.idb.load_data( red.toString(), 0x1001, PRI_DATA, "png" )
        this.idb.load_data( yellow.toString(), 0x2001, PRI_DATA, "png" )
        this.idb.load_data( green.toString(), 0x3001, PRI_DATA, "png" )

        yellow.delete()

        assertFailsWith<NoSuchFileException>( "Commit succeeded on missing file" ) {
            this.idb.commit()
        }

        assertTrue( red.isFile(), "File 0x1001 not rolled back on failed commit" )
        assertTrue( green.isFile(), "File 0x3001 not rolled back on failed commit" )
    }

    @Test
    fun test_delete() {

        // State should be clean on start-up
        assertEquals( StreamDatabase.State.CLEAN, this.idb.get_state(),
                        "Database not clean on start-up" )

        val red = this.utils._load_data( TestUtils.red )
        val green = this.utils._load_data( TestUtils.green )
        this.idb.load_data( red.toString(), 0x123, PRI_DATA, "png" )
        this.idb.load_data( green.toString(), 0xabc, PRI_THUMB, "png" )

        this.idb.commit()

        this.idb.delete( 0x123, PRI_DATA, "png" )
        this.idb.delete( 0xabc, PRI_THUMB, "png" )

        assertTrue( this.utils.db_path.resolve( "imgdat/000/000/0000000000000123.png" )
                        .toFile().isFile(), "Image file removed before commit" )
        assertTrue( this.utils.db_path.resolve( "tbdat/000/000/0000000000000abc.png" )
                        .toFile().isFile(), "Thumb file removed before commit" )

        this.idb.prepare_commit()

        assertFalse( this.utils.db_path.resolve( "imgdat/000/000/0000000000000123.png" )
                        .toFile().isFile(), "Image file delete failed" )
        assertFalse( this.utils.db_path.resolve( "tbdat/000/000/0000000000000abc.png" )
                        .toFile().isFile(), "Image file delete failed" )

        this.idb.rollback()

        assertTrue( this.utils.db_path.resolve( "imgdat/000/000/0000000000000123.png" )
                        .toFile().isFile(), "Image file rollback from delete failed" )
        assertTrue( this.utils.db_path.resolve( "tbdat/000/000/0000000000000abc.png" )
                        .toFile().isFile(), "Image file rollback from delete failed" )
    }
}
