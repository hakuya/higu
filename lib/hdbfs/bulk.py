""" Bulk operation framework for batch modifications.

This module provides a framework for performing bulk operations on database
objects. Operations can be applied to query results or lists of objects,
with support for dry-run mode (simulation) before committing changes.

Key classes:
    BulkOperation: Base class for bulk operations
    BulkNameReplaceOp: Regex-based name replacement
    SetAttribute: Set metadata attribute on objects
    UnsetAttribute: Remove metadata attribute from objects
    AssignTag: Assign tag to objects
    UnassignTag: Remove tag from objects

Functions:
    op_from_string: Parse operation from string syntax
"""

import re

import hdbfs

from typing import Optional, Tuple, List, Dict

class ParseError( Exception ):
    """ Exception raised when parsing bulk operation syntax fails.

    Raised by op_from_string when the operation string cannot be parsed.
    """

    def __init__( self ):
        Exception.__init__( self )

class BadArgument( Exception ):
    """ Exception raised when operation arguments are invalid.

    Raised when an operation receives invalid arguments or parameters.
    """

    def __init__( self ):
        Exception.__init__( self )

class BulkOperation:
    """ Base class for bulk operations on database objects.

    Provides a framework for performing batch modifications to multiple
    objects. Subclasses implement the _process() method to define the
    specific operation logic.

    Operations can be run in simulation mode (commit=False) to preview
    changes before applying them.

    Attributes:
        _db: Database session
        _commit: Whether to commit changes (True) or simulate (False)
        _modified_list: List of (object, comment) tuples for modified items
    """

    def __init__( self, db: 'hdbfs.Database' ):
        """ Initialize a bulk operation.

        Args:
            db: Database session to operate on
        """

        self._db = db
        self._commit = False
        self._modified_list: List[Tuple[hdbfs.Obj, str]] = []

    def _modified( self, it: hdbfs.Obj, comment: str ) -> None:
        """ Record that an object was modified.

        Should be called by _process() when an object is modified.

        Args:
            it: The modified object
            comment: Description of the modification
        """

        self._modified_list.append( ( it, comment, ) )

    def _process( self, it: hdbfs.Obj ) -> None:
        """ Process a single object (abstract method).

        Subclasses must implement this method to define the operation logic.
        Should call _modified() when an object is modified.

        Args:
            it: Object to process
        """

        pass

    def set_commit( self, commit: bool = True ) -> 'BulkOperation':
        """ Configure whether to commit changes or simulate.

        Args:
            commit: If True, apply changes. If False, simulate only.

        Returns:
            Self for method chaining
        """

        self._commit = commit
        return self

    def execute( self, db: 'hdbfs.Database', query ) -> List[Tuple[hdbfs.Obj, str]]:
        """ Execute the bulk operation on query results.

        Args:
            db: Database session (for compatibility)
            query: Query object to execute, or list of objects

        Returns:
            List of (object, comment) tuples for all modified objects

        Example:
            >>> op = BulkNameReplaceOp(db, r'IMG_', 'Photo_')
            >>> op.set_commit(False)  # Simulate first
            >>> results = op.execute(db, query)
            >>> for obj, comment in results:
            ...     print(f"{obj.get_name()}: {comment}")
            >>> op.set_commit(True).execute(db, query)  # Apply changes
        """

        if( isinstance( query, list ) ):
            rs = query
        else:
            rs = query.execute( db )

        for it in rs:
            self._process( it )

        return self._modified_list

class BulkNameReplaceOp( BulkOperation ):
    """ Bulk rename operation using regex replacement.

    Applies a regex substitution to object names. Objects without names
    are skipped.

    Attributes:
        __pattern: Regex pattern to match
        __repl: Replacement string (can use regex groups like \\1, \\2)
    """

    def __init__( self, db: 'hdbfs.Database', pattern: str, repl: str ):
        """ Initialize a bulk name replacement operation.

        Args:
            db: Database session
            pattern: Regex pattern to match in names
            repl: Replacement string
        """

        super().__init__( db )
        self.__pattern = pattern
        self.__repl = repl

    def _process( self, it: hdbfs.Obj ) -> None:

        name = it.get_name()
        if( name is None ):
            return

        subd = re.sub( self.__pattern, self.__repl, name )

        if( subd != name ):
            if( self._commit ):
                it.set_name( subd )

            self._modified( it, f'{name} -> {subd}' )

