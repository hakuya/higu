""" Query interface for searching and filtering database objects.

This module provides a flexible query system for finding files, albums, tags,
and other objects in the database. Queries can be built incrementally by adding
constraints for tags, names, types, dates, and other properties.

The Query class uses a constraint-based approach where each constraint narrows
down the result set. Constraints can be combined with AND, OR, and NOT logic.

Key classes:
    Query: Main query builder interface
    TagConstraint: Filter by tag assignment
    TagCountConstraint: Filter by number of tags
    NameConstraint: Filter by object name
    TypeConstraint: Filter by object type
    AddedConstraint: Filter by creation date
    AlbumConstraint: Filter by album membership
    ImportConstraint: Filter by import session

Functions:
    QueryInt: Parse integer values with special handling for month names
"""

import calendar
import datetime

import hdbfs

import hdbfs.model as model

from hdbfs.session import SessionObjectFactoryIterator

from typing import Union, Optional, List, Any, Tuple, Protocol

class Constraint( Protocol ):
    """ Protocol for query constraint objects.

    All constraint classes must implement these methods to be usable
    in Query objects.
    """

    def get_preferred_order( self ) -> Optional[Union[str, Tuple[str, bool]]]:
        """ Get the preferred sort order for this constraint.

        Returns:
            None, a sort field string, or a (field, descending) tuple
        """
        ...

    def to_db_constraint( self, db: 'hdbfs.Database' ) -> 'sqlalchemy.orm.Query':
        """ Convert this constraint to a database query.

        Args:
            db: Database session to use for query building

        Returns:
            SQLAlchemy query selecting object IDs that match the constraint
        """
        ...

class TagConstraint:
    """ Constraint that matches objects tagged with a specific tag.

    Filters objects by tag assignment. Supports exact tag matching or fuzzy
    matching with wildcards. Can match by tag object, tag name, or tag ID.

    Attributes:
        __tag: Tag to match (can be Obj, int ID, or string name)
        __fuzzy: Whether to enable fuzzy/wildcard matching
    """

    def __init__( self, tag: Union['hdbfs.Obj', int, str], fuzzy: bool = False ):
        """ Initialize a tag constraint.

        Args:
            tag: Tag to filter by (Obj, object ID, or tag name string)
            fuzzy: If True, enables wildcard matching with * in tag names
        """

        self.__tag = tag
        self.__fuzzy = fuzzy

    def get_preferred_order( self ) -> Optional[Tuple[str, bool]]:
        """ Get the preferred sort order for this constraint.

        Returns:
            None (no preferred order for tag constraints)
        """

        return None

    def to_db_constraint( self, db: 'hdbfs.Database' ) -> 'sqlalchemy.orm.Query':
        """ Convert this constraint to a database query.

        Args:
            db: Database session to use for query building

        Returns:
            SQLAlchemy query selecting object IDs that match the constraint
        """

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
                tag = db.model.query( model.Object.object_id ) \
                        .filter( model.Object.object_type.in_( hdbfs.ObjectClass.CLASSIFIER.all_type_values() ) ) \
                        .filter( model.Object.name.like( sql_s ) )
            else:
                tag = db.get_tag( self.__tag )

        if( isinstance( tag, hdbfs.Obj ) ):
            return db.model.query( model.Relation.child_id ) \
                     .filter( model.Relation.parent_id == tag.obj.object_id )
        else:
            return db.model.query( model.Relation.child_id ) \
                     .filter( model.Relation.parent_id.in_( tag ) )

