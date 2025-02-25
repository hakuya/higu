import re

import hdbfs

from typing import Optional, Tuple, List, Dict

class ParseError( Exception ):

    def __init__( self ):
        Exception.__init__( self )

class BadArgument( Exception ):

    def __init__( self ):
        Exception.__init__( self )

class BulkOperation:
    '''Protocol for a bulk operation. Subclases should implement the _process()
    method.'''

    def __init__( self, db: 'hdbfs.Database' ):

        self._db = db
        self._commit = False
        self._modified_list = []

    def _modified( self, it: hdbfs.Obj, comment: str ):

        self._modified_list.append( ( it, comment, ) )

    def _process( self, it: hdbfs.Obj ) -> None:
        '''Abstract method to process an item in the operation. Takes in an
        item 'it' and returns a tuple containing 'it' and a comment string
        if the item was modified.

        This method should call _modified() when an item is modified.
        '''

        pass

    def set_commit( self, commit: bool = True ) -> None:
        '''Configures whether this operation should take real effect. If
        commit is False, the operation should be a simulation.
        '''

        self._commit = commit
        return self

    def execute( self, db, query ) -> List[ Tuple[hdbfs.Obj,str] ]:
        '''Calls the bulk operation on a query.'''

        if( isinstance( query, list ) ):
            rs = query
        else:
            rs = query.execute( db )

        for it in rs:
            self._process( it )

        return self._modified_list

class BulkNameReplaceOp( BulkOperation ):
    '''Performs a bulk rename with a regex replacement.'''

    def __init__( self, db: 'hdbfs.Database', pattern: str, repl: str ):

        super().__init__( db )
        self.__pattern = pattern
        self.__repl = repl

    def _process( self, it ):

        name = it.get_name()
        if( name is None ):
            return

        subd = re.sub( self.__pattern, self.__repl, name )

        if( subd != name ):
            if( self._commit ):
                it.set_name( subd )

            self._modified( it, f'{name} -> {subd}' )

class BulkNameDelOp( BulkOperation ):
    '''Deletes the name of all queried items.'''

    def __init__( self, db: 'hdbfs.Database', pattern: Optional[str] = None ):

        super().__init__( db )
        self.__pattern = pattern

    def _process( self, it ):

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
    '''If an item has a name in its import log that matches the pattern
    sets the item to that name.
    '''

    def __init__( self,
                db: 'hdbfs.Database',
                pattern: Optional[str] = None,
                force: bool = False
            ):

        super().__init__( db )
        self.__pattern = pattern
        self.__force = force

    def _process( self, it ):

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
    '''Sets a rating.'''

    def __init__( self, db: 'hdbfs.Database', rating: int ):

        super().__init__( db )
        self.__rating = rating

    def _process( self, it ):

        if( self._commit ):
            it['rating'] = self.__rating

        self._modified( it, f'-> rating {self.__rating}' )

class BulkAssignOp( BulkOperation ):
    '''Performs bulk assign or unassign operations on the membership tree.'''

    def __init__( self,
                db: 'hdbfs.Database',
                assign: List[hdbfs.Obj] = [],
                unassign: List[hdbfs.Obj] = []
            ):

        super().__init__( db )
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

        self._modified( it, f'assign: {assign_str}' )

class BulkDivide( BulkOperation ):
    '''Divides an album into sub-albums.

    The items of the album are grouped by pattern, looking at the file name.
    If a subset_name is provided, it will be used to name the new albums.

    If 'inplace' is true, then the subsets will replace the album's contents.
    '''

    def __init__( self,
                db: 'hdbfs.Database',
                inplace: bool,
                pattern: str,
                subset_pattern: Optional[str] = None
            ):

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

    def _process( self, it ):

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
    '''Performs bulk assign or unassign operations on the membership tree.'''

    def __init__( self, db: 'hdbfs.Database', duplicate: bool ):

        super().__init__( db )
        self.__duplicate = duplicate

    def _process( self, it ):

        if( it.get_type() != hdbfs.ObjectType.ALBUM_CLOSED ):
            return

        if( self._commit ):
            imp = self._db.album_to_import( it, self.__duplicate )
        else:
            imp = it

        self._modified( imp, f'Converted to import' )

def op_from_string( db: 'hdbfs.Database', s: str ) -> BulkOperation:
    '''Constructs a bulk operation from a operation string.

    The operation string has the following format,

      operation:operand

    Valid operations are,

      name:s/pattern/repl       - bulk rename with a pattern
      name:del[/pattern]        - bulk delete name (if pattern matches)
      name:select[!][/pattern]  - select the name with the given pattern

      rate:rating               - bulk rate matching items

      tag:[tags]... [-tags]...  - bulk assign or unassign tags
      untag:[tags]...           - (shorthand) bulk unassign tags

      divide[!]:pattern[/name]  - divides an album
      '''

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
