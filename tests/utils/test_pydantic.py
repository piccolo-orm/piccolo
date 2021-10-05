import decimal
from unittest import TestCase

import pydantic
from pydantic import ValidationError

from piccolo.columns import JSON, JSONB, Array, Numeric, Secret, Text, Varchar
from piccolo.columns.column_types import ForeignKey
from piccolo.table import Table
from piccolo.utils.pydantic import create_pydantic_model


class TestVarcharColumn(TestCase):
    def test_varchar_length(self):
        class Director(Table):
            name = Varchar(length=10)

        pydantic_model = create_pydantic_model(table=Director)

        with self.assertRaises(ValidationError):
            pydantic_model(name="This is a really long name")

        pydantic_model(name="short name")


class TestNumericColumn(TestCase):
    """
    Numeric and Decimal are the same - so we'll just Numeric.
    """

    def test_numeric_digits(self):
        class Movie(Table):
            box_office = Numeric(digits=(5, 1))

        pydantic_model = create_pydantic_model(table=Movie)

        with self.assertRaises(ValidationError):
            # This should fail as there are too much numbers after the decimal
            # point
            pydantic_model(box_office=decimal.Decimal("1.11"))

        with self.assertRaises(ValidationError):
            # This should fail as there are too much numbers in total
            pydantic_model(box_office=decimal.Decimal("11111.1"))

        pydantic_model(box_office=decimal.Decimal("1.0"))

    def test_numeric_without_digits(self):
        class Movie(Table):
            box_office = Numeric()

        try:
            create_pydantic_model(table=Movie)
        except TypeError:
            self.fail(
                "Creating numeric field without"
                " digits failed in pydantic model."
            )
        else:
            self.assertTrue(True)


class TestSecretColumn(TestCase):
    def test_secret_param(self):
        class TopSecret(Table):
            confidential = Secret()

        pydantic_model = create_pydantic_model(table=TopSecret)
        self.assertEqual(
            pydantic_model.schema()["properties"]["confidential"]["extra"][
                "secret"
            ],
            True,
        )


class TestArrayColumn(TestCase):
    def test_array_param(self):
        class Band(Table):
            members = Array(base_column=Varchar(length=16))

        pydantic_model = create_pydantic_model(table=Band)

        self.assertEqual(
            pydantic_model.schema()["properties"]["members"]["items"]["type"],
            "string",
        )


class TestTextColumn(TestCase):
    def test_text_format(self):
        class Band(Table):
            bio = Text()

        pydantic_model = create_pydantic_model(table=Band)

        self.assertEqual(
            pydantic_model.schema()["properties"]["bio"]["format"],
            "text-area",
        )


class TestColumnHelpText(TestCase):
    """
    Make sure that columns with `help_text` attribute defined have the
    relevant text appear in the schema.
    """

    def test_help_text_present(self):
        help_text = "In millions of US dollars."

        class Movie(Table):
            box_office = Numeric(digits=(5, 1), help_text=help_text)

        pydantic_model = create_pydantic_model(table=Movie)
        self.assertEqual(
            pydantic_model.schema()["properties"]["box_office"]["extra"][
                "help_text"
            ],
            help_text,
        )


class TestTableHelpText(TestCase):
    """
    Make sure that tables with `help_text` attribute defined have the
    relevant text appear in the schema.
    """

    def test_help_text_present(self):
        help_text = "Movies which were released in cinemas."

        class Movie(Table, help_text=help_text):
            name = Varchar()

        pydantic_model = create_pydantic_model(table=Movie)
        self.assertEqual(
            pydantic_model.schema()["help_text"],
            help_text,
        )


class TestJSONColumn(TestCase):
    def test_default(self):
        class Movie(Table):
            meta = JSON()
            meta_b = JSONB()

        pydantic_model = create_pydantic_model(table=Movie)

        json_string = '{"code": 12345}'

        model_instance = pydantic_model(meta=json_string, meta_b=json_string)
        self.assertEqual(model_instance.meta, json_string)
        self.assertEqual(model_instance.meta_b, json_string)

    def test_deserialize_json(self):
        class Movie(Table):
            meta = JSON()
            meta_b = JSONB()

        pydantic_model = create_pydantic_model(
            table=Movie, deserialize_json=True
        )

        json_string = '{"code": 12345}'
        output = {"code": 12345}

        model_instance = pydantic_model(meta=json_string, meta_b=json_string)
        self.assertEqual(model_instance.meta, output)
        self.assertEqual(model_instance.meta_b, output)

    def test_validation(self):
        class Movie(Table):
            meta = JSON()
            meta_b = JSONB()

        for deserialize_json in (True, False):
            pydantic_model = create_pydantic_model(
                table=Movie, deserialize_json=deserialize_json
            )

            json_string = "error"

            with self.assertRaises(pydantic.ValidationError):
                pydantic_model(meta=json_string, meta_b=json_string)

    def test_json_format(self):
        class Movie(Table):
            features = JSON()

        pydantic_model = create_pydantic_model(table=Movie)

        self.assertEqual(
            pydantic_model.schema()["properties"]["features"]["format"],
            "json",
        )


