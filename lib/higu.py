import datetime
import os
import re
import sys
import time
import threading

from hash import calculate_details

import ark
import config
import model

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

def check_tag_name( s ):

    if( re.match( '^[\w\-_:]+$', s ) is None ):
        raise ValueError, '"%s" is not a valid tag name' % ( s, )

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

    def get_creation_time( self ):

        return datetime.datetime.fromtimestamp( self.obj.create_ts )

    def get_creation_time_utc( self ):

        return datetime.datetime.utcfromtimestamp( self.obj.create_ts )

    def get_tags( self ):

        tag_objs = [ obj for obj in self.obj.parents if obj.type == TYPE_CLASSIFIER ]
        return map( lambda x: Tag( self.db, x ), tag_objs )

    def _assign( self, group, order ):

        rel = self.db.session.query( model.Relation ) \
                .filter( model.Relation.parent == group.obj.id ) \
                .filter( model.Relation.child == self.obj.id ).first()
        if( rel is not None ):
            rel.sort = order
            return
        rel = model.Relation( order )
        rel.parent_obj = group.obj
        rel.child_obj = self.obj

    def assign( self, group, order = None ):

        with self.db._access( write = True ):
            self._assign( group, order )

    def _unassign( self, group ):

        rel = self.db.session.query( model.Relation ) \
                .filter( model.Relation.parent == group.obj.id ) \
                .filter( model.Relation.child == self.obj.id ).first()

        if( rel is not None ):
            self.db.session.delete( rel )

    def unassign( self, group ):

        with self.db._access( write = True ):
            self._unassign( group )

    def _reorder( self, group, order ):

        rel = self.db.session.query( model.Relation ) \
                .filter( model.Relation.parent == group.obj.id ) \
                .filter( model.Relation.child == self.obj.id ).first()
        if( rel is None ):
            raise ValueError, str( self ) + ' is not in ' + str( group )
        rel.sort = order

    def reorder( self, group, order = None ):

        with self.db._access( write = True ):
            self._reorder( group, order )

    def get_order( self, group ):

        rel = self.db.session.query( model.Relation ) \
                .filter( model.Relation.parent == group.obj.id ) \
                .filter( model.Relation.child == self.obj.id ).first()
        if( rel is None ):
            raise ValueError, str( self ) + ' is not in ' + str( group )
        return rel.sort
        
    def get_name( self ):

        return self.obj.name

    def _set_name( self, name, saveold ):

        oname = self.obj.name
        self.obj.name = name

        if( saveold and oname is not None ):
            self._add_name( oname )

    def set_name( self, name, saveold = False ):

        with self.db._access( write = True ):
            self._set_name( name, saveold )

    def _add_name( self, name ):

        name = make_unicode( name )

        if( self.get_name() is None ):
            self._set_name( name, False )
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

    def add_name( self, name ):

        with self.db._access( write = True ):
            self._add_name( name )

    def get_names( self ):

        names = [ self.get_repr() ]

        try:
            xnames = self.obj['altname']
            names.extend( xnames.split( ':' ) )
        except KeyError:
            pass

        return names

    def set_text( self, text ):

        self.obj['text'] = text

    def get_text( self ):

        try:
            return self.obj['text']
        except KeyError:
            return None

    def get_repr( self ):

        name = self.get_name()
        if( name is not None ):
            return name
        else:
            return '%016x' % ( self.obj.id )

    def __getitem__( self, key ):

        return self.obj[key]

    def __setitem__( self, key, value ):

        with self.db._access( write = True ):
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

        with self.db._access( write = True ):

            all_objs = self.get_files()
            
            for child in enumerate( children ):
                assert( child[1] in all_objs )
                all_objs.remove( child[1] )
                
                child[1]._reorder( self, child[0] )

            offset = len( children )

            for child in enumerate( all_objs ):
                child[1]._reorder( self, offset + child[0] )

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

        with self.db._access( write = True ):
            assert( isinstance( parent, File ) )

            self.obj.type = TYPE_FILE_DUP
            self.obj.similar_to = parent.obj

    def set_varient_of( self, parent ):

        with self.db._access( write = True ):
            assert( isinstance( parent, File ) )

            self.obj.type = TYPE_FILE_VAR
            self.obj.similar_to = parent.obj

    def clear_duplication( self ):

        with self.db._access( write = True ):
            self.obj.type = TYPE_FILE
            self.obj.similar_to = None

    def get_repr( self ):

        name = self.get_name()
        if( name is not None ):
            return name
        else:
            e = self.db.imgdb.get_ext( self.obj.id )
            if( e == None ):
                return '%016x' % ( self.get_id(), )
            else:
                return '%016x.%s' % ( self.get_id(), e, )

    def get_length( self ):

        return self.obj.fchk.len

    def get_hash( self ):

        return self.obj.fchk.sha1

    def rotate( self, rot ):

        with self.db._access( write = True ):
            try:
                rotation = self.obj['rotation']
            except:
                rotation = 0;

            rotation += int( rot )
            rotation %= 4

            if( rotation < 0 ):
                rotation += 4

            try:
                gen = self.obj['thumb-gen']
                gen += 1
            except:
                gen = 1

            self.obj['rotation'] = rotation
            self.obj['thumb-gen'] = gen

            self.db.tbcache.purge_thumbs( self.obj.id )

    def get_mime( self ):

        return self.db.imgdb.get_mime( self.obj.id )

    def read( self ):

        return self.db.imgdb.read( self.obj.id )

    def read_thumb( self, exp ):

        return self.db.tbcache.read_thumb( self, exp )

