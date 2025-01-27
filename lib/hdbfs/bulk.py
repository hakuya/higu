import re

import hdbfs

class ParseError( Exception ):

    def __init__( self ):
        Exception.__init__( self )

class BadArgument( Exception ):

    def __init__( self ):
        Exception.__init__( self )

class BulkOperation:

    def __init__( self ):

        self._commit = False

    def _process( self, it ):

        return None

    def set_commit( self, commit = True ):

        self._commit = commit
        return self

    def execute( self, db, query ):

        if( isinstance( query, list ) ):
            rs = query
        else:
            rs = query.execute( db )

        return [r for r in map( self._process, rs ) if r is not None ]

class BulkNameReplaceOp( BulkOperation ):

    def __init__( self, pattern, repl ):

        BulkOperation.__init__( self )
        self.__pattern = pattern
        self.__repl = repl

    def _process( self, it ):

        name = it.get_name()
        if( name is None ):
            return None

        subd = re.sub( self.__pattern, self.__repl, name )

        if( subd != name ):
            if( self._commit ):
                it.set_name( subd )

            return ( it, f'{name} -> {subd}' )

class BulkNameDelOp( BulkOperation ):

    def __init__( self, pattern = None ):

        BulkOperation.__init__( self )
        self.__pattern = pattern

    def _process( self, it ):

        name = it.get_name()
        if( name is None ):
            return None

        if( self.__pattern is not None
        and not re.match( self.__pattern, name ) ):
            return None

        if( self._commit ):
            it.set_name( None )

        items.append( ( it, f'{name} -> [none]' ) )

class BulkNameSelectOp( BulkOperation ):

    def __init__( self, pattern = None, force = False ):

        BulkOperation.__init__( self )
        self.__pattern = pattern
        self.__force = force

    def _process( self, it ):

        if( it.get_type() != hdbfs.TYPE_FILE ):
            return None

        name = it.get_name()
        if( name is not None and not self.__force ):
            return None

        new_name = None
        for n in it.get_origin_names():

            if( self.__pattern is None
             or re.match( self.__pattern, n ) ):

                new_name = n
                break

        if( new_name is None or new_name == name ):
            return None

        if( self._commit ):
            it.set_name( new_name )

        if( name is not None ):
            return ( it, f'{name} -> {new_name}' )
        else:
            return ( it, f'[none] -> {new_name}' )

class BulkRateOp( BulkOperation ):

    def __init__( self, rating ):

        BulkOperation.__init__( self )
        self.__rating = rating

    def _process( self, it ):

        if( self._commit ):
            it['rating'] = self.__rating

        return ( it, f'-> rating {self.__rating}' )

class BulkAssignOp( BulkOperation ):

    def __init__( self, assign = [], unassign = [] ):

        BulkOperation.__init__( self )
        self.__assign = list( assign )
        self.__unassign = list( unassign )

    def _process( self, it ):

        if( self._commit ):
            for jt in self.__unassign:
                it.unassign( jt )
            for jt in self.__assign:
                it.assign( jt )

        assign_str = ' '.join( [jt.get_repr() for jt in self.__assign]
                             + ['-' + jt.get_repr() for jt in self.__unassign] )

        return ( it, f'assign: {assign_str}' )

def op_from_string( db, s ):

    try:
        action, operand = tuple( map( lambda x: x.strip(), s.split( ':', 1 ) ) )
    except:
        raise ParseError()

    if( action == 'name' ):

        parts = list( map( lambda x: x.replace( '\0', '/' ),
                            operand.replace( '\\/', '\0' ).split( '/' ) ) )

        if( parts[0] == 's' ):
            if( len( parts ) == 3 ):
                return BulkNameReplaceOp( parts[1], parts[2] )
        elif( parts[0] == 'del' ):
            if( len( parts ) <= 2 ):
                return BulkNameDelOp( parts[1] if len( parts ) == 2 else None )
        elif( parts[0] in [ 'select', 'select!' ] ):
            if( len( parts ) <= 2 ):
                return BulkNameSelectOp(
                            parts[1] if len( parts ) == 2 else None,
                            parts[0] == 'select!' )

        raise ParseError()

    elif( action == 'rate' ):
        try:
            rating = int( operand )
        except:
            raise BadArgument()

        if( rating not in [ 2, 4, 6, 8, 10 ] ):
            raise BadArgument()

        return BulkRateOp( rating )

    elif( action in ['tag', 'untag'] ):
        tags = operand.strip().split( ' ' )

        try:
            assign = [db.get_tag( t ) for t in tags if t[0] != '-']
            unassign = [db.get_tag( t[1:] ) for t in tags if t[0] == '-']
        except:
            return BadArgument()
        
        if( action == 'untag' ):
            assign, unassign = unassign, assign

        return BulkAssignOp( assign, unassign )

    raise ParseError()