class TestExcludeColumn(TestCase):
    def test_all(self):
        class Computer(Table):
            CPU = Varchar()
            GPU = Varchar()

        pydantic_model = create_pydantic_model(Computer, exclude_columns=())

        properties = pydantic_model.schema()["properties"]
        self.assertIsInstance(properties["GPU"], dict)
        self.assertIsInstance(properties["CPU"], dict)

    def test_exclude(self):
        class Computer(Table):
            CPU = Varchar()
            GPU = Varchar()

        pydantic_model = create_pydantic_model(
            Computer,
            exclude_columns=(Computer.CPU,),
        )

        properties = pydantic_model.schema()["properties"]
        self.assertIsInstance(properties.get("GPU"), dict)
        self.assertIsNone(properties.get("CPU"))

    def test_exclude_all_manually(self):
        class Computer(Table):
            GPU = Varchar()
            CPU = Varchar()

        pydantic_model = create_pydantic_model(
            Computer,
            exclude_columns=(Computer.GPU, Computer.CPU),
        )

        self.assertEqual(pydantic_model.schema()["properties"], {})

    def test_exclude_all_meta(self):
        class Computer(Table):
            GPU = Varchar()
            CPU = Varchar()

        pydantic_model = create_pydantic_model(
            Computer,
            exclude_columns=tuple(Computer._meta.columns),
        )

        self.assertEqual(pydantic_model.schema()["properties"], {})

    def test_invalid_column_str(self):
        class Computer(Table):
            CPU = Varchar()
            GPU = Varchar()

        with self.assertRaises(ValueError):
            create_pydantic_model(
                Computer,
                exclude_columns=("CPU",),
            )

    def test_invalid_column_different_table(self):
        class Computer(Table):
            CPU = Varchar()
            GPU = Varchar()

        class Computer2(Table):
            SSD = Varchar()

        with self.assertRaises(ValueError):
            create_pydantic_model(Computer, exclude_columns=(Computer2.SSD,))

    def test_invalid_column_different_table_same_type(self):
        class Computer(Table):
            CPU = Varchar()
            GPU = Varchar()

        class Computer2(Table):
            CPU = Varchar()

        with self.assertRaises(ValueError):
            create_pydantic_model(Computer, exclude_columns=(Computer2.CPU,))


class TestNestedModel(TestCase):
    def test_nested_models(self):
        class Country(Table):
            name = Varchar(length=10)

        class Director(Table):
            name = Varchar(length=10)
            country = ForeignKey(Country)

        class Movie(Table):
            name = Varchar(length=10)
            director = ForeignKey(Director)

        MovieModel = create_pydantic_model(table=Movie, nested=True)

        #######################################################################

        DirectorModel = MovieModel.__fields__["director"].type_

        self.assertTrue(issubclass(DirectorModel, pydantic.BaseModel))

        director_model_keys = [i for i in DirectorModel.__fields__.keys()]
        self.assertEqual(director_model_keys, ["name", "country"])

        #######################################################################

        CountryModel = DirectorModel.__fields__["country"].type_

        self.assertTrue(issubclass(CountryModel, pydantic.BaseModel))

        country_model_keys = [i for i in CountryModel.__fields__.keys()]
        self.assertEqual(country_model_keys, ["name"])

    def test_cascaded_args(self):
        """
        Make sure that arguments passed to ``create_pydantic_model`` are
        cascaded to nested models.
        """

        class Country(Table):
            name = Varchar(length=10)

        class Director(Table):
            name = Varchar(length=10)
            country = ForeignKey(Country)

        class Movie(Table):
            name = Varchar(length=10)
            director = ForeignKey(Director)

        MovieModel = create_pydantic_model(
            table=Movie, nested=True, include_default_columns=True
        )

        #######################################################################

        DirectorModel = MovieModel.__fields__["director"].type_

        self.assertTrue(issubclass(DirectorModel, pydantic.BaseModel))

        director_model_keys = [i for i in DirectorModel.__fields__.keys()]
        self.assertEqual(director_model_keys, ["id", "name", "country"])

        #######################################################################

        CountryModel = DirectorModel.__fields__["country"].type_

        self.assertTrue(issubclass(CountryModel, pydantic.BaseModel))

        country_model_keys = [i for i in CountryModel.__fields__.keys()]
        self.assertEqual(country_model_keys, ["id", "name"])


class TestDBColumnName(TestCase):
    def test_db_column_name(self):
        """
        Make sure that the Pydantic model has an alias if ``db_column_name``
        is specified for a column.
        """

        class Band(Table):
            name = Varchar(db_column_name="regrettable_column_name")

        BandModel = create_pydantic_model(table=Band)

        model = BandModel(regrettable_column_name="test")

        self.assertTrue(model.name == "test")
