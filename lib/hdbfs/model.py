from sqlalchemy import *
from sqlalchemy import event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, backref, sessionmaker, scoped_session
from sqlalchemy.ext.associationproxy import association_proxy

import calendar
import numbers
import re
import time
import threading

TYPE_NILL       = 0
TYPE_FILE       = 1000
TYPE_GROUP      = 2000
TYPE_ALBUM      = 2001
TYPE_CLASSIFIER = 2002

SP_EXPENDABLE = 1000
SP_NORMAL     = 2000
SP_PRIORITY   = 3000

VERSION = 10
REVISION = 0

IMGDB_VERSION = 1
IMGDB_REVISION = 0

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
    imgdb_ver = Column( Integer )

    def __init__( self, ver, rev ):

        self.uuid = uuid.uuid1()
        self.ver = ver
        self.rev = rev

    def __repr__( self ):

        return 'DatabaseInfo( %r, %r, %r )' % ( self.uuid, self.ver, self.rev )

class Relation( Base ):
    __tablename__ = 'relations'
    __table_args__ = (
        PrimaryKeyConstraint( 'child_id', 'parent_id' ),
    )

    child_id = Column( Integer, ForeignKey( 'objects.object_id' ), primary_key = True )
    parent_id = Column( Integer, ForeignKey( 'objects.object_id' ), primary_key = True )
    sort = Column( Integer )

    def __init__( self, sort = None ):

        self.sort = sort

    def __repr__( self ):

        return 'Relation( %r, %r, %r )' % (
                self.child_id, self.parent_id, self.sort )

class Object( Base ):
    __tablename__ = 'objects'

    object_id = Column( Integer, primary_key = True )
    object_type = Column( Integer, nullable = False )
    create_ts = Column( Integer, nullable = False )
    name = Column( Text )

    # use_alter is required here to avoid circular dependency
    root_stream_id = Column( Integer,
                             ForeignKey( 'streams.stream_id',
                                         name = 'objects_root_stream_id_constraint',
                                         use_alter = True ) )

    child_rel = relation(
        'Relation',
        primaryjoin = 'Object.object_id==Relation.parent_id',
        backref = backref( 'parent_obj', uselist = False ),
        order_by = 'Relation.sort' )
    parent_rel = relation(
        'Relation',
        primaryjoin = 'Object.object_id==Relation.child_id',
        backref = backref( 'child_obj', uselist = False ) )

    parents = association_proxy( 'parent_rel', 'parent_obj' )
    children = association_proxy( 'child_rel', 'child_obj' )

    # We need post update here to avoid the circular dependency. Only update
    # root_stream after both the object and stream have been created
    root_stream = relation( 'Stream', foreign_keys = [ root_stream_id ],
                            backref = backref( 'objects', uselist = False ),
                            post_update = True )

    def __init__( self, object_type, name = None ):

        self.object_type = object_type
        self.name = name
        self.create_ts = calendar.timegm(time.gmtime())

    def __getitem__( self, key ):

        row = self.metadata.filter( ObjectMetadata.key == key ).first()

        if( row is None ):
            raise KeyError

        if( row.numeric is not None ):
            return row.numeric
        else:
            return row.value

    def __setitem__( self, key, value ):

        value_s = value
        value_i = value if( isinstance( value, numbers.Number ) ) else None

        row = self.metadata.filter( ObjectMetadata.key == key ).first()

        if( row is not None ):
            row.value = value_s
            row.numeric = value_i
        else:
            row = ObjectMetadata( key, value_s, value_i )
            self.metadata.append( row )

    def __delitem__( self, key ):

        row = self.metadata.filter( ObjectMetadata.key == key ).first()
        if( row is None ):
            raise KeyError

        self.metadata.remove( row )

    def __repr__( self ):

        return 'Object( %r, %r, %r )' % ( self.id, self.type, time.gmtime( self.create_ts ), self.name )

