import calendar
import datetime

import hdbfs

import model

class TagConstraint:

    def __init__( self, tag, fuzzy = False ):

        self.__tag = tag
        self.__fuzzy = fuzzy

    def get_preferred_order( self ):

        return None

    def to_db_constraint( self, db ):

        from sqlalchemy import and_

        if( isinstance( self.__tag, hdbfs.Obj ) ):
            tag = self.__tag
        elif( isinstance( self.__tag, int ) ):
            tag = db.get_object_by_id( self.__tag )
        else:
            tag = str( self.__tag )
            if( '*' in tag and self.__fuzzy ):
                sql_s = tag.replace( '%', '[%]' ) \
                           .replace( '*', '%' )
                tag = db.session.query( model.Object.object_id ) \
                        .filter( model.Object.object_type == hdbfs.TYPE_CLASSIFIER ) \
                        .filter( model.Object.name.like( sql_s ) )
            else:
                tag = db.get_tag( self.__tag )

        if( isinstance( tag, hdbfs.Obj ) ):
            return db.session.query( model.Relation.child_id ) \
                     .filter( model.Relation.parent_id == tag.obj.object_id )
        else:
            return db.session.query( model.Relation.child_id ) \
                     .filter( model.Relation.parent_id.in_( tag ) )

class TagCountConstraint:

    def __init__( self, op, c ):

        self.__op = op
        self.__c = int( c )

    def get_preferred_order( self ):

        return None

    def to_db_constraint( self, db ):

        from sqlalchemy import func, literal_column

        tagged = db.session.query( model.Relation.child_id.label( 'id' ),
                                   func.count( model.Relation.child_id ).label( 'tagc' ) ) \
                   .join( model.Object, model.Object.object_id == model.Relation.parent_id ) \
                   .filter( model.Object.object_type == model.TYPE_CLASSIFIER ) \
                   .group_by( model.Relation.child_id.label( 'id' ) )
        notags = db.session.query( model.Object.object_id, literal_column( '0' ).label( 'tagc' ) ) \
                   .filter( ~model.Object.object_id.in_(
                                db.session.query( model.Relation.child_id ) \
                                  .join( model.Object, model.Object.object_id
                                                    == model.Relation.parent_id ) \
                                  .filter( model.Object.object_type == model.TYPE_CLASSIFIER ) ) )
        tagq = tagged.union( notags ).subquery()

        q = db.session.query( tagq.c.id )

        return {
            '='  : lambda q: q.filter( tagq.c.tagc == self.__c ),
            '!=' : lambda q: q.filter( tagq.c.tagc != self.__c ),
            '>'  : lambda q: q.filter( tagq.c.tagc > self.__c ),
            '>=' : lambda q: q.filter( tagq.c.tagc >= self.__c ),
            '<'  : lambda q: q.filter( tagq.c.tagc < self.__c ),
            '<=' : lambda q: q.filter( tagq.c.tagc <= self.__c ),
        }[self.__op]( q )

class NameConstraint:

    def __init__( self, op, s ):

        from sqlalchemy import and_

        if( op == '=' or op == '!=' ):

            if( s is None ):
                self.__constraint = (model.Object.name == None)
            else:
                s = str( s )
                if( '*' in s ):
                    sql_s = s.replace( '%', '[%]' ) \
                             .replace( '*', '%' )
                    self.__constraint = (model.Object.name.like( sql_s ))
                else:
                    self.__constraint = (model.Object.name == s)

            if( op == '!=' ):
                self.__constraint = ~self.__constraint

        else:
            assert False

    def get_preferred_order( self ):

        return 'name'

    def to_db_constraint( self, db ):

        return db.session.query( model.Object.object_id ) \
                         .filter( self.__constraint )

class UnboundConstraint:

    def __init__( self, s ):

        self.__s = s

    def get_preferred_order( self ):

        return None

    def to_db_constraint( self, db ):

        try:
            c = TagConstraint( self.__s )
            db_c = c.to_db_constraint( db )
            if( db_c is not None ):
                return db_c
        except:
            pass

        c = NameConstraint( '=', '*' + self.__s + '*' )
        return c.to_db_constraint( db )

