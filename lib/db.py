import sqlite3
import re

def check_name( str ):

    assert re.search( '[ ,()]', str[0] ) == None

def check_type( str ):

    assert re.search( '[,()]', str[1] ) == None

class QueryError:

    def __init__( self, ex ):

        self.ex = ex

    def __str__( self ):

        return self.ex.__str__()

class Query:

    def __init__( self, select, table ):

        self.select = select
        self.table  = table
        self.db     = table.db

    def build_query( self ):

        return self.select.build_query( self.table )

    def eval( self, single_col = False, single_row = False ):

        if( single_row ):
            try:
                if( single_col ):
                    return self.__iter__().next()[0]
                else:
                    return self.__iter__().next()
            except StopIteration:
                return None
        else:
            if( single_col ):
                return [r[0] for r in self.__iter__()]
            else:
                return [r for r in self.__iter__()]

    def __iter__( self ):

        q, k = self.build_query()

        try:
            c = self.db.cursor()
            if( k == None ):
                c.execute( q )
            else:
                c.execute( q, k )

            return ResultSet( c )

        except sqlite3.OperationalError, ex:
            raise QueryError( ex )

class ResultSet:

    def __init__( self, rs ):

        self.rs = rs

    def __iter__( self ):

        return self

    def next( self ):

        return self.rs.next()

class Operator:

    def make_query( self ):

        return '', []

class ComparisonOperator( Operator ):

    def __init__( self, operator, lhs, rhs ):

        self.operator = operator
        self.lhs = lhs
        self.rhs = rhs

    def make_query( self ):

        return '%s %s ?' % ( self.lhs, self.operator, ), [ self.rhs ]

class InequalityOperator( ComparisonOperator ):

    def __init__( self, lhs, rhs ):

        ComparisonOperator.__init__( self, '!=', lhs, rhs )

class LogicOperator( Operator ):

    def __init__( self, operator, constraints ):

        self.operator = operator
        self.constraints = constraints

    def make_query( self ):

        s = ''
        p = []

        for c in self.constraints:

            if( isinstance( c, Operator ) ):
                q = c.make_query()

                s += '(' + q[0] + ') %s ' % ( self.operator )
                p.extend( q[1] )
            else:
                check_name( c[0] )

                s += '%s = ? %s ' % ( c[0], self.operator )
                p.append( c[1] )

        s = s[:-(len( self.operator ) + 2)]

        return s, p

class AndOperator( LogicOperator ):

    def __init__( self, constraints ):

        LogicOperator.__init__( self, 'AND', constraints )

class OrOperator( LogicOperator ):

    def __init__( self, constraints ):

        LogicOperator.__init__( self, 'OR', constraints )

class NullOperator( Operator ):

    def __init__( self, field, is_null ):

        self.field = field
        self.is_null = is_null

    def make_query( self ):

        if( self.is_null ):
            return '%s is null' % ( self.field, ), []
        else:
            return '%s is not null' % ( self.field, ), []

class InOperator( Operator ):

    def __init__( self, col, query, neg = False ):

        self.col = col
        self.query = query
        self.neg = neg

    def make_query( self ):

        q, k = self.query.build_query()

        if( self.neg ):
            return '%s not in (%s)' % ( self.col, q ), k
        else:
            return '%s in (%s)' % ( self.col, q ), k

class LeftOuterJoinOperator( Operator ):

    def __init__( self, table_a, table_b, name_a, name_b, var_a, var_b = None ):

        self.db = table_a.db
        self.table_a = table_a
        self.table_b = table_b
        self.name_a = name_a
        self.name_b = name_b
        self.var_a = var_a
        if( var_b == None ):
            self.var_b = var_a
        else:
            self.var_b = var_b

    def make_query( self ):

        q = ''
        k = []

        if( isinstance( self.table_a, Query ) ):
            qt, kt = self.table_a.build_query()
            q += '(%s) %s' % ( qt, self.name_a )
            k.extend( kt )
        else:
            q += '%s %s' % ( self.table_a.name, self.name_a )

        q += ' LEFT OUTER JOIN '

        if( isinstance( self.table_b, Query ) ):
            qt, kt = self.table_b.build_query()
            q += '(%s) %s' % ( qt, self.name_b )
            k.extend( kt )
        else:
            q += '%s %s' % ( self.table_b.name, self.name_b )

        q += ' ON %s.%s = %s.%s' % ( self.name_a, self.var_a, self.name_b, self.var_b, )

        return q, k