class TagCountConstraint:
    """ Constraint that matches objects by their tag count.

    Filters objects based on how many tags they have assigned. Supports
    various comparison operators (=, !=, <, <=, >, >=).

    Attributes:
        __op: Comparison operator string
        __c: Count value to compare against
    """

    def __init__( self, op: str, c: Union[int, str] ):
        """ Initialize a tag count constraint.

        Args:
            op: Comparison operator ('=', '!=', '<', '<=', '>', '>=')
            c: Tag count to compare against (int or string that converts to int)
        """

        self.__op = op
        self.__c = int( c )

    def get_preferred_order( self ) -> Optional[Tuple[str, bool]]:
        """ Get the preferred sort order for this constraint.

        Returns:
            None (no preferred order for tag count constraints)
        """

        return None

    def to_db_constraint( self, db: 'hdbfs.Database' ) -> 'sqlalchemy.orm.Query':
        """ Convert this constraint to a database query.

        Builds a query that counts tags per object and filters by the count.

        Args:
            db: Database session to use for query building

        Returns:
            SQLAlchemy query selecting object IDs that match the constraint
        """

        from sqlalchemy import func, literal_column

        tagged = db.model.query( model.Relation.child_id.label( 'id' ),
                                   func.count( model.Relation.child_id ).label( 'tagc' ) ) \
                   .join( model.Object, model.Object.object_id == model.Relation.parent_id ) \
                   .filter( model.Object.object_type.in_( model.ObjectClass.CLASSIFIER.all_type_values() ) ) \
                   .group_by( model.Relation.child_id.label( 'id' ) )
        notags = db.model.query( model.Object.object_id, literal_column( '0' ).label( 'tagc' ) ) \
                   .filter( ~model.Object.object_id.in_(
                                db.model.query( model.Relation.child_id ) \
                                  .join( model.Object, model.Object.object_id
                                                    == model.Relation.parent_id ) \
                                  .filter( model.Object.object_type.in_( model.ObjectClass.CLASSIFIER.all_type_values() ) ) ) )
        tagq = tagged.union( notags ).subquery()

        q = db.model.query( tagq.c.id )

        return {
            '='  : lambda q: q.filter( tagq.c.tagc == self.__c ),
            '!=' : lambda q: q.filter( tagq.c.tagc != self.__c ),
            '>'  : lambda q: q.filter( tagq.c.tagc > self.__c ),
            '>=' : lambda q: q.filter( tagq.c.tagc >= self.__c ),
            '<'  : lambda q: q.filter( tagq.c.tagc < self.__c ),
            '<=' : lambda q: q.filter( tagq.c.tagc <= self.__c ),
        }[self.__op]( q )

class NameConstraint:
    """ Constraint that matches objects by name.

    Filters objects based on their name field. Supports exact matching,
    wildcard matching with *, and null checking.

    Attributes:
        __constraint: SQLAlchemy constraint expression
    """

    def __init__( self, op: str, s: Optional[str] ):
        """ Initialize a name constraint.

        Args:
            op: Comparison operator ('=' or '!=')
            s: Name to match (supports * wildcards), or None to check for null
        """

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

    def get_preferred_order( self ) -> str:
        """ Get the preferred sort order for this constraint.

        Returns:
            'name' (results should be sorted by name)
        """

        return 'name'

    def to_db_constraint( self, db: 'hdbfs.Database' ) -> 'sqlalchemy.orm.Query':
        """ Convert this constraint to a database query.

        Args:
            db: Database session to use for query building

        Returns:
            SQLAlchemy query selecting object IDs that match the constraint
        """

        return db.model.query( model.Object.object_id ) \
                       .filter( self.__constraint )

class UnboundConstraint:
    """ Constraint that performs a broad search across names and tags.

    A fallback constraint that searches for the given string in object names
    and tag names. First tries to match as a tag name, then falls back to
    substring search in names and tag assignments.

    Attributes:
        __s: Search string
    """

    def __init__( self, s: str ):
        """ Initialize an unbound constraint.

        Args:
            s: String to search for in names and tags
        """

        self.__s = s

    def get_preferred_order( self ) -> Optional[Tuple[str, bool]]:
        """ Get the preferred sort order for this constraint.

        Returns:
            None (no preferred order for unbound constraints)
        """

        return None

    def to_db_constraint( self, db: 'hdbfs.Database' ) -> 'sqlalchemy.orm.Query':
        """ Convert this constraint to a database query.

        Tries tag matching first, then falls back to substring search in
        object names and objects tagged with matching tags.

        Args:
            db: Database session to use for query building

        Returns:
            SQLAlchemy query selecting object IDs that match the constraint
        """

        from sqlalchemy import or_

        try:
            c = TagConstraint( self.__s )
            db_c = c.to_db_constraint( db )
            if( db_c is not None ):
                return db_c
        except:
            pass

        sql_s = self.__s.replace( '%', '[%]' ) \
                    .replace( '*', '%' )

        tag_q = db.model.query( model.Object.object_id ) \
                  .filter( model.Object.object_type.in_( hdbfs.ObjectClass.CLASSIFIER.all_type_values() ) ) \
                  .filter( model.Object.name.like( '%' + sql_s + '%' ) )

        child_q = db.model.query( model.Relation.child_id ) \
                    .filter( model.Relation.parent_id.in_( tag_q ) )

        return db.model.query( model.Object.object_id ) \
                 .filter(
                        or_(
                            model.Object.name.like( '%' + sql_s + '%' ),
                            model.Object.object_id.in_( child_q )
                        )
                    )

