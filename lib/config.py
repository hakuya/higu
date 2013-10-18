import ConfigParser
import os

cfg = None

class SubConfig:

    def __init__( self, main, sec ):

        self.main = main
        self.sec = sec

    def __getitem__( self, key ):

        return self.main.cfg.get( self.sec, key )

class MainConfig:

    def __init__( self, config ):

        self.cfg = ConfigParser.SafeConfigParser()
        self.cfg.read( config )
        self.base = os.path.split( config )[0]

    def get_base_path( self ):

        return self.base

    def subsection( self, section ):

        return SubConfig( self, section )

    def get_path( self, key ):

        return os.path.join( self.base, self.cfg.get( 'main', key ) )

    def __getitem__( self, key ):

        return self.cfg.get( 'main', key )

def config():
    global cfg

    return cfg

def init( config = None ):
    global cfg

    if( config is None ):
        config = 'default.cfg'

    cfg = MainConfig( config )
    return cfg
