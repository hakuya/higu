import db
import uuid
import os
import re

from hash import calculate_details

VERSION = 4
REVISION = 0

GFDB_PATH = os.path.join( os.environ['HOME'], '.gfdb' )
LFDB_NAME = '.lfdb'
GFDB = None

ORDER_VARIENT   = -1
ORDER_DUPLICATE = -2

TYPE_NILL       = 0
TYPE_FILE       = 1000
TYPE_GROUP      = 2000
TYPE_ALBUM      = 2001
TYPE_CLASSIFIER = 2002

REL_CHILD       = 0
REL_DUPLICATE   = 1000
REL_VARIANT     = 1001
REL_CLASS       = 2000

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
            rell.insert( [ ( 'id', id, ), ( 'parent', parent, ), ( 'rel', REL_VARIANT, ) ] )
        elif( parent != None and order == ORDER_DUPLICATE ):
            rell.insert( [ ( 'id', id, ), ( 'parent', parent, ), ( 'rel', REL_DUPLICATE, ) ] )
        elif( parent != None ):
            coltbl[id] = [ parent, order ]
            if( not collst.has_key( parent ) ):
                collst[parent] = -1
        # Create collections at the end so we don't mess up the ids

    for collection in collst.keys():
        colid = objl.insert( [ ( 'type', TYPE_ALBUM, ), ], [ 'id' ] ).eval( True, True )
        collst[collection] = colid
        rell.insert( [ ( 'id', collection, ), ( 'parent', colid, ), ( 'rel', REL_CHILD, ), ( 'sort', 0, ) ] )

    for member in coltbl.keys():
        collection, order = coltbl[member]
        rell.insert( [ ( 'id', member, ), ( 'parent', collst[collection], ), ( 'rel', REL_CHILD, ), ( 'sort', order, ) ] )

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
                ( 'rel', REL_CLASS, ), ] )

    tagl.drop()
    dbi.update( [ ( 'ver', 4, ), ( 'rev', 0, ) ] )

    db.commit()

class ResultIterator:

    def __init__( self, rs, fn = lambda x: x ):

        self.rs = rs
        self.fn = fn

    def next( self ):

        return self.fn( self.rs.next() )

    def __iter__( self ):

        return self

