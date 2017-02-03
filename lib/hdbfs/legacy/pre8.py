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

    log.info( 'Database upgrade from VER 0 -> VER 1' )

    mfl = session.get_table( 'mfl' )
    dbi = session.get_table( 'dbi' )

    mfl.add_col( 'parent', 'INTEGER' )
    mfl.add_col( 'gorder', 'INTEGER' )
    dbi.update( [ ( 'ver', 1, ), ( 'rev', 0, ) ] )

    session.commit()

def upgrade_from_1_to_2( log, session ):

    log.info( 'Database upgrade from VER 1 -> VER 2' )

    mfl = session.get_table( 'mfl' )
    coll = session.get_table( 'coll' )
    objl = session.get_table( 'objl' )
    rell = session.get_table( 'rell' )
    fchk = session.get_table( 'fchk' )
    dbi = session.get_table( 'dbi' )

    objl.create( [ ( 'id',     'INTEGER PRIMARY KEY', ),
                   ( 'type',   'INTEGER NOT NULL', ), ] )

    rell.create( [ ( 'id',     'INTEGER NOT NULL', ),
                   ( 'parent', 'INTEGER NOT NULL', ),
                   ( 'rel',    'INTEGER NOT NULL', ),
                   ( 'sort',  'INTEGER', ), ] )

    fchk.create( [ ( 'id',     'INTEGER PRIMARY KEY', ),
                   ( 'len',    'INTEGER', ),
                   ( 'crc32',  'TEXT', ),
                   ( 'md5',    'TEXT', ),
                   ( 'sha1',   'TEXT', ), ] )

    cursor = mfl.select( order = 'id' )
    coltbl = {}
    collst = {}

    # Note: this code uses the former naming scheme where albums were called collections

    for item in cursor:
        id, len, crc32, md5, sha1, parent, order = item
        objl.insert( [ ( 'id', id, ), ( 'type', TYPE_FILE, ), ] )
        fchk.insert( [ ( 'id', id, ), ( 'len', len, ), ( 'crc32', crc32, ), ( 'md5', md5, ), ( 'sha1', sha1, ) ] )

        if( parent != None and order == ORDER_VARIENT ):
            rell.insert( [ ( 'id', id, ), ( 'parent', parent, ), ( 'rel', LEGACY_REL_VARIANT, ) ] )
        elif( parent != None and order == ORDER_DUPLICATE ):
            rell.insert( [ ( 'id', id, ), ( 'parent', parent, ), ( 'rel', LEGACY_REL_DUPLICATE, ) ] )
        elif( parent != None ):
            coltbl[id] = [ parent, order ]
            if( not collst.has_key( parent ) ):
                collst[parent] = -1
        # Create collections at the end so we don't mess up the ids

    for collection in collst.keys():
        colid = objl.insert( [ ( 'type', TYPE_ALBUM, ), ], [ 'id' ] ).eval( True, True )
        collst[collection] = colid
        rell.insert( [ ( 'id', collection, ), ( 'parent', colid, ), ( 'rel', LEGACY_REL_CHILD, ), ( 'sort', 0, ) ] )

    for member in coltbl.keys():
        collection, order = coltbl[member]
        rell.insert( [ ( 'id', member, ), ( 'parent', collst[collection], ), ( 'rel', LEGACY_REL_CHILD, ), ( 'sort', order, ) ] )

    mfl.drop()
    # Note: naming of collections was never fully implemented in ver. 1 so it is not preserved
    try:
        coll.drop()
    except hdbfs.db.QueryError:
        pass
    dbi.update( [ ( 'ver', 2, ), ( 'rev', 0, ) ] )

    session.commit()

def upgrade_from_2_to_3( log, session ):

    log.info( 'Database upgrade from VER 2 -> VER 3' )

    objl = session.get_table( 'objl' )
    meta = session.get_table( 'meta' )
    naml = session.get_table( 'naml' )
    dbi = session.get_table( 'dbi' )

    meta.create( [ ( 'id',     'INTEGER NOT NULL', ),
                   ( 'tag',    'TEXT NOT NULL', ),
                   ( 'value',  'TEXT' ), ] )

    objl.add_col( 'name', 'TEXT' )

    cursor = naml.select( order = 'id' )

    # Note: this code uses the former naming scheme where albums were called collections
    nameset_last = None
    for id, name in cursor:
        if( id == nameset_last ):
            meta.insert( [ ( 'id', id, ), ( 'tag' , 'altname' ), ( 'value', name, ), ] )
        else:
            objl.update( [ ( 'name', name, ), ], [ ( 'id', id, ) ] )

        nameset_last = id

    naml.drop()
    dbi.update( [ ( 'ver', 3, ), ( 'rev', 0, ) ] )

    session.commit()