def QueryInt( v: Union[int, str], ceil: bool = False ) -> int:
    """ Parse an integer or date string to Unix timestamp.

    Converts various input formats to integers. Handles plain integers,
    date strings (YYYY/MM/DD), and date-time strings (YYYY/MM/DD_HH:MM:SS).
    Month names in date strings are not yet supported.

    Args:
        v: Value to parse (int or date string)
        ceil: If True, rounds partial dates to end of period (e.g., '2024'
            becomes end of 2024). If False, uses start of period.

    Returns:
        Integer value or Unix timestamp

    Raises:
        ValueError: If string cannot be parsed as int or date

    Example:
        >>> QueryInt('2024/06/15')  # June 15, 2024 at 00:00:00
        >>> QueryInt('2024', ceil=True)  # End of 2024
        >>> QueryInt('2024/06/15_14:30:00')  # Specific date and time
    """

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
            raise ValueError()

        if( time_str is not None and len( date_str ) >= 3 ):
            time_str = time_str.split( ':' )
            hour = int( time_str[0] ) if( len( time_str ) >= 1 ) else 0
            tmin = int( time_str[1] ) if( len( time_str ) >= 2 ) else 0
            tsec = int( time_str[2] ) if( len( time_str ) >= 3 ) else 0

            if( len( time_str ) >= 4 ):
                raise ValueError()
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
    """ Constraint that matches objects by their object ID.

    Filters objects by their unique object_id. Supports various comparison
    operators and range syntax.

    Attributes:
        __constraint: SQLAlchemy constraint expression
    """

    def __init__( self, op: str, value: Union[int, str] ):
        """ Initialize an object ID constraint.

        Args:
            op: Comparison operator:
                - '=', '!=', '<', '<=', '>', '>=': Standard comparisons
                - '~': Range syntax (see below)
            value: Object ID or range specification:
                - Integer: single ID
                - 'N-M': range from N to M inclusive
                - 'N|R': range N±R (N-R to N+R inclusive)
        """

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

    def get_preferred_order( self ) -> Tuple[str, bool]:
        """ Get the preferred sort order for this constraint.

        Returns:
            ('add', False) - sort by creation order (object ID), ascending
        """

        return ( 'add', False, )

    def to_db_constraint( self, db: 'hdbfs.Database' ) -> 'sqlalchemy.orm.Query':
        """ Convert this constraint to a database query.

        Args:
            db: Database session to use for query building

        Returns:
            SQLAlchemy query selecting object IDs that match the constraint
        """

        return db.model.query( model.Object.object_id ) \
                       .filter( self.__constraint )

class ParameterConstraint:
    """ Constraint that matches objects by metadata/parameter values.

    Filters objects based on their metadata key-value pairs. Supports string
    matching (with wildcards), numeric comparisons, and null checks.

    Attributes:
        __key: Metadata key to filter on
        __constraint: SQLAlchemy constraint expression
    """

    def __init__( self, key: str, op: str, value: Optional[Union[int, str]] ):
        """ Initialize a parameter constraint.

        Args:
            key: Metadata key name to filter on
            op: Comparison operator:
                - '=' or '!=': equality/inequality (supports wildcards)
                - '<', '<=', '>', '>=': numeric comparison (uses QueryInt)
                - '~': range syntax (see value description)
            value: Value to compare against:
                - None: null check
                - String with *: wildcard match
                - Integer or date string: numeric comparison
                - 'N-M': range from N to M inclusive
                - 'N|R': range N±R (N-R to N+R inclusive)
        """

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

    def get_preferred_order( self ) -> Optional[Tuple[str, bool]]:
        """ Get the preferred sort order for this constraint.

        Returns:
            None (no preferred order for parameter constraints)
        """

        return None

    def to_db_constraint( self, db: 'hdbfs.Database' ) -> 'sqlalchemy.orm.Query':
        """ Convert this constraint to a database query.

        Args:
            db: Database session to use for query building

        Returns:
            SQLAlchemy query selecting object IDs that match the constraint
        """

        from sqlalchemy import and_

        return db.model.query( model.ObjectMetadata.object_id ) \
                       .filter( and_( model.ObjectMetadata.key == self.__key, \
                                        self.__constraint ) )

