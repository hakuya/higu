import db
import uuid
import os
import re

from hash import calculate_details

VERSION = 5
REVISION = 0

GFDB_PATH = os.path.join( os.environ['HOME'], '.gfdb' )
LFDB_NAME = '.lfdb'
GFDB = None

ORDER_VARIENT   = -1
ORDER_DUPLICATE = -2

TYPE_NILL       = 0
TYPE_FILE       = 1000
TYPE_FILE_DUP   = 1001
TYPE_FILE_VAR   = 1002
TYPE_GROUP      = 2000
TYPE_ALBUM      = 2001
TYPE_CLASSIFIER = 2002

LEGACY_REL_CHILD       = 0
LEGACY_REL_DUPLICATE   = 1000
LEGACY_REL_VARIANT     = 1001
LEGACY_REL_CLASS       = 2000

def check_len( length ):

    assert isinstance( length, int ) or isinstance( length, long ) and length >= 0
    return length

def check_crc32( hash ):

    assert isinstance( hash, str )
    hash = hash.lower()
    assert re.match( '^[0-9a-f]{8}$', hash )
    return hash

def check_md5( hash ):

    assert isinstance( hash, str )
    hash = hash.lower()
    assert re.match( '^[0-9a-f]{32}$', hash )
    return hash

def check_sha1( hash ):

    assert isinstance( hash, str )
    hash = hash.lower()
    assert re.match( '^[0-9a-f]{40}$', hash )
    return hash

def upgrade_from_0_to_1( db ):

    print 'Database upgrade from VER 0 -> VER 1'

    mfl = db.get_table( 'mfl' )
    dbi = db.get_table( 'dbi' )

    mfl.add_col( 'parent', 'INTEGER' )
    mfl.add_col( 'gorder', 'INTEGER' )
    dbi.update( [ ( 'ver', 1, ), ( 'rev', 0, ) ] )

    db.commit()

def upgrade_from_1_to_2( db ):

    print 'Database upgrade from VER 1 -> VER 2'

    mfl = db.get_table( 'mfl' )
    coll = db.get_table( 'coll' )
    objl = db.get_table( 'objl' )
    rell = db.get_table( 'rell' )
    fchk = db.get_table( 'fchk' )
    dbi = db.get_table( 'dbi' )

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
    coll.drop()
    dbi.update( [ ( 'ver', 2, ), ( 'rev', 0, ) ] )

    db.commit()

def upgrade_from_2_to_3( db ):

    print 'Database upgrade from VER 2 -> VER 3'

    objl = db.get_table( 'objl' )
    meta = db.get_table( 'meta' )
    naml = db.get_table( 'naml' )
    dbi = db.get_table( 'dbi' )

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

    naml.drop()
    dbi.update( [ ( 'ver', 3, ), ( 'rev', 0, ) ] )

    db.commit()

def upgrade_from_3_to_4( db ):

    print 'Database upgrade from VER 3 -> VER 4'

    objl = db.get_table( 'objl' )
    tagl = db.get_table( 'tagl' )
    rell = db.get_table( 'rell' )
    dbi = db.get_table( 'dbi' )

    tagmap = {}

    for item in tagl.select( [ 'tag' ], distinct = True ):

        tagmap[item[0]] = objl.insert( [ ( 'type', TYPE_CLASSIFIER, ),
                ( 'name', item[0], ) ], [ 'id' ] ).eval( True, True )        

    for item in tagl.select():

        rell.insert( [ ( 'id', item[0], ), ( 'parent', tagmap[item[1]], ),
                ( 'rel', LEGACY_REL_CLASS, ), ] )

    tagl.drop()
    dbi.update( [ ( 'ver', 4, ), ( 'rev', 0, ) ] )

    db.commit()

def upgrade_from_4_to_5( db ):

    print 'Database upgrade from VER 4 -> VER 5'

    dbi = db.get_table( 'dbi' )
    objl = db.get_table( 'objl' )
    rell = db.get_table( 'rell' )
    meta = db.get_table( 'meta' )
    rel2 = db.get_table( 'rel2' )
    mtda = db.get_table( 'mtda' )

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
    db.commit()


