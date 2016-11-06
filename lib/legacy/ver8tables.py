import uuid

import db

VERSION = 8
REVISION = 1

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

class DatabaseInfo:

    def __init__( self, dbi ):

        self.dbi = dbi

        try:
            self.dbi.create( [  ( 'uuid',       'TEXT', ),
                                ( 'ver',        'INTEGER', ),
                                ( 'rev',        'INTEGER', ),
                                ( 'imgdb_ver',  'INTEGER', ) ] )

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
