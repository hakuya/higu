import model
import os
import shutil
import sys
import config

from hash import calculate_details

VERSION = 1
REVISION = 0

DEFAULT_ENVIRON = os.path.join( os.environ['HOME'], '.higu' )
HIGURASHI_DB_NAME = 'hfdb.dat'
HIGURASHI_DATA_PATH = 'imgdat'

TYPE_FILE       = model.TYPE_FILE
TYPE_FILE_DUP   = model.TYPE_FILE_DUP
TYPE_FILE_VAR   = model.TYPE_FILE_VAR
TYPE_GROUP      = model.TYPE_GROUP
TYPE_ALBUM      = model.TYPE_ALBUM
TYPE_CLASSIFIER = model.TYPE_CLASSIFIER

def make_unicode( s ):

    if( not isinstance( s, unicode ) ):
        return unicode( s, 'utf-8' )
    else:
        return s

def model_obj_to_higu_obj( db, obj ):

    if( obj.type == TYPE_FILE 
     or obj.type == TYPE_FILE_DUP
     or obj.type == TYPE_FILE_VAR ):
        return File( db, obj )
    elif( obj.type == TYPE_ALBUM ):
        return Album( db, obj )
    elif( obj.type == TYPE_CLASSIFIER ):
        return Tag( db, obj )
    else:
        assert False

class Obj:

    def __init__( self, db, obj ):

        self.db = db
        self.obj = obj

    def get_id( self ):

        return self.obj.id

    def get_type( self ):

        return self.obj.type

    def get_tags( self ):

        tag_objs = [ obj for obj in self.obj.parents if obj.type == TYPE_CLASSIFIER ]
        return map( lambda x: Tag( self.db, x ), tag_objs )

    def assign( self, group, order = None ):

        rel = self.db.session.query( model.Relation ) \
                .filter( model.Relation.parent == group.obj.id ) \
                .filter( model.Relation.child == self.obj.id ).first()
        if( rel is not None ):
            rel.sort = order
            return
        rel = model.Relation( order )
        rel.parent_obj = group.obj
        rel.child_obj = self.obj

    def unassign( self, group ):

        rel = self.db.session.query( model.Relation ) \
                .filter( model.Relation.parent == group.obj.id ) \
                .filter( model.Relation.child == self.obj.id ).first()

        if( rel is not None ):
            self.db.session.delete( rel )

    def reorder( self, group, order = None ):

        rel = self.db.session.query( model.Relation ) \
                .filter( model.Relation.parent == group.obj.id ) \
                .filter( model.Relation.child == self.obj.id ).first()
        if( rel is None ):
            raise ValueError, str( self ) + ' is not in ' + str( group )
        rel.sort = order

    def get_order( self, group ):

        rel = self.db.session.query( model.Relation ) \
                .filter( model.Relation.parent == group.obj.id ) \
                .filter( model.Relation.child == self.obj.id ).first()
        if( rel is None ):
            raise ValueError, str( self ) + ' is not in ' + str( group )
        return rel.sort
        
    def get_name( self ):

        return self.obj.name

    def set_name( self, name, saveold = False ):

        oname = self.obj.name
        self.obj.name = name

        if( saveold and oname is not None ):
            self.add_name( oname )

    def add_name( self, name ):

        name = make_unicode( name )

        if( self.get_name() is None ):
            self.set_name( name )
        else:
            try:
                xnames = self.obj['altname']

                if( len( xnames ) == 0 ):
                    self.obj['altname'] = name
                else:
                    xnames = xnames.split( ':' )
                    if( name not in xnames ):
                        xnames.append( name )
                        xnames = ':'.join( xnames )
                        self.obj['altname'] = xnames

            except KeyError:
                self.obj['altname'] = name

    def get_names( self ):

        names = [ self.get_repr() ]

        try:
            xnames = self.obj['altname']
            names.extend( xnames.split( ':' ) )
        except KeyError:
            pass

        return names

    def get_repr( self ):

        name = self.get_name()
        if( name is not None ):
            return name
        else:
            return '%016x' % ( self.obj.id )

    def __getitem__( self, key ):

        return self.obj[key]

    def __setitem__( self, key, value ):

        self.obj[key] = value

    def __hash__( self ):

        return self.id

    def __eq__( self, o ):

        if( o == None ):
            return False
        if( not isinstance( o, self.__class__ ) ):
            return False
        return self.db == o.db and self.obj == o.obj

class Group( Obj ):

    def __init__( self, db, obj ):

        Obj.__init__( self, db, obj )

    def is_ordered( self ):

        return False

    def get_files( self ):

        objs = [ obj for obj in self.obj.children if( obj.type == TYPE_FILE or obj.type == TYPE_FILE_DUP or obj.type == TYPE_FILE_VAR ) ]
        return map( lambda x: File( self.db, x ), objs )

