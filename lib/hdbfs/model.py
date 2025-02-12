from sqlalchemy import *
from sqlalchemy import event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, backref, sessionmaker, scoped_session
from sqlalchemy.ext.associationproxy import association_proxy

import calendar
import numbers
import re
import time

from typing import Optional, List
from enum import Enum

class ObjectClass( Enum ):

    NILL        = 0

    FILE        = 100

    ALBUM       = 200
    CLASSIFIER  = 201
    IMPORT      = 202

    def all_types( self ) -> List['ObjectType']:

        ALL_TYPES_MAP = {
            ObjectClass.FILE : [
                ObjectType.FILE,
                ObjectType.DUPLICATE,
            ],

            ObjectClass.ALBUM : [
                ObjectType.ALBUM_FREE,
                ObjectType.ALBUM_FORMAL,
                ObjectType.ALBUM_CLOSED
            ],

            ObjectClass.CLASSIFIER : [ ObjectType.CLASSIFIER ],

            ObjectClass.IMPORT : [
                ObjectType.IMPORT_CLOSED,
                ObjectType.IMPORT_OPEN
            ]
        }

        return ALL_TYPES_MAP[self]

    def all_type_values( self ) -> List[int]:

        return list( map( lambda ty: ty.value, self.all_types() ) )

class ObjectType( Enum ):

    NILL          = 0

    FILE          = 10000
    DUPLICATE     = 10001

    ALBUM_FREE    = 20000
    ALBUM_FORMAL  = 20001
    ALBUM_CLOSED  = 20002

    CLASSIFIER    = 20100

    IMPORT_OPEN   = 20200
    IMPORT_CLOSED = 20201

    def get_class( self ) -> ObjectClass:
        return ObjectClass( self.value // 100 )

class StreamPriority( Enum ):

    EXPENDABLE = 1000
    NORMAL     = 2000
    PRIORITY   = 3000

VERSION = 15
REVISION = 0

IMGDB_VERSION = 1
IMGDB_REVISION = 0

class ImageRequestPriority( Enum ):
    NONE = 0
    BACKGROUND = 1
    IMMEDIATE = 100

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
        Index( 'Relation_sort_child_id', 'sort', 'child_id' ),
        Index( "Relation_parent_id", 'parent_id' )
    )

    child_id = Column( Integer, ForeignKey( 'objects.object_id' ), primary_key = True )
    parent_id = Column( Integer, ForeignKey( 'objects.object_id' ), primary_key = True )
    sort = Column( Integer )
    child_name = Column( Text )

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

    def __init__( self, object_type: ObjectType, name: Optional[str] = None ):

        self.object_type = object_type.value
        self.name = name
        self.create_ts = calendar.timegm(time.gmtime())

    def get_type( self ) -> ObjectType:

        return ObjectType( self.object_type )

    def set_type( self, new_type: ObjectType ) -> None:

        self.object_type = new_type.value

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

        self.metadata.filter( ObjectMetadata.key == key ).delete()

    def __repr__( self ):

        return 'Object( {id}, {type}, {create_ts}, {name} )'.format(
                    id = self.object_id,
                    type = self.object_type,
                    create_ts = time.gmtime( self.create_ts ),
                    name = self.name )

class Stream( Base ):
    __tablename__ = 'streams'
    __table_args__ = (
        UniqueConstraint( 'object_id', 'name' ),
        Index( 'Stream_object_id', 'object_id' ),
        Index( 'Stream_origin_stream_id', 'origin_stream_id' )
    )

    stream_id = Column( Integer, primary_key = True )
    object_id = Column( Integer, ForeignKey( 'objects.object_id' ), nullable = False )
    name = Column( Text, nullable = False )
    priority = Column( Integer, nullable = False )
    origin_stream_id = Column( Integer, ForeignKey( 'streams.stream_id' ) )
    extension = Column( Text )
    mime_type = Column( Text )
    stream_length = Column( Integer )
    hash_crc32 = Column( Text )
    hash_md5 = Column( Text )
    hash_sha1 = Column( Text )

    # TODO: why is lazy = 'select' leading to a unit test failure here?
    obj = relation( 'Object', foreign_keys = [ object_id ], lazy = 'joined',
                    backref = backref( 'streams', lazy = 'dynamic' ) )
    origin_stream = relation( 'Stream',
                        backref = 'derived_streams',
                            remote_side = [ stream_id ] )

    def __init__( self, obj: Object, name: str, priority: int,
                  origin_stream: 'Stream', extension: str, mime_type: str ):

        self.obj = obj
        self.name = name
        self.priority = priority
        self.origin_stream = origin_stream
        self.extension = extension
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

        return 'Stream( %r, %r, %r, %r, %r, %r, %r, %r, %r, %r )' % (
                self.stream_id, self.object_id, self.name, self.priority,
                self.origin_stream_id, self.mime_type, self.stream_length,
                self.hash_crc32, self.hash_md5, self.hash_sha1 )

