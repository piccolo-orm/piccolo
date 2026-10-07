from piccolo.columns import ForeignKey, Integer, Serial, Varchar
from piccolo.table import Table
from piccolo.testing.test_case import TableTest


class Manager(Table, tablename="managerTable"):
    primaryKey = Serial(primary_key=True)
    theName = Varchar()


class Band(Table, tablename="bandTable"):
    primaryKey = Serial(primary_key=True)
    theName = Varchar()
    theManager = ForeignKey(Manager)
    popularityValue = Integer()


class TestCamelCase(TableTest):

    tables = [Manager, Band]

    def test_queries(self):
        """
        Make sure that basic queries work when the columns and table names use
        camelCase (or similarly TitleCase).
        """
        manager_names = ("Guido", "Maz", "Graydon")
        band_names = ("Pythonistas", "Rubyists", "Rustaceans")

        # Test create
        for manager_name, band_name in zip(manager_names, band_names):
            manager = Manager.objects().create(theName=manager_name).run_sync()
            Band.objects().create(
                theName=band_name, theManager=manager
            ).run_sync()

        # Test select, with joins
        response = (
            Band.select(
                Band.theName,
                Band.theManager.theName.as_alias("theManagerName"),
            )
            .order_by(Band.theName)
            .run_sync()
        )
        self.assertListEqual(
            response,
            [
                {"theName": "Pythonistas", "theManagerName": "Guido"},
                {"theName": "Rubyists", "theManagerName": "Maz"},
                {"theName": "Rustaceans", "theManagerName": "Graydon"},
            ],
        )

        # Test delete
        Band.delete().where(Band.theName == "Rubyists").run_sync()

        # Test exists
        self.assertFalse(
            Band.exists().where(Band.theName == "Rubyists").run_sync()
        )

        # Test math delegate
        # https://github.com/piccolo-orm/piccolo/issues/1402
        Band.update(
            {Band.popularityValue: Band.popularityValue + 10},
            force=True,
        ).run_sync()
