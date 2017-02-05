import calendar
import time

import hdbfs.db

TYPE_NILL       = 0
TYPE_FILE       = 1000
TYPE_FILE_DUP   = 1001
TYPE_FILE_VAR   = 1002
TYPE_GROUP      = 2000
TYPE_ALBUM      = 2001
TYPE_CLASSIFIER = 2002

ORDER_VARIENT   = -1
ORDER_DUPLICATE = -2

LEGACY_REL_CHILD       = 0
LEGACY_REL_DUPLICATE   = 1000
LEGACY_REL_VARIANT     = 1001
LEGACY_REL_CLASS       = 2000

def upgrade_from_0_to_1( log, session ):

    print 'Database upgrade from VER 0 -> VER 1'

    session.execute( 'ALTER TABLE mfl ADD COLUMN parent INTEGER' )
    session.execute( 'ALTER TABLE mfl ADD COLUMN gorder INTEGER' )

    return 1, 0

def upgrade_from_1_to_2( log, session ):

    log.info( 'Database upgrade from VER 1 -> VER 2' )

    session.execute( 'CREATE TABLE objl ( '
                     '  id      INTEGER PRIMARY KEY, '
                     '  type    INTEGER NOT NULL )' )

    session.execute( 'CREATE TABLE rell ( '
                     '  id      INTEGER NOT NULL, '
                     '  parent  INTEGER NOT NULL, '
                     '  rel     INTEGER NOT NULL, '
                     '  sort    INTEGER )' )

    session.execute( 'CREATE TABLE fchk ( '
                     '  id      INTEGER PRIMARY KEY, '
                     '  len     INTEGER, '
                     '  crc32   TEXT, '
                     '  md5     TEXT, '
                     '  sha1    TEXT )' )

    coltbl = {}
    collst = {}

    session.execute( 'INSERT INTO objl ( id, type ) '
                     'SELECT id, :file_type AS type FROM mfl ORDER BY id ASC',
                     { 'file_type' : TYPE_FILE } )
    session.execute( 'INSERT INTO fchk ( id, len, crc32, md5, sha1 ) '
                     'SELECT id, len, crc32, md5, sha1 FROM mfl ORDER BY id ASC' )
    session.execute( 'INSERT INTO rell ( id, parent, rel ) '
                     'SELECT id, parent, CASE gorder '
                     '      WHEN :order_dup THEN :rel_dup '
                     '      ELSE                 :rel_var '
                     '      END rel '
                     ' FROM mfl '
                     '  WHERE gorder IN ( :order_dup, :order_var ) ORDER BY id ASC',
                     { 'order_dup' : ORDER_DUPLICATE,
                       'order_var' : ORDER_VARIENT,
                       'rel_dup' : LEGACY_REL_DUPLICATE,
                       'rel_var' : LEGACY_REL_VARIANT } )

    # In schema ver 1.0, the album object is the first image in the album.
    # Create a mapping table that will add album objects into the objl table
    # and map them back to the first image in the album
    session.execute( 'CREATE TEMPORARY TABLE album_map ('
                     '  old_parent  INTEGER PRIMARY KEY, '
                     '  album_id    INTEGER )' )
    session.execute( 'CREATE TEMPORARY TRIGGER update_album_map AFTER INSERT ON album_map '
                     ' BEGIN '
                     '  INSERT INTO objl ( type ) VALUES ( %d ); '
                     '  UPDATE album_map SET album_id = (SELECT id FROM objl WHERE rowid = last_insert_rowid()) '
                     '   WHERE old_parent = NEW.old_parent; '
                     ' END' % ( TYPE_ALBUM, ) )

    # Add all the albums into the album map
    session.execute( 'INSERT INTO album_map ( old_parent ) '
                     'SELECT DISTINCT parent FROM mfl WHERE parent NOT NULL and gorder >= 0' )

    # Add all the first images to the albums
    session.execute( 'INSERT INTO rell ( id, parent, rel, sort ) '
                     'SELECT old_parent, album_id, :child_rel, 0 FROM album_map',
                     { 'child_rel' : LEGACY_REL_CHILD } )
    # Add all the subsequent images to the albums
    session.execute( 'INSERT INTO rell ( id, parent, rel, sort ) '
                     'SELECT o.id, m.album_id, :child_rel AS rel, o.gorder + 1'
                     ' FROM mfl o '
                     ' INNER JOIN album_map m ON o.parent == m.old_parent',
                     { 'child_rel' : LEGACY_REL_CHILD } )

    session.execute( 'DROP TRIGGER update_album_map' )
    session.execute( 'DROP TABLE album_map' )

    return 2, 0

def upgrade_from_2_to_3( log, session ):

    log.info( 'Database upgrade from VER 2 -> VER 3' )

    session.execute( 'ALTER TABLE objl ADD COLUMN name TEXT' )
    session.execute( 'CREATE TABLE meta ( '
                     '  id      INTEGER NOT NULL, '
                     '  tag     TEXT NOT NULL, '
                     '  value   TEXT )' )

    session.execute( 'INSERT INTO meta ( id, tag, value ) '
                     'SELECT id, "altname" AS tag, name FROM naml' )

    session.execute( 'CREATE TEMPORARY TABLE single_names ('
                     '  rid     INTEGER PRIMARY KEY, '
                     '  id      INTEGER NOT NULL, '
                     '  name    TEXT NOT NULL )' )
    session.execute( 'INSERT INTO single_names '
                     'SELECT min( rowid ), id, name FROM naml GROUP BY id' )
    session.execute( 'UPDATE objl SET name = ('
                     '  SELECT s.name from single_names s WHERE s.id = objl.id)'
                     ' WHERE EXISTS (SELECT * FROM single_names s WHERE s.id = objl.id)' )
    session.execute( 'DROP TABLE single_names' )

    session.execute( 'DELETE FROM meta '
                     ' WHERE meta.tag = "altname" '
                     '   AND EXISTS ('
                     '    SELECT * FROM objl o WHERE o.id = meta.id '
                     '                           AND o.name = meta.value)' )

    session.execute( 'DROP TABLE naml' )

    session.execute( 'UPDATE dbi SET ver = 3, rev = 0' )
    return 3, 0

