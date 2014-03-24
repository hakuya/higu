from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, backref, sessionmaker, scoped_session
from sqlalchemy.ext.associationproxy import association_proxy

import re

TYPE_NILL       = 0
TYPE_FILE       = 1000
TYPE_FILE_DUP   = 1001
TYPE_FILE_VAR   = 1002
TYPE_GROUP      = 2000
TYPE_ALBUM      = 2001
TYPE_CLASSIFIER = 2002

VERSION = 5
REVISION = 0

def check_len( length ):

    assert isinstance( length, int ) or isinstance( length, long ) and length >= 0
    return length

def check_crc32( hash ):

    assert isinstance( hash, str )
    hash = hash.lower()
    assert re.match( '^[0-9a-f]{8}$', hash )
    return hash

def check_md5( hash ):

    assert isinstance( hash, str )
    hash = hash.lower()
    assert re.match( '^[0-9a-f]{32}$', hash )
    return hash

def check_sha1( hash ):

    assert isinstance( hash, str )
    hash = hash.lower()
    assert re.match( '^[0-9a-f]{40}$', hash )
    return hash

Base = declarative_base()

class DatabaseInfo( Base ):
    __tablename__ = 'dbi'

    uuid = Column( Text, primary_key = True )
    ver = Column( Integer, nullable = False )
    rev = Column( Integer, nullable = False )

    def __init__( self, ver, rev ):

        self.uuid = uuid.uuid1()
        self.ver = ver
        self.rev = rev

    def __repr__( self ):

        return 'DatabaseInfo( %r, %r, %r )' % ( self.uuid, self.ver, self.rev )

class Relation( Base ):
    __tablename__ = 'rel2'

    child = Column( Integer, ForeignKey( 'objl.id' ), primary_key = True )
    parent = Column( Integer, ForeignKey( 'objl.id' ), primary_key = True )
    sort = Column( Integer )

    def __init__( self, sort = None ):

        self.sort = sort

    def __repr__( self ):

        return 'Relation( %r, %r, %r )' % (
                self.child, self.parent, self.sort )

class Object( Base ):
    __tablename__ = 'objl'

    id = Column( Integer, primary_key = True )
    type = Column( Integer, nullable = False )
    name = Column( Text )
    dup = Column( Integer, ForeignKey( 'objl.id' ) )

    child_rel = relation(
        'Relation',
        primaryjoin = 'Object.id==Relation.parent',
        backref = backref( 'parent_obj', uselist = False ),
        order_by = 'Relation.sort' )
    parent_rel = relation(
        'Relation',
        primaryjoin = 'Object.id==Relation.child',
        backref = backref( 'child_obj', uselist = False ) )

    parents = association_proxy( 'parent_rel', 'parent_obj' )
    children = association_proxy( 'child_rel', 'child_obj' )

    similars = relation( 'Object', backref = backref( 'similar_to', remote_side = [ id ] ) )

    def __init__( self, type, name = None ):

        self.type = type
        self.name = name

    def __getitem__( self, key ):

        row = self.meta.filter( Metadata.key == key ).first()
        if( row is None ):
            raise KeyError

        return row.value

    def __setitem__( self, key, value ):

        row = self.meta.filter( Metadata.key == key ).first()
        if( row is not None ):
            row.value = value
        else:
            row = Metadata( key, value )
            self.meta.append( row )

    def __delitem__( self, key ):

        row = self.meta.filter( Metadata.key == key ).first()
        if( row is None ):
            raise KeyError

        self.meta.remove( row )

    def __repr__( self ):

        return 'Object( %r, %r, %r )' % ( self.id, self.type, self.name )

class FileChecksum( Base ):
    __tablename__ = 'fchk'

    id = Column( Integer, ForeignKey( 'objl.id' ), primary_key = True )
    len = Column( Integer )
    crc32 = Column( Text )
    md5 = Column( Text )
    sha1 = Column( Text )

    obj = relation( 'Object', backref = backref( 'fchk', uselist = False ) )

    def __init__( self, obj, len, crc32, md5, sha1 ):

        self.obj = obj
        self.len = len
        self.crc32 = crc32
        self.md5 = md5
        self.sha1 = sha1

    def __repr__( self ):

        return 'FileChecksum( %r, %r, %r, %r, %r )' % (
                self.id, self.len, self.crc32, self.md5, self.sha1 )

class Metadata( Base ):
    __tablename__ = 'mtda'

    id = Column( Integer, ForeignKey( 'objl.id' ), primary_key = True )
    key = Column( Text, nullable = False, primary_key = True )
    value = Column( Text )

    obj = relation( 'Object', backref = backref( 'meta', lazy = 'dynamic' ) )

    def __init__( self, key, value = None ):

        self.key = key
        self.value = value

    def __repr__( self ):

        return 'Metadata( %r, %r, %r )' % ( self.id, self.tag, self.value )

Session = None
engine = None

def init( database_file ):
    global Session
    global engine

    import legacy
    legacy.update_legacy_database( database_file )

    engine = create_engine( 'sqlite:///' + database_file )
    Base.metadata.create_all( engine )

    session_factory = sessionmaker( bind = engine )
    Session = scoped_session( session_factory )

def dispose():

    Session = None
    engine.dispose()

def load():

    session = Session()
    info = session.Query(DatabaseInfo).first()
    assert( info.ver == VERSION )
    session.close()
