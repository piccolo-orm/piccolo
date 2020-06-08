from ..base import DBTestCase
from ..example_project.tables import Band, Poster


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


class TestIntUpdateOperators(DBTestCase):
    def test_add(self):
        self.insert_row()

        Band.update({Band.popularity: Band.popularity + 10}).run_sync()

        response = Band.select(Band.popularity).first().run_sync()

        self.assertEqual(response["popularity"], 1010)

    def test_add_column(self):
        self.insert_row()

        Band.update(
            {Band.popularity: Band.popularity + Band.popularity}
        ).run_sync()

        response = Band.select(Band.popularity).first().run_sync()

        self.assertEqual(response["popularity"], 2000)

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


class TestVarcharUpdateOperators(DBTestCase):
    def test_add(self):
        self.insert_row()

        Band.update({Band.name: Band.name + "!!!"}).run_sync()

        response = Band.select(Band.name).first().run_sync()

        self.assertEqual(response["name"], "Pythonistas!!!")

    def test_add_column(self):
        self.insert_row()

        Band.update({Band.name: Band.name + Band.name}).run_sync()

        response = Band.select(Band.name).first().run_sync()

        self.assertEqual(response["name"], "PythonistasPythonistas")

    def test_radd(self):
        self.insert_row()

        Band.update({Band.name: "!!!" + Band.name}).run_sync()

        response = Band.select(Band.name).first().run_sync()

        self.assertEqual(response["name"], "!!!Pythonistas")


class TestTextUpdateOperators(DBTestCase):
    def setUp(self):
        super().setUp()
        Poster(content="Join us for this amazing show").save().run_sync()

    def test_add(self):
        Poster.update({Poster.content: Poster.content + "!!!"}).run_sync()

        response = Poster.select(Poster.content).first().run_sync()

        self.assertEqual(
            response["content"], "Join us for this amazing show!!!"
        )

    def test_add_column(self):
        self.insert_row()

        Poster.update(
            {Poster.content: Poster.content + Poster.content}
        ).run_sync()

        response = Poster.select(Poster.content).first().run_sync()

        self.assertEqual(
            response["content"], "Join us for this amazing show" * 2,
        )

    def test_radd(self):
        self.insert_row()

        Poster.update({Poster.content: "!!!" + Poster.content}).run_sync()

        response = Poster.select(Poster.content).first().run_sync()

        self.assertEqual(
            response["content"], "!!!Join us for this amazing show"
        )
