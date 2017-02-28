import hdbfs.db

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

    def next( self ):

        while True:
            ( obj_id, ) = self.__iter.next()

            try:
                self.__session.execute( 'SELECT id FROM objl WHERE dup = :obj',
                                        { 'obj' : obj_id } ).__iter__().next()
                return obj_id
            except StopIteration:
                pass

            try:
                self.__session.execute( 'SELECT parent FROM rel2 WHERE child = :obj',
                                        { 'obj' : obj_id } ).__iter__().next()
                return obj_id
            except StopIteration:
                pass

            try:
                self.__session.execute( 'SELECT child FROM rel2 WHERE parent = :obj',
                                        { 'obj' : obj_id } ).__iter__().next()
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
                       'create_ts           INTEGER NOT NULL,\n'
                       'origin_stream_id    INTEGER,\n'
                       'origin_method       TEXT,\n'
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

    # Copy objl
    session.execute( 'INSERT INTO objects ( object_id, '
                                           'object_type, '
                                           'create_ts, '
                                           'name ) '
                     'SELECT id, type, create_ts, name '
                     'FROM objl ' 
                     'WHERE type != 1001' )

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
                                            'create_ts, '
                                            'origin_method, '
                                            'stream_length, '
                                            'hash_crc32, '
                                            'hash_md5, '
                                            'hash_sha1 ) '
                     'SELECT f.id, f.id, ".", 2000, o.create_ts, '
                            '"hdbfs:legacy", f.len, f.crc32, f.md5, '
                            'f.sha1 '
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
                                              '"rotation" ) ' )

    # Copy altnames from primaries
    session.execute( 'INSERT INTO stream_metadata ( stream_id, '
                                                   'key, '
                                                   'value ) '
                     'SELECT o.id, "names", o.name || ":" || m.value '
                     'FROM mtda m '
                     'INNER JOIN objl o ON o.id = m.id '
                     'WHERE m.key = "altname"' )

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
                                            'create_ts, '
                                            'origin_method, '
                                            'stream_length, '
                                            'hash_crc32, '
                                            'hash_md5, '
                                            'hash_sha1 ) '
                     'SELECT o.id, o.dup, "dup:" || f.sha1, '
                            '2000, o.create_ts, "hdbfs:legacy", '
                            'f.len, f.crc32, f.md5, f.sha1 '
                     'FROM objl o '
                     'INNER JOIN fchk f ON f.id = o.id '
                     'WHERE o.type = 1001' )

    # Copy altnames from duplicates
    session.execute( 'INSERT INTO stream_metadata ( stream_id, '
                                                   'key, '
                                                   'value ) '
                     'SELECT o.id, "names", o.name || ":" || m.value '
                     'FROM objl o '
                     'INNER JOIN mtda m ON m.id = o.id '
                     'WHERE o.type = 1001 '
                       'AND m.key = "altname"' )

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

    # Copy rotation from primaries
    session.execute( 'INSERT INTO stream_metadata ( stream_id, '
                                                   'key, '
                                                   'value, '
                                                   'numeric ) '
                     'SELECT o.id, m.key, m.value, m.num '
                     'FROM objl o '
                     'INNER JOIN mtda m ON m.id = o.id '
                     'WHERE o.type = 1001 '
                       'AND m.key = "rotation"' )

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

    session.execute( 'DROP TABLE objl' )
    session.execute( 'DROP TABLE fchk' )
    session.execute( 'DROP TABLE mtda' )
    session.execute( 'DROP TABLE rel2' )
    return 10, 0
