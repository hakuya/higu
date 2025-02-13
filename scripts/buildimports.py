import datetime
import sys

import logging
log = logging.getLogger( __name__ )
logging.basicConfig()

import hdbfs
import hdbfs.model as model
import higu.config
import time

from optparse import OptionParser
from typing import List, Dict, Optional, NamedTuple
from functools import reduce

class AlbumEntry( NamedTuple ):
    object_id: int
    object_type: hdbfs.ObjectType
    add_ts: int

    def __repr__( self ):

        dt = datetime.datetime.fromtimestamp( self.add_ts )
        return f'Album( id={self.object_id} type={self.object_type} ts={dt} )'

class ImportEntry:

    def __init__( self,
                log_id: int,
                timestamp: int,
                stream_id: int,
                name: Optional[str],
                object_id: int,
                dedup_id: int
            ):

        self.log_id = log_id
        self.timestamp = timestamp
        self.stream_id = stream_id
        self.name = name
        self.object_id = object_id
        self.dedup_id = dedup_id
        self.album_ids = None
        self.import_id = None

    def shares_album( self, o: 'ImportEntry' ) -> bool:

        return len( [a for a in self.album_ids if a in o.album_ids] ) != 0

    def resolve_albums( self, album_map: Dict[ int, List[int] ] ) -> None:

        if( self.object_id != self.dedup_id ):
            self.album_ids = album_map.get( self.object_id, [] ) \
                           + album_map.get( self.dedup_id, [] )
        else:
            self.album_ids = album_map.get( self.object_id, [] )

    def resolve_import( self,
                import_map: Dict[ int, List[int] ],
                import_info: Dict[ int, AlbumEntry ],
                threshold: int
            ) -> None:

        matches: List[AlbumEntry] = []

        for import_id in import_map.get( self.object_id, [] ):
            info = import_info[ import_id ]

            if( info.add_ts < self.timestamp
                    and self.timestamp - info.add_ts < threshold ):
                matches.append( info )

        if( matches == [] ):
            return

        best = matches[0]
        for oth in matches[1:]:
            if( oth.object_id == 240099 or best.object_id == 240099 ):
                print( self )
                print( best )
                print( oth )
            if( (self.timestamp - oth.add_ts)
                    < (self.timestamp - best.add_ts) ):
                best = oth

        self.import_id = best.object_id

    def __repr__( self ):

        dt = datetime.datetime.fromtimestamp( self.timestamp )
        return f'Entry( ts={dt}, object={self.object_id}, name={self.name}, albums={self.album_ids}, import={self.import_id} )'