class FileMgmtDb:

    def __init__( self, dbfile ):

        self.db = db.SqlLiteDatabase( dbfile )
        self.dbi = DatabaseInfo( self.db.get_table( 'dbi' ) )

        while( True ):
            ver = self.dbi.get_version()
         
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
                    upgrade_from_0_to_1( self.db )
                    upgrade_from_1_to_2( self.db )
                    upgrade_from_2_to_3( self.db )
                    upgrade_from_3_to_4( self.db )
                    continue
                elif( ver == 1 ):
                    upgrade_from_1_to_2( self.db )
                    upgrade_from_2_to_3( self.db )
                    upgrade_from_3_to_4( self.db )
                    continue
                elif( ver == 2 ):
                    upgrade_from_2_to_3( self.db )
                    upgrade_from_3_to_4( self.db )
                    continue
                elif( ver == 3 ):
                    upgrade_from_3_to_4( self.db )
                    continue
                else:
                    raise RuntimeError( 'Incompatible database version' )
            elif( self.dbi.get_revision() > REVISION ):
                raise RuntimeError( 'Incompatible database revision' )
            elif( self.dbi.get_revision() != REVISION ):
                self.dbi.set_revision( REVISION )
                self.commit()

            break

        self.objl = MasterObjectList( self.db.get_table( 'objl' ) )
        self.rell = RelationList( self.db.get_table( 'rell' ) )
        self.fchk = FileChecksumList( self.db.get_table( 'fchk' ) )
        self.meta = MetaList( self.db.get_table( 'meta' ) )

    def commit( self ):

        self.db.commit()

    def close( self ):

        self.db.close()
        self.objl = None
        self.rell = None
        self.fchk = None
        self.naml = None

    def get_objl( self ):

        return self.objl

    def get_rell( self ):

        return self.rell

    def get_fchk( self ):

        return self.fchk

    def get_meta( self ):

        return self.meta

    def get_uuid( self ):

        return self.dbi.get_uuid()

    def get_version( self ):

        return self.dbi.get_version()

    def get_revision( self ):

        return self.dbi.get_revision()

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
                                    ( 'name',   'TEXT', ), ] )
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
                                    ( 'rel',    'INTEGER NOT NULL', ),
                                    ( 'sort',   'INTEGER', ), ] )
        except db.QueryError:
            pass

    def get_parents( self, id, rel ):

        return self.rell.select( [ 'parent' ], [ ( 'id', id, ), ( 'rel', rel, ), ] ).eval( True )

    def get_children( self, id, rel ):

        return self.rell.select( [ 'id' ], [ ( 'parent', id, ), ( 'rel', rel, ), ] ).eval( True )

    def assign_parent( self, id, parent, rel, order = None ):

        if( len( self.rell.select( query = [ ( 'id', id, ), ( 'parent', parent, ) ] ).eval() ) > 0 ):
            self.rell.update(   [ ( 'rel', rel, ), ( 'sort', order, ), ],
                                [ ( 'id', id, ), ( 'parent', parent, ) ] )
        else:
            self.rell.insert( [ ( 'id', id, ), ( 'parent', parent, ),
                                ( 'rel', rel, ), ( 'sort', order, ), ] )

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

    def child_iterator( self, id, rel ):

        result = self.rell.select( [ 'id' ], [ ( 'parent', id, ), ( 'rel', rel, ) ], 'sort' )
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
                                ( 'tag',    'TEXT NOT NULL', ),
                                ( 'value',  'TEXT', ), ] )
        except db.QueryError:
            pass

    def all_tags( self ):

        return ResultIterator( self.meta.select( [ 'tag' ], distinct = True ).__iter__(),
                lambda x: x[0] )

    def lookup_tags( self, id ):

        return ResultIterator( self.meta.select( [ 'tag' ], [ ( 'id', id, ) ],
                distinct = True ).__iter__(), lambda x: x[0] )

    def clear_tag( self, id, tag ):

        self.tagl.delete( [ ( 'id', id, ), ( 'tag', tag, ) ] )

    def clear_single( self, id, tag, value ):

        self.tagl.delete( [ ( 'id', id, ), ( 'tag', tag, ), ( 'value', value, ) ] )

    def set_tag( self, id, tag, value ):

        try:
            ovalue = self.meta.select( [ 'value' ],
                    [ ( 'id', id, ), ( 'tag', tag, ) ] ).eval( True, True )
            self.meta.update( [ ( 'value', value, ) ],
                    [ ( 'id', id, ), ( 'tag', tag, ), ( 'value', ovalue, ) ] )
        except StopIteration:
            self.meta.insert( [ ( 'id', id, ), ( 'tag', tag, ), ( 'value', value, ) ] )
            return True

    def set_single( self, id, tag, value ):

        try:
            self.meta.select( [ 'value' ],
                    [ ( 'id', id, ), ( 'tag', tag, ), ( 'value', value, ) ] ).__iter__().next()
            self.meta.update( [ ( 'value', value, ) ], [ ( 'id', id, ), ( 'tag', tag, ) ] )
        except StopIteration:
            self.meta.insert( [ ( 'id', id, ), ( 'tag', tag, ), ( 'value', value, ) ] )
            return True

    def get_value( self, id, tag ):

        return self.meta.select( [ 'value' ],
                [ ( 'id', id, ), ( 'tag', tag, ) ] ).eval( True, True )

    def get_values( self, id, tag ):

        return self.meta.select( [ 'value' ],
                [ ( 'id', id, ), ( 'tag', tag, ) ] ).eval( True )

    def rename_tag( self, tag, new_name ):

        self.meta.update( [ ( 'tag', new_name, ) ], [ ( 'tag', tag, ) ] )

    def unregister( self, id ):

        self.meta.delete( [ ( 'id', id, ) ] )

# vim:sts=4:et
