from piccolo.apps.migrations.auto import MigrationManager

ID = "2020-03-31T20:38:22"


async def forwards():
    manager = MigrationManager(migration_id=ID)
    manager.add_table("Band", tablename="band")
    manager.add_column(
        table_class_name="Band",
        tablename="band",
        column_name="name",
        column_class_name="Varchar",
        params={
            "length": 150,
            "default": "",
            "null": True,
            "primary": False,
            "key": False,
            "unique": False,
            "index": False,
        },
    )

    return manager
