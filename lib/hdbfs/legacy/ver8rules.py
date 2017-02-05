import hdbfs.db

TYPE_NILL       = 0
TYPE_FILE       = 1000
TYPE_FILE_DUP   = 1001
TYPE_FILE_VAR   = 1002
TYPE_GROUP      = 2000
TYPE_ALBUM      = 2001
TYPE_CLASSIFIER = 2002

class LinkedDuplicateIterator:

    def __init__( self, session ):

        self.__session = session

        self.__iter = self.__session.execute(
                'SELECT id FROM objl WHERE type = :type',
                { 'type' : TYPE_FILE_DUP, } ).__iter__()

    def __iter__( self ):

        return self

    def next( self ):

        while True:
            ( obj_id, ) = self.__iter.next()

            try:
                self.__session.execute( 'SELECT id FROM objl WHERE dup = :obj',
                                        { 'obj' : obj_id } ).__iter__().next()
                return obj_id
            except StopIteration:
                pass

            try:
                self.__session.execute( 'SELECT parent FROM rel2 WHERE child = :obj',
                                        { 'obj' : obj_id } ).__iter__().next()
                return obj_id
            except StopIteration:
                pass

            try:
                self.__session.execute( 'SELECT child FROM rel2 WHERE parent = :obj',
                                        { 'obj' : obj_id } ).__iter__().next()
                return obj_id
            except StopIteration:
                pass

def determine_duplicate_parent( session, obj_id ):

    result = session.execute( 'SELECT type, dup FROM objl WHERE id = :obj',
                              { 'obj' : obj_id } ).first()
    if( result is None ):
        return None

    if( result['type'] != TYPE_FILE_DUP ):
        return obj_id
    else:
        return determine_duplicate_parent( session, result['dup'] )

def correct_linked_duplicates( session ):

    for obj_id in LinkedDuplicateIterator( session ):
        parent_id = determine_duplicate_parent( session, obj_id )

        mapping = { 'obj' : obj_id, 'par' : parent_id }

        # Move all dup/vars
        session.execute( 'UPDATE objl SET dup = :par WHERE dup = :obj',
                         mapping )

        # Move parents
        for result in session.execute( 'SELECT parent FROM rel2 WHERE child = :par',
                                       mapping ):

            session.execute( 'DELETE FROM rel2 WHERE child = :obj and parent = :oth',
                             { 'obj' : obj_id,
                               'oth' : result['parent'] } )

        session.execute( 'DELETE FROM rel2 WHERE child = :obj and parent = :par',
                         mapping )
        session.execute( 'UPDATE rel2 SET child = :par WHERE child = :obj',
                         mapping )

        # Move children
        for result in session.execute( 'SELECT child FROM rel2 WHERE parent = :par',
                                       mapping ):

            session.execute( 'DELETE FROM rel2 WHERE parent = :obj and child = :oth',
                             { 'obj' : obj_id,
                               'oth' : result['child'] } )

        session.execute( 'DELETE FROM rel2 WHERE parent = :obj and child = :par',
                         mapping )
        session.execute( 'UPDATE rel2 SET parent = :par WHERE parent = :obj',
                         mapping )

def upgrade_from_8_to_8_1( log, session ):

    log.info( 'Database upgrade from VER 8 -> VER 8.1' )

    correct_linked_duplicates( session )

    session.execute( 'UPDATE dbi SET ver = 8, rev = 1' )
    return 8, 1

def upgrade_from_8_1_to_9( log, session ):

    log.info( 'Database upgrade from VER 8.1 -> VER 9' )

    session.execute( 'DROP TABLE dbi' )
    return 9, 0