class ModelObjToHiguObjIterator:

    def __init__( self, db, iterable ):

        self.db = db
        self.it = iterable.__iter__()

    def __iter__( self ):

        return ModelObjToHiguObjIterator( self.db, self.it )

    def next( self ):

        return model_obj_to_higu_obj( self.db, self.it.next() )

class _AccessContext:

    def __init__( self, db, manager, write, auto_commit = True ):

        self.__db = db
        self.__manager = manager
        self.__write = write
        self.__auto_commit = auto_commit
        self.__active = False

    def __enter__( self ):

        self.__manager._begin_access( self.__write )
        self.__active = True
        return self

    def __exit__( self, type, value, trace ):

        self.__active = False

        if( type is None and self.__write and self.__auto_commit ):
            self.__db._commit()

        self.__manager._end_access()
        if( type is not None ):
            raise type, value, trace

    def commit( self ):

        assert self.__write, 'Can only commit with write access'
        self.__db._commit()

    def rollback( self ):

        self.__db._rollback()

class AccessManager:

    def __init__( self, db ):

        self.__db = db
        self.__write_lock = threading.Lock()
        self.__write_permitted = False

    def _begin_access( self, write ):

        assert not write or self.__write_permitted, 'Read-Only Access'
        self.__write_lock.__enter__()

    def _end_access( self ):

        self.__write_lock.__exit__()

    def enable_writes( self ):

        self.__write_permitted = True

    def __call__( self, **kwargs ):

        return _AccessContext( self.__db, self, **kwargs )