class OrderedGroup( Group ):

    def __init__( self, db, obj ):

        Group.__init__( self, db, obj )

    def is_ordered( self ):

        #TODO: check if ordered
        return True

    def clear_order( self ):

        all_objs = self.get_files()

        for child in all_objs:
            child.reorder( self )

    def set_order( self, children ):

        all_objs = self.get_files()
        
        for child in enumerate( children ):
            assert( child[1] in all_objs )
            all_objs.remove( child[1] )
            
            child[1].reorder( self, child[0] )

        offset = len( children )

        for child in enumerate( all_objs ):
            child[1].reorder( self, offset + child[0] )

class Tag( Group ):

    def __init__( self, db, obj ):

        Group.__init__( self, db, obj )

class Album( OrderedGroup ):

    def __init__( self, db, obj ):

        OrderedGroup.__init__( self, db, obj )

class File( Obj ):

    def __init__( self, db, obj ):

        Obj.__init__( self, db, obj )

    def is_duplicate( self ):

        return self.obj.type == TYPE_FILE_DUP

    def is_variant( self ):

        return self.obj.type == TYPE_FILE_VAR

    def get_albums( self ):

        objs = [ obj for obj in self.obj.parents if obj.type == TYPE_ALBUM ]
        return map( lambda x: Album( self.db, x ), objs )

    def get_duplicates( self ):

        objs = [ obj for obj in self.obj.similars if obj.type == TYPE_FILE_DUP ]
        return map( lambda x: File( self.db, x ), objs )

    def get_variants( self ):

        objs = [ obj for obj in self.obj.similars if obj.type == TYPE_FILE_VAR ]
        return map( lambda x: File( self.db, x ), objs )

    def get_similar_to( self ):

        if( self.obj.similar_to is None ):
            return None
        else:
            return File( self.db, self.obj.similar_to )

    def set_duplicate_of( self, parent ):

        assert( isinstance( parent, File ) )

        self.obj.type = TYPE_FILE_DUP
        self.obj.similar_to = parent.obj

    def set_varient_of( self, parent ):

        assert( isinstance( parent, File ) )

        self.obj.type = TYPE_FILE_VAR
        self.obj.similar_to = parent.obj

    def clear_duplication( self ):

        self.obj.type = TYPE_FILE
        self.obj.similar_to = None

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

        return self.obj.fchk.len

    def get_hash( self ):

        return self.obj.fchk.sha1

    def get_path( self ):

        return self.db.imgdb.get_image( self.obj.id )

    def get_thumb( self, exp ):

        return self.db.imgdb.get_thumb( self.obj.id, exp )

class ModelObjToHiguObjIterator:

    def __init__( self, db, iterable ):

        self.db = db
        self.it = iterable.__iter__()

    def __iter__( self ):

        return ModelObjToHiguObjIterator( self.db, self.it )

    def next( self ):

        return model_obj_to_higu_obj( self.db, self.it.next() )

class ImageDatabase:

    def __init__( self ):

        self.data_path = os.path.join(
                config.config().get_path( 'library' ),
                HIGURASHI_DATA_PATH )

        self.tmp_path = os.path.join( self.data_path, 'tmp' )
        self.to_commit = []

    def commit( self, commit_on_finish = None ):

        completion = 0

        try:
            for t in self.to_commit:
                shutil.move( t[0], t[1] )
                completion += 1

            if( commit_on_finish is not None ):
                commit_on_finish()

            # Comitted
            self.to_commit = []
        except:
            # Something went wrong, rollback
            for t in self.to_commit[:completion]:
                shutil.move( t[1], t[0] )

            # Sometimes move() seems to leave files behind
            for t in self.to_commit:
                try:
                    if( os.path.isfile( t[1] ) ):
                        os.remove( t[1] )
                except:
                    pass

            raise

    def rollback( self ):

        self.to_commit = []

    def get_dir_for_id( self, id ):

        lv2 = (id >> 12) % 0xfff
        lv3 = (id >> 24) % 0xfff
        lv4 = id >> 36

        assert lv4 == 0

        return os.path.join( self.data_path, '%03x' % ( lv3 ),
                                             '%03x' % ( lv2 ) )

    def get_fname_base( self, id ):

        fname = '%016x' % ( id, )
        return os.path.join( self.get_dir_for_id( id ), fname )

    def load_data( self, path, id ):

        tgt_path = self.get_dir_for_id( id )
        if( not os.path.isdir( tgt_path ) ):
            os.makedirs( tgt_path )

        name = os.path.split( path )[-1]
        try:
            ext = name[name.rindex( '.' ):]
        except ValueError:
            ext = '.dat'

        tgt = os.path.join( tgt_path, '%016x%s' % ( id, ext ) )
        self.to_commit.append( ( path, tgt, ) )

    def get_image( self, id ):

        try:
            d = self.get_dir_for_id( id )
            ls = os.listdir( d )
            ids = '%016x.' % ( id )
        except OSError:
            return None

        for f in ls:
            try:
                if( f.index( ids ) == 0 ):
                    return os.path.join( d, f )
            except ValueError:
                pass

        return None

    def get_thumb( self, id, exp ):

        from PIL import Image

        t = self.get_fname_base( id ) + '_%02d.jpg' % ( exp, )
        if( os.path.isfile( t ) ):
            return t

        f = self.get_image( id )
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

    def make_thumb( self, id, exp ):

        from PIL import Image

        i = Image.open( self.get_image( id ) )
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
        
        t = self.get_fname_base( id ) + '_%02d.jpg' % ( exp, )
        if( os.path.isfile( t ) ):
            os.remove( t )
        r.save( t )

    def purge_thumbs( self, id ):

        from glob import glob
    
        fs = glob( self.db.get_fname_base( id ) + '_*.jpg' )
        for f in fs:
            os.remove( f )

