import db
import uuid
import os
import re

from hash import calculate_details

VERSION = 1
REVISION = 0

GFDB_PATH = os.path.join( os.environ['HOME'], '.gfdb' )
LFDB_NAME = '.lfdb'
GFDB = None

ORDER_VARIENT   = -1
ORDER_DUPLICATE = -2

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
                if( ver == 0 ): 
                    upgrade_from_0_to_1( self.db )
                    continue
                else:
                    raise RuntimeError( 'Incompatible database version' )
            elif( self.dbi.get_revision() > REVISION ):
                raise RuntimeError( 'Incompatible database revision' )

            break

        self.mfl = MasterFileList( self.db.get_table( 'mfl' ) )
        self.naml = NameList( self.db.get_table( 'naml' ) )
        self.tagl = TagList( self.db.get_table( 'tagl' ) )

    def commit( self ):

        self.db.commit()

    def close( self ):

        self.db.close()
        self.mfl = None
        self.naml = None

    def get_mfl( self ):

        return self.mfl

    def get_naml( self ):

        return self.naml

    def get_tagl( self ):

        return self.tagl

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

class MasterFileList:

    def __init__( self, mfl ):

        self.mfl = mfl

        try:
            self.mfl.create( [  ( 'id',     'INTEGER PRIMARY KEY', ),
                                ( 'len',    'INTEGER', ),
                                ( 'crc32',  'TEXT', ),
                                ( 'md5',    'TEXT', ),
                                ( 'sha1',   'TEXT', ),
                                ( 'parent', 'INTEGER', ),
                                ( 'gorder',  'INTEGER', ), ] )
        except db.QueryError:
            pass

    def details( self, id ):

        return self.mfl.select( [ 'len', 'crc32', 'md5', 'sha1' ],
                [ ( 'id', id ) ] ).eval( True, True )

    def get_parent( self, id ):

        return self.mfl.select( [ 'parent' ], [ ( 'id', id ) ] ).eval( True, True )

    def set_parent( self, id, parent, order = 0 ):

        if( parent == None ):
            order = None

        self.mfl.update( [ ( 'parent', parent, ), ( 'gorder', order, ) ],
                [ ( 'id', id, ) ] )

    def get_order( self, id ):

        return self.mfl.select( [ 'gorder' ], [ ( 'id', id ) ] ).eval( True, True )

    def set_order( self, id, order ):

        self.mfl.update( [ ( 'gorder', order, ) ], [ ( 'id', id, ) ] )

    def child_iterator( self, id ):

        result = self.mfl.select( [ 'id' ], [ ( 'parent', id ) ], 'gorder' )
        return ResultIterator( result.__iter__(), lambda x: x[0] )

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
            result = self.mfl.select( [ 'id' ] )
        else:
            result = self.mfl.select( [ 'id' ], query )

        return ResultIterator( result.__iter__(), lambda x: x[0] )

    def register( self, length, crc32, md5, sha1 ):

        if( len( self.lookup( length, crc32, md5, sha1 ) ) != 0 ):
            return False

        length = check_len( length )
        crc32 = check_crc32( crc32 )
        md5 = check_md5( md5 )
        sha1 = check_sha1( sha1 )

        self.mfl.insert( [ ( 'len', length, ), ( 'crc32', crc32, ), ( 'md5', md5, ), ( 'sha1', sha1, ) ] )

        return self.lookup( length, crc32, md5, sha1 ).next()

class TagList:

    def __init__( self, tagl ):

        self.tagl = tagl

        try:
            self.tagl.create( [ ( 'id',     'INTEGER', ),
                                ( 'tag',    'TEXT', ) ] )
        except db.QueryError:
            pass

    def all_tags( self ):

        return ResultIterator( self.tagl.select( [ 'tag' ], distinct = True ).__iter__(),
                lambda x: x[0] )

    def lookup_tags( self, id ):

        return ResultIterator( self.tagl.select( [ 'tag' ], [ ( 'id', id, ) ] ).__iter__(),
                lambda x: x[0] )

    def restrict_ids( self, tbl, require, add = [], sub = [], strict = False ):

        def require_tag( tag, neg = False ):

            return db.InOperator( 'id', db.Query( db.Selection( [ 'id' ],
                    [ ( 'tag', tag, ) ] ), self.tagl ), neg )

        req_c = [require_tag( t, False ) for t in require]
        add_c = [require_tag( t, False ) for t in add]
        sub_c = [require_tag( t, True ) for t in sub]

        if( len( add_c ) > 0 ):
            add_op = db.OrOperator( add_c )
            req_c.append( add_op )

        if( len( sub_c ) > 0 ):
            sub_op = db.AndOperator( sub_c )
            req_c.append( sub_op )

        if( strict ):
            all_tags = require + add + sub
            others = map( lambda x: db.InequalityOperator( 'tag', x ), all_tags )
            if( len( others ) > 0 ):
                others_op = [ db.AndOperator( others ) ]
            else:
                others_op = []

            invalidate = db.InOperator( 'id', db.Query( db.Selection( [ 'id' ],
                    others_op ), self.tagl ), True )

            req_c.append( invalidate )

        return db.Query( db.Selection( [ 'id' ], req_c, distinct = True ), tbl )

    def tag( self, id, tag ):

        try:
            self.tagl.select( query = [ ( 'id', id, ), ( 'tag', tag, ) ] ).__iter__().next()
            return False
        except StopIteration:
            self.tagl.insert( [ ( 'id', id, ), ( 'tag', tag, ) ] )
            return True

    def untag( self, id, tag ):

        self.tagl.delete( [ ( 'id', id, ), ( 'tag', tag, ) ] )

    def rename_tag( self, tag, new_name ):

        self.tagl.update( [ ( 'tag', new_name, ) ], [ ( 'tag', tag, ) ] )

class NameList:

    def __init__( self, naml ):

        self.naml = naml

        try:
            self.naml.create( [ ( 'id',     'INTEGER', ),
                                ( 'name',   'TEXT', ) ] )
        except db.QueryError:
            pass

    def lookup_names_by_query( self, query ):

        q = db.Query( db.Selection( [ 'a.id', 'b.name' ], group = 'a.id' ),
                db.LeftOuterJoinOperator( query, self.naml, 'a', 'b', 'id' ) )

        return q

    def lookup_names( self, id ):

        return ResultIterator( self.naml.select( [ 'name' ], [ ( 'id', id, ) ] ).__iter__(),
                lambda x: x[0] )

    def lookup_ids( self, name ):

        return ResultIterator( self.naml.select( [ 'id' ], [ ( 'name', name, ) ] ).__iter__(),
                lambda x: x[0] )

    def all_names( self ):

        return ReultIterator( self.naml.select( [ 'name' ], distinct = True ).__iter__(),
                lambda x: x[0] )

    def register( self, id, name ):

        try:
            self.naml.select( query = [ ( 'id', id, ), ( 'name', name, ) ] ).__iter__().next()
            return False
        except StopIteration:
            self.naml.insert( [ ( 'id', id, ), ( 'name', name, ) ] )
            return True

    def unregister( self, id, name ):

        self.naml.delete( [ ( 'id', id, ), ( 'name', name, ) ] )

# vim:sts=4:et