def QueryInt( v, ceil = False ):

    try:
        # Try as int
        return int( v )

    except ValueError:

        # Try as date
        if( '_' in v ):
            date_str, time_str = v.split( '_' )
        else:
            date_str = v
            time_str = None

        date_str = v.split( '/' )
        year = int( date_str[0] )
        dmon = int( date_str[1] ) if( len( date_str ) >= 2 ) else 1
        dday = int( date_str[2] ) if( len( date_str ) >= 3 ) else 1

        if( len( date_str ) >= 4 ):
            raise ValueError

        if( time_str is not None and len( date_str ) >= 3 ):
            time_str = time_str.split( ':' )
            hour = int( time_str[0] ) if( len( time_str ) >= 1 ) else 0
            tmin = int( time_str[1] ) if( len( time_str ) >= 2 ) else 0
            tsec = int( time_str[2] ) if( len( time_str ) >= 3 ) else 0

            if( len( time_str ) >= 4 ):
                raise ValueError
        else:
            hour = 0
            tmin = 0
            tsec = 0

        if( ceil ):
            if( len( date_str ) == 1 ):
                year += 1
            elif( len( date_str ) == 2 ):
                dmon += 1
            elif( len( date_str ) == 3 ):
                if( time_str is None or len( time_str ) == 0 ):
                    dday += 1
                elif( len( time_str ) == 1 ):
                    hour += 1
                elif( len( time_str ) == 2 ):
                    tmin += 1
                elif( len( time_str ) == 3 ):
                    tsec += 1

        dt = datetime.datetime( year, dmon, dday, hour, tmin, tsec )
        dt = calendar.timegm( dt.timetuple() )

        if( ceil ):
            dt -= 1

        return dt

class ObjIdConstraint:

    def __init__( self, op, value ):

        from sqlalchemy import and_

        if( op == '=' ):
            self.__constraint = (model.Object.object_id == int( value ))
        elif( op == '!=' ):
            self.__constraint = (model.Object.object_id != int( value ))
        elif( op == '>' ):
            self.__constraint = (model.Object.object_id > int( value ))
        elif( op == '>=' ):
            self.__constraint = (model.Object.object_id >= int( value ))
        elif( op == '<' ):
            self.__constraint = (model.Object.object_id < int( value ))
        elif( op == '<=' ):
            self.__constraint = (model.Object.object_id <= int( value ))
        elif( op == '~' ):
            if( '-' in value ):
                lower, upper = map( int, value.split( '-' ) )
            elif( '|' in value ):
                value, vrange = map( int, value.split( '|' ) )
                lower = value - vrange
                upper = value + vrange
            else:
                lower = int( value )
                upper = lower
        
            if( lower != upper ):
                self.__constraint = and_( model.Object.object_id >= lower,
                                          model.Object.object_id <= upper )
            else:
                self.__constraint = (model.Object.object_id == lower)
        else:
            assert False

    def get_preferred_order( self ):

        return ( 'add', False, )

    def to_db_constraint( self, db ):

        return db.session.query( model.Object.object_id ) \
                         .filter( self.__constraint )

class ParameterConstraint:

    def __init__( self, key, op, value ):

        from sqlalchemy import and_

        self.__key = key

        if( op == '=' or op == '!=' ):

            if( value is None ):
                self.__constraint = (model.ObjectMetadata.value == None)
            else:
                value = str( value )
                if( '*' in value ):
                    sql_s = value.replace( '%', '[%]' ) \
                                 .replace( '*', '%' )
                    self.__constraint = (model.ObjectMetadata.value.like( sql_s ))
                else:
                    self.__constraint = (model.ObjectMetadata.value == value)

            if( op == '!=' ):
                self.__constraint = ~self.__constraint

        elif( op == '>' ):
            self.__constraint = (model.ObjectMetadata.numeric > QueryInt( value ))
        elif( op == '>=' ):
            self.__constraint = (model.ObjectMetadata.numeric >= QueryInt( value ))
        elif( op == '<' ):
            self.__constraint = (model.ObjectMetadata.numeric < QueryInt( value ))
        elif( op == '<=' ):
            self.__constraint = (model.ObjectMetadata.numeric <= QueryInt( value ))
        elif( op == '~' ):
            if( '-' in value ):
                lower, upper = map( QueryInt, value.split( '-' ) )
            elif( '|' in value ):
                value, vrange = value.split( '|' )
                lower = QueryInt( value, False ) - int( vrange )
                upper = QueryInt( value, True ) + int( vrange )
            else:
                lower = QueryInt( value, False )
                upper = QueryInt( value, True )
        
            if( lower != upper ):
                self.__constraint = and_( model.ObjectMetadata.numeric >= lower,
                                          model.ObjectMetadata.numeric <= upper )
            else:
                self.__constraint = (model.ObjectMetadata.numeric == lower)
        else:
            assert False

    def get_preferred_order( self ):

        return None

    def to_db_constraint( self, db ):

        from sqlalchemy import and_

        return db.session.query( model.ObjectMetadata.object_id ) \
                         .filter( and_( model.ObjectMetadata.key == self.__key, \
                                        self.__constraint ) )