class BulkNameDelOp( BulkOperation ):
    """ Bulk operation to delete object names.

    Removes names from objects, optionally filtered by pattern. Objects
    without names are skipped.

    Attributes:
        __pattern: Optional regex pattern - only delete names matching this
    """

    def __init__( self, db: 'hdbfs.Database', pattern: Optional[str] = None ):
        """ Initialize a bulk name deletion operation.

        Args:
            db: Database session
            pattern: Optional regex - only delete names matching this pattern
        """

        super().__init__( db )
        self.__pattern = pattern

    def _process( self, it: hdbfs.Obj ) -> None:

        name = it.get_name()
        if( name is None ):
            return

        if( self.__pattern is not None
        and not re.match( self.__pattern, name ) ):
            return

        if( self._commit ):
            it.set_name( None )

        self._modified( it, f'{name} -> [none]' )

class BulkNameSelectOp( BulkOperation ):
    """ Bulk operation to select names from import log.

    Sets object names from their import log (origin names). Useful for
    restoring original filenames from imports.

    Only processes FILE objects.

    Attributes:
        __pattern: Optional regex to filter origin names
        __force: If True, overwrite existing names
    """

    def __init__( self,
                db: 'hdbfs.Database',
                pattern: Optional[str] = None,
                force: bool = False
            ):
        """ Initialize a bulk name selection operation.

        Args:
            db: Database session
            pattern: Optional regex - only select origin names matching this
            force: If True, overwrite existing names. If False, skip objects
                that already have names
        """

        super().__init__( db )
        self.__pattern = pattern
        self.__force = force

    def _process( self, it: hdbfs.Obj ) -> None:

        if( it.get_type() != hdbfs.ObjectType.FILE ):
            return

        name = it.get_name()
        if( name is not None and not self.__force ):
            return

        new_name = None
        for n in it.get_origin_names():

            if( self.__pattern is None
             or re.match( self.__pattern, n ) ):

                new_name = n
                break

        if( new_name is None or new_name == name ):
            return

        if( self._commit ):
            it.set_name( new_name )

        if( name is not None ):
            self._modified( it, f'{name} -> {new_name}' )
        else:
            self._modified( it, f'[none] -> {new_name}' )

class BulkRateOp( BulkOperation ):
    """ Bulk operation to set rating metadata.

    Sets the 'rating' metadata attribute on all objects.

    Attributes:
        __rating: Rating value to set
    """

    def __init__( self, db: 'hdbfs.Database', rating: int ):
        """ Initialize a bulk rating operation.

        Args:
            db: Database session
            rating: Rating value to set on all objects
        """

        super().__init__( db )
        self.__rating = rating

    def _process( self, it: hdbfs.Obj ) -> None:

        if( self._commit ):
            it['rating'] = self.__rating

        self._modified( it, f'-> rating {self.__rating}' )

class BulkAssignOp( BulkOperation ):
    """ Bulk operation to assign/unassign objects to/from groups.

    Modifies group membership for objects. Can assign to multiple groups
    and unassign from multiple groups in a single operation.

    Attributes:
        __assign: List of groups to assign objects to
        __unassign: List of groups to unassign objects from
    """

    def __init__( self,
                db: 'hdbfs.Database',
                assign: List[hdbfs.Obj] = [],
                unassign: List[hdbfs.Obj] = []
            ):
        """ Initialize a bulk assign/unassign operation.

        Args:
            db: Database session
            assign: List of groups (tags, albums) to assign objects to
            unassign: List of groups to unassign objects from
        """

        super().__init__( db )
        self.__assign = list( assign )
        self.__unassign = list( unassign )

    def _process( self, it: hdbfs.Obj ) -> None:

        if( self._commit ):
            for jt in self.__unassign:
                it.unassign( jt )
            for jt in self.__assign:
                it.assign( jt )

        assign_str = ' '.join( [jt.get_repr() for jt in self.__assign]
                             + ['-' + jt.get_repr() for jt in self.__unassign] )

        self._modified( it, f'assign: {assign_str}' )