class Database:

    def __init__( self ):

        self.session = model.Session()
        self.imgdb = ImageDatabase()

    def commit( self ):

        self.imgdb.commit( self.session.commit )

    def rollback( self ):

        self.imgdb.rollback()
        self.session.rollback()

    def close( self ):

        self.session.close()

    def create_album( self ):

        album = model.Object( TYPE_ALBUM )
        self.session.add( album )
        return model_obj_to_higu_obj( self, album )

    def get_object_by_id( self, id ):

        obj = self.session.query( model.Object ).filter( model.Object.id == id ).first()
        if( obj is None ):
            return None

        return model_obj_to_higu_obj( self, obj )

    def all_albums_or_free_files( self ):

        files = self.session.query( model.Object.id ) \
                .filter( model.Object.type == TYPE_FILE )
        albums = self.session.query( model.Object.id ) \
                .filter( model.Object.type == TYPE_ALBUM )
        all_children = self.session.query( model.Relation.child ) \
                .filter( model.Relation.parent.in_( albums ) )
        free_files = files.filter( ~model.Object.id.in_( all_children ) )

        select_ids = free_files.union( albums )

        return ModelObjToHiguObjIterator( self, 
                self.session.query( model.Object )
                    .filter( model.Object.id.in_( select_ids ) )
                    .order_by( 'RANDOM()' ) )

    def unowned_files( self ):

        from sqlalchemy import or_

        all_children = self.session.query( model.Relation.child )
        return ModelObjToHiguObjIterator( self,
                self.session.query( model.Object )
                    .filter( or_( model.Object.type == TYPE_FILE, model.Object.type == TYPE_ALBUM ) )
                    .filter( ~model.Object.id.in_( all_children ) )
                    .order_by( 'RANDOM()' ) )

    def lookup_files_by_details( self, len = None, crc32 = None, md5 = None, sha1 = None ):

        q = self.session.query( model.FileChecksum.id )
        if( len is not None ):
            q = q.filter( model.FileChecksum.len == len )
        if( crc32 is not None ):
            q = q.filter( model.FileChecksum.crc32 == crc32 )
        if( md5 is not None ):
            q = q.filter( model.FileChecksum.md5 == md5 )
        if( sha1 is not None ):
            q = q.filter( model.FileChecksum.sha1 == sha1 )

        objs = self.session.query( model.Object ).filter(
                model.Object.id.in_( q ) )
        return ModelObjToHiguObjIterator( self, objs )

    def lookup_ids_by_tags( self, require, add = [], sub = [], strict = False, type = None, random_order = False ):

        if( len( add ) > 0 ):
            add_q = map( lambda x: self.session.query( model.Relation.child ) \
                    .filter( model.Relation.parent == x.obj.id ), add )
            add_q = add_q[0].union( *add_q[1:] )
        else:
            add_q = None

        if( len( sub ) > 0 ):
            sub_q = map( lambda x: self.session.query( model.Relation.child ) \
                    .filter( model.Relation.parent == x.obj.id ), sub )
            sub_q = sub_q[0].union( *sub_q[1:] )
        else:
            sub_q = None

        if( len( require ) > 0 ):
            req_q = map( lambda x: self.session.query( model.Relation.child ) \
                    .filter( model.Relation.parent == x.obj.id ), require )
            req_q = req_q[0].intersect( *req_q[1:] )
        else:
            req_q = None

        if( req_q is not None ):
            q = req_q

            if( add_q is not None ):
                q = q.union( add_q )
        else:
            q = add_q

        if( sub_q is not None ):
            q = q.except_( sub_q )

        query = self.session.query( model.Object ) \
                    .filter( model.Object.id.in_( q ) )
        if( random_order ):
            query = query.order_by( 'RANDOM()' )

        return ModelObjToHiguObjIterator( self, query ) 

    def lookup_untagged_files( self ):

        return self.unowned_files()

    def all_tags( self ):

        objs = self.session.query( model.Object ) \
                .filter( model.Object.type == TYPE_CLASSIFIER ) \
                .order_by( model.Object.name )

        return ModelObjToHiguObjIterator( self, objs )

    def get_tag( self, name ):

        obj = self.session.query( model.Object ) \
                .filter( model.Object.type == TYPE_CLASSIFIER ) \
                .filter( model.Object.name == name ).first()
        if( obj is None ):
            raise KeyError, 'No such tag "%s"' % ( name )

        return model_obj_to_higu_obj( self, obj )

    def make_tag( self, name ):

        try:
            return self.get_tag( name )
        except KeyError:
            obj = model.Object( TYPE_CLASSIFIER, name )
            self.session.add( obj )
            return model_obj_to_higu_obj( self, obj )

    def delete_tag( self, tag ):

        tag = self.get_tag( tag )
        self.delete_object( tag )

    def move_tag( self, tag, target ):

        c = self.get_tag( tag ).obj

        try:
            d = self.get_tag( target ).obj
            self.session.query( model.Relation ).filter( model.Relation.parent == c.id ).update( { 'parent' : d.id } )
            self.session.delete( c )

        except KeyError:
            c.name = target

    def copy_tag( self, tag, target ):

        c = self.get_tag( tag ).obj

        try:
            d = self.get_tag( target ).obj
        except KeyError:
            d = model.Object( TYPE_CLASSIFIER, target )
            self.session.add( d )

        for rel in c.child_rel:
            rel_copy = model.Relation( rel.sort )
            rel_copy.parent_obj = d
            rel_copy.child_obj = rel.child_obj

    def register_file( self, path, add_name = True ):

        name = os.path.split( path )[1].decode( sys.getfilesystemencoding() )
        details = calculate_details( path )

        try:
            results = self.lookup_files_by_details( *details )
            f = results.next()
        except StopIteration:
            obj = model.Object( TYPE_FILE )
            self.session.add( obj )
            fchk = model.FileChecksum( obj, *details )
            self.session.add( fchk )
            f = File( self, obj )
            self.session.flush()

        id = f.get_id()

        if( add_name ):
            ename = f.get_name()
            if( ename is None ):
                f.set_name( name )
            elif( ename != name ):
                f.add_name( name )

        if( f.get_path() is None ):
            self.imgdb.load_data( path, id )

        return f

    def recover_file( self, path ):

        name = os.path.split( path )[1]

        details = calculate_details( path )
        results = self.lookup_files_by_details( *details )

        try:
            id = results.next().get_id()
        except StopIteration:
            return False

        self.imgdb.load_data( path, id )
        return True

    def delete_object( self, obj ):

        if( isinstance( obj, File ) ):
            obj.purge_thumbs()
            p = obj.get_path()
        else:
            p = None

        id = obj.get_id()

        # Clear out similar to
        objs = [ o for o in obj.obj.similars ]
        for o in objs:
            if( o.type == TYPE_FILE_DUP or o.type == TYPE_FILE_VAR ):
                o.type = TYPE_FILE
            o.similar_to = None

        self.session.query( model.Metadata ) \
                .filter( model.Metadata.id == id ).delete()
        self.session.query( model.Relation ) \
                .filter( model.Relation.parent == id ).delete()
        self.session.query( model.Relation ) \
                .filter( model.Relation.child == id ).delete()
        self.session.query( model.FileChecksum ) \
                .filter( model.FileChecksum.id == id ).delete()
        self.session.query( model.Object ) \
                .filter( model.Object.id == id ).delete()

        if( p != None ):
            os.remove( p )

def init( config_file = None ):

    cfg = config.init( config_file )
    lib = cfg.get_path( 'library' )

    if( not os.path.isdir( lib ) ):
        os.makedirs( lib )

    model.init( os.path.join( lib, HIGURASHI_DB_NAME ) )

def compare_details( a, b ):

    return long( a[0] ) == long( b[0] ) \
       and str( a[1] ) == str( b[1] ) \
       and str( a[2] ) == str( b[2] ) \
       and str( a[3] ) == str( b[3] )

# vim:sts=4:sw=4:et
