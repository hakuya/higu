import filemgmt
import os

from hash import calculate_details
from filemgmt import ResultIterator

DEFAULT_ENVIRON = os.path.join( os.environ['HOME'], '.higu' )
HIGURASHI_DB_NAME = 'hfdb.dat'
HIGURASHI_DATA_PATH = 'imgdat'

TYPE_FILE = filemgmt.TYPE_FILE
TYPE_ALBUM = filemgmt.TYPE_ALBUM

def make_unicode( s ):

    if( not isinstance( s, unicode ) ):
        return unicode( s, 'utf-8' )
    else:
        return s

class Album:

    def __init__( self, db, id ):

        self.db = db
        self.id = id

    def get_id( self ):

        return self.id

    def get_files( self ):

        return map( lambda x: File( self.db, x ),
                    self.db.db.get_rell().get_children( self.id, filemgmt.REL_CHILD ) )

    def add_file( self, f, order = None ):

        if( isinstance( f, File ) ):
            f = f.id

        self.db.db.get_rell().assign_parent( f, self.id, filemgmt.REL_CHILD, order )

    def get_tags( self ):

        return self.db.db.get_tagl().lookup_tags( self.id )

    def tag( self, tag ):

        return self.db.db.get_tagl().tag( self.id, tag )

    def untag( self, tag ):

        return self.db.db.get_tagl().untag( self.id, tag )

    def get_name( self ):

        try:
            return self.get_names().next()
        except StopIteration:
            return '%016x' % ( self.id )

    def get_names( self ):

        return self.db.db.get_naml().lookup_names( self.id )

    def register_name( self, name ):

        self.db.db.get_naml().register( self.id, make_unicode( name ) )

    def register_file( self, f, order = None ):

        pass

    def __eq__( self, o ):

        if( o == None ):
            return False
        if( not isinstance( o, Album ) ):
            return False
        return self.db == o.db and self.id == o.id