class StreamLog( Base ):
    __tablename__ = 'stream_log'
    __table_args__ = (
        Index( 'StreamLog_stream_id', 'stream_id' ),
        Index( 'StreamLog_origin_stream_id', 'origin_stream_id' )
    )

    log_id = Column( Integer, primary_key = True )
    stream_id = Column( Integer, ForeignKey( 'streams.stream_id' ), nullable = False )
    timestamp = Column( Integer, nullable = False )
    origin_method = Column( Text, nullable = False )
    origin_stream_id = Column( Integer, ForeignKey( 'streams.stream_id' ) )
    origin_name = Column( Text )

    stream = relation( 'Stream', foreign_keys = [ stream_id ],
                        backref = backref( 'log_entries', lazy = 'dynamic' ) )
    origin_stream = relation( 'Stream', foreign_keys = [ origin_stream_id ] )

    def __init__( self, stream, origin_method,
                  origin_stream, origin_name ):

        self.stream = stream
        self.timestamp = calendar.timegm(time.gmtime())
        self.origin_method = origin_method
        self.origin_stream = origin_stream
        self.origin_name = origin_name

    def __repr__( self ):

        return 'StreamLog( %r, %r, %r, %r, %r )' % (
                self.stream_id, self.timestamp, self.origin_method,
                self.origin_stream_id, self.origin_name )

class ObjectMetadata( Base ):
    __tablename__ = 'object_metadata'
    __table_args__ = (
        PrimaryKeyConstraint( 'object_id', 'key' ),
        Index( 'ObjectMetadata_object_id', 'object_id' ),
        Index( 'U_ObjectMetadata_key_object_id', 'key', 'object_id', unique = True )
    )

    object_id = Column( Integer, ForeignKey( 'objects.object_id' ),
                        nullable = False )
    key = Column( Text, nullable = False )
    value = Column( Text )
    numeric = Column( Integer )

    obj = relation( 'Object',
                    backref = backref( 'metadata',
                                       lazy = 'dynamic',
                                       cascade = 'all, delete-orphan' ) )

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
        Index( 'StreamMetadata_stream_id', 'stream_id' ),
        Index( 'U_StreamMetadata_key_stream_id', 'key', 'stream_id', unique = True )
    )

    stream_id = Column( Integer, ForeignKey( 'streams.stream_id' ),
                        nullable = False )
    key = Column( Text, nullable = False )
    value = Column( Text )
    numeric = Column( Integer )

    stream = relation( 'Stream',
                       backref = backref( 'metadata',
                                          lazy = 'dynamic',
                                          cascade = 'all, delete-orphan' ) )

    def __init__( self, key, value, numeric ):

        self.key = key
        self.value = value
        self.numeric = numeric

    def __repr__( self ):

        return 'StreamMetadata( %r, %r, %r, %r )' % (
                self.object_id, self.key, self.value, self.numeric )

class ImageInfo( Base ):
    __tablename__ = 'imageinfo'

    object_id = Column( Integer, ForeignKey( 'objects.object_id' ), primary_key = True )

    width = Column( Integer, nullable = False )
    height = Column( Integer, nullable = False )
    gen = Column( Integer, nullable = False, default = 0 )
    max_e = Column( Integer )
    use_root = Column( Integer )
    avail_e = Column( Integer )

    obj = relation( 'Object',
                    backref = backref( 'info',
                                       uselist = False,
                                       cascade = 'all, delete-orphan' ) )

    def __init__( self, obj, width, height ):

        self.obj = obj
        self.width = width
        self.height = height
        self.gen = 0

    def __repr__( self ):

        format_dict = dict( self.__dict__ )
        format_dict['avail_e'] = hex( self.avail_e ) if( self.avail_e is not None ) else repr( None )

        return 'ImageInfo( {object_id}, {width}x{height}, g{gen}, {max_e}, {use_root}, {avail_e} )' \
                    .format( **format_dict )

class ImageRequest( Base ):
    __tablename__ = 'imagerequest'

    object_id = Column( Integer, ForeignKey( 'objects.object_id' ), primary_key = True )

    prio = Column( Integer, nullable = False )
    exp_mask = Column( Integer )

    obj = relation( 'Object',
                    backref = backref( 'request',
                                       uselist = False,
                                       cascade = 'all, delete-orphan' ) )

    def __init__( self, obj, prio = 0, exp_mask = None ):

        self.obj = obj
        self.prio = prio
        self.exp_mask = exp_mask

    def __repr__( self ):

        format_dict = dict( self.__dict__ )
        format_dict['exp_mask'] = hex( self.exp_mask ) if( self.exp_mask is not None ) else repr( None )

        return 'ImageInfo( {object_id}, {prio}, {exp_mask} )' \
                    .format( **format_dict )

class StreamInfo( Base ):
    __tablename__ = 'streaminfo'

    stream_id = Column( Integer, ForeignKey( 'streams.stream_id' ), primary_key = True )

    width = Column( Integer, nullable = False )
    height = Column( Integer, nullable = False )
    orientation = Column( Integer )

    stream = relation( 'Stream',
                       backref = backref( 'info',
                                          uselist = False,
                                          cascade = 'all, delete-orphan' ) )

    def __init__( self, stream, width, height ):

        self.stream = stream
        self.width = width
        self.height = height

    def __repr__( self ):

        return 'ImageInfo( {object_id}, {width}x{height}, {max_e}, {use_root}, {avail_e:x} )' \
                    .format( self )

dbfile = None
Session = None

def _init_schema( engine, ver, rev ):
    global dbfile

    Base.metadata.create_all( engine )

def init( database_file, imgdb_path ):
    global dbfile
    global Session

    import hdbfs.db_utils as db_utils
    import hdbfs.legacy as legacy

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
