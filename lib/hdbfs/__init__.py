import datetime
import os
import re
import sys
import time

from hash import calculate_details

import ark
import model

VERSION = 1
REVISION = 0

DB_VERSION  = model.VERSION
DB_REVISION = model.REVISION

DEFAULT_LIBRARY = os.path.join( os.environ['HOME'], '.higu' )
HIGURASHI_DB_NAME = 'hfdb.dat'
HIGURASHI_DATA_PATH = 'imgdat'

TYPE_FILE       = model.TYPE_FILE
TYPE_FILE_DUP   = model.TYPE_FILE_DUP
TYPE_FILE_VAR   = model.TYPE_FILE_VAR
TYPE_GROUP      = model.TYPE_GROUP
TYPE_ALBUM      = model.TYPE_ALBUM
TYPE_CLASSIFIER = model.TYPE_CLASSIFIER

_LIBRARY = None

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

    def is_duplicate( self ):

        return self.get_type() == TYPE_FILE_DUP

    def is_variant( self ):

        return self.get_type() == TYPE_FILE_VAR

    def get_id( self ):

        with self.db._access():
            return self.obj.id

    def get_type( self ):

        with self.db._access():
            return self.obj.type

    def get_creation_time( self ):

        with self.db._access():
            return datetime.datetime.fromtimestamp( self.obj.create_ts )

    def get_creation_time_utc( self ):

        with self.db._access():
            return datetime.datetime.utcfromtimestamp( self.obj.create_ts )

    def get_tags( self ):

        with self.db._access():
            tag_objs = [ obj for obj in self.obj.parents if obj.type == TYPE_CLASSIFIER ]
            return map( lambda x: Tag( self.db, x ), tag_objs )

    def _assign( self, group, order ):
    
        if( self.obj.type == TYPE_FILE_DUP ):
            raise ValueError, 'Cannot assign to a duplicate'

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

        with self.db._access():
            rel = self.db.session.query( model.Relation ) \
                    .filter( model.Relation.parent == group.obj.id ) \
                    .filter( model.Relation.child == self.obj.id ).first()
            if( rel is None ):
                raise ValueError, str( self ) + ' is not in ' + str( group )
            return rel.sort
        
    def get_name( self ):

        with self.db._access():
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

        if( self.obj.name is None ):
            self._set_name( name, False )
        elif( self.obj.name != name ):
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
            xnames = self['altname']
            names.extend( xnames.split( ':' ) )
        except KeyError:
            pass

        return names

    def set_text( self, text ):

        self['text'] = text

    def get_text( self ):

        try:
            return self['text']
        except KeyError:
            return None

    def get_repr( self ):

        name = self.get_name()
        if( name is not None ):
            return name
        else:
            return '%016x' % ( self.get_id() )

    def __getitem__( self, key ):

        with self.db._access():
            return self.obj[key]

    def __setitem__( self, key, value ):

        with self.db._access( write = True ):
            self.obj[key] = value

    def __hash__( self ):

        return self.get_id()

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

    def _get_files( self ):

        objs = [ obj for obj in self.obj.children if( obj.type == TYPE_FILE or obj.type == TYPE_FILE_DUP or obj.type == TYPE_FILE_VAR ) ]
        return map( lambda x: File( self.db, x ), objs )

    def get_files( self ):

        with self.db._access():
            return self._get_files()

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

            all_objs = self._get_files()
            
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

    def _get_albums( self ):

        objs = [ obj for obj in self.obj.parents if obj.type == TYPE_ALBUM ]
        return map( lambda x: Album( self.db, x ), objs )

    def get_albums( self ):

        with self.db._access():
            return self._get_albums()

    def _get_duplicates( self ):

        objs = [ obj for obj in self.obj.similars if obj.type == TYPE_FILE_DUP ]
        return map( lambda x: File( self.db, x ), objs )

    def get_duplicates( self ):

        with self.db._access():
            return self._get_duplicates()

    def _get_variants( self ):

        objs = [ obj for obj in self.obj.similars if obj.type == TYPE_FILE_VAR ]
        return map( lambda x: File( self.db, x ), objs )

    def get_variants( self ):

        with self.db._access():
            return self._get_variants()

    def _get_similar_to( self ):

        if( self.obj.similar_to is None ):
            return None
        else:
            return File( self.db, self.obj.similar_to )

    def get_similar_to( self ):

        with self.db._access():
            return self._get_similar_to()

    def _set_duplicate_of( self, parent ):

        assert( isinstance( parent, File ) )
        assert( parent.obj != self.obj )

        # Remove any previous duplication
        self._clear_duplication()

        # If we are a duplicate, we need to move all our assignments and
        # children to our parent. We begin by moving over all our
        # association
        assocs = [ ( assoc.parent, assoc.sort )
                    for assoc in self.obj.parent_rel ]
        for obj_id, sort in assocs:
            group = self.db._get_object_by_id( obj_id )
            parent._assign( group, sort )
            self._unassign( group )

        # Now we move across all our duplicates to our parent
        dups = self._get_duplicates()
        for d in dups:
            if( d == parent ):
                # Protect from circular duplication
                d._clear_duplication()
            else:
                d._set_duplicate_of( parent )

        # Now we move across all our variants to our parent
        variants = self._get_variants()
        for v in variants:
            if( v.obj.id == parent.obj.id ):
                v._clear_duplication()
            else:
                v._set_variant_of( parent )

        self.obj.type = TYPE_FILE_DUP
        self.obj.similar_to = parent.obj

    def set_duplicate_of( self, parent ):

        with self.db._access( write = True ):
            self._set_duplicate_of( parent )

    def _set_variant_of( self, parent ):

        assert( isinstance( parent, File ) )
        assert( parent.obj != self.obj )

        # Protect from circular duplication
        if( parent in self._get_duplicates()
         or parent in self._get_variants() ):

            parent._clear_duplication()

        self.obj.type = TYPE_FILE_VAR
        self.obj.similar_to = parent.obj

    def set_variant_of( self, parent ):

        with self.db._access( write = True ):
            self._set_variant_of( parent )

    def _clear_duplication( self ):

        self.obj.type = TYPE_FILE
        self.obj.similar_to = None

    def clear_duplication( self ):

        with self.db._access( write = True ):
            self._clear_duplication()

    def get_repr( self ):

        name = self.get_name()
        if( name is not None ):
            return name
        else:
            obj_id = self.get_id()

            e = self.db.imgdb.get_ext( obj_id )
            if( e == None ):
                return '%016x' % ( obj_id, )
            else:
                return '%016x.%s' % ( obj_id, e, )

    def get_length( self ):

        with self.db._access():
            return self.obj.fchk.len

    def get_hash( self ):

        with self.db._access():
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

        return self.db.imgdb.get_mime( self.get_id() )

    def _read( self ):

        return self.db.imgdb.read( self.obj.id )

    def read( self ):

        with self.db._access():
            return self._read()

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

    def __init__( self, db, manager, write = False, auto_commit = True ):

        self.__db = db
        self.__manager = manager
        self.__write = write
        self.__auto_commit = auto_commit
        self.__active = False

    def __enter__( self ):

        self.__db._begin( self.__write )
        self.__manager._begin_access( self.__write )
        self.__active = True
        return self

    def __exit__( self, type, value, trace ):

        self.__active = False

        if( self.__write ):
            committed = False

            if( type is None
            and self.__auto_commit ):

                try:
                    self.__db._commit()
                    committed = True

                except:
                    type, value, trace = sys.exc_info()

            if( not committed ):
                self.__db._rollback()

        self.__manager._end_access()
        if( type is not None ):
            raise type, value, trace

    def commit( self ):

        assert self.__write, 'Can only commit with write access'
        self.__db._commit()
        self.__db._begin( self.__write )

    def rollback( self ):

        self.__db._rollback()
        self.__db._begin( self.__write )