class ImportGroup:

    def __init__( self, entries: List[ImportEntry], existing_id: Optional[int] = None ):

        self.timestamp = entries[0].timestamp
        self.entries = entries

        self.albums = entries[0].album_ids
        for it in entries[1:]:
            if( len( self.albums ) == 0 ):
                break
            self.albums = [a for a in self.albums if a in it.album_ids]

        self.existing_id = existing_id

    def print( self ):

        print( self )
        for e in self.entries:
            print( '>', e )

    def force_split( self, n: int ) -> List[ 'ImportGroup' ]:

        if( len( self.albums ) != 0 ):
            return [ self ]

        out = []
        next = self

        while( len( next.entries ) > n and len( next.albums ) == 0 ):

            split_pos = None

            # Seek backward for a pos that doesn't split an album
            for i in range( n - 1, -1, -1 ):

                # Don't split across an album
                if( next.entries[i].shares_album( next.entries[i+1] ) ):
                    continue

                split_pos = i
                break

            if( split_pos is None ):
                # Seek forward for a pos that doesn't split an album
                for i in range( n, len( next.entries ) - 1 ):

                    # Don't split across an album
                    if( next.entries[i].shares_album( next.entries[i+1] ) ):
                        continue

                    split_pos = i
                    break

            if( split_pos is None ):
                # Case where though there is no one common album, members may
                # belong to multiple albums such that there is no one point
                # that can be chosen which doesn't cut an album
                break

            out.append( ImportGroup( next.entries[:split_pos+1] ) )
            next = ImportGroup( next.entries[split_pos+1:] )

        out.append( next )
        return out

    def split_gap( self, dt: int ) -> List[ 'ImportGroup' ]:

        if( len( self.albums ) != 0 ):
            return [ self ]

        split = True
        out = []
        next = self

        while( split ):
            split = False

            for i in range( len( next.entries ) - 1 ):

                # Don't split across an album
                if( next.entries[i].shares_album( next.entries[i+1] ) ):
                    continue

                gap = next.entries[i+1].timestamp - next.entries[i].timestamp
                if( gap > dt ):
                    out.append( ImportGroup( next.entries[:i+1] ) )
                    next = ImportGroup( next.entries[i+1:] )
                    split = True
                    break

        out.append( next )
        return out

    def split_largest_gap( self ) -> List[ 'ImportGroup' ]:

        if( len( self.albums ) != 0 ):
            return [ self ]

        max_gap = ( 0, None )
        for i in range( len( self.entries ) - 1 ):

            # Don't split across an album
            if( self.entries[i].shares_album( self.entries[i+1] ) ):
                continue

            gap = self.entries[i+1].timestamp - self.entries[i].timestamp
            if( gap > max_gap[0] ):
                max_gap = ( gap, i )

        if( max_gap[1] is not None ):
            split_idx = max_gap[1] + 1
            return [
                ImportGroup( self.entries[:split_idx] ),
                ImportGroup( self.entries[split_idx:] )
            ]
        else:
            return [ self ]

    def __repr__( self ):

        dt = datetime.datetime.fromtimestamp( self.timestamp )
        return f'Group( ts={dt}, entries={len( self.entries )}, albums={self.albums}, existing_id={self.existing_id} )'

