import higu
import model

from sqlalchemy import func;

def check_dups_dbi():

    s = model.Session()
    q = s.query( model.DatabaseInfo )
    it = q.__iter__()

    info = it.next()

    for item in it:
        assert False, 'Multiple entries in DBI'

def check_dups_objl():

    s = model.Session()
    q = s.query( model.Object ) \
         .group_by( model.Object.id ) \
         .having( func.count() > 1 )

    print 'The following duplicates exist in objl:'
    for item in q:
        print item

def check_dups_tags():

    s = model.Session()
    q = s.query( model.Object ) \
         .filter( model.Object.type == model.TYPE_CLASSIFIER ) \
         .group_by( model.Object.name ) \
         .having( func.count() > 1 )

    print 'The following duplicate tags exist in objl:'
    for item in q:
        print item

def check_tag_names():

    s = model.Session()
    q = s.query( model.Object ) \
         .filter( model.Object.type == model.TYPE_CLASSIFIER )

    print 'The following tags have bad names:'
    for item in q:
        try:
            higu.check_tag_name( item.name )
        except ValueError:
            print item

def check_dups_fchk():

    s = model.Session()
    q = s.query( model.FileChecksum ) \
         .group_by( model.FileChecksum.id ) \
         .having( func.count() > 1 )

    print 'The following duplicates exist in fchk:'
    for item in q:
        print item

def check_dups_rel2():

    s = model.Session()
    q = s.query( model.Relation ) \
         .group_by( model.Relation.child, model.Relation.parent ) \
         .having( func.count() > 1 )

    print 'The following duplicates exist in rel2:'
    for item in q:
        print item

def check_dups_mtda():

    s = model.Session()
    q = s.query( model.Metadata ) \
         .group_by( model.Metadata.id, model.Metadata.key ) \
         .having( func.count() > 1 )

    print 'The following duplicates exist in mtda:'
    for item in q:
        print item

def check():

    check_dups_dbi()
    check_dups_objl()
    check_dups_tags()
    check_tag_names()
    check_dups_fchk()
    check_dups_rel2()
    check_dups_mtda()

def init( config_file = None ):

    higu.init( config_file )

if( __name__ == '__main__' ):

    import sys

    argv = sys.argv[1:]

    if( len( argv ) < 1 ):
        print 'Usage: modelcheck.py [-c config]'

    if( argv[0] == '-c' ):
        init( argv[1] )
        argv = argv[2:]
    else:
        init()

    check()

# vim:sts=4:et:sw=4
