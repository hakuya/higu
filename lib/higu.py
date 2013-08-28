import filemgmt
import os
import shutil

import db as dblib

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

class Obj:

    def __init__( self, db, id ):

        self.db = db
        self.id = id

    def get_id( self ):

        return self.id

    def get_tags( self ):

        return map( lambda x: Tag( self.db, x ), self.db.db.get_rell().get_parents( self.id, filemgmt.REL_CLASS ) )

    def assign( self, group ):

        if( isinstance( group, Tag ) ):
            return self.db.db.get_rell().assign_parent( self.id, group.id, filemgmt.REL_CLASS )
        elif( isinstance( group, Album ) ):
            return self.db.db.get_rell().assign_parent( self.id, group.id, filemgmt.REL_CHILD )

        assert False

    def unassign( self, group ):

        self.db.db.get_rell().clear_parent( self.id, group.id )
        
    def get_name( self ):

        return self.db.db.get_objl().get_name( self.id )

    def set_name( self, name ):

        name = make_unicode( name )
        self.db.db.get_objl().set_name( self.id, name )

    def get_repr( self ):

        name = self.get_name()
        if( name is not None ):
            return name
        else:
            return '%016x' % ( self.id )

    def get_names( self ):

        names = []
        names.append( self.get_repr() )
        for value in self.db.db.get_meta().get_values( self.id, 'altname' ):
            names.append( value )
        return names

    def register_name( self, name ):

        name = make_unicode( name )
        if( self.get_name() is None ):
            self.set_name( name )
        else:
            self.db.db.get_meta().set_single( self.id, 'altname', name )

    def __hash__( self ):

        return self.id

    def __eq__( self, o ):

        if( o == None ):
            return False
        if( not isinstance( o, self.__class__ ) ):
            return False
        return self.db == o.db and self.id == o.id

class Group( Obj ):

    def __init__( self, db, id ):

        Obj.__init__( self, db, id )

    def get_files( self ):

        return map( lambda x: File( self.db, x ),
                    self.db.db.get_rell().get_children( self.id, filemgmt.REL_CHILD ) )

class Tag( Group ):

    def __init__( self, db, id ):

        Group.__init__( self, db, id )

class Album( Group ):

    def __init__( self, db, id ):

        Group.__init__( self, db, id )

