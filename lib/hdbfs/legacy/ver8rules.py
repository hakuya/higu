import calendar
import time

TYPE_NILL       = 0
TYPE_FILE       = 1000
TYPE_FILE_DUP   = 1001
TYPE_FILE_VAR   = 1002
TYPE_GROUP      = 2000
TYPE_ALBUM      = 2001
TYPE_CLASSIFIER = 2002

class LinkedDuplicateIterator:

    def __init__( self, session ):

        self.__session = session

        self.__iter = self.__session.execute(
                'SELECT id FROM objl WHERE type = :type',
                { 'type' : TYPE_FILE_DUP, } ).__iter__()

    def __iter__( self ):

        return self

    def __next__( self ):

        while True:
            ( obj_id, ) = self.__iter.__next__()

            try:
                self.__session.execute( 'SELECT id FROM objl WHERE dup = :obj',
                                        { 'obj' : obj_id } ).__iter__().__next__()
                return obj_id
            except StopIteration:
                pass

            try:
                self.__session.execute( 'SELECT parent FROM rel2 WHERE child = :obj',
                                        { 'obj' : obj_id } ).__iter__().__next__()
                return obj_id
            except StopIteration:
                pass

            try:
                self.__session.execute( 'SELECT child FROM rel2 WHERE parent = :obj',
                                        { 'obj' : obj_id } ).__iter__().__next__()
                return obj_id
            except StopIteration:
                pass

def determine_duplicate_parent( session, obj_id ):

    result = session.execute( 'SELECT type, dup FROM objl WHERE id = :obj',
                              { 'obj' : obj_id } ).first()
    if( result is None ):
        return None

    if( result['type'] != TYPE_FILE_DUP ):
        return obj_id
    else:
        return determine_duplicate_parent( session, result['dup'] )

def correct_linked_duplicates( session ):

    for obj_id in LinkedDuplicateIterator( session ):
        parent_id = determine_duplicate_parent( session, obj_id )

        mapping = { 'obj' : obj_id, 'par' : parent_id }

        # Move all dup/vars
        session.execute( 'UPDATE objl SET dup = :par WHERE dup = :obj',
                         mapping )

        # Move parents
        for result in session.execute( 'SELECT parent FROM rel2 WHERE child = :par',
                                       mapping ):

            session.execute( 'DELETE FROM rel2 WHERE child = :obj and parent = :oth',
                             { 'obj' : obj_id,
                               'oth' : result['parent'] } )

        session.execute( 'DELETE FROM rel2 WHERE child = :obj and parent = :par',
                         mapping )
        session.execute( 'UPDATE rel2 SET child = :par WHERE child = :obj',
                         mapping )

        # Move children
        for result in session.execute( 'SELECT child FROM rel2 WHERE parent = :par',
                                       mapping ):

            session.execute( 'DELETE FROM rel2 WHERE parent = :obj and child = :oth',
                             { 'obj' : obj_id,
                               'oth' : result['child'] } )

        session.execute( 'DELETE FROM rel2 WHERE parent = :obj and child = :par',
                         mapping )
        session.execute( 'UPDATE rel2 SET parent = :par WHERE parent = :obj',
                         mapping )

def upgrade_from_8_to_8_1( log, session ):

    log.info( 'Database upgrade from VER 8 -> VER 8.1' )

    correct_linked_duplicates( session )

    session.execute( 'UPDATE dbi SET ver = 8, rev = 1' )
    return 8, 1

def upgrade_from_8_1_to_9( log, session ):

    log.info( 'Database upgrade from VER 8.1 -> VER 9' )
    return 9, 0

