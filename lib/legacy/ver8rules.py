import db

TYPE_NILL       = 0
TYPE_FILE       = 1000
TYPE_FILE_DUP   = 1001
TYPE_FILE_VAR   = 1002
TYPE_GROUP      = 2000
TYPE_ALBUM      = 2001
TYPE_CLASSIFIER = 2002

class LinkedDuplicateIterator:

    def __init__( self, session ):

        self.__objl = session.get_table( 'objl' )
        self.__rel2 = session.get_table( 'rel2' )

        self.__iter = self.__objl.select( [ 'id' ],
                [ ( 'type', TYPE_FILE_DUP, ) ] ).__iter__()

    def __iter__( self ):

        return self

    def next( self ):

        while True:
            ( obj_id, ) = self.__iter.next()

            try:
                self.__objl.select( [ 'id' ], [ ( 'dup', obj_id, ), ] ).__iter__().next()
                return obj_id
            except StopIteration:
                pass

            try:
                self.__rel2.select( [ 'parent' ], [ ( 'child', obj_id, ), ] ).__iter__().next()
                return obj_id
            except StopIteration:
                pass

            try:
                self.__rel2.select( [ 'child' ], [ ( 'parent', obj_id, ), ] ).__iter__().next()
                return obj_id
            except StopIteration:
                pass

def determine_duplicate_parent( session, obj_id ):

    objl = session.get_table( 'objl' )

    try:
        ( obj_type, obj_parent ) = objl.select( [ 'type', 'dup', ],
                [ ( 'id', obj_id, ), ] ).__iter__().next()
    except StopIteration:
        return None

    if( obj_type != TYPE_FILE_DUP ):
        return obj_id
    else:
        return determine_duplicate_parent( session, obj_parent )

def correct_linked_duplicates( session ):

    objl = session.get_table( 'objl' )
    rel2 = session.get_table( 'rel2' )

    for obj_id in LinkedDuplicateIterator( session ):
        parent_id = determine_duplicate_parent( session, obj_id )

        # Move all dup/vars
        objl.update( [ ( 'dup', parent_id, ), ], [ ( 'dup', obj_id, ), ] )

        # Move parents
        for ( other_id, ) in rel2.select( [ 'parent', ],
                [ ( 'child', parent_id, ), ] ):

            rel2.delete( [ ( 'child', obj_id, ), ( 'parent', other_id, ), ] )

        rel2.delete( [ ( 'child', obj_id, ), ( 'parent', parent_id, ), ] )
        rel2.update( [ ( 'child', parent_id, ), ], [ ( 'child', obj_id, ), ] )

        # Move children
        for ( other_id, ) in rel2.select( [ 'child', ],
                [ ( 'parent', parent_id, ), ] ):

            rel2.delete( [ ( 'parent', obj_id, ), ( 'child', other_id, ), ] )

        rel2.delete( [ ( 'parent', obj_id, ), ( 'child', parent_id, ), ] )
        rel2.update( [ ( 'parent', parent_id, ), ], [ ( 'parent', obj_id, ), ] )

def upgrade_from_8_to_8_1( log, session ):

    log.info( 'Database upgrade from VER 8 -> VER 8.1' )

    dbi = session.get_table( 'dbi' )

    correct_linked_duplicates( session )

    dbi.update( [ ( 'ver', 8, ), ( 'rev', 1, ) ] )
    session.commit()
