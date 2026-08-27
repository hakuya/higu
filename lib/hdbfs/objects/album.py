import datetime

from hdbfs.session import Session, SessionObject
from hdbfs.objects.groups import OrderedGroup
from hdbfs.objects.metadata import MetadataManager
from hdbfs.objects.basic import Stream

import hdbfs.model as model

from typing import Optional

class Album( OrderedGroup ):
    """ Represents an album for organizing files and nested albums.

    Albums are user-created collections with explicit ordering and metadata.
    They support hierarchical organization (albums within albums) and have
    three states:

    - FREE: Draft album, automatically deduplicates (cannot store duplicate files)
    - FORMAL: Published album, can explicitly store duplicate file references
    - CLOSED: Locked album that cannot be modified, can store duplicates

    The key difference is in duplicate file handling:
    - FREE albums: Deduplication happens automatically - if you add a duplicate
      file, only the original is stored
    - FORMAL/CLOSED albums: Can explicitly store references to duplicate files,
      allowing you to preserve which specific duplicate was in the album

    Albums automatically maintain aggregate metadata (origin time, etc.) by
    tracking changes to their contents.

    Attributes:
        obj: The underlying model.Object database record
        metaman: MetadataManager for handling album metadata
    """

    def __init__( self, session: Session, metaman: MetadataManager, obj: model.Object ):

        super().__init__( session, obj )
        self.metaman = metaman

    def _on_created( self, stream: Stream ) -> None:
        """ Hook called when a new stream is created for this album.

        Triggers metadata initialization to update album metadata based
        on the new content.

        Args:
            stream: The newly created Stream object
        """

        self.metaman.require_metadata_init( self, None )

    def _on_children_changed( self ) -> None:
        """ Hook called when child relationships change.

        Triggers metadata initialization to update album metadata when
        files or sub-albums are added or removed.
        """

        self.metaman.require_metadata_init( self, None )

    @SessionObject._with_access( write = True )
    def make_formal_album( self ) -> None:
        """ Promote this album to FORMAL state.

        FORMAL albums can explicitly store duplicate file references, allowing
        you to preserve the specific duplicates that were in the album rather
        than auto-deduplicating to originals.

        Requirements:
        - All child albums must be FORMAL or CLOSED

        Transitioning from FREE to FORMAL validates that all nested albums
        meet the formal requirements.

        Raises:
            AssertionError: If child albums are not formal/closed
        """

        if( self.obj.get_type() == model.ObjectType.ALBUM_FREE ):
            # Ensure all children are formal
            for alb in self.get_albums():
                assert alb.obj.get_type() in [
                            model.ObjectType.ALBUM_FORMAL,
                            model.ObjectType.ALBUM_CLOSED
                        ]

            self.obj.set_type( model.ObjectType.ALBUM_FORMAL )

        elif( self.obj.get_type() in [
                    model.ObjectType.ALBUM_FORMAL,
                    model.ObjectType.ALBUM_CLOSED
                ] ):
            pass

        else:
            assert False

    @SessionObject._with_access( write = True )
    def make_free_album( self ) -> None:
        """ Demote this album to FREE (draft) state.

        FREE albums automatically deduplicate files - duplicate file references
        are not allowed. When demoting from FORMAL/CLOSED to FREE:
        - Must not contain any duplicate file references
        - All relationships must be single-instance (no poly-linking)

        Raises:
            AssertionError: If album contains duplicate file references or poly-linked items
        """

        if( self.obj.get_type() == model.ObjectType.ALBUM_FREE ):
            pass

        if( self.obj.get_type() in [
                    model.ObjectType.ALBUM_FORMAL,
                    model.ObjectType.ALBUM_CLOSED
                ] ):

            # There can't be any duplicates in an unpublished album
            assert len( [f for f in self.get_files()
                    if f.obj.get_type() == model.ObjectType.DUPLICATE] ) == 0

            for rel in self.obj.child_rel:
                assert rel.instance == 0

            self.obj.set_type( model.ObjectType.ALBUM_FREE )

        else:
            assert False

    @SessionObject._with_access( write = True )
    def close_album( self ) -> None:
        """ Lock this album in CLOSED state.

        CLOSED albums cannot be modified. When closing:
        - All child albums must already be CLOSED
        - Album can be FREE or FORMAL before closing

        Raises:
            AssertionError: If child albums are not closed
        """

        if( self.obj.get_type() in [
                    model.ObjectType.ALBUM_FREE,
                    model.ObjectType.ALBUM_FORMAL
                ] ):

            # Ensure all children are closed
            for alb in self.get_albums():
                assert alb.obj.get_type() == model.ObjectType.ALBUM_CLOSED

            self.obj.set_type( model.ObjectType.ALBUM_CLOSED )

        elif( self.obj.get_type() == model.ObjectType.ALBUM_CLOSED ):
            pass

        else:
            assert False

    @SessionObject._with_access( write = True )
    def open_album( self ) -> None:
        """ Reopen a CLOSED album to FORMAL state.

        Allows modifications to a previously locked album. Only CLOSED
        albums can be opened (becomes FORMAL). FREE and FORMAL albums
        are already open.
        """

        if( self.obj.get_type() in [
                    model.ObjectType.ALBUM_FREE,
                    model.ObjectType.ALBUM_FORMAL
                ] ):
            pass

        elif( self.obj.get_type() == model.ObjectType.ALBUM_CLOSED ):
            self.obj.set_type( model.ObjectType.ALBUM_FORMAL )

        else:
            assert False

    @SessionObject._with_access( write = True )
    def gather_tags( self ) -> None:
        """ Aggregate tags from all child items onto this album.

        Collects all tags from child files and albums and applies them to
        this album. For ordered tags, preserves the earliest (lowest) order
        value. After gathering, tags are removed from individual children
        so they only appear on the album.
        """

        files = self.get_items()

        tags = {}

        def accum( tags, f ):

            for t in f.get_tags():
                order = None
                if( t.get_type() == model.ObjectType.CLASSIFIER_ORDERED ):
                    order = f.get_order( t )
                if( t not in tags
                    or order is not None and (
                        tags[t] is None
                        or order < tags[t]
                    ) ):

                    tags[t] = order

        # Accumulate self, or we may loose our own order
        accum( tags, self )

        for f in files:
            accum( tags, f )

        for t, order in tags.items():
            self.assign( t, order = order )
            for f in files:
                f.unassign( t )

    def get_origin_time( self ) -> Optional[datetime.datetime]:
        """ Get the origin time of this album.

        The origin time is aggregated from the album's contents and
        represents when the album's content was originally created/captured.

        Returns:
            Datetime object (UTC) if origin_time metadata exists, None otherwise
        """

        self.check_metadata()
        try:
            return datetime.datetime\
                    .utcfromtimestamp( self['origin_time'] )
        except:
            return None

    def check_metadata( self ) -> None:
        """ Ensure album metadata is up to date.

        Triggers metadata recalculation if the album's metadata is stale.
        Metadata includes aggregated information like origin time from
        the album's contents.
        """

        self.metaman.check_metadata( self, None )
