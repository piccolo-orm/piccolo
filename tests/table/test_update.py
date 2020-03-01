from ..base import DBTestCase
from ..example_project.tables import Band


class TestUpdate(DBTestCase):
    def test_update(self):
        self.insert_rows()

        Band.update({Band.name: "Pythonistas3"}).where(
            Band.name == "Pythonistas"
        ).run_sync()

        response = (
            Band.select(Band.name)
            .where(Band.name == "Pythonistas3")
            .run_sync()
        )
        print(f"response = {response}")

        self.assertEqual(response, [{"name": "Pythonistas3"}])

    def test_update_values(self):
        self.insert_rows()

        Band.update({Band.name: "Pythonistas3"}).where(
            Band.name == "Pythonistas"
        ).run_sync()

        response = (
            Band.select(Band.name)
            .where(Band.name == "Pythonistas3")
            .run_sync()
        )
        print(f"response = {response}")

        self.assertEqual(response, [{"name": "Pythonistas3"}])


class TestUpdateOperators(DBTestCase):
    def test_add(self):
        self.insert_row()

        Band.update({Band.popularity: Band.popularity + 10}).run_sync()

        response = Band.select(Band.popularity).first().run_sync()

        self.assertEqual(response["popularity"], 1010)

    def test_radd(self):
        self.insert_row()

        Band.update({Band.popularity: 10 + Band.popularity}).run_sync()

        response = Band.select(Band.popularity).first().run_sync()

        self.assertEqual(response["popularity"], 1010)

    def test_sub(self):
        self.insert_row()

        Band.update({Band.popularity: Band.popularity - 10}).run_sync()

        response = Band.select(Band.popularity).first().run_sync()

        self.assertEqual(response["popularity"], 990)

    def test_rsub(self):
        self.insert_row()

        Band.update({Band.popularity: 1100 - Band.popularity}).run_sync()

        response = Band.select(Band.popularity).first().run_sync()

        self.assertEqual(response["popularity"], 100)

    def test_mul(self):
        self.insert_row()

        Band.update({Band.popularity: Band.popularity * 2}).run_sync()

        response = Band.select(Band.popularity).first().run_sync()

        self.assertEqual(response["popularity"], 2000)

    def test_rmul(self):
        self.insert_row()

        Band.update({Band.popularity: 2 * Band.popularity}).run_sync()

        response = Band.select(Band.popularity).first().run_sync()

        self.assertEqual(response["popularity"], 2000)

    def test_div(self):
        self.insert_row()

        Band.update({Band.popularity: Band.popularity / 10}).run_sync()

        response = Band.select(Band.popularity).first().run_sync()

        self.assertEqual(response["popularity"], 100)

    def test_rdiv(self):
        self.insert_row()

        Band.update({Band.popularity: 1000 / Band.popularity}).run_sync()

        response = Band.select(Band.popularity).first().run_sync()

        self.assertEqual(response["popularity"], 1)