def upgrade_from_3_to_4( log, session ):

    log.info( 'Database upgrade from VER 3 -> VER 4' )

    session.execute( 'INSERT INTO objl ( type, name ) '
                     'SELECT DISTINCT :tag_type AS type, tag from tagl',
                     { 'tag_type' : TYPE_CLASSIFIER } )

    session.execute( 'INSERT INTO rell ( id, parent, rel ) '
                     'SELECT t.id, o.id, :tag_rel AS rel '
                     ' FROM tagl t INNER JOIN objl o ON o.type = :tag_type '
                     '                              AND o.name = t.tag',
                     { 'tag_rel' : LEGACY_REL_CLASS,
                       'tag_type' : TYPE_CLASSIFIER } )

    session.execute( 'DROP TABLE tagl' )

    session.execute( 'UPDATE dbi SET ver = 4, rev = 0' )
    return 4, 0

def upgrade_from_4_to_5( log, session ):

    log.info( 'Database upgrade from VER 4 -> VER 5' )

    # Step 1, create new tables
    session.execute( 'ALTER TABLE objl ADD COLUMN dup INTEGER' )
    session.execute( 'CREATE TABLE rel2 ( '
                     '  child   INTEGER NOT NULL, '
                     '  parent  INTEGER NOT NULL, '
                     '  sort    INTEGER )' )
    session.execute( 'CREATE TABLE mtda ( '
                     '  id      INTEGER NOT NULL, '
                     '  key     TEXT NOT NULL, '
                     '  value   TEXT )' )

    # Step 2, convert relations
    session.execute( 'INSERT INTO rel2 ( child, parent, sort ) '
                     'SELECT id, parent, sort FROM rell '
                     ' WHERE rel = :child_type OR rel = :class_type',
                     { 'child_type' : LEGACY_REL_CHILD,
                       'class_type' : LEGACY_REL_CLASS } )
    for result in session.execute( 'SELECT id, parent, rel, sort FROM rell'
                                   ' WHERE rel = :dup_type OR rel = :var_type',
                                   { 'dup_type' : LEGACY_REL_DUPLICATE,
                                     'var_type' : LEGACY_REL_VARIANT } ):

        if( result['rel'] == LEGACY_REL_DUPLICATE ):
            target_type = TYPE_FILE_DUP
        elif( result['rel'] == LEGACY_REL_VARIANT ):
            target_type = TYPE_FILE_VAR
        else:
            assert False

        session.execute( 'UPDATE objl SET type = :type, dup = :parent WHERE id = :child',
                         { 'child' : result['id'],
                           'parent' : result['parent'],
                           'type' : target_type } )

    # Step 3, collapse meta into mtda
    for result in session.execute( 'SELECT DISTINCT id, tag FROM meta' ):
        values = [ r['value'] for r in session.execute( 'SELECT value FROM meta where id = :id AND tag = :tag', result ) ]

        if( len( values ) == 1 ):
            value = values[0]
        else:
            assert( result['tag'] == 'altname' )
            value = ':'.join( values )

        session.execute( 'INSERT INTO mtda ( id, key, value ) VALUES ( :id, :key, :value )',
                         { 'id' : result['id'],
                           'key' : result['tag'],
                           'value' : value } )

    # Step 4, drop old tables
    session.execute( 'DROP TABLE rell' )
    session.execute( 'DROP TABLE meta' )

    # Step 5, update the database file
    session.execute( 'UPDATE dbi SET ver = 5, rev = 0' )
    return 5, 0

def upgrade_from_5_to_6( log, session ):

    log.info( 'Database upgrade from VER 5 -> VER 6' )

    session.execute( 'ALTER TABLE dbi ADD COLUMN imgdb_ver INTEGER' )

    session.execute( 'UPDATE dbi SET ver = 6, rev = 0, imgdb_ver = 0' )
    return 6, 0

def upgrade_from_6_to_7( log, session ):

    log.info( 'Database upgrade from VER 6 -> VER 7' )

    # Note, I normally wouldn't want to add a default, because having
    # an exception thrown if we ever try to insert an empty time is
    # a good way to catch errors. However, SqlLite doesn't provide
    # any good mechinisms to add a not-null column, then revoke the
    # default.
    session.execute( 'ALTER TABLE objl ADD COLUMN create_ts INTEGER NOT NULL DEFAULT 0' )
    session.execute( 'UPDATE objl SET create_ts = :now',
                     { 'now' : calendar.timegm( time.gmtime() ) } )

    session.execute( 'UPDATE dbi SET ver = 7, rev = 0' )
    return 7, 0

def upgrade_from_7_to_8( log, session ):

    log.info( 'Database upgrade from VER 7 -> VER 8' )

    session.execute( 'ALTER TABLE mtda ADD COLUMN num INTEGER' )

    session.execute( 'UPDATE dbi SET ver = 8, rev = 0' )
    return 8, 0