def main() -> int:

    parser = OptionParser( usage = 'Usage: %prog [options]' )

    parser.add_option( '-c', '--config',
        dest = 'config',
        help = 'Configuration File' )
    parser.add_option( '-x', '--execute',
        dest = 'execute', action = 'store_true', default = False,
        help = 'Runs for real. By default the program runs a dry run' )
    parser.add_option( '-g', '--split-gap',
        dest = 'split_gap',
        help = 'Always split gaps larget that this' )
    parser.add_option( '-n', '--max-size',
        dest = 'max_size',
        help = 'Maximum import size' )

    opts = parser.parse_args()[0]

    max_size = int( opts.max_size ) if( opts.max_size is not None ) else None
    split_gap = int( opts.split_gap ) if( opts.split_gap is not None ) else None

    if( opts.config is not None ):
        cfg = higu.config.init( opts.config )
        hdbfs.init( cfg.get_path( 'library' ) )
    else:
        hdbfs.init()

    h = hdbfs.Database()

    h.model.execute(
        '''CREATE TEMPORARY TABLE temp_import_entries(\n'''
        '''     log_id      PRIMARY KEY,\n'''
        '''     timestamp   INTEGER NOT NULL,\n'''
        '''     stream_id   INTEGER NOT NULL,\n'''
        '''     name        TEXT\n,'''
        '''     object_id   INTEGER NOT NULL,\n'''
        '''     dedup_id    INTEGER NOT NULL\n'''
        ''')''' )

    h.model.execute(
        '''CREATE TEMPORARY TABLE temp_import_entry_albums(\n'''
        '''     object_id   INTEGER NOT NULL,\n'''
        '''     album_id    INTEGER NOT NULL,\n'''
        '''     album_type  INTEGER NOT NULL,\n'''
        '''     album_ts    INTEGER NOT NULL\n'''
        ''')''' )

    h.model.execute(
        '''INSERT INTO temp_import_entries\n'''
        '''SELECT\n'''
        '''     log.log_id,\n'''
        '''     log.timestamp,\n'''
        '''     log.stream_id,\n'''
        '''     COALESCE( log.origin_name, lname.origin_name ),\n'''
        '''     o.object_id,\n'''
        '''     COALESCE( dedup.object_id, o.object_id )\n'''
        '''FROM stream_log log\n'''
        '''INNER JOIN objects o\n'''
        '''     ON log.stream_id = o.root_stream_id\n'''
        '''LEFT OUTER JOIN (\n'''
        '''         SELECT\n'''
        '''             relations.child_id as child_id,\n'''
        '''             objects.object_id as object_id\n'''
        '''         FROM relations\n'''
        '''         INNER JOIN objects\n'''
        '''             ON relations.parent_id = objects.object_id\n'''
        '''             AND objects.object_type = {ftype}\n'''
        '''     ) dedup\n'''
        '''     ON o.object_type = {duptype}\n'''
        '''     AND dedup.child_id = o.object_id\n'''
        '''LEFT OUTER JOIN stream_log lname\n'''
        '''     ON log.stream_id = lname.stream_id\n'''
        '''     AND log.origin_method = "hdbfs:legacy_create"\n'''
        '''     AND lname.origin_method = "hdbfs:legacy_name"\n'''
        '''WHERE log.origin_method IN (\n'''
        '''     "hdbfs:legacy_create",\n'''
        '''     "hdbfs:register"\n'''
        ''')\n'''
        '''GROUP BY log.log_id\n'''.format(
            ftype = model.ObjectType.FILE.value,
            duptype = model.ObjectType.DUPLICATE.value
        )
    )

    h.model.execute(
        '''INSERT INTO temp_import_entry_albums\n'''
        '''SELECT\n'''
        '''     e.object_id,\n'''
        '''     o.object_id,\n'''
        '''     o.object_type,\n'''
        '''     o.add_ts\n'''
        '''FROM (\n'''
        '''         SELECT DISTINCT object_id\n'''
        '''         FROM (\n'''
        '''             SELECT object_id FROM temp_import_entries\n'''
        '''             UNION\n'''
        '''             SELECT dedup_id FROM temp_import_entries\n'''
        '''         )\n'''
        '''     ) e\n'''
        '''INNER JOIN relations r\n'''
        '''     ON e.object_id = r.child_id\n'''
        '''INNER JOIN objects o\n'''
        '''     ON o.object_type IN ( {alb_types} )\n'''
        '''     AND o.object_id = r.parent_id'''.format(
            alb_types = ",".join(
                [
                    str( it )
                    for it in
                        model.ObjectClass.all_type_values( model.ObjectClass.ALBUM )
                      + model.ObjectClass.all_type_values( model.ObjectClass.IMPORT )
                ]
            )
        )
    )

    #'hdbfs:legacy_create',
    #'hdbfs:legacy_name',
    #'hdbfs:legacy_altname',
    #'hdbfs:register',

    rs = h.model.execute(
        '''SELECT * FROM temp_import_entries'''
    )

    entries = [ImportEntry( *it ) for it in rs]

    rs = h.model.execute(
        '''SELECT * FROM temp_import_entry_albums'''
    )

    album_entries = {}
    entry_albums = {}
    entry_imports = {}

    for it in rs:
        if( it[1] not in album_entries ):
            alb = AlbumEntry( it[1], hdbfs.ObjectType( it[2] ), it[3] )
            album_entries[ it[1] ] = alb
        else:
            alb = album_entries[ it[1] ]

        if( alb.object_type in hdbfs.ObjectClass.IMPORT.all_types() ):
            try:
                entry_imports[ it[0] ].append( it[1] )
            except KeyError:
                entry_imports[ it[0] ] = [ it[1] ]
        else:
            try:
                entry_albums[ it[0] ].append( it[1] )
            except KeyError:
                entry_albums[ it[0] ] = [ it[1] ]

    h.model.execute( '''DROP TABLE temp_import_entry_albums''' )
    h.model.execute( '''DROP TABLE temp_import_entries''' )

    for e in entries:
        e.resolve_albums( entry_albums )
        e.resolve_import( entry_imports, album_entries, split_gap )

    def split_gap_fn( g: ImportGroup, gap: int ):

        if( g.existing_id is not None ):
            return [ g ]

        if( gap is not None ):
            return g.split_gap( gap )
        else:
            return [ g ]

    def split_largest_gap_fn( g: ImportGroup, n: int ):

        if( g.existing_id is not None ):
            return [ g ]

        if( len( g.entries ) > n ):
            return g.split_largest_gap()
        else:
            return [ g ]

    def force_split_fn( g: ImportGroup, n: int ):

        if( g.existing_id is not None ):
            return [ g ]

        if( len( g.entries ) > n ):
            return g.force_split( n )
        else:
            return [ g ]

    def split_and_flatten_single( g: ImportGroup, fn, *args ):

        groups = fn( g, *args )

        if( len( groups ) == 1 ):
            return groups

        return split_and_flatten( groups, fn, *args )

    def split_and_flatten( groups: List[ImportGroup], fn, *args ) -> List[ImportGroup]:

        r = []
        for it in groups:
            r.extend( split_and_flatten_single( it, fn, *args ) )

        return r

    def build_groups( entries: List[ImportEntry] ) -> List[ImportGroup]:

        groups: List[ImportGroup] = []
        current: List[ImportEntry] = []

        for it in entries:
            if( current != [] and it.import_id != current[0].import_id ):

                prev = groups[-1] if( groups != [] ) else None
                if( prev is not None
                        and prev.existing_id is not None
                        and it.import_id == prev.existing_id ):
                    # Handle odd case where imports are interleaved
                    groups[-1] = ImportGroup( prev.entries + [ it ], prev.existing_id )
                else:
                    groups.append( ImportGroup( current, current[0].import_id ) )
                    current = [ it ]
            else:
                current.append( it )

        groups.append( ImportGroup( current, current[0].import_id ) )

        return groups

    groups = build_groups( entries )
    #groups = [ ImportGroup( entries ) ]
    groups = split_and_flatten( groups, split_gap_fn, split_gap )
    groups = split_and_flatten( groups, split_largest_gap_fn, max_size )
    groups = split_and_flatten( groups, force_split_fn, max_size )

    for a in album_entries.values():
        print( a )

    for g in groups:
        g.print()

    existing_counts = {}
    groups_to_create: List[ImportGroup] = []

    for g in groups:
        if( g.existing_id is not None ):
            import_id = g.existing_id
            existing_counts[ import_id ] = existing_counts.get( import_id, 0 ) + 1
        else:
            groups_to_create.append( g )

    for import_id, count in existing_counts.items():
        if( count > 1 ):
            print( f'WARNING: import {import_id} is repeated {count}' )

    print( f'Will create {len( groups_to_create )} groups' )

    if( opts.execute ):
        time.sleep( 5 )

        h.enable_write_access()

        with h.transaction():
            for i, g in enumerate( groups_to_create ):
                print( f'{i+1}/{len( groups_to_create )}: {g}' )
                sys.stdout.flush()

                if( opts.execute ):
                    obj = model.Object( hdbfs.ObjectType.IMPORT_CLOSED )
                    obj.add_ts = g.timestamp
                    obj.name = None

                    h.model.add( obj )
                    h.model.flush()

                    instance_map = {}

                    for j, it in enumerate( g.entries ):

                        # Get an instance number, starting with 0 (-1 + 1)
                        instance = instance_map.get( it.object_id, -1 ) + 1
                        instance_map[it.object_id] = instance

                        r = model.Relation()
                        r.child_id = it.object_id
                        r.parent_id = obj.object_id
                        r.instance = instance
                        r.add_ts = it.timestamp
                        r.sort = j
                        r.child_name = it.name

                        h.model.add( r )

                    h.model.flush()

    else:
        for i, g in enumerate( groups_to_create ):
            print( f'{i+1}/{len( groups_to_create )}: {g}' )

if( __name__ == '__main__' ):
    sys.exit( main() )