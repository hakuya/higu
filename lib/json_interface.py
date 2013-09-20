import higu
import model
import sys

VERSION = 0
REVISION = 0

class JsonInterface:

    def __init__( self ):

        self.db = higu.Database()

    def close( self ):

        self.db.close()

    def execute( self, data ):

        #try:
        fn = getattr( self, 'cmd_' + data['action'] )
        return fn( data )
        #except:
        #    return {
        #        'result' : 'error',
        #        'errmsg' : sys.exc_info()[0],
        #    }

    def cmd_version( self, data ):

        return {
            'result'    : 'ok',
            'json_ver'  : [ VERSION, REVISION ],
            'higu_ver'  : [ higu.VERSION, higu.REVISION ],
            'db_ver'    : [ model.VERSION, model.REVISION ],
        }

    def cmd_info( self, data ):

        targets = data['targets']
        targets = map( self.db.get_object_by_id, targets )

        items = data['items']

        def fetch_info( target ):

            info = {}

            if( 'type' in items ):
                type = target.get_type()
                if( type == higu.TYPE_FILE
                 or type == HIGU.TYPE_FILE_DUP
                 or type == HIGU.TYPE_FILE_VAR ):
                    info['type'] = 'file'
                elif( type == higu.TYPE_ALBUM ):
                    info['type'] = 'album'
                elif( type == higu.TYPE_CLASSIFIER ):
                    info['type'] = 'tag'
                else:
                    info['type'] = 'unknown'
            if( 'repr' in items ):
                info['repr'] = target.get_repr()
            if( 'tags' in items ):
                tags = target.get_tags()
                info['tags'] = map( lambda x: x.get_name(), tags )
            if( 'names' in items ):
                info['names'] = target.get_names()
            if( 'duplication' in items ):
                if( target.is_duplicate() ):
                    info['duplication'] = 'duplicate'
                elif( target.is_variant() ):
                    info['duplication'] = 'variant'
                else:
                    info['duplication'] = 'original'
            if( 'similar_to' in items ):
                similar = target.get_similar_to()
                if( similar is not None ):
                    info['similar_to'] = [ similar.get_id(), similar.get_repr() ]
            if( 'duplicates' in items ):
                duplicates = target.get_duplicates()
                info['duplicates'] = map(
                        lambda x: [ x.get_id(), x.get_repr() ],
                        duplicates )
            if( 'variants' in items ):
                variants = target.get_variants()
                info['variants'] = map(
                        lambda x: [ x.get_id(), x.get_repr() ],
                        variants )
            if( 'albums' in items ):
                albums = target.get_albums()
                info['albums'] = map(
                        lambda x: [ x.get_id(), x.get_repr() ],
                        albums )
            if( isinstance( target, higu.Album ) and 'files' in items ):
                files = target.get_files()
                info['files'] = map(
                        lambda x: [ x.get_id(), x.get_repr() ],
                        albums )

            return info

        results = map( fetch_info, targets )
        return {
            'info' : results,
            'result' : 'ok',
        }

    def cmd_tag( self, data ):

        print 'xxx'
        print data

        targets = data['targets']
        targets = map( self.db.get_object_by_id, targets )

        add_tags = data['add_tags']
        sub_tags = data['sub_tags']
        new_tags = data['new_tags']

        add = map( self.db.get_tag, add_tags )
        sub = map( self.db.get_tag, sub_tags )
        add += map( self.db.make_tag, new_tags )

        for obj in targets:
            for t in sub:
                obj.unassign( t )
            for t in add:
                obj.assign( t )

        self.db.commit()

        return { 'result' : 'ok' }

init = higu.init
init_default = higu.init_default