def update_legacy_database( dbfile ):

    session = db.SqlLiteDatabase( dbfile )
    dbi = DatabaseInfo( session.get_table( 'dbi' ) )

    while( True ):
        ver = dbi.get_version()
        print 'Database is version v' + str( ver )
     
        if( ver != VERSION ):

            # Back-up the dbfile
            f = file( dbfile, 'rb' )
            n = 0
            while( 1 ):
                if( not os.path.isfile( dbfile + '.bak' + str( n ) ) ):
                    break
                n += 1
            g = file( dbfile + '.bak' + str( n ), 'wb' )
            while( 1 ):
                buff = f.read( 1024 )
                if( len( buff ) == 0 ):
                    f.close()
                    g.close()
                    break
                g.write( buff )

            if( ver == 0 ): 
                upgrade_from_0_to_1( session )
                upgrade_from_1_to_2( session )
                upgrade_from_2_to_3( session )
                upgrade_from_3_to_4( session )
                upgrade_from_4_to_5( session )
                continue
            elif( ver == 1 ):
                upgrade_from_1_to_2( session )
                upgrade_from_2_to_3( session )
                upgrade_from_3_to_4( session )
                upgrade_from_4_to_5( session )
                continue
            elif( ver == 2 ):
                upgrade_from_2_to_3( session )
                upgrade_from_3_to_4( session )
                upgrade_from_4_to_5( session )
                continue
            elif( ver == 3 ):
                upgrade_from_3_to_4( session )
                upgrade_from_4_to_5( session )
                continue
            elif( ver == 4 ):
                upgrade_from_4_to_5( session )
                continue
            else:
                raise RuntimeError( 'Incompatible database version' )
        elif( dbi.get_revision() > REVISION ):
            raise RuntimeError( 'Incompatible database revision' )
        elif( dbi.get_revision() != REVISION ):
            dbi.set_revision( REVISION )
            session.commit()

        break

    session.commit()
    session.close()

class DatabaseInfo:

    def __init__( self, dbi ):

        self.dbi = dbi

        try:
            self.dbi.create( [  ( 'uuid',   'TEXT', ),
                                ( 'ver',    'VERSION', ),
                                ( 'rev',    'INTEGER', ) ] )

            self.dbi.insert( [ ( 'uuid', str( uuid.uuid1() ), ), ( 'ver', VERSION ), ( 'rev', REVISION, ) ] )
        except db.QueryError:
            pass

    def get_uuid( self ):

        return self.dbi.select( [ 'uuid' ] ).eval( True, True )

    def get_version( self ):

        return self.dbi.select( [ 'ver' ] ).eval( True, True )

    def get_revision( self ):

        return self.dbi.select( [ 'rev' ] ).eval( True, True )

    def set_revision( self, rev ):

        self.dbi.update( [ ( 'rev', rev, ) ] )

class MasterObjectList:

    def __init__( self, objl ):

        self.objl = objl

        try:
             self.objl.create( [    ( 'id',     'INTEGER PRIMARY KEY', ),
                                    ( 'type',   'INTEGER NOT NULL', ),
                                    ( 'name',   'TEXT', ),
                                    ( 'dup',    'INTEGER', ), ] )
        except db.QueryError:
            pass

    def lookup( self, type = None, name = None, sortby = None ):

        query = []
        if( type is not None ):
            query.append( ( 'type', type, ) )
        if( name is not None ):
            query.append( ( 'name', name, ) )

        if( sortby != None ):
            result = self.objl.select( [ 'id' ], query, order = sortby )
        else:
            result = self.objl.select( [ 'id' ], query )

        return ResultIterator( result.__iter__(), lambda x: x[0] )

    def get_type( self, id ):

        return self.objl.select( [ 'type' ], [ ( 'id', id, ) ] ).eval( True, True )

    def get_name( self, id ):

        return self.objl.select( [ 'name' ], [ ( 'id', id, ) ] ).eval( True, True )

    def set_name( self, id, name ):

        self.objl.update( [ ( 'name', name, ), ], [ ( 'id', id, ), ] )

    def register( self, type, name = None ):

        return self.objl.insert( [ ( 'type', type, ), ( 'name', name, ) ],
                                 [ 'id' ] ).eval( True, True )

    def unregister( self, id ):

        self.objl.delete( [ ( 'id', id, ) ] )
    
    def restrict_by_type( self, tbl, type ):

        invalidate = db.InOperator( 'id', db.Query( db.Selection( [ 'id' ],
            [ ( 'type', type, ) ] ), self.objl ) )

        return db.Query( db.Selection( [ 'id' ], [ invalidate ] ), tbl )

    def lookup_names_by_query( self, query ):

        q = db.Query( db.Selection( [ 'a.id', 'b.name' ], group = 'a.id' ),
                db.LeftOuterJoinOperator( query, self.objl, 'a', 'b', 'id' ) )

        return q