class BulkDivide( BulkOperation ):
    """ Bulk operation to divide albums into sub-albums.

    Groups an album's items by regex pattern matching on names, creating
    sub-albums for each group. Can either replace the album's contents
    (inplace) or add sub-albums alongside existing items.

    Only processes Album objects with more than one item.

    Attributes:
        _inplace: If True, move items to sub-albums. If False, copy items.
        _pattern: Regex pattern to extract group names from item names
        _subset_pattern: Optional regex to transform group names for sub-album names
    """

    def __init__( self,
                db: 'hdbfs.Database',
                inplace: bool,
                pattern: str,
                subset_pattern: Optional[str] = None
            ):
        """ Initialize a bulk album divide operation.

        Args:
            db: Database session
            inplace: If True, move items to sub-albums and remove from parent.
                If False, copy items to sub-albums.
            pattern: Regex pattern to extract group identifier from item names
            subset_pattern: Optional regex substitution to transform group name
                into sub-album name
        """

        super().__init__( db )
        self._inplace = inplace
        self._pattern = pattern
        self._subset_pattern = subset_pattern

    def _compute_groups( self,
                        children: List[hdbfs.Obj]
                    ) -> Tuple[
                            List[str],
                            Dict[ Optional[str], List[hdbfs.Obj] ]
                        ]:

        groups = []
        group_map = {}

        for child in children:
            name = child.get_name()

            if( name is None ):
                group = None
            else:
                group = re.match( self._pattern, name ).group( 0 )

                if( self._subset_pattern is not None ):
                    group = re.sub( self._pattern, self._subset_pattern, group )

            if( group not in group_map ):
                groups.append( group )
                group_map[group] = []

            group_map[group].append( child )

        return groups, group_map

    def _process( self, it: hdbfs.Obj ) -> None:

        if( not isinstance( it, hdbfs.Album ) ):
            return

        children = it.get_items()
        if( len( children ) <= 1 ):
            return

        groups, group_map = self._compute_groups( children )

        if( len( groups ) <= 1 ):
            return

        for gname in groups:
            if( self._commit ):
                alb = self._db.create_album( [], gname )
            else:
                alb = None

            if( gname is not None ):
                subset_alb_log = f'subset album {gname}'
            else:
                subset_alb_log = 'subset album'

            self._modified( alb, f'Created {subset_alb_log}' )

            if( self._inplace ):
                if( self._commit ):
                    alb.assign( it )

                self._modified( it, f'Attached {subset_alb_log}' )

            for member in group_map[gname]:
                if( self._commit ):
                    member.assign( alb )
                    if( self._inplace ):
                        member.unassign( it )

                if( self._inplace ):
                    self._modified( member, f'Moved to {subset_alb_log}' )
                else:
                    self._modified( member, f'Attached to {subset_alb_log}' )

class BulkAlbum2Import( BulkOperation ):
    """ Bulk operation to convert closed albums to imports.

    Converts CLOSED albums to IMPORT_CLOSED objects. Useful for reopening
    albums for editing or reorganization.

    Only processes ALBUM_CLOSED objects.

    Attributes:
        __duplicate: If True, creates a copy before converting. If False,
            replaces the album with an import.
    """

    def __init__( self, db: 'hdbfs.Database', duplicate: bool ):
        """ Initialize a bulk album-to-import operation.

        Args:
            db: Database session
            duplicate: If True, keep original album and create an import copy.
                If False, replace album with import.
        """

        super().__init__( db )
        self.__duplicate = duplicate

    def _process( self, it: hdbfs.Obj ) -> None:

        if( it.get_type() != hdbfs.ObjectType.ALBUM_CLOSED ):
            return

        if( self._commit ):
            imp = self._db.album_to_import( it, self.__duplicate )
        else:
            imp = it

        self._modified( imp, f'Converted to import' )