class File( Obj ):

    def __init__( self, db, id ):

        Obj.__init__( self, db, id )

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

    def get_repr( self ):

        name = self.get_name()
        if( name is not None ):
            return name
        else:
            p = self.get_path()
            if( p == None ):
                return 'unknown'
            else:
                return os.path.split( p )[-1]

    def get_length( self ):

        return self.db.db.get_fchk().details( self.id )[0]

    def get_hash( self ):

        return self.db.db.get_fchk().details( self.id )[3]

    def get_path( self ):

        try:
            d = self.db._get_path_for_id( self.id )
            ls = os.listdir( d )
            ids = '%016x.' % ( self.id )
        except OSError:
            return None

        for f in ls:
            try:
                if( f.index( ids ) == 0 ):
                    return os.path.join( d, f )
            except ValueError:
                pass

        return None

    def get_thumb( self, exp ):

        from PIL import Image

        t = self.db._get_fname_base( self.id ) + '_%02d.jpg' % ( exp, )
        if( os.path.isfile( t ) ):
            return t

        f = self.get_path()
        if( f is None ):
            return None

        i = Image.open( f )
        s = 2**exp
        w, h = i.size

        if( w < s and h < s ):
            return f

        if( w > h ):
            tw = s
            th = h * s / w
        else:
            tw = w * s / h
            th = s

        r = i.resize( ( tw, th, ), Image.ANTIALIAS )
        r.save( t )
        return t

    def make_thumb( self, exp ):

        from PIL import Image

        i = Image.open( self.get_path() )
        s = 2**exp
        w, h = i.size

        if( w < s and h < s ):
            return

        if( w > h ):
            tw = s
            ht = h * s / w
        else:
            tw = w * s / h
            th = s

        r = i.resize( ( tw, th, ), Image.ANTIALIAS )
        
        t = self.db._get_fname_base( self.id ) + '_%02d.jpg' % ( exp, )
        if( os.path.isfile( t ) ):
            os.remove( t )
        r.save( t )

    def purge_thumbs( self ):

        from glob import glob
    
        fs = glob( self.db._get_fname_base( self.id ) + '_*.jpg' )
        for f in fs:
            os.remove( f )

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

    def _get_fname_base( self, id ):

        fname = '%016x' % ( id, )
        return os.path.join( self._get_path_for_id( id ), fname )

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

        shutil.move( path, tgt )

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

    def all_albums( self ):

        objl = self.db.get_objl().objl
        rell = self.db.get_rell().rell
        albums = dblib.Query( dblib.Selection( [ 'id' ], [ ( 'type', TYPE_ALBUM, ) ], order = 'RANDOM()' ), objl )
        return albums.__iter__()

    def all_albums_or_free_files( self ):

        objl = self.db.get_objl().objl
        rell = self.db.get_rell().rell
        albums = dblib.Query( dblib.Selection( [ 'id' ], [ ( 'type', TYPE_ALBUM, ) ] ), objl )
        albums_n_files = dblib.Query( dblib.Selection( [ 'id' ], [ dblib.OrOperator( [ ( 'type', TYPE_ALBUM, ), ( 'type', TYPE_FILE, ) ] ) ] ), objl )
        files_with_alb = dblib.Query( dblib.Selection( [ 'a.id' ] ), dblib.InnerJoinOperator( rell, albums, 'a', 'b', 'a.parent', 'b.id' ) )
        invalidate = dblib.InOperator( 'id', files_with_alb, True )
        files_with_noalb = dblib.Query( dblib.Selection( [ 'id' ], [ invalidate ], order = 'RANDOM()' ), albums_n_files )
        return files_with_noalb.__iter__()

    def unowned_files( self ):

        objl = self.db.get_objl().objl
        rell = self.db.get_rell().rell

        files = dblib.Query( dblib.Selection( [ 'id' ], [ ( 'type', TYPE_FILE, ) ] ), objl )
        owned_objects = dblib.Query( dblib.Selection( [ 'id' ] ), rell )
        invalidate = dblib.InOperator( 'id', owned_objects, True )
        files_with_noown = dblib.Query( dblib.Selection( [ 'id' ], [ invalidate ], order = 'RANDOM()' ), files )
        return files_with_noown.__iter__()

    def lookup_files_by_details( self, len = None, crc32 = None, md5 = None, sha1 = None ):

        fchk = self.db.get_fchk()
        return ResultIterator( fchk.lookup( len, crc32, md5, sha1 ),
                lambda x: File( self, x ) )

    def lookup_ids_by_tags( self, require, add = [], sub = [], strict = False, type = None, random_order = False ):

        add = map( lambda x: x.id, add )
        sub = map( lambda x: x.id, sub )
        require = map( lambda x: x.id, require )

        q = self.db.get_rell().restrict_ids( self.db.get_objl().objl, require, add, sub, random_order )
        if( type is not None ):
            q = self.db.get_objl().restrict_by_type( q, type )
        if( strict ):
            q = self.db.get_rell().select_no_parent( q )        

        return q.__iter__()

    def lookup_objects_by_tags_with_names( self, require, add = [], sub = [], strict = False, type = TYPE_FILE ):

        add = map( lambda x: x.id, add )
        sub = map( lambda x: x.id, sub )
        require = map( lambda x: x.id, require )

        q = self.db.get_rell().restrict_ids( self.db.get_objl().objl, require, add, sub, strict )
        q = self.db.get_objl().restrict_by_type( q, type )
        if( strict ):
            q = self.db.get_rell().select_no_parent( q )        

        q = self.db.get_objl().lookup_names_by_query( q )

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
                    name = f.get_repr()
                return f, name

        return ResultWithNameIterator( q.__iter__() )

    def lookup_untagged_files( self ):

        fchk = self.db.get_fchk()
        rell = self.db.get_rell()

        return ResultIterator( rell.select_no_parent( fchk.fchk ).__iter__(),
                lambda x: File( self, x ) )

    def all_files( self ):

        fchk = self.db.get_fchk()
        return ResultIterator( fchk.lookup(), lambda x: File( self, x ) )

    def all_tags( self ):

        return [Tag( self, c )
                for c in self.db.get_objl().lookup( filemgmt.TYPE_CLASSIFIER,
                sortby = "name" )]

    def get_tag( self, name ):

        c = self.db.get_objl().lookup( filemgmt.TYPE_CLASSIFIER, name ).next()
        return Tag( self, c )

    def make_tag( self, name ):

        try:
            return self.get_tag( name )
        except StopIteration:
            c = self.db.get_objl().register( filemgmt.TYPE_CLASSIFIER, name )
            return Tag( self, c )

    def rename_tag( self, tag, new_name ):

        c = self.get_tag( tag )

        try:
            d = self.get_tag( new_name )
            self.db.get_rell().transfer_parent( c.id, d.id )
            self.delete_object( c )

        except StopIteration:
            c.set_name( new_name )

    def register_file( self, path, add_name = True ):

        name = os.path.split( path )[1]

        details = calculate_details( path )
        results = self.lookup_files_by_details( *details )

        objl = self.db.get_objl()
        fchk = self.db.get_fchk()
        meta = self.db.get_meta()

        try:
            id = results.next().get_id()
        except StopIteration:
            id = objl.register( filemgmt.TYPE_FILE )
            fchk.register( id, *details )

        if( add_name ):
            ename = objl.get_name( id )
            if( ename is None ):
                objl.set_name( id, name )
            elif( ename != name ):
                meta.set_single( id, 'altname', name )
        self.commit()

        f = File( self, id )
        if( f.get_path() == None ):
            self._load_data( path, id )

        return f

    def recover_file( self, path ):

        name = os.path.split( path )[1]

        details = calculate_details( path )
        results = self.lookup_files_by_details( *details )

        objl = self.db.get_objl()
        fchk = self.db.get_fchk()
        meta = self.db.get_meta()

        try:
            id = results.next().get_id()
        except StopIteration:
            return False

        self._load_data( path, id )
        return True

    def delete_object( self, obj ):

        if( isinstance( obj, File ) ):
            obj.purge_thumbs()
            p = obj.get_path()
        else:
            p = None

        self.db.get_meta().unregister( obj.get_id() )
        self.db.get_rell().unregister( obj.get_id() )
        self.db.get_fchk().unregister( obj.get_id() )
        self.db.get_objl().unregister( obj.get_id() )

        if( p != None ):
            os.remove( p )

def init_default():

    return Database( DEFAULT_ENVIRON )

def compare_details( a, b ):

    return long( a[0] ) == long( b[0] ) \
       and str( a[1] ) == str( b[1] ) \
       and str( a[2] ) == str( b[2] ) \
       and str( a[3] ) == str( b[3] )

# vim:sts=4:sw=4:et
