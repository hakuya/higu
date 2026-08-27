from hdbfs.objects.basic import Obj
from hdbfs.objects.file import File
from hdbfs.session import Session, SessionObject

import hdbfs.model as model

from enum import Enum
from typing import List, Optional

import random

class Group( Obj ):
    """ Represents a group container (album, tag, import).

    Groups contain collections of files and/or albums. The Group class
    provides the base functionality for organizing and retrieving items,
    with support for different ordering strategies.

    Groups can be:
    - Albums: User-created collections
    - Tags: Classification/categorization groups
    - Imports: Batch import collections

    Attributes:
        obj: The underlying model.Object database record
    """

    class Order( Enum ):
        """ Ordering strategy for items in a group.

        Determines how items are sorted when retrieved from the group.
        """

        UNORDERED = 0  # Random/unspecified order
        EXPLICIT = 1   # User-defined explicit ordering
        NAME = 2       # Alphabetical by name
        DATE = 3       # Chronological by origin/add time

    def __init__( self, session: Session, obj: model.Object ):

        super().__init__( session, obj )

    def get_ordering( self ) -> 'Group.Order':
        """ Get the ordering strategy for this group.

        Returns:
            Order enum value (UNORDERED for base Group class)
        """

        return Group.Order.UNORDERED

    def get_items( self, limit: Optional[int] = None ) -> List[Obj]:
        """ Get all items (files and albums) in this group.

        Items are sorted according to the group's ordering strategy:
        - UNORDERED: Natural order (no specific sorting)
        - NAME: Alphabetically by name
        - DATE: Chronologically by origin time or add time
        - EXPLICIT: User-defined order (handled by OrderedGroup)

        Args:
            limit: Maximum number of items to return

        Returns:
            List of Obj objects (File and Album instances)
        """

        items = self.get_children( [
                    model.ObjectClass.FILE,
                    model.ObjectClass.ALBUM
                ], limit )
        if( self.get_ordering() == Group.Order.UNORDERED ):
            # Will cause mismatch in ordering between the tag
            # view and opening up the tile in the webui
            # random.shuffle( items )
            pass
        elif( self.get_ordering() == Group.Order.NAME ):
            items.sort( key = lambda it: it.get_name()
                       if it.get_name() is not None else '' )
        elif( self.get_ordering() == Group.Order.DATE ):
            items.sort( key = lambda it: it.get_origin_time()
                       if it.get_origin_time() is not None else it.get_add_time() )

        return items

    def get_albums( self, limit: Optional[int] = None ) -> List['Album']:
        """ Get all albums in this group.

        Args:
            limit: Maximum number of albums to return

        Returns:
            List of Album objects
        """

        return self.get_children( model.ObjectClass.ALBUM, limit )

    def get_files( self, limit: Optional[int] = None ) -> List[File]:
        """ Get all files in this group.

        Args:
            limit: Maximum number of files to return

        Returns:
            List of File objects
        """

        return self.get_children( model.ObjectClass.FILE, limit )

class OrderedGroup( Group ):
    """ A group with explicit user-defined ordering.

    OrderedGroup extends Group to support custom ordering where the user
    can explicitly set the position of each item. This is used for albums
    and ordered tags where the display order matters.

    Attributes:
        obj: The underlying model.Object database record
    """

    def __init__( self, session: Session, obj: model.Object ):

        super().__init__( session, obj )

    def get_ordering( self ) -> Group.Order:
        """ Get the ordering strategy for this group.

        Returns:
            Always returns Group.Order.EXPLICIT
        """

        return Group.Order.EXPLICIT

    def clear_order( self ) -> None:
        """ Remove explicit ordering from all files in the group.

        Resets the sort order for all files, allowing them to return to
        natural/default ordering.
        """

        all_objs = self.get_files()

        for child in all_objs:
            child.reorder( self )

    def set_order( self, children: List[Obj] ) -> None:
        """ Set explicit ordering for items in the group.

        Assigns sort positions to the provided items in the given order.
        Items not in the list are appended after the specified items.

        Args:
            children: List of Obj items in desired display order

        Raises:
            AssertionError: If any child is not actually in this group
        """

        with self.session._access( write = True ):

            all_objs = self.get_items()

            for child in enumerate( children ):
                assert( child[1] in all_objs )
                all_objs.remove( child[1] )

                child[1].reorder( self, child[0] )

            offset = len( children )

            for child in enumerate( all_objs ):
                child[1].reorder( self, offset + child[0] )


class Tag( OrderedGroup ):
    """ Represents a tag (classifier) for organizing files.

    Tags are used to categorize and classify files and albums. Unlike
    albums, tags support multiple ordering strategies that can be changed
    dynamically. The tag type in the database determines its ordering.

    Tag types map to ordering strategies:
    - CLASSIFIER_UNORDERED: Random/unspecified order
    - CLASSIFIER_ORDERED: User-defined explicit ordering
    - CLASSIFIER_NAME_ORDER: Alphabetical by name
    - CLASSIFIER_DATE_ORDER: Chronological by date

    Attributes:
        obj: The underlying model.Object database record
    """

    def __init__( self, db: Session, obj: model.Object ):

        Group.__init__( self, db, obj )

    def get_ordering( self ) -> Group.Order:
        """ Get the current ordering strategy for this tag.

        The ordering is determined by the tag's database type
        (CLASSIFIER_* ObjectType).

        Returns:
            Order enum value based on the tag type
        """

        return {
            model.ObjectType.CLASSIFIER_UNORDERED  : Group.Order.UNORDERED,
            model.ObjectType.CLASSIFIER_ORDERED    : Group.Order.EXPLICIT,
            model.ObjectType.CLASSIFIER_NAME_ORDER : Group.Order.NAME,
            model.ObjectType.CLASSIFIER_DATE_ORDER : Group.Order.DATE,
        }[self.obj.get_type()]

    @SessionObject._with_access( write = True )
    def set_ordering( self, ordering: Group.Order ) -> None:
        """ Change the ordering strategy for this tag.

        When switching away from EXPLICIT ordering, any existing explicit
        order is cleared. The tag's database type is updated to match the
        new ordering strategy.

        Args:
            ordering: New ordering strategy to use

        Example:
            tag.set_ordering(Group.Order.NAME)  # Sort alphabetically
        """

        if( self.obj.get_type() == model.ObjectType.CLASSIFIER_ORDERED
        and ordering != Group.Order.EXPLICIT ):

            self.clear_order()

        self.obj.set_type( {
                Group.Order.UNORDERED : model.ObjectType.CLASSIFIER_UNORDERED,
                Group.Order.EXPLICIT  : model.ObjectType.CLASSIFIER_ORDERED,
                Group.Order.NAME      : model.ObjectType.CLASSIFIER_NAME_ORDER,
                Group.Order.DATE      : model.ObjectType.CLASSIFIER_DATE_ORDER,
            }[ordering] )
