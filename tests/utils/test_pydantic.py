import decimal
from unittest import TestCase

import pydantic
import pytest
from pydantic import ValidationError

from piccolo.columns import (
    JSON,
    JSONB,
    Array,
    Email,
    Integer,
    Numeric,
    Secret,
    Text,
    Varchar,
)
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


class TestEmailColumn(TestCase):
    def test_email(self):
        class Director(Table):
            email = Email()

        pydantic_model = create_pydantic_model(table=Director)

        self.assertEqual(
            pydantic_model.schema()["properties"]["email"]["format"],
            "email",
        )

        with self.assertRaises(ValidationError):
            pydantic_model(email="not a valid email")

        # Shouldn't raise an exception:
        pydantic_model(email="test@gmail.com")


class TestNumericColumn(TestCase):
    """
    Numeric and Decimal are the same - so we'll just test Numeric.
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


class TestForeignKeyColumn(TestCase):
    def test_target_column(self):
        """
        Make sure the target_column is correctly set in the Pydantic schema.
        """

        class Manager(Table):
            name = Varchar(unique=True)

        class BandA(Table):
            manager = ForeignKey(Manager, target_column=Manager.name)

        class BandB(Table):
            manager = ForeignKey(Manager, target_column="name")

        class BandC(Table):
            manager = ForeignKey(Manager)

        self.assertEqual(
            create_pydantic_model(table=BandA).schema()["properties"][
                "manager"
            ]["extra"]["target_column"],
            "name",
        )

        self.assertEqual(
            create_pydantic_model(table=BandB).schema()["properties"][
                "manager"
            ]["extra"]["target_column"],
            "name",
        )

        self.assertEqual(
            create_pydantic_model(table=BandC).schema()["properties"][
                "manager"
            ]["extra"]["target_column"],
            "id",
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

    def test_null_value(self):
        class Movie(Table):
            meta = JSON(null=True)
            meta_b = JSONB(null=True)

        pydantic_model = create_pydantic_model(table=Movie)
        movie = pydantic_model(meta=None, meta_b=None)

        self.assertIsNone(movie.meta)
        self.assertIsNone(movie.meta_b)


class TestExcludeColumns(TestCase):
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

    def test_exclude_nested(self):
        class Manager(Table):
            name = Varchar()
            phone_number = Integer()

        class Band(Table):
            name = Varchar()
            manager = ForeignKey(Manager)
            popularity = Integer()

        pydantic_model = create_pydantic_model(
            table=Band,
            exclude_columns=(
                Band.popularity,
                Band.manager.phone_number,
            ),
            nested=(Band.manager,),
        )

        model_instance = pydantic_model(
            name="Pythonistas", manager={"name": "Guido"}
        )
        self.assertEqual(
            model_instance.dict(),
            {"name": "Pythonistas", "manager": {"name": "Guido"}},
        )


class TestIncludeColumns(TestCase):
    def test_include(self):
        class Band(Table):
            name = Varchar()
            popularity = Integer()

        pydantic_model = create_pydantic_model(
            Band,
            include_columns=(Band.name,),
        )

        properties = pydantic_model.schema()["properties"]
        self.assertIsInstance(properties.get("name"), dict)
        self.assertIsNone(properties.get("popularity"))

    def test_include_exclude_error(self):
        """
        An exception should be raised if both `include_columns` and
        `exclude_columns` are provided.
        """

        class Band(Table):
            name = Varchar()
            popularity = Integer()

        with self.assertRaises(ValueError):
            create_pydantic_model(
                Band,
                exclude_columns=(Band.name,),
                include_columns=(Band.name,),
            )

    def test_nested(self):
        """
        Make sure that columns on related tables work.
        """

        class Manager(Table):
            name = Varchar()
            phone_number = Integer()

        class Band(Table):
            name = Varchar()
            manager = ForeignKey(Manager)
            popularity = Integer()

        pydantic_model = create_pydantic_model(
            table=Band,
            include_columns=(
                Band.name,
                Band.manager.name,
            ),
            nested=(Band.manager,),
        )

        model_instance = pydantic_model(
            name="Pythonistas", manager={"name": "Guido"}
        )
        self.assertEqual(
            model_instance.dict(),
            {"name": "Pythonistas", "manager": {"name": "Guido"}},
        )


class TestNestedModel(TestCase):
    def test_true(self):
        """
        Make sure all foreign key columns are converted to nested models, when
        `nested=True`.
        """

        class Country(Table):
            name = Varchar(length=10)

        class Manager(Table):
            name = Varchar(length=10)
            country = ForeignKey(Country)

        class Band(Table):
            name = Varchar(length=10)
            manager = ForeignKey(Manager)

        BandModel = create_pydantic_model(table=Band, nested=True)

        #######################################################################

        ManagerModel = BandModel.__fields__["manager"].type_
        self.assertTrue(issubclass(ManagerModel, pydantic.BaseModel))
        self.assertEqual(
            [i for i in ManagerModel.__fields__.keys()], ["name", "country"]
        )

        #######################################################################

        CountryModel = ManagerModel.__fields__["country"].type_
        self.assertTrue(issubclass(CountryModel, pydantic.BaseModel))
        self.assertEqual([i for i in CountryModel.__fields__.keys()], ["name"])

    def test_tuple(self):
        """
        Make sure only the specified foreign key columns are converted to
        nested models.
        """

        class Country(Table):
            name = Varchar()

        class Manager(Table):
            name = Varchar()
            country = ForeignKey(Country)

        class Band(Table):
            name = Varchar()
            manager = ForeignKey(Manager)
            assistant_manager = ForeignKey(Manager)

        class Venue(Table):
            name = Varchar()

        class Concert(Table):
            band_1 = ForeignKey(Band)
            band_2 = ForeignKey(Band)
            venue = ForeignKey(Venue)

        #######################################################################
        # Test one level deep

        BandModel = create_pydantic_model(table=Band, nested=(Band.manager,))

        ManagerModel = BandModel.__fields__["manager"].type_
        self.assertTrue(issubclass(ManagerModel, pydantic.BaseModel))
        self.assertEqual(
            [i for i in ManagerModel.__fields__.keys()], ["name", "country"]
        )
        self.assertEqual(ManagerModel.__qualname__, "Band.manager")

        AssistantManagerType = BandModel.__fields__["assistant_manager"].type_
        self.assertIs(AssistantManagerType, int)

        #######################################################################
        # Test two levels deep

        BandModel = create_pydantic_model(
            table=Band, nested=(Band.manager.country,)
        )

        ManagerModel = BandModel.__fields__["manager"].type_
        self.assertTrue(issubclass(ManagerModel, pydantic.BaseModel))
        self.assertEqual(
            [i for i in ManagerModel.__fields__.keys()], ["name", "country"]
        )
        self.assertEqual(ManagerModel.__qualname__, "Band.manager")

        AssistantManagerType = BandModel.__fields__["assistant_manager"].type_
        self.assertIs(AssistantManagerType, int)

        CountryModel = ManagerModel.__fields__["country"].type_
        self.assertTrue(issubclass(CountryModel, pydantic.BaseModel))
        self.assertEqual([i for i in CountryModel.__fields__.keys()], ["name"])
        self.assertEqual(CountryModel.__qualname__, "Band.manager.country")

        #######################################################################
        # Test three levels deep

        ConcertModel = create_pydantic_model(
            Concert, nested=(Concert.band_1.manager,)
        )

        VenueModel = ConcertModel.__fields__["venue"].type_
        self.assertIs(VenueModel, int)

        BandModel = ConcertModel.__fields__["band_1"].type_
        self.assertTrue(issubclass(BandModel, pydantic.BaseModel))
        self.assertEqual(
            [i for i in BandModel.__fields__.keys()],
            ["name", "manager", "assistant_manager"],
        )
        self.assertEqual(BandModel.__qualname__, "Concert.band_1")

        ManagerModel = BandModel.__fields__["manager"].type_
        self.assertTrue(issubclass(ManagerModel, pydantic.BaseModel))
        self.assertEqual(
            [i for i in ManagerModel.__fields__.keys()],
            ["name", "country"],
        )
        self.assertEqual(ManagerModel.__qualname__, "Concert.band_1.manager")

        AssistantManagerType = BandModel.__fields__["assistant_manager"].type_
        self.assertIs(AssistantManagerType, int)

        CountryModel = ManagerModel.__fields__["country"].type_
        self.assertIs(CountryModel, int)

        #######################################################################
        # Test with `model_name` arg

        MyConcertModel = create_pydantic_model(
            Concert,
            nested=(Concert.band_1.manager,),
            model_name="MyConcertModel",
        )

        BandModel = MyConcertModel.__fields__["band_1"].type_
        self.assertEqual(BandModel.__qualname__, "MyConcertModel.band_1")

        ManagerModel = BandModel.__fields__["manager"].type_
        self.assertEqual(
            ManagerModel.__qualname__, "MyConcertModel.band_1.manager"
        )

    def test_cascaded_args(self):
        """
        Make sure that arguments passed to ``create_pydantic_model`` are
        cascaded to nested models.
        """

        class Country(Table):
            name = Varchar(length=10)

        class Manager(Table):
            name = Varchar(length=10)
            country = ForeignKey(Country)

        class Band(Table):
            name = Varchar(length=10)
            manager = ForeignKey(Manager)

        BandModel = create_pydantic_model(
            table=Band, nested=True, include_default_columns=True
        )

        ManagerModel = BandModel.__fields__["manager"].type_
        self.assertTrue(issubclass(ManagerModel, pydantic.BaseModel))
        self.assertEqual(
            [i for i in ManagerModel.__fields__.keys()],
            ["id", "name", "country"],
        )

        CountryModel = ManagerModel.__fields__["country"].type_
        self.assertTrue(issubclass(CountryModel, pydantic.BaseModel))
        self.assertEqual(
            [i for i in CountryModel.__fields__.keys()], ["id", "name"]
        )


class TestRecursionDepth(TestCase):
    def test_max(self):
        class Country(Table):
            name = Varchar()

        class Manager(Table):
            name = Varchar()
            country = ForeignKey(Country)

        class Band(Table):
            name = Varchar()
            manager = ForeignKey(Manager)
            assistant_manager = ForeignKey(Manager)

        class Venue(Table):
            name = Varchar()

        class Concert(Table):
            band = ForeignKey(Band)
            venue = ForeignKey(Venue)

        ConcertModel = create_pydantic_model(
            table=Concert, nested=True, max_recursion_depth=2
        )

        VenueModel = ConcertModel.__fields__["venue"].type_
        self.assertTrue(issubclass(VenueModel, pydantic.BaseModel))

        BandModel = ConcertModel.__fields__["band"].type_
        self.assertTrue(issubclass(BandModel, pydantic.BaseModel))

        ManagerModel = BandModel.__fields__["manager"].type_
        self.assertTrue(issubclass(ManagerModel, pydantic.BaseModel))

        # We should have hit the recursion depth:
        CountryModel = ManagerModel.__fields__["country"].type_
        self.assertIs(CountryModel, int)


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

        self.assertEqual(model.name, "test")


class TestSchemaExtraKwargs(TestCase):
    def test_schema_extra_kwargs(self):
        """
        Make sure that the ``schema_extra_kwargs`` arguments are reflected in
        Pydantic model's schema.
        """

        class Band(Table):
            name = Varchar()

        model = create_pydantic_model(Band, visible_columns=("name",))
        self.assertEqual(model.schema()["visible_columns"], ("name",))


class TestPydanticExtraFields(TestCase):
    def test_pydantic_extra_fields(self):
        """
        Make sure that the value of ``extra`` in the config class
        is correctly propagated to the generated model.
        """

        class Band(Table):
            name = Varchar()

        for v in ["ignore", "allow", "forbid"]:

            class MyConfig(pydantic.BaseConfig):
                extra = v

            model = create_pydantic_model(Band, pydantic_config_class=MyConfig)
            self.assertEqual(model.Config.extra, v)

    def test_pydantic_invalid_extra_fields(self):
        """
        Make sure that invalid values for ``extra`` in the config class
        are rejected.
        """

        class Band(Table):
            name = Varchar()

        class MyConfig(pydantic.BaseConfig):
            extra = "foobar"

        with pytest.raises(ValueError):
            create_pydantic_model(Band, pydantic_config_class=MyConfig)
