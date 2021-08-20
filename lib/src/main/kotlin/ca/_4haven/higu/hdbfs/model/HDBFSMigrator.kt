package ca._4haven.higu.hdbfs.model

import ca._4haven.higu.hdbfs.dbutils.*

class HDBFSMigrator : Migrator {

    override fun determine_schema_info( session: Session ): SchemaEntry? {
        /* TODO
        try:
            result = session.execute( 'SELECT ver, rev, uuid FROM dbi' ).first()
            return result['ver'], result['rev'], result['uuid']
        except:
            return None, None, None*/
        return null
    }

    override fun init_schema( session: Session, version: Schema.Version ) {
        session.useTransaction {
            Objects.create( session )
            Streams.create( session )
            Relations.create( session )
            ObjectMetadata.create( session )
            StreamMetadata.create( session )
            StreamLog.create( session )
        }
    }

    override fun upgrade_schema( session: Session, version: Schema.Version ): Schema.Version {
        /* TODO
        if( ver == 0 ): 
            return pre8.upgrade_from_0_to_1( log, session )
        elif( ver == 1 ):
            return pre8.upgrade_from_1_to_2( log, session )
        elif( ver == 2 ):
            return pre8.upgrade_from_2_to_3( log, session )
        elif( ver == 3 ):
            return pre8.upgrade_from_3_to_4( log, session )
        elif( ver == 4 ):
            return pre8.upgrade_from_4_to_5( log, session )
        elif( ver == 5 ):
            return pre8.upgrade_from_5_to_6( log, session )
        elif( ver == 6 ):
            return pre8.upgrade_from_6_to_7( log, session )
        elif( ver == 7 ):
            return pre8.upgrade_from_7_to_8( log, session )
        elif( ver == 8 and rev == 0 ):
            return ver8rules.upgrade_from_8_to_8_1( log, session )
        elif( ver == 8 ):
            return ver8rules.upgrade_from_8_1_to_9( log, session )
        elif( ver == 9 ):
            return ver8rules.upgrade_from_9_to_10( log, session )
        else:
            raise RuntimeError( 'Incompatible database version for upgrade' )*/
        throw RuntimeException()
    }
}