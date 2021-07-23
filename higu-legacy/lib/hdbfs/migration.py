from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Schema( Base ):
    __tablename__ = 'db_schema'

    uuid = Column( Text, primary_key = True )
    schema = Column( Text, nullable = False )
    ver = Column( Integer, nullable = False )
    rev = Column( Integer, nullable = False )

    def __init__( self, schema, ver, rev ):

        self.uuid = uuid.uuid1()
        self.schema = schema
        self.ver = ver
        self.rev = rev

    def __repr__( self ):

        return 'Schema( %r, %r, %r, %r )' % ( self.uuid, self.schema, self.ver, self.rev )

def back_up_db_file( dbfile ):

    f = file( dbfile, 'rb' )
    n = 0
    while( 1 ):
        if( not os.path.isfile( dbfile + '.bak' + str( n ) ) ):
            break
        n += 1
    g = file( dbfile + '.bak' + str( n ), 'wb' )
    while( 1 ):
        buff = f.read( 1024 )
        if( len( buff ) == 0 ):
            f.close()
            g.close()
            break
        g.write( buff )

def _determine_db_version( dbfile, schema, migrator ):

    engine = create_engine( 'sqlite:///' + database_file )

def migrate( dbfile, migrator ):

    session = SqlLiteDatabase( dbfile )
    dbi = ver8tables.DatabaseInfo( session.get_table( 'dbi' ) )

    while( True ):
        ver = dbi.get_version()
        rev = dbi.get_revision()
        log.debug( 'Database is version v%s', str( ver ) )
     
        if( ver != VERSION or rev != REVISION ):

            # Back-up the dbfile
            back_up_db_file( dbfile )

            if( ver == 0 ): 
                pre8.upgrade_from_0_to_1( log, session )
                continue
            elif( ver == 1 ):
                pre8.upgrade_from_1_to_2( log, session )
                continue
            elif( ver == 2 ):
                pre8.upgrade_from_2_to_3( log, session )
                continue
            elif( ver == 3 ):
                pre8.upgrade_from_3_to_4( log, session )
                continue
            elif( ver == 4 ):
                pre8.upgrade_from_4_to_5( log, session )
                continue
            elif( ver == 5 ):
                pre8.upgrade_from_5_to_6( log, session )
                continue
            elif( ver == 6 ):
                pre8.upgrade_from_6_to_7( log, session )
                continue
            elif( ver == 7 ):
                pre8.upgrade_from_7_to_8( log, session )
                continue
            elif( ver == 8 and rev == 0 ):
                ver8rules.upgrade_from_8_to_8_1( log, session )
                continue
            else:
                raise RuntimeError( 'Incompatible database version' )
        elif( dbi.get_revision() > REVISION ):
            raise RuntimeError( 'Incompatible database revision' )
        elif( dbi.get_revision() != REVISION ):
            dbi.set_revision( REVISION )
            session.commit()

        break

    session.commit()
    session.close()
