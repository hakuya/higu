import hdbfs
import higu.config
import higu.server

if( __name__ == '__main__' ):

    import sys

    if( len( sys.argv ) > 1 ):
        cfg = higu.config.init( sys.argv[1] )
    else:
        cfg = higu.config.init()

    hdbfs.init( cfg.get_path( 'library' ) )
    higu.server.start()