class FileChecksumList:

    def __init__( self, fchk ):

        self.fchk = fchk

        try:
            self.fchk.create( [ ( 'id',     'INTEGER PRIMARY KEY', ),
                                ( 'len',    'INTEGER', ),
                                ( 'crc32',  'TEXT', ),
                                ( 'md5',    'TEXT', ),
                                ( 'sha1',   'TEXT', ), ] )
        except db.QueryError:
            pass

    def details( self, id ):

        return self.fchk.select( [ 'len', 'crc32', 'md5', 'sha1' ],
                [ ( 'id', id ) ] ).eval( True, True )

    def lookup( self, length = None, crc32 = None, md5 = None, sha1 = None ):

        query = []
        if( length != None ):
            query.append( ( 'len', length, ) )
        if( crc32 != None ):
            query.append( ( 'crc32', crc32.lower(), ) )
        if( md5 != None ):
            query.append( ( 'md5', md5.lower(), ) )
        if( sha1 != None ):
            query.append( ( 'sha1', sha1.lower(), ) )

        if( len( query ) == 0 ):
            result = self.fchk.select( [ 'id' ] )
        else:
            result = self.fchk.select( [ 'id' ], query )

        return ResultIterator( result.__iter__(), lambda x: x[0] )

    def register( self, id, length, crc32, md5, sha1 ):

        length = check_len( length )
        crc32 = check_crc32( crc32 )
        md5 = check_md5( md5 )
        sha1 = check_sha1( sha1 )

        self.fchk.insert( [ ( 'id', id, ), ( 'len', length, ), ( 'crc32', crc32, ), ( 'md5', md5, ), ( 'sha1', sha1, ) ] )

    def unregister( self, id ):

        self.fchk.delete( [ ( 'id', id, ) ] )

class RelationList:

    def __init__( self, rell ):

        self.rell = rell

        try:
             self.rell.create( [    ( 'id',     'INTEGER NOT NULL', ),
                                    ( 'parent', 'INTEGER NOT NULL', ),
                                    ( 'sort',   'INTEGER', ), ] )
        except db.QueryError:
            pass

    def get_parents( self, id ):

        return self.rell.select( [ 'parent' ], [ ( 'id', id, ), ] ).eval( True )

    def get_children( self, id ):

        return self.rell.select( [ 'id' ], [ ( 'parent', id, ), ] ).eval( True )

    def assign_parent( self, id, parent, order = None ):

        if( len( self.rell.select( query = [ ( 'id', id, ), ( 'parent', parent, ) ] ).eval() ) > 0 ):
            self.rell.update(   [ ( 'sort', order, ), ],
                                [ ( 'id', id, ), ( 'parent', parent, ) ] )
        else:
            self.rell.insert( [ ( 'id', id, ), ( 'parent', parent, ), ( 'sort', order, ), ] )

    def transfer_parent( self, old_parent, new_parent ):

        self.rell.update( [ ( 'parent', new_parent, ) ],
                          [ ( 'parent', old_parent, ) ] )

    def clear_parent( self, id, parent ):

        self.rell.delete( [ ( 'id', id, ), ( 'parent', parent, ) ] )