def upgrade_from_9_to_10( log, session ):

    log.info( 'Database upgrade from VER 9 -> VER 10' )
    now = calendar.timegm(time.gmtime())

    session.execute( 'CREATE TABLE objects (\n'
                       'object_id       INTEGER PRIMARY KEY,\n'
                       'object_type     INTEGER NOT NULL,\n'
                       'create_ts       INTEGER NOT NULL,\n'
                       'name            TEXT,\n'
                       'root_stream_id  INTEGER )' )

    session.execute( 'CREATE TABLE streams (\n'
                       'stream_id           INTEGER PRIMARY KEY,\n'
                       'object_id           INTEGER NOT NULL,\n'
                       'name                TEXT NOT NULL,\n'
                       'priority            INTEGER NOT NULL,\n'
                       'origin_stream_id    INTEGER,\n'
                       'extension           TEXT,\n'
                       'mime_type           TEXT,\n'
                       'stream_length       INTEGER,\n'
                       'hash_crc32          TEXT,\n'
                       'hash_md5            TEXT,\n'
                       'hash_sha1           TEXT,\n'
                       'UNIQUE ( object_id, name ),\n'
                       'FOREIGN KEY ( object_id ) '
                         'REFERENCES objects( object_id ),\n'
                       'FOREIGN KEY ( origin_stream_id ) '
                         'REFERENCES streams( stream_id ) )\n' )

    session.execute( 'CREATE TABLE object_metadata (\n'
                     'object_id         INTEGER NOT NULL,\n'
                     'key               TEXT NOT NULL,\n'
                     'value             TEXT,\n'
                     'numeric           INTEGER,\n'
                     'PRIMARY KEY ( object_id, key ),\n'
                     'FOREIGN KEY ( object_id ) '
                       'REFERENCES objects( object_id ) )\n' )

    session.execute( 'CREATE TABLE stream_metadata (\n'
                     'stream_id         INTEGER NOT NULL,\n'
                     'key               TEXT NOT NULL,\n'
                     'value             TEXT,\n'
                     'numeric           INTEGER,\n'
                     'PRIMARY KEY ( stream_id, key ),\n'
                     'FOREIGN KEY ( stream_id ) '
                       'REFERENCES objects( object_id ) )\n' )

    session.execute( 'CREATE TABLE relations (\n'
                     'child_id          INTEGER NOT NULL,\n'
                     'parent_id         INTEGER NOT NULL,\n'
                     'sort              INTEGER,\n'
                     'PRIMARY KEY ( child_id, parent_id ),\n'
                     'FOREIGN KEY ( child_id ) '
                       'REFERENCES objects( object_id ),\n'
                     'FOREIGN KEY ( parent_id ) '
                       'REFERENCES objects( object_id ) )\n' )

    session.execute( 'CREATE TABLE stream_log(\n'
                     'log_id            INTEGER PRIMARY KEY,\n'
                     'stream_id         INTEGER NOT NULL,\n'
                     'timestamp         INTEGER NOT NULL,\n'
                     'origin_method     TEXT NOT NULL,\n'
                     'origin_stream_id  INTEGER,\n'
                     'origin_name       TEXT,\n'
                     'FOREIGN KEY ( stream_id ) '
                       'REFERENCES streams( stream_id ),\n'
                     'FOREIGN KEY ( origin_stream_id ) '
                       'REFERENCES streams( stream_id ) )\n' )

    # Copy objl
    session.execute( 'INSERT INTO objects ( object_id, '
                                           'object_type, '
                                           'create_ts, '
                                           'name ) '
                     'SELECT id, type, create_ts, name '
                     'FROM objl '
                     'WHERE type != 1001' )

    # Bugs in earlier versions of hdbfs can lead to duplicate rows in the rel2
    # table. Delete the duplicate rows now
    session.execute( 'DELETE FROM rel2 '
                     'WHERE rowid NOT IN ( '
                       'SELECT MIN( rowid ) '
                       'FROM rel2 GROUP BY parent, child )' )

    # Copy rel2
    session.execute( 'INSERT INTO relations '
                     'SELECT r.child, r.parent, r.sort '
                     'FROM rel2 r '
                     'INNER JOIN objl a ON a.id = r.child '
                     'INNER JOIN objl b ON b.id = r.parent '
                     'WHERE a.type != 1001 '
                       'AND b.type != 1001' )

    # Remove the variant type
    session.execute( 'UPDATE objects SET object_type = 1000 '
                     'WHERE object_type = 1002' )

    # Copy primary streams
    session.execute( 'INSERT INTO streams ( stream_id, '
                                            'object_id, '
                                            'name, '
                                            'priority, '
                                            'stream_length, '
                                            'hash_crc32, '
                                            'hash_md5, '
                                            'hash_sha1 ) '
                     'SELECT f.id, f.id, ".", 2000, f.len, '
                            'f.crc32, f.md5, f.sha1 '
                     'FROM fchk f '
                     'INNER JOIN objl o ON o.id = f.id '
                     'WHERE o.type != 1001' )

    # Copy primary metadata (except altname, original-width, original-height)
    session.execute( 'INSERT INTO object_metadata ( object_id, '
                                                   'key, '
                                                   'value, '
                                                   'numeric ) '
                     'SELECT id, key, value, num '
                     'FROM mtda '
                     'WHERE id IN (SELECT object_id FROM objects) '
                             'AND key NOT IN ( "altname", '
                                              '"original-width", '
                                              '"original-height", '
                                              '"rotation", '
                                              '"thumb-gen" ) ' )

    # Copy original-width/height from primaries
    session.execute( 'INSERT INTO stream_metadata ( stream_id, '
                                                   'key, '
                                                   'value, '
                                                   'numeric ) '
                     'SELECT id, "width", value, num '
                     'FROM mtda '
                     'WHERE id IN (SELECT object_id FROM objects) '
                             'AND key = "original-width"' )
    session.execute( 'INSERT INTO stream_metadata ( stream_id, '
                                                   'key, '
                                                   'value, '
                                                   'numeric ) '
                     'SELECT id, "height", value, num '
                     'FROM mtda '
                     'WHERE id IN (SELECT object_id FROM objects) '
                             'AND key = "original-height"' )

    # Copy rotation from primaries
    session.execute( 'INSERT INTO stream_metadata ( stream_id, '
                                                   'key, '
                                                   'value, '
                                                   'numeric ) '
                     'SELECT id, key, value, num '
                     'FROM mtda '
                     'WHERE id IN (SELECT object_id FROM objects) '
                             'AND key = "rotation"' )

    # Resolve variants
    session.execute( 'INSERT INTO relations ( child_id, parent_id ) '
                     'SELECT id, dup '
                     'FROM objl '
                     'WHERE type = 1002' )

    # Copy duplicate streams
    session.execute( 'INSERT INTO streams ( stream_id, '
                                            'object_id, '
                                            'name, '
                                            'priority, '
                                            'stream_length, '
                                            'hash_crc32, '
                                            'hash_md5, '
                                            'hash_sha1 ) '
                     'SELECT o.id, o.dup, "dup:" || f.sha1, '
                            '2000, f.len, f.crc32, f.md5, f.sha1 '
                     'FROM objl o '
                     'INNER JOIN fchk f ON f.id = o.id '
                     'WHERE o.type = 1001' )

    # Copy original-width/height from duplicates
    session.execute( 'INSERT INTO stream_metadata ( stream_id, '
                                                   'key, '
                                                   'value, '
                                                   'numeric ) '
                     'SELECT o.id, "width", m.value, m.num '
                     'FROM objl o '
                     'INNER JOIN mtda m ON m.id = o.id '
                     'WHERE o.type = 1001 '
                       'AND m.key = "original-width"' )
    session.execute( 'INSERT INTO stream_metadata ( stream_id, '
                                                   'key, '
                                                   'value, '
                                                   'numeric ) '
                     'SELECT o.id, "height", m.value, m.num '
                     'FROM objl o '
                     'INNER JOIN mtda m ON m.id = o.id '
                     'WHERE o.type = 1001 '
                       'AND m.key = "original-height"' )

    # Copy rotation from duplicates
    session.execute( 'INSERT INTO stream_metadata ( stream_id, '
                                                   'key, '
                                                   'value, '
                                                   'numeric ) '
                     'SELECT o.id, m.key, m.value, m.num '
                     'FROM objl o '
                     'INNER JOIN mtda m ON m.id = o.id '
                     'WHERE o.type = 1001 '
                       'AND m.key = "rotation"' )

    # Add the log entries for creation
    session.execute( 'INSERT INTO stream_log ( stream_id, '
                                              'timestamp, '
                                              'origin_method ) '
                     'SELECT f.id, o.create_ts, '
                            '"hdbfs:legacy_create" '
                     'FROM fchk f '
                     'INNER JOIN objl o ON o.id = f.id' )

    # We don't know what time the streams were named, so name them now
    session.execute( 'INSERT INTO stream_log ( stream_id, '
                                              'timestamp, '
                                              'origin_method, '
                                              'origin_name ) '
                     'SELECT f.id, :now, '
                            '"hdbfs:legacy_name", '
                            'o.name '
                     'FROM fchk f '
                     'INNER JOIN objl o ON o.id = f.id '
                     'WHERE o.name IS NOT NULL',
                     { 'now' : now, } )

    # Now add all the alt-names. This gets a bit dicey
    for stream_id, altnames \
     in session.execute( 'SELECT f.id, m.value '
                         'FROM fchk f '
                         'INNER JOIN mtda m ON m.id = f.id '
                         'WHERE m.key = "altname"' ):

        altnames = altnames.split( ':' )

        for name in altnames:
            session.execute( 'INSERT INTO stream_log ( stream_id, '
                                                      'timestamp, '
                                                      'origin_method, '
                                                      'origin_name ) '
                             'VALUES ( :stream_id, :now, '
                                      '"hdbfs:legacy_altname", '
                                      ':name )',
                             { 'stream_id' : stream_id,
                               'now' : now,
                               'name' : name, } )

    # Assign root streams
    session.execute( 'UPDATE objects SET root_stream_id = object_id '
                     'WHERE object_id IN (SELECT stream_id FROM streams)' )

    # Create indexes
    session.execute( 'CREATE UNIQUE INDEX streams_object_id_name_index '
                     'ON streams ( object_id, name )' )
    session.execute( 'CREATE UNIQUE INDEX object_metadata_object_id_key_index '
                     'ON object_metadata( object_id, key )' )
    session.execute( 'CREATE UNIQUE INDEX stream_metadata_stream_id_key_index '
                     'ON stream_metadata( stream_id, key )' )
    session.execute( 'CREATE INDEX stream_log_stream_id_index '
                     'ON stream_log ( stream_id )' )

    session.execute( 'DROP TABLE objl' )
    session.execute( 'DROP TABLE fchk' )
    session.execute( 'DROP TABLE mtda' )
    session.execute( 'DROP TABLE rel2' )
    return 10, 0

