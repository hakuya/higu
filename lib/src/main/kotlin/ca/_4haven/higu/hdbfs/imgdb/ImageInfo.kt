package ca._4haven.higu.hdbfs.imgdb

import ca._4haven.higu.hdbfs.ark.*

class ImageInfo( val imgdb: StreamDatabase, val obj: ImageFile ) {

    private var root_si: StreamInfo? = null

    private var tb_gen: Int? = null
    private var max_e: Int? = null
    private var use_root: Int? = null

    private var obj_w: Int? = null
    private var obj_h: Int? = null

    private var origin_time: Int? = null

    /* TODO
    def get_root_stream_info( self ):

        if( self.root_si is None ):
            root_s = self.obj.get_root_stream()
            if( root_s is not None ):
                self.root_si = StreamInfo( self.imgdb, root_s )

        return self.root_si

    def get_root_stream( self ):

        root_si = self.get_root_stream_info()
        if( root_si is not None ):
            return root_si.stream
        else:
            return None

    def get_img( self ):

        root_si = self.get_root_stream_info()
        if( root_si is not None ):
            return root_si.get_img()
        else:
            return None

    def get_orientation( self ):

        root_si = self.get_root_stream_info()
        if( root_si is not None ):
            return root_si.get_orientation()
        else:
            return 1

    def get_dims( self ):

        root_si = self.get_root_stream_info()
        if( root_si is not None ):
            return root_si.get_dims()
        else:
            return None, None

    def get_origin_time( self ):

        if( self.origin_time is None ):
            try:
                self.origin_time = self.obj['origin_time']
            except:
                pass

        if( self.origin_time is None ):
            root_si = self.get_root_stream_info()
            if( root_si is not None ):
                self.origin_time = root_si.get_origin_time()

            if( self.origin_time is not None ):
                self.obj['origin_time'] = self.origin_time

        return self.origin_time

    def get_obj_dims( self, verify = False ):

        if( self.obj_w is None or self.obj_h is None ):

            try:
                self.obj_w = self.obj['width']
            except:
                pass

            try:
                self.obj_h = self.obj['height']
            except:
                pass

        if( verify or self.obj_w is None or self.obj_h is None ):

            w, h = self.get_dims()
            orientation = self.get_orientation()

            if( orientation > 4 ):
                w, h = h, w

            if( self.obj_w != w or self.obj_h != h ):
                self.obj_w = w
                self.obj_h = h

                self.obj['width'] = w
                self.obj['height'] = h

        return self.obj_w, self.obj_h

    def get_tb_info( self, bump_gen = False ):

        if( self.tb_gen is None
         or self.max_e is None
         or self.use_root is None ):

            try:
                tb_info = map( int, self.obj['.tbinfo'].split( ':' ) )

                self.tb_gen = tb_info[0]
                self.max_e = tb_info[1]
                self.use_root = tb_info[2]

            except:
                pass

        if( bump_gen
         or self.tb_gen is None
         or self.max_e is None
         or self.use_root is None ):

            w, h = self.get_dims()
            orientation = self.get_orientation()

            if( self.tb_gen is not None ):
                self.tb_gen += 1
            else:
                self.tb_gen = 0

            self.max_e = 0
            if( orientation == 1 ):
                self.use_root = 1
            else:
                self.use_root = 0

            while( 2**self.max_e < w or 2**self.max_e < h ):
                self.max_e += 1

            tb_info = [ self.tb_gen, self.max_e, self.use_root ]
            self.obj['.tbinfo'] = ':'.join( map( str, tb_info ) )

        return self.tb_gen, self.max_e, self.use_root*/
}