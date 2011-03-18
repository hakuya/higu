import filemgmt
import os

from hash import calculate_details
from filemgmt import ResultIterator

DEFAULT_ENVIRON = os.path.join( os.environ['HOME'], '.higu' )
HIGURASHI_DB_NAME = 'hfdb.dat'
HIGURASHI_DATA_PATH = 'imgdat'

class File:

    def __init__( self, db, id ):

        self.db = db
        self.id = id

    def get_id( self ):

        return self.id

    def get_parent( self ):

        parent = self.db.db.get_mfl().get_parent( self.id )

        if( parent == None ):
            return None
        else:
            return File( self.db, parent )

    def set_parent( self, parent ):

        if( isinstance( parent, File ) ):
            parent = parent.id

        self.db.db.get_mfl().set_parent( self.id, parent )

    def set_duplicate_of( self, parent ):

        if( isinstance( parent, File ) ):
            parent = parent.id

        self.db.db.get_mfl().set_parent( self.id, parent, filemgmt.ORDER_DUPLICATE )

    def set_varient_of( self, parent ):

        if( isinstance( parent, File ) ):
            parent = parent.id

        self.db.db.get_mfl().set_parent( self.id, parent, filemgmt.ORDER_VARIENT )

    def is_duplicate( self ):

        return self.db.db.get_mfl().get_order( self.id ) == filemgmt.ORDER_DUPLICATE

    def is_varient( self ):

        return self.db.db.get_mfl().get_order( self.id ) == filemgmt.ORDER_VARIENT

    def child_iterator( self ):

        return ResultIterator( self.db.db.get_mfl().child_iterator( self.id ),
                lambda x: File( self.db, x ) )

    def get_name( self ):

        try:
            iter = self.get_names()
            name = iter.next()
            try:
                while 1:
                    iter.next()
            except StopIteration:
                return name
        except StopIteration:
            raise 'blah'
            p = self.get_path()
            if( p == None ):
                name = 'unknown'
            else:
                name = os.path.split( p )[-1]

    def get_names( self ):

        return self.db.db.get_naml().lookup_names( self.id )

    def get_length( self ):

        return self.db.db.get_mfl().details( self.id )[0]

    def get_hash( self ):

        return self.db.db.get_mfl().details( self.id )[3]

    def get_tags( self ):

        return self.db.db.get_tagl().lookup_tags( self.id )

    def tag( self, tag ):

        return self.db.db.get_tagl().tag( self.id, tag )

    def untag( self, tag ):

        return self.db.db.get_tagl().untag( self.id, tag )

    def get_path( self ):

        try:
            d = self.db._get_path_for_id( self.id )
            ls = os.listdir( d )
            ids = '%016x' % ( self.id )
        except OSError:
            return None

        for f in ls:
            try:
                if( f.index( ids ) == 0 ):
                    return os.path.join( d, f )
            except ValueError:
                pass

        return None

    def __eq__( self, o ):

        return self.db == o.db and self.id == o.id

class Database:

    def __init__( self, environ ):

        self.environ = environ

        if( not os.path.isdir( self.environ ) ):
            os.makedirs( self.environ )

        self.db = filemgmt.FileMgmtDb( os.path.join( environ, HIGURASHI_DB_NAME ) )

    def _get_path_for_id( self, id ):

        lv2 = (id >> 12) % 0xfff
        lv3 = (id >> 24) % 0xfff
        lv4 = id >> 36

        assert lv4 == 0

        return os.path.join( self.environ, HIGURASHI_DATA_PATH, '%03x' % ( lv3 ), \
                                                                '%03x' % ( lv2 ) )

    def _load_data( self, path, id ):

        tgt_path = self._get_path_for_id( id )
        if( not os.path.isdir( tgt_path ) ):
            os.makedirs( tgt_path )

        name = os.path.split( path )[-1]
        try:
            ext = name[name.rindex( '.' ):]
        except ValueError:
            ext = '.dat'

        tgt = os.path.join( tgt_path, '%016x%s' % ( id, ext ) )

        os.rename( path, tgt )

    def commit( self ):

        self.db.commit()

    def close( self ):

        self.db.close()

    def get_file_by_id( self, id ):

        return File( self, id )

    def lookup_files_by_details( self, len = None, crc32 = None, md5 = None, sha1 = None ):

        mfl = self.db.get_mfl()
        return ResultIterator( mfl.lookup( len, crc32, md5, sha1 ),
                lambda x: File( self, x ) )

    def lookup_files_by_name( self, name ):

        return [].__iter__()

    def lookup_files_by_tags( self, require, add = [], sub = [], strict = False ):

        q = self.db.get_tagl().restrict_ids( self.db.get_mfl().mfl, require, add, sub, strict )
        if( strict ):
            q = self.db.get_mfl().select_no_collection( q )        

        return ResultIterator( q.__iter__(), lambda x: File( self, x[0] ) )

    def lookup_files_by_tags_with_names( self, require, add = [], sub = [], strict = False ):

        q = self.db.get_tagl().restrict_ids( self.db.get_mfl().mfl, require, add, sub, strict )
        if( strict ):
            q = self.db.get_mfl().select_no_collection( q )        
        q = self.db.get_naml().lookup_names_by_query( q )

        class ResultWithNameIterator:

            def __init__( iself, iter ):

                iself.iter = iter

            def __iter__( iself ):

                return iself

            def next( iself ):

                id, name = iself.iter.next()
                f = File( self, id )
                if( name == None ):
                    name = f.get_name()
                return f, name

        return ResultWithNameIterator( q.__iter__() )

    def lookup_untagged_files( self ):

        mfl = self.db.get_mfl()
        tagl = self.db.get_tagl()
        
        all = mfl.lookup()
        tagged = [i for i in tagl.lookup_ids( [] )]

        class UntaggedIterator:

            def __init__( self, all_iter, tagged ):

                self.all_iter = all_iter
                self.tagged = tagged

            def next( self ):

                while( 1 ):
                    n = self.all_iter.next()
                    if( n not in self.tagged ):
                        return n

        untagged = [f for f in all if f not in tagged]

        return ResultIterator( UntaggedIterator( all, tagged ),
                lambda x: File( self, x ) )

    def all_files( self ):

        mfl = self.db.get_mfl()
        return ResultIterator( mfl.lookup(), lambda x: File( self, x ) )

    def all_tags( self ):

        tagl = self.db.get_tagl()
        return tagl.all_tags()

    def register_file( self, path ):

        name = os.path.split( path )[1]

        details = calculate_details( path )
        results = self.lookup_files_by_details( *details )

        mfl = self.db.get_mfl()
        naml = self.db.get_naml()

        try:
            id = results.next().get_id()
        except StopIteration:
            id = mfl.register( *details )

        naml.register( id, name )
        self.commit()

        f = File( self, id )
        if( f.get_path() == None ):
            self._load_data( path, id )

        return f

    def rename_tag( self, tag, new_name ):

        tagl = self.db.get_tagl()
        return tagl.rename_tag( tag, new_name )

def init_default():

    return Database( DEFAULT_ENVIRON )

def compare_details( a, b ):

    return long( a[0] ) == long( b[0] ) \
       and str( a[1] ) == str( b[1] ) \
       and str( a[2] ) == str( b[2] ) \
       and str( a[3] ) == str( b[3] )

# vim:sts=4:sw=4:et