class Stream( Base ):
    __tablename__ = 'streams'
    __table_args__ = (
        UniqueConstraint( 'object_id', 'name' ),
        Index( 'streams_object_id_name_index',
               'object_id', 'name', unique = True ),
    )

    stream_id = Column( Integer, primary_key = True )
    object_id = Column( Integer, ForeignKey( 'objects.object_id' ), nullable = False )
    name = Column( Text, nullable = False )
    priority = Column( Integer, nullable = False )
    create_ts = Column( Integer, nullable = False )
    origin_stream_id = Column( Integer, ForeignKey( 'streams.stream_id' ) )
    origin_method = Column( Text )
    mime_type = Column( Text )
    stream_length = Column( Integer )
    hash_crc32 = Column( Text )
    hash_md5 = Column( Text )
    hash_sha1 = Column( Text )

    obj = relation( 'Object', foreign_keys = [ object_id ],
                    backref = backref( 'streams', lazy = 'dynamic' ) )
    origin_stream = relation( 'Stream',
                        backref = 'derived_streams',
                            remote_side = [ stream_id ] )

    def __init__( self, obj, name, priority,
                  origin_stream, origin_method, mime_type ):

        self.obj = obj
        self.name = name
        self.priority = priority
        self.create_ts = calendar.timegm(time.gmtime())
        self.origin_stream = origin_stream
        self.origin_method = origin_method
        self.mime_type = mime_type

    def set_details( self, stream_length, hash_crc32, hash_md5, hash_sha1 ):

        self.stream_length = stream_length
        self.hash_crc32 = hash_crc32
        self.hash_md5 = hash_md5
        self.hash_sha1 = hash_sha1

    def __getitem__( self, key ):

        from sqlalchemy import and_

        row = self.metadata.filter( StreamMetadata.key == key ).first()

        if( row is None ):
            raise KeyError

        if( row.numeric is not None ):
            return row.numeric
        else:
            return row.value

    def __setitem__( self, key, value ):

        value_s = value
        value_i = value if( isinstance( value, numbers.Number ) ) else None

        row = self.metadata.filter( StreamMetadata.key == key ).first()

        if( row is not None ):
            row.value = value_s
            row.numeric = value_i
        else:
            row = StreamMetadata( key, value_s, value_i )
            self.metadata.append( row )

    def __delitem__( self, key ):

        row = self.metadata.filter( StreamMetadata.key == key ).first()
        if( row is None ):
            raise KeyError

        self.metadata.remove( row )

    def __repr__( self ):

        return 'Stream( %r, %r, %r, %r, %r, %r, %r, %r, %r, %r, %r, %r )' % (
                self.stream_id, self.object_id, self.name, self.priority,
                self.create_ts, self.origin_stream_id, self.origin_method,
                self.mime_type, self.stream_length, self.hash_crc32,
                self.hash_md5, self.hash_sha1 )

class ObjectMetadata( Base ):
    __tablename__ = 'object_metadata'
    __table_args__ = (
        PrimaryKeyConstraint( 'object_id', 'key' ),
        Index( 'object_metadata_object_id_key_index',
               'object_id', 'key', unique = True ),
    )

    object_id = Column( Integer, ForeignKey( 'objects.object_id' ),
                        nullable = False )
    key = Column( Text, nullable = False )
    value = Column( Text )
    numeric = Column( Integer )

    obj = relation( 'Object', backref = backref( 'metadata', lazy = 'dynamic' ) )

    def __init__( self, key, value, numeric ):

        self.key = key
        self.value = value
        self.numeric = numeric

    def __repr__( self ):

        return 'ObjectMetadata( %r, %r, %r, %r )' % (
                self.object_id, self.key, self.value, self.numeric )

class StreamMetadata( Base ):
    __tablename__ = 'stream_metadata'
    __table_args__ = (
        PrimaryKeyConstraint( 'stream_id', 'key' ),
        Index( 'stream_metadata_stream_id_key_index',
               'stream_id', 'key', unique = True ),
    )

    stream_id = Column( Integer, ForeignKey( 'streams.stream_id' ),
                        nullable = False )
    key = Column( Text, nullable = False )
    value = Column( Text )
    numeric = Column( Integer )

    stream = relation( 'Stream', backref = backref( 'metadata', lazy = 'dynamic' ) )

    def __init__( self, key, value, numeric ):

        self.key = key
        self.value = value
        self.numeric = numeric

    def __repr__( self ):

        return 'StreamMetadata( %r, %r, %r, %r )' % (
                self.object_id, self.key, self.value, self.numeric )

dbfile = None
Session = None

def _init_schema( engine, ver, rev ):
    global dbfile

    Base.metadata.create_all( engine )

def init( database_file, imgdb_path ):
    global dbfile
    global Session

    import db_utils
    import legacy

    migrators = {
        'hdbfs' : legacy.HDBFSMigrator( _init_schema ),
        'imgdb' : legacy.ImgDBMigrator( imgdb_path ),
    }

    dbfile = db_utils.DatabaseFile( database_file, migrators )
    dbfile.init()

    dbfile.init_schema( 'hdbfs', VERSION, REVISION )
    dbfile.init_schema( 'imgdb', IMGDB_VERSION, IMGDB_REVISION )

    Session = dbfile.get_session

def dispose():
    global dbfile
    global Session

    if( dbfile is not None ):
        Session = None
        dbfile.dispose()
        dbfile = None