class Query:

    def __init__( self ):

        self.__obj_type = None
        self.__order_by = None
        self.__expand = False
        self.__nochild = False

        self.__req_constraints = []
        self.__or_constraints = []
        self.__not_constraints = []

    def __create_constraint( self, s ):

        if( s.startswith( '@' ) ):
            return NameConstraint( '=', '*' + s[1:] + '*' )
        elif( s.startswith( '#' ) ):
            return TagConstraint( s[1:], fuzzy = True )
        elif( s.startswith( '&' ) ):
            if( s[1:].startswith( '!' ) ):
                if( s[1:].startswith( '!!' ) ):
                    not_null = True
                    key = s[3:]
                else:
                    not_null = False
                    key = s[2:]

                if( key in [ 'id', 'tagc' ] ):
                    raise ValueError, 'Bad Parameter Constraint'
                elif( key == 'name' ):
                    return NameConstraint( '!=' if( not_null ) else '=', None )
                else:
                    return ParameterConstraint( key, '!=' if( not_null ) else '=', None )
            else:
                ops = [ '>=', '<=', '>', '<', '!=', '=', '~' ]
                s = s[1:]

                for i in ops:
                    try:
                        idx = s.index( i[0] )
                        key = s[0:idx]
                        op = i
                        value = s[idx+len(i[0]):]

                        if( key == 'id' ):
                            return ObjIdConstraint( op, value )
                        elif( key == 'tagc' ):
                            return TagCountConstraint( op, value )
                        elif( key == 'name' ):
                            return NameConstraint( op, value )
                        else:
                            return ParameterConstraint( key, op, value )
                    except ValueError:
                        pass
                else:
                    raise ValueError, 'Bad Parameter Constraint'
        else:
            return UnboundConstraint( s )

    def __process_command( self, cmd ):

        cmd = cmd.split( ':' )

        if( cmd[0] == 'sort' ):
            if( len( cmd ) < 2 ):
                raise ValueError, 'Sort command needs an argument'

            desc = False

            if( len( cmd ) > 2 and cmd[2] == 'desc' ):
                desc = True

            self.set_order( cmd[1], desc )

        elif( cmd[0] == 'type' ):
            if( len( cmd ) < 2 ):
                raise ValueError, 'Type command needs an argument'

            if( cmd[1] == 'file' ):
                self.set_type( hdbfs.TYPE_FILE );
            elif( cmd[1] == 'album' ):
                self.set_type( hdbfs.TYPE_ALBUM );
            else:
                raise ValueError, 'Bad type'

        elif( cmd[0] == 'expand' ):
            self.set_expand()

        elif( cmd[0] == 'untagged' ):
            self.set_untagged()

        else:
            raise ValueError, 'Bad Command'

    def from_string( self, s ):

        clauses = s.split( ' ' )
        clauses = [i for i in clauses if( len( i ) > 0 )]

        commands = [i[1:] for i in clauses if( i[0] == '$' )]
        add = [i[1:] for i in clauses if( i[0] == '?' )]
        sub = [i[1:] for i in clauses if( i[0] == '!' )]
        req = [i for i in clauses if( i[0] != '$' and i[0] != '?' and i[0] != '!' )]

        map( self.__process_command, commands )

        self.__req_constraints.extend( map( self.__create_constraint, req ) )
        self.__or_constraints.extend( map( self.__create_constraint, add ) )
        self.__not_constraints.extend( map( self.__create_constraint, sub ) )

        return self

    def set_expand( self, expand = True ):

        self.__expand = expand
        return self

    def set_untagged( self ):

        self.__nochild = True
        self.__req_constraints = [ TagCountConstraint( '=', 0 ) ]
        self.__add_constraints = []
        self.__not_constratins = []

        return self

    def set_type( self, obj_type ):

        self.__obj_type = obj_type
        return self

    def set_order( self, prop, desc = False ):

        self.__order_by = ( prop, desc )
        return self

    def add_require_constraint( self, constraint ):

        self.__req_constraints.append( constraint )
        return self

    def add_or_constraint( self, constraint ):

        self.__or_constraints.append( constraint )
        return self

    def add_not_constraint( self, constraint ):

        self.__not_constraints.append( constraint )
        return self

    def set_constraints( self, req_c = [], or_c = [], not_c = [] ):

        self.__req_constraints = list( req_c )
        self.__or_constraints = list( or_c )
        self.__not_constraints = list( not_c )
        return self

    def execute( self, db ):

        from sqlalchemy.sql.expression import func

        to_db_c = lambda c: c.to_db_constraint( db )
        q_order = None

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

        if( len( self.__req_constraints ) == 1 and len( self.__or_constraints ) == 0 ):
            q_order = self.__req_constraints[0].get_preferred_order()

        if( self.__order_by is not None ):
            q_order = self.__order_by

        if( q_order is None ):
            q_order = ( 'rand', False, )

        query = db.session.query( model.Object.object_id )

        if( req_q is not None ):
            q = req_q

            if( add_q is not None ):
                q = q.union( add_q )

            query = query.filter( model.Object.object_id.in_( q ) )
        elif( add_q is not None ):
            query = query.filter( model.Object.object_id.in_( add_q ) )

        if( sub_q is not None ):
            query = query.filter( ~model.Object.object_id.in_( sub_q ) )

        if( self.__obj_type is not None ):
            query = query.filter( model.Object.object_type == self.__obj_type )
        else:
            query = query.filter( model.Object.object_type.in_(
                        hdbfs.FILE_TYPES + hdbfs.ALBUM_TYPES ) )

        if( self.__nochild
         or (self.__obj_type is None and req_q is None and add_q is None) ):

            # Extra filter applied in this case if there are otherwise no
            # other filters. We don't want to show files which will already
            # be presented in an album
            all_r = db.session.query( model.Object.object_id ) \
                      .filter( model.Object.object_type.in_(
                                    hdbfs.FILE_TYPES + hdbfs.ALBUM_TYPES ) )
            children = db.session.query( model.Relation.child_id ) \
                    .filter( model.Relation.parent_id.in_( all_r ) )

            query = query.filter( ~model.Object.object_id.in_( children ) )

        if( self.__expand ):
            from sqlalchemy import or_

            query = db.session.query( model.Object ) \
                    .join( model.Relation, model.Relation.child_id == model.Object.object_id ) \
                    .filter( model.Object.object_type.in_( hdbfs.FILE_TYPES ) ) \
                    .filter( or_( model.Object.object_id.in_( query ),
                                  model.Relation.parent_id.in_( query ) ) )
        else:
            query = db.session.query( model.Object ) \
                    .filter( model.Object.object_id.in_( query ) )

        if( q_order[0] == 'rand' ):
            query = query.order_by( func.random() )
        elif( q_order[0] == 'add' ):
            if( not q_order[1] ):
                query = query.order_by( model.Object.object_id )
            else:
                query = query.order_by( model.Object.object_id.desc() )
        elif( q_order[0] == 'name' ):
            if( not q_order[1] ):
                query = query.order_by( model.Object.name,
                                        model.Object.object_id )
            else:
                query = query.order_by( model.Object.name.desc(),
                                        model.Object.object_id.desc() )
        elif( q_order[0] == 'origin' ):
            query = query.join( model.ObjectMetadata )\
                         .filter( model.ObjectMetadata.key == 'origin_time' )
            if( not q_order[1] ):
                query = query.order_by( model.ObjectMetadata.numeric,
                                        model.Object.object_id )
            else:
                query = query.order_by( model.ObjectMetadata.numeric.desc(),
                                        model.Object.object_id.desc() )

        return hdbfs.ModelObjToHiguObjIterator( db, query ) 

