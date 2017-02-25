import hdbfs

import model

class TagConstraint:

    def __init__( self, tag ):

        self.__tag = tag

    def to_db_constraint( self, db ):

        if( isinstance( self.__tag, hdbfs.Obj ) ):
            tag = self.__tag
        elif( isinstance( self.__tag, int ) ):
            tag = db.get_object_by_id( self.__tag )
        else:
            tag = db.get_tag( self.__tag )
        return db.session.query( model.Relation.child ) \
                         .filter( model.Relation.parent == tag.obj.id )

class StringConstraint:

    def __init__( self, s ):

        self.__s = s

    def to_db_constraint( self, db ):

        if( len( self.__s ) == 0 ):
            sql_s = '%'
        else:
            sql_s = self.__s.replace( '%', '[%]' ) \
                            .replace( '*', '%' )
            if( sql_s[0] != '%' ):
                sql_s = '%' + sql_s
            if( sql_s[-1] != '%' ):
                sql_s = sql_s + '%'

        return db.session.query( model.Object.id ) \
                         .filter( model.Object.name.like( sql_s ) )

class UnboundConstraint:

    def __init__( self, s ):

        self.__s = s

    def to_db_constraint( self, db ):

        try:
            c = TagConstraint( self.__s )
            db_c = c.to_db_constraint( db )
            if( db_c is not None ):
                return db_c
        except:
            pass

        c = StringConstraint( self.__s )
        return c.to_db_constraint( db )

class ParameterConstraint:

    def __init__( self, key, op, value ):

        self.__key = key

        if( op == '=' ):
            self.__constraint = (model.Metadata.value == str( value ))
        elif( op == '!=' ):
            self.__constraint = (model.Metadata.value != str( value ))
        elif( op == '>' ):
            self.__constraint = (model.Metadata.num > int( value ))
        elif( op == '>=' ):
            self.__constraint = (model.Metadata.num >= int( value ))
        elif( op == '<' ):
            self.__constraint = (model.Metadata.num < int( value ))
        elif( op == '<=' ):
            self.__constraint = (model.Metadata.num <= int( value ))
        else:
            assert False

    def to_db_constraint( self, db ):

        from sqlalchemy import and_

        return db.session.query( model.Metadata.id ) \
                         .filter( and_( model.Metadata.key == self.__key, \
                                        self.__constraint ) )

class Query:

    def __init__( self ):

        self.__obj_type = None
        self.__order_by = 'rand'
        self.__order_desc = False
        self.__strict = False

        self.__req_constraints = []
        self.__or_constraints = []
        self.__not_constraints = []

    def set_strict( self ):

        self.__strict = True

    def set_type( self, obj_type ):

        self.__obj_type = obj_type

    def set_order( self, prop, desc = False ):

        self.__order_by = prop
        self.__order_desc = desc

    def add_require_constraint( self, constraint ):

        self.__req_constraints.append( constraint )

    def add_or_constraint( self, constraint ):

        self.__or_constraints.append( constraint )

    def add_not_constraint( self, constraint ):

        self.__not_constraints.append( constraint )

    def set_constraints( self, req_c = [], or_c = [], not_c = [] ):

        self.__req_constraints = list( req_c )
        self.__or_constraints = list( or_c )
        self.__not_constraints = list( not_c )

    def execute( self, db ):

        to_db_c = lambda c: c.to_db_constraint( db )

        if( len( self.__or_constraints ) > 0 ):
            add_q = map( to_db_c, self.__or_constraints )
            add_q = add_q[0].union( *add_q[1:] )
        else:
            add_q = None

        if( len( self.__not_constraints ) > 0 ):
            sub_q = map( to_db_c, self.__not_constraints )
            sub_q = sub_q[0].union( *sub_q[1:] )
        else:
            sub_q = None

        if( len( self.__req_constraints ) > 0 ):
            req_q = map( to_db_c, self.__req_constraints )
            req_q = req_q[0].intersect( *req_q[1:] )
        else:
            req_q = None

        query = db.session.query( model.Object )

        if( req_q is not None ):
            q = req_q

            if( add_q is not None ):
                q = q.union( add_q )

            query = query.filter( model.Object.id.in_( q ) )
        elif( add_q is not None ):
            query = query.filter( model.Object.id.in_( add_q ) )

        if( sub_q is not None ):
            query = query.filter( ~model.Object.id.in_( sub_q ) )

        if( self.__obj_type is not None ):
            query = query.filter( model.Object.type == self.__obj_type )
        else:
            query = query.filter( model.Object.type.in_( [
                hdbfs.TYPE_FILE, hdbfs.TYPE_FILE_VAR, hdbfs.TYPE_ALBUM ] ) )

        if( self.__order_by == 'rand' ):
            query = query.order_by( 'RANDOM()' )
        elif( self.__order_by == 'add' ):
            if( not self.__order_desc ):
                query = query.order_by( model.Object.id )
            else:
                query = query.order_by( model.Object.id.desc() )
        elif( self.__order_by == 'name' ):
            if( not self.__order_desc ):
                query = query.order_by( model.Object.name,
                                        model.Object.id )
            else:
                query = query.order_by( model.Object.name.desc(),
                                        model.Object.id.desc() )

        return hdbfs.ModelObjToHiguObjIterator( db, query ) 

def create_constraint( s ):

    if( s.startswith( '@' ) ):
        return StringConstraint( s[1:] )
    elif( s.startswith( '#' ) ):
        return TagConstraint( s[1:] )
    elif( s.startswith( '&' ) ):
        ops = [ '>=', '<=', '>', '<', '!=', '=' ]
        s = s[1:]

        for i in ops:
            try:
                idx = s.index( i[0] )
                key = s[0:idx]
                op = i
                value = s[idx+len(i[0]):]

                return ParameterConstraint( key, op, value )
            except:
                pass
        else:
            raise ValueError, 'Bad Parameter Constraint'
    else:
        return UnboundConstraint( s )

def build_query( s ):

    query = Query()

    clauses = s.split( ' ' )
    clauses = [i for i in clauses if( len( i ) > 0 )]

    commands = [i[1:] for i in clauses if( i[0] == '$' )]
    add = [i[1:] for i in clauses if( i[0] == '?' )]
    sub = [i[1:] for i in clauses if( i[0] == '!' )]
    req = [i for i in clauses if( i[0] != '$' and i[0] != '?' and i[0] != '!' )]

    for cmd in commands:
        cmd = cmd.split( ':' )

        if( cmd[0] == 'strict' ):
            query.set_strict()

        elif( cmd[0] == 'sort' ):
            if( len( cmd ) < 2 ):
                raise ValueError, 'Sort command needs an argument'

            desc = False

            if( len( cmd ) > 2 and cmd[2] == 'desc' ):
                desc = True

            query.set_order( cmd[1], desc )

        elif( cmd[0] == 'type' ):
            if( len( cmd ) < 2 ):
                raise ValueError, 'Type command needs an argument'

            if( cmd[1] == 'orig' ):
                query.set_type( hdbfs.TYPE_FILE );
            elif( cmd == 'dup' ):
                query.set_type( hdbfs.TYPE_FILE_DUP );
            elif( cmd == 'var' ):
                query.set_type( hdbfs.TYPE_FILE_VAR );
            elif( cmd == 'album' ):
                query.set_type( hdbfs.TYPE_ALBUM );
            else:
                raise ValueError, 'Bad type'

        else:
            raise ValueError, 'Bad Command'

    req = map( create_constraint, req )
    add = map( create_constraint, add )
    sub = map( create_constraint, sub )

    query.set_constraints( req, add, sub )

    return query
