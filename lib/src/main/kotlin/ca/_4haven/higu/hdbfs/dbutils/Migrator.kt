package ca._4haven.higu.hdbfs.dbutils

interface Migrator {
    fun determine_schema_info( session: Session ): SchemaEntry?
    fun init_schema( session: Session, version: Schema.Version )
    fun upgrade_schema( session: Session, version: Schema.Version ): Schema.Version
}