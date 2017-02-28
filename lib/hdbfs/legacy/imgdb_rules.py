import mimetypes
import os
import shutil

from hdbfs import model
from hdbfs import calculate_details

MIN_THUMB_EXP = 7

def _get_dir_for_id( base, id ):

    lv2 = (id >> 12) % 0xfff
    lv3 = (id >> 24) % 0xfff
    lv4 = id >> 36

    assert lv4 == 0

    return os.path.join( base, '%03x' % ( lv3 ),
                               '%03x' % ( lv2 ) )

def _get_fname_base( base, id ):

    fname = '%016x' % ( id, )
    return os.path.join( _get_dir_for_id( base, id ), fname )

def _get_thumb_path( base, id, exp ):

    return _get_fname_base( base, id ) + '_%02d.jpg' % ( exp, )

def _get_max_thumb_path( base, id ):

    return _get_fname_base( base, id ) + '_max.jpg'

def upgrade_from_0_to_1( log, session, dbpath ):

    # In imgdb schema ver 0, thumbnails where stored beside the object image
    # files with the suffix _yyy.jpg, where yyy was the thumb exponent or yyy
    # was 'max', indicating it is the same size as the image. In schema ver
    # 1, thumbnails are stored as separate streams attached to the same
    # object.
    #
    # We could just dump all the thumbnails, but this might be expensive for
    # some large databases. Instead, we look for all files with the suffix
    # and register them as thumbnails.

    file_moves = []
    base_path = os.path.join( dbpath, 'imgdat' )
    thumb_path = os.path.join( dbpath, 'tbdat' )

    try:
        for stream in session.query( model.Stream ):

            obj = session.query( model.Object ) \
                         .filter( model.Object.root_stream_id == stream.stream_id ) \
                         .first()

            path = _get_dir_for_id( base_path, stream.stream_id )
            thumb_base = '%016x_' % ( stream.stream_id, )

            thumbs = []
            for fname in os.listdir( path ):
                try:
                    if( fname.index( thumb_base ) == 0 ):
                        thumbs.append( os.path.join( path, fname ) )
                except ValueError:
                    pass
            
            if( obj is None ):
                for t in thumbs:
                    os.remove( t )
                continue

            for t in thumbs:
                # The path for t is in the format,
                # .../xxx/xxx/xxx/xxxxxxxxxxxxxxxx_yyy.jpg .
                # Grab the yyy
                exp = os.path.split( t )[1] \
                        .split( '.' )[0][len( thumb_base ):]

                if( exp == 'max' ):
                    w = obj['width']
                    h = obj['height']

                    e = 0
                    while( 2**e < w or 2**e < h ):
                        e += 1
                    
                    exp = str( e )

                details = calculate_details( t )
                mime_type = mimetypes.guess_type( t, strict=False )[0]

                t_stream = model.Stream( obj, 'thumb:' + exp,
                                         model.SP_EXPENDABLE,
                                         stream, 'imgdb:legacy',
                                         mime_type )
                t_stream.set_details( *details )
                session.add( t_stream )
                session.flush()

                new_path = _get_dir_for_id( thumb_path, t_stream.stream_id )
                new_t = os.path.join( new_path, '%016x.jpg' % ( t_stream.stream_id ) )

                if( not os.path.isdir( new_path ) ):
                    os.makedirs( new_path )
                shutil.move( t, new_t )
                file_moves.append( ( t, new_t, ) )

        session.execute( 'DROP TABLE dbi' )
        return 1, 0

    except:
        for old_path, new_path in file_moves:
            shutil.move( new_path, old_path )
        raise