def upgrade_from_10_to_11( log, session ):

    log.info( 'Database upgrade from VER 10 -> VER 11' )

    session.execute( 'ALTER TABLE relations ADD COLUMN child_name TEXT' )
    session.execute( 'ALTER TABLE relations ADD COLUMN child_stream_id INTEGER' )

    return 11, 0

def upgrade_from_11_to_12( log, session ):

    log.info( 'Database upgrade from VER 11 -> VER 12' )

    # Ver 12 no longer uses holds duplicates as additional streams for files.
    # It's a bit of a throwback, in that duplicates are full on files.
    #
    # To migrate, we need to promote all 'dup' streams to new file objects

    #for row in session.execute( 'SELECT * from objects' ):
    #    print row
    #for row in session.execute( 'SELECT * from stream_log' ):
    #    print row

    # Create new objects for the duplicates. This is a beefy query.
    session.execute(
        'INSERT INTO objects (\n'
                'object_type,\n'
                'create_ts,\n'
                'name,\n'
                'root_stream_id\n'
            ')\n'
        'SELECT\n'
            '1001,\n'
            'COALESCE( first_stream_sighting.timestamp, objects.create_ts ),\n'
            'stream_log.origin_name,\n'
            'streams.stream_id\n'
        # We take our streams
        'FROM streams\n'
        # Join them against their current objects,
        # so we have a fallback for the create_ts
        'INNER JOIN objects\n'
                'ON objects.object_id = streams.object_id\n'
        # Join against the earliest timestamp we
        # have in the stream_log for that stream
        'LEFT JOIN (\n'
                'SELECT\n'
                    'stream_id,\n'
                    'MIN( timestamp ) AS timestamp\n'
                'FROM stream_log\n'
                'GROUP BY stream_id\n'
            ') AS first_stream_sighting\n'
            'ON first_stream_sighting.stream_id = streams.stream_id\n'
        # Join against the name with the earliest
        # timestamp we have for that stream. The name may have been
        # assigned later, especially in certain migration cases,
        # so we can't rely on the first stream_log entry containing
        # a name
        'LEFT JOIN (\n'
                'SELECT\n'
                    'stream_id,\n'
                    'MIN( timestamp ) AS timestamp\n'
                'FROM stream_log\n'
                'WHERE origin_name NOT NULL\n'
                'GROUP BY stream_id\n'
            ') AS first_stream_name\n'
            'ON first_stream_name.stream_id = streams.stream_id\n'
        # Join once more against the names, so we can retrieve the name
        'LEFT JOIN stream_log\n'
               'ON stream_log.stream_id = first_stream_name.stream_id\n'
              'AND stream_log.timestamp = first_stream_name.timestamp\n'
              'AND stream_log.origin_name NOT NULL\n'
        # And we pick out only duplicate streams
        'WHERE streams.name LIKE \'dup:%\'\n'
        # Eliminate dups from all this joining
        'GROUP BY streams.stream_id' )

    # We're going to need to link these new duplicate objects
    # to the streams and their parent obejcts, so we create
    # a temporary table to track the relationships
    session.execute( 'CREATE TEMPORARY TABLE _dups (\n'
                     'object_id          INTEGER NOT NULL,\n'
                     'parent_id          INTEGER NOT NULL,\n'
                     'stream_id          INTEGER NOT NULL )' )
    session.execute( 'INSERT INTO _dups\n'
                     'SELECT\n'
                         'objects.object_id,\n'
                         'streams.object_id,\n'
                         'streams.stream_id\n'
                     'FROM objects\n'
                     'INNER JOIN streams\n'
                             'ON streams.stream_id = objects.root_stream_id\n'
                     'WHERE streams.name LIKE \'dup:%\'' )

    # Fix up the object id for the stream in the streams and relations tables
    for row in session.execute( 'SELECT object_id, stream_id FROM _dups' ):
        session.execute( 'UPDATE streams\n'
                         'SET object_id = :object_id\n,'
                             'name = \'.\'\n'
                         'WHERE stream_id = :stream_id',
                         row )
        session.execute( 'UPDATE relations\n'
                         'SET child_id = :object_id\n'
                         'WHERE child_stream_id = :stream_id',
                         row )

    # Copy our relations table to delete the child_stream_id column
    session.execute( 'ALTER TABLE relations RENAME TO _relations;' )
    session.execute( 'CREATE TABLE relations (\n'
                     'child_id          INTEGER NOT NULL,\n'
                     'parent_id         INTEGER NOT NULL,\n'
                     'sort              INTEGER,\n'
                     'child_name        TEXT, \n'
                     'PRIMARY KEY ( child_id, parent_id ),\n'
                     'FOREIGN KEY ( child_id ) '
                       'REFERENCES objects( object_id ),\n'
                     'FOREIGN KEY ( parent_id ) '
                       'REFERENCES objects( object_id ) )\n' )

    session.execute( 'INSERT INTO relations\n'
                     'SELECT child_id,\n'
                            'parent_id,\n'
                            'sort,\n'
                            'child_name\n'
                     'FROM _relations' )

    # Link the duplicates back to the parent object
    session.execute( 'INSERT INTO relations(\n'
                             'child_id,\n'
                             'parent_id\n'
                         ')\n'
                     'SELECT object_id,\n'
                            'parent_id\n'
                     'FROM _dups' )

    # Albums linking directly to duplicates is only allowed when
    # published, so immediate publish albums that did this
    session.execute( 'UPDATE objects\n'
                     'SET object_type = 2003\n'
                     'WHERE object_type = 2001\n'
                       'AND object_id IN (\n'
                        'SELECT relations.parent_id\n'
                        'FROM relations\n'
                        'INNER JOIN objects\n'
                                'ON objects.object_id = relations.child_id\n'
                        'WHERE objects.object_type = 1001\n'
                     ')' )

    # Tidy up
    session.execute( 'DROP TABLE _relations' )
    session.execute( 'DROP TABLE _dups' )

    return 12, 0