class Selection:

    def __init__( self, rows = None, query = None, order = None, group = None, descending = False, distinct = False ):

        self.rows = rows
        self.query = query
        self.order = order
        self.group = group
        self.descending = descending
        self.distinct = distinct

    def build_query( self, table ):

        if( self.rows == None ):
            sel = '*'
        else:
            sel = ''

            for row in self.rows:
                check_name( row )
                sel += row + ', '

            sel = sel[:-2]

        q = 'SELECT '
        k = []

        if( self.distinct ):
            q += 'DISTINCT '

        if( isinstance( table, Table ) ):
            q += '%s FROM %s' % ( sel, table.name )
        elif( isinstance( table, Operator ) ):
            qt, kt = table.make_query()
            q += '%s FROM %s' % ( sel, qt )
            k.extend( kt )
        elif( isinstance( table, Query ) ):
            qt, kt = table.build_query()
            q += '%s FROM (%s)' % ( sel, qt )
            k.extend( kt )

        if( self.query == None or len( self.query ) == 0 ):
            pass
        else:
            if( not isinstance( self.query, Operator ) ):
                query = AndOperator( self.query )
            else:
                query = self.query

            query, constraints = query.make_query()

            q += ' WHERE ' + query
            k.extend( constraints )

        if( self.group != None ):
            check_name( self.group )

            q += ' GROUP BY %s' % ( self.group )

        if( self.order != None ):
            check_name( self.order )

            q += ' ORDER BY %s' % ( self.order )

            if( self.descending ):
                q += ' DESC'

        return q, k

class SqlLiteDatabase:

    def __init__( self, dbfile ):

        self.dbfile = dbfile
        self.db = sqlite3.connect( self.dbfile )

    def close( self ):

        self.db.close()

    def commit( self ):

        self.db.commit()

    def get_table( self, name ):

        return Table( self.db, name )

class Table:

    def __init__( self, db, name ):

        check_name( name )

        self.db = db
        self.name = name

    def create( self, cols, temp = False ):

        s = ''

        for col in cols:
            check_name( col[0] )
            check_type( col[1] )

            s += col[0] + ' ' + col[1] + ', '

        s = s[:-2]

        try:
            c = self.db.cursor()
            if( temp ): 
                c.execute( 'CREATE TEMPORARY TABLE %s (%s)' % ( self.name, s ) )
            else:
                c.execute( 'CREATE TABLE %s (%s)' % ( self.name, s ) )
        except sqlite3.OperationalError, ex:
            raise QueryError( ex )

    def drop( self ):

        try:
            c = self.db.cursor()
            c.execute( 'DROP TABLE %s' % ( self.name ) )
        except sqlite3.OperationalError, ex:
            raise QueryError( ex )

    def add_col( self, name, type ):

        check_name( name )
        check_type( type )

        try:
            c = self.db.cursor()
            c.execute( 'ALTER TABLE %s ADD %s %s' % ( self.name, name, type ) )
        except sqlite3.OperationalError, ex:
            raise QueryError( ex )

    def insert( self, rows, select = None ):

        s = ''
        t = ''

        for row in rows:
            check_name( row[0] )

            s += row[0] + ','
            t += '?,'

        s = s[:-1]
        t = t[:-1]

        try:
            c = self.db.cursor()
            c.execute( 'INSERT INTO %s(%s) VALUES (%s)' % ( self.name, s, t ), map( lambda x: x[1], rows ) )

            return self.select( rows = select, query = [ ( '_ROWID_', c.lastrowid, ) ] )
        except sqlite3.OperationalError, ex:
            raise QueryError( ex )

    def insert_selection( self, selection, table, rows = None ):

        if( rows != None and len( rows ) > 0 ):
            s = ''

            for row in rows:
                check_name( row )

                s += row + ','

            s = s[:-1]
        else:
            s = None

        q, k = selection.build_query( table.name )

        if( s != None ):
            q = 'INSERT INTO %s(%s) %s' % ( self.name, s, q )
        else:
            q = 'INSERT INTO %s %s' % ( self.name, q )

        try:
            c = self.db.cursor()
            if( k != None ):
                c.execute( q, k )
            else:
                c.execute( q )
        except sqlite3.OperationalError, ex:
            raise QueryError( ex )

    def delete( self, query ):

        q = 'DELETE FROM %s WHERE ' % ( self.name )

        if( not isinstance( query, Operator ) ):
            query = AndOperator( query )

        query, constraints = query.make_query()

        q += query

        try:
            c = self.db.cursor()
            c.execute( q, constraints )
        except sqlite3.OperationalError, ex:
            raise QueryError( ex )

    def update( self, rows, query = None ):

        q = 'UPDATE %s SET ' % ( self.name )
        p = []

        for row in rows:
            check_name( row[0] )

            q += '%s = ?, ' % ( row[0] )
            p.append( row[1] )

        q = q[:-2]

        if( query != None ):
            q = q + ' WHERE '

            if( not isinstance( query, Operator ) ):
                query = AndOperator( query )

            query, constraints = query.make_query()

            q += query
            p.extend( constraints )

        try:
            c = self.db.cursor()
            c.execute( q, p )
        except sqlite3.OperationalError, ex:
            raise QueryError( ex )

    def select( self, rows = None, query = None, order = None, group = None, descending = False, distinct = False ):

        s = Selection( rows, query, order, group, descending, distinct )
        return Query( s, self )

# vim:sts=4:et:sw=4
