from basic_objs import *

_STM_FACTORIES = []
_OBJ_FACTORIES = []

def add_stream_factory( f ):
    global _STM_FACTORIES

    _STM_FACTORIES.insert( 0, f )

def add_obj_factory( f ):
    global _OBJ_FACTORIES

    _OBJ_FACTORIES.insert( 0, f )

def model_stream_to_higu_stream( db, stream ):
    global _STM_FACTORIES

    result = None
    for f in _STM_FACTORIES:
        result = f( db, stream )
        if( result is not None ):
            return result
    else:
        assert False

def model_obj_to_higu_obj( db, obj ):
    global _OBJ_FACTORIES

    result = None
    for f in _OBJ_FACTORIES:
        result = f( db, obj )
        if( result is not None ):
            return result
    else:
        assert False

class ModelObjToHiguObjIterator:

    def __init__( self, db, iterable ):

        self.db = db
        self.it = iterable.__iter__()

    def __iter__( self ):

        return ModelObjToHiguObjIterator( self.db, self.it )

    def next( self ):

        return model_obj_to_higu_obj( self.db, self.it.next() )