class File:

    def __init__( self, db, id ):

        self.db = db
        self.id = id

    def get_id( self ):

        return self.id

    def get_parents( self ):

        return self.db.db.get_rell().get_parents( self.id, filemgmt.REL_CHILD )

    def get_albums( self ):

        parents = self.get_parents()
        albums = []

        for parent in parents:
            if( self.db.db.get_objl().get_type( parent ) == filemgmt.TYPE_ALBUM ):
                albums.append( parent )

        return map( lambda x: Album( self.db, x ), albums )

    def get_duplicates( self ):

        return map( lambda x: File( self.db, x ),
                    self.db.db.get_rell().get_children( self.id, filemgmt.REL_DUPLICATE ) )

    def get_variants( self ):

        return map( lambda x: File( self.db, x ),
                    self.db.db.get_rell().get_children( self.id, filemgmt.REL_VARIANT ) )

    def get_duplicates_of( self ):

        return map( lambda x: File( self.db, x ),
                    self.db.db.get_rell().get_parents( self.id, filemgmt.REL_DUPLICATE ) )

    def get_variants_of( self ):

        return map( lambda x: File( self.db, x ),
                    self.db.db.get_rell().get_parents( self.id, filemgmt.REL_VARIANT ) )

    def set_duplicate_of( self, parent ):

        if( isinstance( parent, File ) ):
            parent = parent.id

        self.db.db.get_rell().assign_parent( self.id, parent, filemgmt.REL_DUPLICATE )

    def set_varient_of( self, parent ):

        if( isinstance( parent, File ) ):
            parent = parent.id

        self.db.db.get_rell().assign_parent( self.id, parent, filemgmt.REL_VARIANT )

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
            p = self.get_path()
            if( p == None ):
                return 'unknown'
            else:
                return os.path.split( p )[-1]

    def get_names( self ):

        return self.db.db.get_naml().lookup_names( self.id )

    def get_length( self ):

        return self.db.db.get_fchk().details( self.id )[0]

    def get_hash( self ):

        return self.db.db.get_fchk().details( self.id )[3]

    def get_tags( self ):

        return self.db.db.get_tagl().lookup_tags( self.id )

    def tag( self, tag ):

        return self.db.db.get_tagl().tag( self.id, make_unicode( tag ) )

    def untag( self, tag ):

        return self.db.db.get_tagl().untag( self.id, make_unicode( tag ) )

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

        if( o == None ):
            return False
        if( not isinstance( o, File ) ):
            return False
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

    def create_album( self ):

        id = self.db.get_objl().register( filemgmt.TYPE_ALBUM )
        return Album( self, id )

    def get_object_by_id( self, id ):

        type = self.db.get_objl().get_type( id ) 

        if( type == TYPE_FILE ):
            return File( self, id )
        elif( type == TYPE_ALBUM ):
            return Album( self, id )
        else:
            return None

    def lookup_files_by_details( self, len = None, crc32 = None, md5 = None, sha1 = None ):

        fchk = self.db.get_fchk()
        return ResultIterator( fchk.lookup( len, crc32, md5, sha1 ),
                lambda x: File( self, x ) )

    def lookup_files_by_name( self, name ):

        return [].__iter__()

    def lookup_files_by_tags( self, require, add = [], sub = [], strict = False ):

        q = self.db.get_tagl().restrict_ids( self.db.get_objl().objl, require, add, sub, strict )
        if( strict ):
            q = self.db.get_rell().select_no_parent( q )        

        return ResultIterator( q.__iter__(), lambda x: File( self, x[0] ) )

    def lookup_objects_by_tags_with_names( self, require, add = [], sub = [], strict = False, type = TYPE_FILE ):

        q = self.db.get_tagl().restrict_ids( self.db.get_objl().objl, require, add, sub, strict )
        q = self.db.get_objl().restrict_by_type( q, type )
        if( strict ):
            q = self.db.get_rell().select_no_parent( q )        

        q = self.db.get_naml().lookup_names_by_query( q )

        if( type == None ):
            q = self.db.get_objl().append_type( q )

        class ResultWithNameIterator:

            def __init__( iself, iter ):

                iself.iter = iter

            def __iter__( iself ):

                return iself

            def next( iself ):

                id, name = iself.iter.next()
                if( type == TYPE_FILE ):
                    f = File( self, id )
                else:
                    f = Album( self, id )
                if( name == None ):
                    name = f.get_name()
                return f, name

        return ResultWithNameIterator( q.__iter__() )

    def lookup_untagged_files( self ):

        fchk = self.db.get_fchk()
        tagl = self.db.get_tagl()
        
        all = fchk.lookup()
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

        fchk = self.db.get_fchk()
        return ResultIterator( fchk.lookup(), lambda x: File( self, x ) )

    def all_tags( self ):

        tagl = self.db.get_tagl()
        return tagl.all_tags()

    def register_file( self, path, add_name = True ):

        name = os.path.split( path )[1]

        details = calculate_details( path )
        results = self.lookup_files_by_details( *details )

        objl = self.db.get_objl()
        fchk = self.db.get_fchk()
        naml = self.db.get_naml()

        try:
            id = results.next().get_id()
        except StopIteration:
            id = objl.register( filemgmt.TYPE_FILE )
            fchk.register( id, *details )

        if( add_name ):
            naml.register( id, name )
        self.commit()

        f = File( self, id )
        if( f.get_path() == None ):
            self._load_data( path, id )

        return f

    def delete_object( self, obj ):

        if( isinstance( obj, File ) ):
            p = obj.get_path()
        else:
            p = None

        self.db.get_naml().unregister( obj.get_id() )
        self.db.get_tagl().unregister( obj.get_id() )
        self.db.get_rell().unregister( obj.get_id() )
        self.db.get_fchk().unregister( obj.get_id() )
        self.db.get_objl().unregister( obj.get_id() )

        if( p != None ):
            os.remove( p )

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