class AccessManager:

    def __init__( self, db ):

        self.__db = db
        self.__write_permitted = False

    def _begin_access( self, write ):

        assert not write or self.__write_permitted, 'Read-Only Access'

    def _end_access( self ):

        pass

    def enable_writes( self ):

        self.__write_permitted = True

    def __call__( self, **kwargs ):

        return _AccessContext( self.__db, self, **kwargs )

class ParameterConstraint:

    def __init__( self, parameter ):

        self.__parameter = parameter
        self.__constraint = None

    def Set_eq( self, value ):

        self.__constraint = (model.Metadata.value == str( value ))

    def Set_ne( self, value ):

        self.__constraint = (model.Metadata.value != str( value ))

    def Set_gt( self, value ):

        self.__constraint = (model.Metadata.num > value )

    def Set_ge( self, value ):

        self.__constraint = (model.Metadata.num >= value )

    def Set_lt( self, value ):

        self.__constraint = (model.Metadata.num < value )

    def Set_le( self, value ):

        self.__constraint = (model.Metadata.num <= value )

    def _Get_constraint( self ):

        from sqlalchemy import and_

        return and_( model.Metadata.key == self.__parameter, self.__constraint )

class Database:

    def __init__( self ):
        global _LIBRARY

        imgpat = os.path.join( _LIBRARY, HIGURASHI_DATA_PATH )

        self.session = model.Session()
        self.imgdb = ark.ImageDatabase( imgpat )
        self.tbcache = ark.ThumbCache( self.imgdb, imgpat )

        self._access = AccessManager( self )
        self._trans_write = False

        self.obj_del_list = []

    def __del__( self ):

        if( self.session is not None ):
            self.session.close()

    def _begin( self, write ):

        if( write ):
            self.session.execute( 'BEGIN EXCLUSIVE' )
            self._trans_write = True

    def _commit( self ):

        if( not self._trans_write ):
            return

        self.imgdb.prepare_commit()
        try:
            self.session.commit()
            self.imgdb.complete_commit()
        except:
            self.imgdb.unprepare_commit()
            raise

        for id in self.obj_del_list:
            self.tbcache.purge_thumbs( id )
        self.obj_del_list = []
        self._trans_write = False

    def _rollback( self ):

        if( not self._trans_write ):
            return

        self.imgdb.rollback()
        self.session.rollback()
        self._trans_write = False

    def close( self ):

        self.session.close()
        self.session = None

    def enable_write_access( self ):

        self._access.enable_writes()

    def _get_object_by_id( self, id ):

        obj = self.session.query( model.Object ).filter( model.Object.id == id ).first()
        if( obj is None ):
            return None

        return model_obj_to_higu_obj( self, obj )

    def get_object_by_id( self, id ):

        with self._access():
            return self._get_object_by_id( id )

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

    def lookup_objects( self, require = [], add = [], sub = [],
            strict = False, type = None, order = None, rsort = False ):

        def gen_query( constraints ):

            parameters = [i for i in constraints if( isinstance( i, ParameterConstraint ) )]
            tags = [i for i in constraints if( i not in parameters )]

            q = []
            if( len( tags ) > 0 ):
                q.extend( map( lambda x: self.session.query( model.Relation.child ) \
                        .filter( model.Relation.parent == x.obj.id ), tags ) )
            if( len( parameters ) > 0 ):
                q.extend( map( lambda x: self.session.query( model.Metadata.id ) \
                        .filter( x._Get_constraint() ), parameters ) )

            return q

        if( len( add ) > 0 ):
            add_q = gen_query( add )
            add_q = add_q[0].union( *add_q[1:] )
        else:
            add_q = None

        if( len( sub ) > 0 ):
            sub_q = gen_query( sub )
            sub_q = sub_q[0].union( *sub_q[1:] )
        else:
            sub_q = None

        if( len( require ) > 0 ):
            req_q = gen_query( require )
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
        else:
            query = query.filter( model.Object.type.in_( [
                TYPE_FILE, TYPE_FILE_VAR, TYPE_ALBUM ] ) )

        if( order == 'rand' ):
            query = query.order_by( 'RANDOM()' )
        elif( order == 'add' ):
            if( not rsort ):
                query = query.order_by( model.Object.id )
            else:
                query = query.order_by( model.Object.id.desc() )

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

    def __verify_file( self, obj ):

        assert isinstance( obj, File )
        fd = obj._read()

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

    def verify_file( self, obj ):

        with self._access():
            return self.__verify_file( obj )

    def __recover_file( self, path ):

        name = os.path.split( path )[1]

        details = calculate_details( path )
        results = self.lookup_files_by_details( *details )

        try:
            f = results.next()
        except StopIteration:
            return False

        if( not self.__verify_file( f ) ):
            self.imgdb.load_data( path, f.obj.id )
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
            album.obj.name = make_unicode( name )

        if( text is not None ):
            album.obj['text'] = make_unicode( text )

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

        id = f.obj.id

        if( add_name ):
            f._add_name( name )

        if( not self.__verify_file( f ) ):
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

                if( x.obj.type == TYPE_FILE_DUP ):
                    x = x._get_similar_to()

                if( album is not None ):
                    x._assign( album, None )
                else:
                    for t in taglist:
                        x._assign( t, None )

    def delete_object( self, obj ):

        with self._access( write = True ):

            id = obj.obj.id

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

def init( library_path = None ):
    global _LIBRARY

    if( library_path is not None ):
        _LIBRARY = library_path
    else:
        _LIBRARY = DEFAULT_LIBRARY

    if( not os.path.isdir( _LIBRARY ) ):
        os.makedirs( _LIBRARY )

    model.init( os.path.join( _LIBRARY, HIGURASHI_DB_NAME ) )

def dispose():
    global _LIBRARY

    model.dispose()
    _LIBRARY = None

def compare_details( a, b ):

    return long( a[0] ) == long( b[0] ) \
       and str( a[1] ) == str( b[1] ) \
       and str( a[2] ) == str( b[2] ) \
       and str( a[3] ) == str( b[3] )

# vim:sts=4:sw=4:et