def op_from_string( db: 'hdbfs.Database', s: str ) -> BulkOperation:
    """ Parse a bulk operation string into a BulkOperation object.

    Parses compact string syntax into corresponding operation objects.
    Format: ``operation:operand``

    Args:
        db: Database session
        s: Operation string to parse

    Returns:
        Appropriate BulkOperation subclass instance

    Raises:
        ParseError: Invalid operation format
        BadArgument: Valid format but invalid argument values

    Valid operations:
        - ``name:s/pattern/repl`` - Regex rename (BulkNameReplaceOp)
        - ``name:del[/pattern]`` - Delete names, optionally filtered (BulkNameDelOp)
        - ``name:select[!][/pattern]`` - Select name from import log (BulkNameSelectOp)
            - ``!`` forces overwrite of existing names
        - ``rate:rating`` - Set rating (BulkRateOp)
            - rating must be 2, 4, 6, 8, or 10
        - ``tag:[tags]... [-tags]...`` - Assign/unassign tags (BulkAssignOp)
            - Prefix with ``-`` to unassign
        - ``untag:[tags]...`` - Unassign tags (BulkAssignOp with swapped args)
        - ``divide[!]:pattern[/name]`` - Divide album into sub-albums (BulkDivide)
            - ``!`` moves items (inplace), without ``!`` copies items
        - ``album2import[!]`` - Convert album to import (BulkAlbum2Import)
            - ``!`` keeps original, without ``!`` replaces album

    Note:
        Use ``\\/`` to escape forward slashes in patterns.

    Examples:
        >>> op_from_string(db, "name:s/old/new")  # Rename old->new
        >>> op_from_string(db, "rate:8")  # Set rating to 8
        >>> op_from_string(db, "tag:mytag -oldtag")  # Assign mytag, unassign oldtag
    """

    try:
        action, operand = tuple( map( lambda x: x.strip(), s.split( ':', 1 ) ) )
    except:
        action = s.strip()
        operand = ''

    if( action == 'name' ):

        parts = list( map( lambda x: x.replace( '\0', '/' ),
                            operand.replace( '\\/', '\0' ).split( '/' ) ) )

        if( parts[0] == 's' ):
            if( len( parts ) == 3 ):
                return BulkNameReplaceOp( db, parts[1], parts[2] )
        elif( parts[0] == 'del' ):
            if( len( parts ) <= 2 ):
                return BulkNameDelOp( db, parts[1] if len( parts ) == 2 else None )
        elif( parts[0] in [ 'select', 'select!' ] ):
            if( len( parts ) <= 2 ):
                return BulkNameSelectOp(
                            db,
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

        return BulkRateOp( db, rating )

    elif( action in ['tag', 'untag'] ):
        tags = operand.strip().split( ' ' )

        try:
            assign = [db.get_tag( t ) for t in tags if t[0] != '-']
            unassign = [db.get_tag( t[1:] ) for t in tags if t[0] == '-']
        except:
            return BadArgument()

        if( action == 'untag' ):
            assign, unassign = unassign, assign

        return BulkAssignOp( db, assign, unassign )

    elif( action in [ 'divide', 'divide!' ] ):

        parts = list( map( lambda x: x.replace( '\0', '/' ),
                            operand.replace( '\\/', '\0' ).split( '/' ) ) )

        return BulkDivide(
                    db,
                    action == 'divide!',
                    parts[0],
                    parts[1] if len( parts ) > 1 else None
                )

    elif( action in [ 'album2import', 'album2import!' ] ):

        return BulkAlbum2Import(
                    db,
                    action == 'album2import' )

    raise ParseError()
