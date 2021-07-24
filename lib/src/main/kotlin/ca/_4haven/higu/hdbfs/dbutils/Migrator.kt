package ca._4haven.higu.hdbfs.dbutils

interface Migrator {
    fun determine_schema_info( session: Session ): Triple<Int,Int,String>
    fun init_schema( session: Session, ver: Int, rev: Int )
    fun upgrade_schema( session: Session, ver: Int, rev: Int )
}