def upgrade_from_3_to_4( log, session ):

    log.info( 'Database upgrade from VER 3 -> VER 4' )

    objl = session.get_table( 'objl' )
    tagl = session.get_table( 'tagl' )
    rell = session.get_table( 'rell' )
    dbi = session.get_table( 'dbi' )

    tagmap = {}

    for item in tagl.select( [ 'tag' ], distinct = True ):

        tagmap[item[0]] = objl.insert( [ ( 'type', TYPE_CLASSIFIER, ),
                ( 'name', item[0], ) ], [ 'id' ] ).eval( True, True )        

    for item in tagl.select():

        rell.insert( [ ( 'id', item[0], ), ( 'parent', tagmap[item[1]], ),
                ( 'rel', LEGACY_REL_CLASS, ), ] )

    tagl.drop()
    dbi.update( [ ( 'ver', 4, ), ( 'rev', 0, ) ] )

    session.commit()

def upgrade_from_4_to_5( log, session ):

    log.info( 'Database upgrade from VER 4 -> VER 5' )

    dbi = session.get_table( 'dbi' )
    objl = session.get_table( 'objl' )
    rell = session.get_table( 'rell' )
    meta = session.get_table( 'meta' )
    rel2 = session.get_table( 'rel2' )
    mtda = session.get_table( 'mtda' )

    # Step 1, create new tables
    objl.add_col( 'dup', 'INTEGER' )

    rel2.create( [ ( 'child',  'INTEGER NOT NULL', ),
                   ( 'parent', 'INTEGER NOT NULL', ),
                   ( 'sort',   'INTEGER', ), ] )

    mtda.create( [ ( 'id',     'INTEGER NOT NULL', ),
                   ( 'key',    'TEXT NOT NULL', ),
                   ( 'value',  'TEXT' ), ] )

    # Step 2, convert relations
    for child, parent, type, sort in rell.select():
        if( type == LEGACY_REL_CHILD or type == LEGACY_REL_CLASS ):
            rel2.insert( [ ( 'child', child, ), ( 'parent', parent, ),
                    ( 'sort', sort, ), ] )
        elif( type == LEGACY_REL_DUPLICATE ):
            objl.update( [ ( 'type', TYPE_FILE_DUP, ), ( 'dup', parent, ) ], [ ( 'id', child, ) ] )
        elif( type == LEGACY_REL_VARIANT ):
            objl.update( [ ( 'type', TYPE_FILE_VAR, ), ( 'dup', parent, ) ], [ ( 'id', child, ) ] )
        else:
            assert( False )

    # Step 3, collapse meta into mtda
    for id, key in meta.select( [ 'id', 'tag', ], distinct = True ):
        values = [ value[0] for value in meta.select( [ 'value' ], [ ( 'id', id, ), ( 'tag', key, ) ] ) ]

        if( len( values ) == 1 ):
            mtda.insert( [ ( 'id', id, ), ( 'key', key, ), ( 'value', values[0], ), ] )
        else:
            assert( key == 'altname' )
            values = ':'.join( values )
            mtda.insert( [ ( 'id', id, ), ( 'key', key, ), ( 'value', values, ), ] )

    # Step 4, drop old tables
    rell.drop()
    meta.drop()

    # Step 5, update the database file
    dbi.update( [ ( 'ver', 5, ), ( 'rev', 0, ) ] )
    session.commit()

def upgrade_from_5_to_6( log, session ):

    log.info( 'Database upgrade from VER 5 -> VER 6' )

    dbi = session.get_table( 'dbi' )
    dbi.add_col( 'imgdb_ver', 'INTEGER' )

    dbi.update( [ ( 'ver', 6, ), ( 'rev', 0, ), ( 'imgdb_ver', 0, ), ] )
    session.commit()

def upgrade_from_6_to_7( log, session ):

    log.info( 'Database upgrade from VER 6 -> VER 7' )

    dbi = session.get_table( 'dbi' )
    objl = session.get_table( 'objl' )

    # Note, I normally wouldn't want to add a default, because having
    # an exception thrown if we ever try to insert an empty time is
    # a good way to catch errors. However, SqlLite doesn't provide
    # any good mechinisms to add a not-null column, then revoke the
    # default.
    objl.add_col( 'create_ts', 'INTEGER NOT NULL', 0 )

    ts_now = calendar.timegm( time.gmtime() )
    objl.update( [ ( 'create_ts', ts_now, ) ] )
    dbi.update( [ ( 'ver', 7, ), ( 'rev', 0, ), ] )
    session.commit()

def upgrade_from_7_to_8( log, session ):

    log.info( 'Database upgrade from VER 7 -> VER 8' )

    dbi = session.get_table( 'dbi' )
    mtda = session.get_table( 'mtda' )

    mtda.add_col( 'num', 'INTEGER' )

    dbi.update( [ ( 'ver', 8, ), ( 'rev', 0, ), ] )
    session.commit()