class Database:

    def __init__( self ):

        imgpat = os.path.join( config.config().get_path( 'library' ),
                HIGURASHI_DATA_PATH )

        self.session = model.Session()
        self.imgdb = ark.ImageDatabase( imgpat )
        self.tbcache = ark.ThumbCache( self.imgdb, imgpat )

        self._access = AccessManager( self )

        self.obj_del_list = []

    def _commit( self ):

        try:
            self.imgdb.commit()
            self.session.commit()
        except:
            if( self.imgdb.get_state() == 'committed' ):
                self.imgdb.rollback()

        for id in self.obj_del_list:
            self.tbcache.purge_thumbs( id )
        self.obj_del_list = []

    def _rollback( self ):

        self.imgdb.rollback()
        self.session.rollback()

    def enable_write_access( self ):

        self._access.enable_writes()

    def close( self ):

        self.session.close()

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

    def generate_thumbs( self, max_exp, force = False, sleep = None ):

        files = self.session.query( model.Object ) \
                    .filter( model.Object.type == TYPE_FILE ) \
                    .order_by( 'RANDOM()' )

        for f in ModelObjToHiguObjIterator( self, files ):
            print 'Generating thumbs for', f.get_id()

            exp = ark.MIN_THUMB_EXP
            while( self.tbcache.make_thumb( f, exp ) is not None and exp <= max_exp ):
                exp += 1

            if( sleep is not None ):
                time.sleep( sleep )

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

    def lookup_ids_by_tags( self, require = [], add = [], sub = [],
            strict = False, type = None, random_order = False ):

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

        query = self.session.query( model.Object )

        if( req_q is not None ):
            q = req_q

            if( add_q is not None ):
                q = q.union( add_q )

            query = query.filter( model.Object.id.in_( q ) )
        elif( add_q is not None ):
            query = query.filter( model.Object.id.in_( add_q ) )

        if( sub_q is not None ):
            query = query.filter( ~model.Object.id.in_( sub_q ) )

        if( type is not None ):
            query = query.filter( model.Object.type == type )
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
            raise KeyError, 'No such tag "%s"' % ( name, )

        return model_obj_to_higu_obj( self, obj )

    def _make_tag( self, name ):

        check_tag_name( name )
        try:
            return self.get_tag( name )
        except KeyError:
            obj = model.Object( TYPE_CLASSIFIER, name )
            self.session.add( obj )
            return model_obj_to_higu_obj( self, obj )

    def make_tag( self, name ):

        with self._access( write = True ):
            return self._make_tag( name )

    def delete_tag( self, tag ):

        tag = self.get_tag( tag )
        self.delete_object( tag )

    def move_tag( self, tag, target ):

        with self._access( write = True ):

            check_tag_name( target )
            c = self.get_tag( tag ).obj

            try:
                d = self.get_tag( target ).obj
                self.session.query( model.Relation ).filter( model.Relation.parent == c.id ).update( { 'parent' : d.id } )
                self.session.delete( c )

            except KeyError:
                c.name = target

    def copy_tag( self, tag, target ):

        with self._access( write = True ):

            check_tag_name( target )
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

    def verify_file( self, obj ):

        assert isinstance( obj, File )
        fd = obj.read()

        if( fd is None ):
            return False

        details = calculate_details( fd )

        if( details[0] != obj.obj.fchk.len ):
            return False
        if( details[1] != obj.obj.fchk.crc32 ):
            return False
        if( details[2] != obj.obj.fchk.md5 ):
            return False
        if( details[3] != obj.obj.fchk.sha1 ):
            return False

        return True

    def __recover_file( self, path ):

        name = os.path.split( path )[1]

        details = calculate_details( path )
        results = self.lookup_files_by_details( *details )

        try:
            f = results.next()
        except StopIteration:
            return False

        if( not self.verify_file( f ) ):
            self.imgdb.load_data( path, f.get_id() )
        return True

    def recover_files( self, files ):

        with self._access( write = True ):
            for f in files:
                if( not self.__recover_file( f ) ):
                    #log.warn( '%s was not found in the db and was ignored', f )
                    pass

    def __create_album( self, tags = [], name = None, text = None ):

        album = model.Object( TYPE_ALBUM )
        self.session.add( album )
        album = model_obj_to_higu_obj( self, album )

        if( name is not None ):
            album.obj.name = name

        if( text is not None ):
            album.obj['text'] = text

        for t in tags:
            album._assign( t, None )

        return album

    def create_album( self, tags = [], name = None, text = None ):

        with self._access( write = True ):
            return self.__create_album( tags, name, text )

    def __register_file( self, path, add_name ):

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
            f._add_name( name )

        if( not self.verify_file( f ) ):
            self.imgdb.load_data( path, id )

        return f

    def register_file( self, path, add_name = True ):

        with self._access( write = True ):
            return self.__register_file( path, add_name )

    def batch_add_files( self, files, tags = [], tags_new = [], save_name = False,
                         create_album = False, album_name = None, album_text = None ):

        with self._access( write = True ):

            # Load tags
            taglist = []
            taglist += map( self.get_tag, tags )
            taglist += map( self._make_tag, tags_new )

            if( create_album ):
                album = self.__create_album( taglist, album_name, album_text )
            else:
                album = None

            for f in files:
                x = self.__register_file( f, save_name )

                if( album is not None ):
                    x._assign( album, None )
                else:
                    for t in taglist:
                        x._assign( t, None )

    def delete_object( self, obj ):

        with self._access( write = True ):

            id = obj.get_id()

            if( isinstance( obj, File ) ):
                self.imgdb.delete( id )
                self.obj_del_list.append( id )

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

def init( config_file = None ):

    cfg = config.init( config_file )
    lib = cfg.get_path( 'library' )

    if( not os.path.isdir( lib ) ):
        os.makedirs( lib )

    model.init( os.path.join( lib, HIGURASHI_DB_NAME ) )

def dispose():

    model.dispose()

def compare_details( a, b ):

    return long( a[0] ) == long( b[0] ) \
       and str( a[1] ) == str( b[1] ) \
       and str( a[2] ) == str( b[2] ) \
       and str( a[3] ) == str( b[3] )

# vim:sts=4:sw=4:et