#        if( parent == None ):
#            order = None
#
#        self.rell.update( [ ( 'parent', parent, ), ( 'sort', order, ) ],
#                [ ( 'id', id, ) ] )

    def get_order( self, id, parent ):

        return self.rell.select( [ 'sort' ], [ ( 'id', id, ), ( 'parent', parent, ) ] ).eval( True, True )

    def set_order( self, id, parent, order ):

        self.rell.update( [ ( 'sort', order, ) ], [ ( 'id', id, ), ( 'parent', parent, ) ] )

    def child_iterator( self, id ):

        result = self.rell.select( [ 'id' ], [ ( 'parent', id, ) ], 'sort' )
        return ResultIterator( result.__iter__(), lambda x: x[0] )

    def select_no_album( self, tbl ):

        invalidate = db.InOperator( 'id', db.Query( db.Selection( [ 'id' ] ), self.rell ), True )
        return db.Query( db.Selection( [ 'id' ], [ invalidate ], distinct = True ), tbl )

    def select_no_parent( self, tbl ):

        invalidate = db.InOperator( 'id', db.Query( db.Selection( [ 'id' ] ), self.rell ), True )
        return db.Query( db.Selection( [ 'id' ], [ invalidate ], distinct = True ), tbl )

    def unregister( self, id ):

        self.rell.delete( [ ( 'id', id, ) ] )
        self.rell.delete( [ ( 'parent', id, ) ] )

    def restrict_ids( self, tbl, require, add = [], sub = [], random = False ):

        def require_parent( parent, neg = False ):

            return db.InOperator( 'id', db.Query( db.Selection( [ 'id' ],
                    [ ( 'parent', parent, ) ] ), self.rell ), neg )

        req_c = [require_parent( p, False ) for p in require]
        add_c = [require_parent( p, False ) for p in add]
        sub_c = [require_parent( p, True ) for p in sub]

        if( len( add_c ) > 0 ):
            add_op = db.OrOperator( add_c )
            req_c.append( add_op )

        if( len( sub_c ) > 0 ):
            sub_op = db.AndOperator( sub_c )
            req_c.append( sub_op )

        if( random ):
            order = 'RANDOM()'
        else:
            order = None

        return db.Query( db.Selection( [ 'id' ], req_c, order = order, distinct = True ), tbl )

class MetaList:

    def __init__( self, meta ):

        self.meta = meta

        try:
            self.meta.create( [ ( 'id',     'INTEGER NOT NULL', ),
                                ( 'key',    'TEXT NOT NULL', ),
                                ( 'value',  'TEXT', ), ] )
        except db.QueryError:
            pass

    def all_keys( self ):

        return ResultIterator( self.meta.select( [ 'key' ], distinct = True ).__iter__(),
                lambda x: x[0] )

    def lookup_keys( self, id ):

        return ResultIterator( self.meta.select( [ 'key' ], [ ( 'id', id, ) ],
                distinct = True ).__iter__(), lambda x: x[0] )

    def clear_key( self, id, key ):

        self.meta.delete( [ ( 'id', id, ), ( 'key', key, ) ] )

    def set_key( self, id, key, value ):

        try:
            self.meta.update( [ ( 'value', value, ) ],
                    [ ( 'id', id, ), ( 'key', key, ) ] )
        except StopIteration:
            self.meta.insert( [ ( 'id', id, ), ( 'key', key, ), ( 'value', value, ) ] )
            return True

    def get_value( self, id, key ):

        return self.meta.select( [ 'value' ],
                [ ( 'id', id, ), ( 'key', key, ) ] ).eval( True, True )

    def rename_key( self, key, new_name ):

        self.meta.update( [ ( 'key', new_name, ) ], [ ( 'key', key, ) ] )

    def unregister( self, id ):

        self.meta.delete( [ ( 'id', id, ) ] )

# vim:sts=4:et