class Query:
    """ Flexible query builder for searching database objects.

    Builds queries incrementally by adding constraints that filter objects by
    tags, names, types, dates, and other properties. Constraints can be
    combined with AND (required), OR (any), and NOT (exclude) logic.

    The Query class supports:
    - Tag-based filtering (with fuzzy matching)
    - Text search in names and metadata
    - Type filtering (files, albums, imports)
    - Date range filtering
    - Sorting and pagination
    - Album expansion (include all files from matching albums)

    Query strings can be parsed from a compact syntax:
        - Plain text: required constraint (AND)
        - `?term`: optional constraint (OR)
        - `!term`: exclusion constraint (NOT)
        - `#tag`: tag search with fuzzy matching
        - `@text`: name substring search
        - `&key=value`: parameter/metadata constraint
        - `$command`: special commands (sort, type, expand, etc.)
        - `^field`: sort by field (prefix ! for descending)

    Example:
        >>> q = Query()
        >>> q.set_type(hdbfs.ObjectClass.FILE)
        >>> q.add_require_constraint(TagConstraint('vacation'))
        >>> results = q.execute(db)

        >>> # Or using string syntax:
        >>> q = Query().from_string('#vacation #beach $sort:add')
        >>> results = q.execute(db)
    """

    def __init__( self ):
        """ Initialize an empty query.

        Sets up default search types (files and albums) and empty constraint
        lists. Use set_* and add_* methods to build the query.
        """

        self.__search_types = [
            hdbfs.ObjectType.FILE.value,
            hdbfs.ObjectType.DUPLICATE.value,
            hdbfs.ObjectType.ALBUM_FREE.value,
            hdbfs.ObjectType.ALBUM_FORMAL.value,
            hdbfs.ObjectType.ALBUM_CLOSED.value
        ]

        self.__order_by = None
        self.__range = None
        self.__expand = False
        self.__nochild = False

        self.__req_constraints = []
        self.__or_constraints = []
        self.__not_constraints = []

    def __create_constraint( self, s ):

        if( s.isdigit() ):
            return ObjIdConstraint( '=', s )
        elif( s.startswith( '@' ) ):
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
                    raise ValueError( 'Bad Parameter Constraint' )
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
                    raise ValueError( 'Bad Parameter Constraint' )
        else:
            return UnboundConstraint( s )

    def __process_command_sort( self, *args ):

        if( len( args ) < 1 ):
            raise ValueError( 'Sort command needs an argument' )

        desc = False

        if( len( args ) > 1 and args[1] == 'desc' ):
            desc = True

        self.set_order( args[0], desc )

    def __process_command_type( self, *args ):

        TYPE_MAP = {
            'file'          : hdbfs.ObjectClass.FILE,
            'file:nodup'    : hdbfs.ObjectType.FILE,
            'file:dup'      : hdbfs.ObjectType.DUPLICATE,
            'album'         : hdbfs.ObjectClass.ALBUM,
            'album:free'    : hdbfs.ObjectType.ALBUM_FREE,
            'album:formal'  : hdbfs.ObjectType.ALBUM_FREE,
            'album:closed'  : hdbfs.ObjectType.ALBUM_CLOSED,
            'import'        : hdbfs.ObjectClass.IMPORT,
            'import:open'   : hdbfs.ObjectType.IMPORT_OPEN,
            'import:closed' : hdbfs.ObjectType.IMPORT_CLOSED,
        }

        if( len( args ) < 1 ):
            raise ValueError( 'Type command needs an argument' )

        ty = TYPE_MAP.get( ':'.join( args ), None )
        if( ty is not None ):
            self.set_type( ty )
        else:
            raise ValueError( 'Bad type' )

    def __process_command_expand( self, *args ):

        self.set_expand()

    def __process_command_untagged( self, *args ):

        self.set_untagged()

    def __process_command_limit( self, *args ):

        self.set_limit( int( args[0] ) )

    def __process_command_range( self, *args ):

        self.set_range( int( args[0] ), int( args[1] ) )

    def __process_command( self, cmd ):

        COMMANDS = {
            'sort' : self.__process_command_sort,
            'type' : self.__process_command_type,
            'expand' : self.__process_command_expand,
            'untagged' : self.__process_command_untagged,
            'limit' : self.__process_command_limit,
            'range' : self.__process_command_range,
        }

        cmd = cmd.split( ':' )

        if( cmd[0] not in COMMANDS ):
            raise ValueError( 'Bad Command' )

        COMMANDS[ cmd[0] ]( *cmd[1:] )

    def __process_sorts( self, sorts ):

        if( len( sorts ) == 0 ):
            return

        if( sorts[0][0] == '!' ):
            self.set_order( sorts[0][1:], True )
        else:
            self.set_order( sorts[0], False )

    def from_string( self, s: str ) -> 'Query':
        """ Parse and apply a query string.

        Parses a compact query syntax and builds the corresponding constraints.
        Special handling: if the entire string is a number, searches all object
        types by ID.

        Syntax:
            - term: required (AND logic)
            - ?term: optional (OR logic)
            - !term: excluded (NOT logic)
            - #tag: tag with fuzzy matching
            - @text: name substring search
            - 123: object ID search
            - &key=val: parameter equals value
            - &key>val, &key<val, etc.: parameter comparison
            - &!key: parameter is null
            - &!!key: parameter is not null
            - $sort:field or $sort:field:desc: set sort order
            - $type:file, $type:album, etc.: set object type filter
            - $expand: expand albums to include their files
            - $untagged: show only untagged items
            - $limit:N: limit to N results
            - $range:offset:limit: pagination
            - ^field or ^!field: sort by field (! = descending)

        Args:
            s: Query string to parse

        Returns:
            Self for method chaining

        Raises:
            ValueError: If syntax is invalid

        Example:
            >>> q = Query().from_string('#vacation ?#beach !#work $sort:add')
            >>> q = Query().from_string('@sunset $type:file ^name')
        """

        try:
            # If the query is an ID, we search all types
            int( s )
            self.__req_constraints = [ self.__create_constraint( s ) ]
            self.__search_types = [
                hdbfs.ObjectType.FILE.value,
                hdbfs.ObjectType.DUPLICATE.value,
                hdbfs.ObjectType.ALBUM_FREE.value,
                hdbfs.ObjectType.ALBUM_FORMAL.value,
                hdbfs.ObjectType.ALBUM_CLOSED.value,
                hdbfs.ObjectType.IMPORT_OPEN.value,
                hdbfs.ObjectType.IMPORT_CLOSED.value
            ]

            return self
        except:
            pass

        clauses = s.split( ' ' )
        clauses = [i for i in clauses if( len( i ) > 0 )]

        commands = [i[1:] for i in clauses if( i[0] == '$' )]
        sorts = [i[1:] for i in clauses if( i[0] == '^' )]
        add = [i[1:] for i in clauses if( i[0] == '?' )]
        sub = [i[1:] for i in clauses if( i[0] == '!' )]
        req = [i for i in clauses if( i[0] not in [ '$', '?', '!', '^' ] )]

        self.__process_sorts( sorts )

        for c in commands:
            self.__process_command( c )

        self.__req_constraints.extend( map( self.__create_constraint, req ) )
        self.__or_constraints.extend( map( self.__create_constraint, add ) )
        self.__not_constraints.extend( map( self.__create_constraint, sub ) )

        return self

    def set_expand( self, expand: bool = True ) -> 'Query':
        """ Enable or disable album expansion.

        When enabled, matching albums will be expanded to include all their
        contained files in the results. This is useful for getting all files
        from albums that match certain criteria.

        Args:
            expand: True to enable expansion, False to disable

        Returns:
            Self for method chaining

        Example:
            >>> q = Query().add_require_constraint(TagConstraint('vacation'))
            >>> q.set_expand()  # Include all files from vacation albums
        """

        self.__expand = expand
        return self

    def set_untagged( self ) -> 'Query':
        """ Configure query to find only untagged objects.

        Replaces all constraints with a single constraint that matches only
        objects with zero tags. This is useful for finding newly imported
        files that haven't been organized yet.

        Returns:
            Self for method chaining

        Example:
            >>> q = Query().set_untagged()
            >>> untagged_files = list(q.execute(db))
        """

        self.__nochild = True
        self.__req_constraints = [ TagCountConstraint( '=', 0 ) ]
        self.__or_constraints = []
        self.__not_constraints = []

        return self

    def set_type( self, obj_type: Union['hdbfs.ObjectClass','hdbfs.ObjectType'] ) -> 'Query':
        """ Set the object type filter.

        Restricts results to specific object types. Can filter by class
        (e.g., all files, all albums) or by specific type (e.g., only
        closed albums, only duplicate files).

        Args:
            obj_type: ObjectClass for all types in that class, or
                ObjectType for a specific type

        Returns:
            Self for method chaining

        Example:
            >>> q = Query().set_type(hdbfs.ObjectClass.FILE)  # All files
            >>> q = Query().set_type(hdbfs.ObjectType.ALBUM_CLOSED)  # Only closed albums
        """

        if( isinstance( obj_type, hdbfs.ObjectClass ) ):
            self.__search_types = obj_type.all_type_values()
        else:
            self.__search_types = [ obj_type.value ]

        return self

    def set_order( self, prop: str, desc: bool = False ) -> 'Query':
        """ Set the result sort order.

        Args:
            prop: Property to sort by:
                - 'rand': random order
                - 'add': creation order (object ID)
                - 'name': alphabetical by name
                - 'origin': by origin_time metadata
            desc: True for descending order, False for ascending

        Returns:
            Self for method chaining

        Example:
            >>> q = Query().set_order('name')  # A-Z
            >>> q = Query().set_order('add', desc=True)  # Newest first
        """

        self.__order_by = ( prop, desc )
        return self

    def set_limit( self, limit: int ) -> 'Query':
        """ Limit the number of results.

        Args:
            limit: Maximum number of results to return

        Returns:
            Self for method chaining

        Example:
            >>> q = Query().set_limit(10)  # First 10 results
        """

        self.__range = ( 0, limit, )
        return self

    def set_range( self, offset: int, limit: int ) -> 'Query':
        """ Set pagination range for results.

        Args:
            offset: Number of results to skip
            limit: Maximum number of results to return after offset

        Returns:
            Self for method chaining

        Example:
            >>> q = Query().set_range(20, 10)  # Results 20-29 (page 3)
        """

        self.__range = ( offset, limit, )
        return self

    def add_require_constraint( self, constraint: Constraint ) -> 'Query':
        """ Add a required constraint (AND logic).

        All required constraints must match for an object to be included
        in results. This narrows down the result set.

        Args:
            constraint: Constraint object (TagConstraint, NameConstraint, etc.)

        Returns:
            Self for method chaining

        Example:
            >>> q = Query()
            >>> q.add_require_constraint(TagConstraint('vacation'))
            >>> q.add_require_constraint(NameConstraint('=', '*beach*'))
        """

        self.__req_constraints.append( constraint )
        return self

    def add_or_constraint( self, constraint: Constraint ) -> 'Query':
        """ Add an optional constraint (OR logic).

        At least one OR constraint must match (if any are specified) for
        an object to be included. This expands the result set.

        Args:
            constraint: Constraint object (TagConstraint, NameConstraint, etc.)

        Returns:
            Self for method chaining

        Example:
            >>> q = Query()
            >>> q.add_or_constraint(TagConstraint('beach'))
            >>> q.add_or_constraint(TagConstraint('ocean'))
            # Matches items tagged with beach OR ocean
        """

        self.__or_constraints.append( constraint )
        return self

    def add_not_constraint( self, constraint: Constraint ) -> 'Query':
        """ Add an exclusion constraint (NOT logic).

        Objects matching any NOT constraint will be excluded from results.
        This filters out unwanted items.

        Args:
            constraint: Constraint object (TagConstraint, NameConstraint, etc.)

        Returns:
            Self for method chaining

        Example:
            >>> q = Query()
            >>> q.add_require_constraint(TagConstraint('vacation'))
            >>> q.add_not_constraint(TagConstraint('private'))
            # Vacation photos except private ones
        """

        self.__not_constraints.append( constraint )
        return self

    def set_constraints( self,
                req_c: List[Constraint] = [],
                or_c: List[Constraint] = [],
                not_c: List[Constraint] = []
            ) -> 'Query':
        """ Replace all constraints at once.

        Replaces the current constraint lists with new ones. Useful for
        building queries programmatically or resetting constraints.

        Args:
            req_c: List of required constraints (AND logic)
            or_c: List of optional constraints (OR logic)
            not_c: List of exclusion constraints (NOT logic)

        Returns:
            Self for method chaining

        Example:
            >>> q = Query()
            >>> q.set_constraints(
            ...     req_c=[TagConstraint('vacation')],
            ...     not_c=[TagConstraint('private')]
            ... )
        """

        self.__req_constraints = list( req_c )
        self.__or_constraints = list( or_c )
        self.__not_constraints = list( not_c )
        return self

    def execute( self, db: 'hdbfs.Database' ) -> SessionObjectFactoryIterator:
        """ Execute the query and return an iterator of matching objects.

        Builds and runs the database query based on all configured constraints,
        filters, and sort order. Returns an iterator that lazily loads objects
        as they're accessed.

        Query logic:
        1. Required constraints are combined with AND (intersection)
        2. Optional constraints are combined with OR (union)
        3. Required and optional are combined (required AND (opt1 OR opt2...))
        4. Exclusion constraints filter out matches (NOT)
        5. Type filter is applied
        6. If no specific constraints, filters out child objects (files already
           in albums) to avoid duplication
        7. If expand=True, albums are expanded to their contained files
        8. Results are sorted and paginated

        Args:
            db: Database session to execute query against

        Returns:
            Iterator of matching objects (File, Album, Tag, Import, etc.)

        Example:
            >>> q = Query().from_string('#vacation $sort:name')
            >>> for obj in q.execute(db):
            ...     print(obj.get_name())
        """

        from sqlalchemy.sql.expression import func

        FILE_TYPES = [
            hdbfs.ObjectType.FILE.value,
            hdbfs.ObjectType.DUPLICATE.value,
        ]

        to_db_c = lambda c: c.to_db_constraint( db )
        q_order = None

        if( len( self.__or_constraints ) > 0 ):
            add_q = list( map( to_db_c, self.__or_constraints ) )
            add_q = add_q[0].union( *add_q[1:] )
        else:
            add_q = None

        if( len( self.__not_constraints ) > 0 ):
            sub_q = list( map( to_db_c, self.__not_constraints ) )
            sub_q = sub_q[0].union( *sub_q[1:] )
        else:
            sub_q = None

        if( len( self.__req_constraints ) > 0 ):
            req_q = list( map( to_db_c, self.__req_constraints ) )
            req_q = req_q[0].intersect( *req_q[1:] )
        else:
            req_q = None

        if( len( self.__req_constraints ) == 1 and len( self.__or_constraints ) == 0 ):
            q_order = self.__req_constraints[0].get_preferred_order()

        if( self.__order_by is not None ):
            q_order = self.__order_by

        if( q_order is None ):
            q_order = ( 'rand', False, )

        query = db.model.query( model.Object.object_id )

        if( req_q is not None ):
            q = req_q

            if( add_q is not None ):
                q = q.union( add_q )

            query = query.filter( model.Object.object_id.in_( q ) )
        elif( add_q is not None ):
            query = query.filter( model.Object.object_id.in_( add_q ) )

        if( sub_q is not None ):
            query = query.filter( ~model.Object.object_id.in_( sub_q ) )

        query = query.filter( model.Object.object_type.in_( self.__search_types ) )

        if( self.__nochild
         or (len( self.__search_types ) > 1 and req_q is None and add_q is None) ):

            # Extra filter applied in this case if there are otherwise no
            # other filters. We don't want to show files which will already
            # be presented in an album
            all_r = db.model.query( model.Object.object_id ) \
                      .filter( model.Object.object_type.in_( self.__search_types ) )
            children = db.model.query( model.Relation.child_id ) \
                    .filter( model.Relation.parent_id.in_( all_r ) )

            query = query.filter( ~model.Object.object_id.in_( children ) )

        if( self.__expand ):
            from sqlalchemy import or_

            query = db.model.query( model.Object ) \
                    .join( model.Relation, model.Relation.child_id == model.Object.object_id ) \
                    .filter( model.Object.object_type.in_( FILE_TYPES ) ) \
                    .filter( or_( model.Object.object_id.in_( query ),
                                  model.Relation.parent_id.in_( query ) ) )
        else:
            query = db.model.query( model.Object ) \
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

        if( self.__range is not None ):
            query = query.limit( self.__range[1] )
            if( self.__range[0] != 0 ):
                query = query.offset( self.__range[0] )

        return SessionObjectFactoryIterator( db, query )