def upgrade_from_12_to_13( log, session ):

    log.info( 'Database upgrade from VER 12 -> VER 13' )

    # Ver 13 just has two new tables
    session.execute( """
        CREATE TABLE imageinfo (
            object_id         INTEGER PRIMARY KEY,
            width             INTEGER NOT NULL,
            height            INTEGER NOT NULL,
            gen               INTEGER NOT NULL DEFAULT 0,
            max_e             INTEGER,
            use_root          INTEGER,
            avail_e           INTEGER,
            FOREIGN KEY ( object_id )
                REFERENCES objects( object_id ) )
    """ )

    session.execute( """
        CREATE TABLE streaminfo (
            stream_id         INTEGER PRIMARY KEY,
            width             INTEGER NOT NULL,
            height            INTEGER NOT NULL,
            orientation       INTEGER,
            FOREIGN KEY ( stream_id )
                REFERENCES streams( stream_id ) )
    """ )

    # Now, we need to copy the info from the metadata tables to the new info tables
    session.execute( """
        INSERT INTO imageinfo
        SELECT
            objects.object_id as object_id,
            w_meta.numeric as width,
            h_meta.numeric as height,
            coalesce( cast( substr( tbi_meta.value, 1, instr( tbi_meta.value, ':' ) - 1 )
                    as INTEGER ), 0 )
                as gen,
            cast( substr( substr( tbi_meta.value, instr( tbi_meta.value, ':' ) + 1 ),
                            1, instr( substr( tbi_meta.value, instr( tbi_meta.value, ':' ) + 1 ), ':' ) - 1 )
                    as INTEGER )
                as max_e,
            cast( substr( substr( tbi_meta.value, instr( tbi_meta.value, ':' ) + 1 ),
                            instr( substr( tbi_meta.value, instr( tbi_meta.value, ':' ) + 1 ), ':' ) + 1 )
                    as INTEGER )
                as use_root,
            NULL as avail_e
        FROM objects
        INNER JOIN object_metadata w_meta
                ON w_meta.object_id = objects.object_id
               AND w_meta.key = 'width'
        INNER JOIN object_metadata h_meta
                ON h_meta.object_id = objects.object_id
               AND h_meta.key = 'height'
        LEFT JOIN object_metadata tbi_meta
               ON tbi_meta.object_id = objects.object_id
              AND tbi_meta.key = '.tbinfo'
        WHERE objects.object_type in (1000, 1001)
          AND w_meta.numeric is not NULL
          AND h_meta.numeric is not NULL
    """ )

    session.execute( """
        INSERT INTO streaminfo
        SELECT
            streams.stream_id as stream_id,
            w_meta.numeric as width,
            h_meta.numeric as height,
            COALESCE(
                ori_meta.numeric,
                CASE rot_meta.numeric
                        WHEN 0 THEN 1
                        WHEN 1 THEN 6
                        WHEN 2 THEN 3
                        WHEN 3 THEN 8
                        ELSE NULL
                END
            ) as orientation
        FROM streams
        INNER JOIN stream_metadata w_meta
                ON w_meta.stream_id = streams.stream_id
               AND w_meta.key = 'width'
        INNER JOIN stream_metadata h_meta
                ON h_meta.stream_id = streams.stream_id
               AND h_meta.key = 'height'
        LEFT JOIN stream_metadata rot_meta
               ON rot_meta.stream_id = streams.stream_id
              AND rot_meta.key = 'rotation'
        LEFT JOIN stream_metadata ori_meta
               ON ori_meta.stream_id = streams.stream_id
              AND ori_meta.key = 'orientation'
        WHERE w_meta.numeric is not NULL
          AND h_meta.numeric is not NULL
    """ )

    # And, delete the metadata entries
    session.execute( """
        DELETE FROM object_metadata
        WHERE key in ( 'width', 'height', '.tbinfo', '.metaver' )
    """ )
    session.execute( """
        DELETE FROM stream_metadata
        WHERE key in ( 'width', 'height', 'rotation', 'orientation', '.metaver' )
    """ )

    return 13, 0

def upgrade_from_13_to_13_1( log, session ):

    # No major changes, albums now allowed to be children of each other

    log.info( 'Database upgrade from VER 13 -> VER 13.1' )

    return 13, 1

def upgrade_from_13_1_to_14( log, session ):

    # In version 14, thumbnail generation can be deferred. So a new
    # table is added to keep track of requests for thumbnails

    log.info( 'Database upgrade from VER 13.1 -> VER 14' )

    # Ver 13 just has two new tables
    session.execute( """
        CREATE TABLE imagerequest (
            object_id         INTEGER PRIMARY KEY,
            prio              INTEGER NOT NULL,
            exp_mask          INTEGER,
            FOREIGN KEY ( object_id )
                REFERENCES objects( object_id ) )
    """ )

    return 14, 0