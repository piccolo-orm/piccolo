from unittest import TestCase

from piccolo.columns import Integer, Varchar
from piccolo.query import CTE, CTEColumn, CTEError, CTERef
from piccolo.querystring import QueryString
from piccolo.table import Table, create_db_tables_sync, drop_db_tables_sync


class Employee(Table):
    name = Varchar()
    manager_id = Integer(null=True)


def compile_query(query) -> str:
    sql, _ = query.querystrings[0].compile_string("sqlite")
    return sql


def compile_cte(cte: CTE) -> str:
    sql, _ = cte.get_inner_querystring().compile_string("sqlite")
    return sql


def counter(name: str = "counter", limit: int = 3) -> CTE:
    return CTE.recursive(
        name,
        base=QueryString("SELECT 1"),
        recursive=QueryString(
            f'SELECT "n" + 1 FROM "{name}" WHERE "n" < {limit}'
        ),
        column_names=["n"],
    )


class TestCTEConstruction(TestCase):
    def test_properties(self):
        cte = CTE("numbers", QueryString("SELECT 1"))
        self.assertEqual(cte.name, "numbers")
        self.assertFalse(cte.is_recursive)
        self.assertIsNone(cte.materialized)

        self.assertTrue(counter().is_recursive)
        self.assertEqual(counter().column_names, ("n",))

    def test_query_body(self):
        cte = CTE(
            "managers",
            Employee.select(Employee.id, Employee.name).where(
                Employee.manager_id.is_null()
            ),
            column_names=["id", "name"],
        )
        self.assertEqual(
            compile_cte(cte),
            '"managers" ("id", "name") AS (SELECT ALL "employee"."id" AS '
            '"id", "employee"."name" AS "name" FROM "employee" WHERE '
            '"employee"."manager_id" IS NULL)',
        )

    def test_invalid_names(self):
        for name in ("", "1abc", "has space", 'quo"te', "drop;table", 5):
            with self.subTest(name=name):
                with self.assertRaises(CTEError):
                    CTE(name, QueryString("SELECT 1"))

        for column_name in ("", "1abc", "a-b", None):
            with self.subTest(column_name=column_name):
                with self.assertRaises(CTEError):
                    CTE(
                        "c",
                        QueryString("SELECT 1"),
                        column_names=[column_name],
                    )

    def test_invalid_column_names(self):
        with self.assertRaises(CTEError):
            CTE("c", QueryString("SELECT 1"), column_names=[])

        with self.assertRaises(CTEError):
            CTE("c", QueryString("SELECT 1, 2"), column_names=["a", "a"])

    def test_invalid_materialized(self):
        with self.assertRaises(CTEError):
            CTE("c", QueryString("SELECT 1"), materialized="yes")

    def test_column_count_mismatch(self):
        with self.assertRaises(CTEError):
            CTE(
                "c",
                Employee.select(Employee.id, Employee.name),
                column_names=["id"],
            )

        with self.assertRaises(CTEError):
            CTE.recursive(
                "c",
                base=Employee.select(Employee.id, Employee.name),
                recursive=Employee.select(Employee.id),
                column_names=["id", "name"],
            )

    def test_recursive_requires_column_names(self):
        with self.assertRaises(CTEError):
            CTE(
                "c",
                QueryString("SELECT 1"),
                recursive_body=QueryString("SELECT 2"),
            )

    def test_invalid_body_type(self):
        cte = CTE("c", 123)
        with self.assertRaises(CTEError):
            cte.get_inner_querystring()


class TestCTEInnerSQL(TestCase):
    def test_non_recursive(self):
        cte = CTE("numbers", QueryString("SELECT 42 AS n"))
        self.assertEqual(compile_cte(cte), '"numbers" AS (SELECT 42 AS n)')

    def test_recursive(self):
        self.assertEqual(
            compile_cte(counter()),
            '"counter" ("n") AS (SELECT 1 UNION ALL SELECT "n" + 1 FROM '
            '"counter" WHERE "n" < 3)',
        )

    def test_column_order(self):
        cte = CTE(
            "c",
            QueryString("SELECT 1, 2, 3"),
            column_names=["z", "a", "m"],
        )
        self.assertEqual(
            compile_cte(cte), '"c" ("z", "a", "m") AS (SELECT 1, 2, 3)'
        )

    def test_materialized(self):
        for materialized, keyword in (
            (True, "MATERIALIZED "),
            (False, "NOT MATERIALIZED "),
            (None, ""),
        ):
            with self.subTest(materialized=materialized):
                cte = CTE(
                    "c",
                    QueryString("SELECT 1"),
                    column_names=["v"],
                    materialized=materialized,
                )
                self.assertIs(cte.materialized, materialized)
                self.assertEqual(
                    compile_cte(cte),
                    f'"c" ("v") AS {keyword}(SELECT 1)',
                )


class TestCTERef(TestCase):
    def setUp(self):
        self.ref = CTE(
            "tree",
            QueryString("SELECT 1, 2, 3"),
            column_names=["id", "parent", "depth"],
        ).ref()

    def test_requires_column_names(self):
        with self.assertRaises(CTEError):
            CTE("c", QueryString("SELECT 1")).ref()

    def test_column(self):
        self.assertIsInstance(self.ref, CTERef)
        column = self.ref.column("parent")
        self.assertIsInstance(column, CTEColumn)
        self.assertEqual(str(column), '"tree"."parent"')

        with self.assertRaises(CTEError):
            self.ref.column("missing")

    def test_attribute_access(self):
        self.assertEqual(str(self.ref.depth), '"tree"."depth"')

        with self.assertRaises(AttributeError):
            self.ref.missing

    def test_collection_protocol(self):
        self.assertEqual(len(self.ref), 3)
        self.assertIn("id", self.ref)
        self.assertNotIn("missing", self.ref)
        self.assertNotIn(42, self.ref)
        self.assertEqual(
            [str(column) for column in self.ref],
            ['"tree"."id"', '"tree"."parent"', '"tree"."depth"'],
        )
        self.assertEqual(
            [str(column) for column in self.ref.columns()],
            ['"tree"."id"', '"tree"."parent"', '"tree"."depth"'],
        )

    def test_from_clause(self):
        sql, _ = self.ref.from_clause().compile_string("sqlite")
        self.assertEqual(sql, '"tree"')

    def test_select_all(self):
        sql, _ = self.ref.select_all().compile_string("sqlite")
        self.assertEqual(
            sql,
            'SELECT "tree"."id", "tree"."parent", "tree"."depth" '
            'FROM "tree"',
        )

    def test_column_get_select_string(self):
        sql, _ = self.ref.id.get_select_string("sqlite").compile_string(
            "sqlite"
        )
        self.assertEqual(sql, '"tree"."id"')


class TestWith(TestCase):
    def test_all_query_types(self):
        cte = CTE("numbers", QueryString("SELECT 1"))

        queries = {
            "SELECT": Employee.select(),
            "UPDATE": Employee.update({Employee.name: "x"}, force=True),
            "DELETE": Employee.delete(force=True),
            "INSERT": Employee.insert(Employee(name="x")),
        }
        for keyword, query in queries.items():
            with self.subTest(keyword=keyword):
                self.assertIs(query.with_(cte), query)
                sql = compile_query(query)
                self.assertTrue(
                    sql.startswith('WITH "numbers" AS (SELECT 1) ' + keyword)
                )

    def test_multiple_ctes_keep_order(self):
        query = Employee.select().with_(
            CTE("b", QueryString("SELECT 2")),
            CTE("a", QueryString("SELECT 1")),
        )
        self.assertTrue(
            compile_query(query).startswith(
                'WITH "b" AS (SELECT 2), "a" AS (SELECT 1) SELECT'
            )
        )

    def test_with_called_twice(self):
        query = (
            Employee.select()
            .with_(CTE("a", QueryString("SELECT 1")))
            .with_(CTE("b", QueryString("SELECT 2")))
        )
        self.assertTrue(
            compile_query(query).startswith(
                'WITH "a" AS (SELECT 1), "b" AS (SELECT 2) SELECT'
            )
        )

    def test_recursive_keyword(self):
        plain = CTE("plain", QueryString("SELECT 1"))

        for ctes in ((counter(),), (plain, counter())):
            with self.subTest(count=len(ctes)):
                sql = compile_query(Employee.select().with_(*ctes))
                self.assertTrue(sql.startswith("WITH RECURSIVE "))

        sql = compile_query(Employee.delete(force=True).with_(counter()))
        self.assertTrue(sql.startswith("WITH RECURSIVE "))

        sql = compile_query(Employee.select().with_(plain))
        self.assertFalse(sql.startswith("WITH RECURSIVE "))

    def test_invalid_arguments(self):
        query = Employee.select()

        with self.assertRaises(CTEError):
            query.with_()

        with self.assertRaises(CTEError):
            query.with_("numbers")

        with self.assertRaises(CTEError):
            query.with_(
                CTE("dup", QueryString("SELECT 1")),
                CTE("dup", QueryString("SELECT 2")),
            )

        query.with_(CTE("dup", QueryString("SELECT 1")))
        with self.assertRaises(CTEError):
            query.with_(CTE("dup", QueryString("SELECT 2")))


class TestWithExecution(TestCase):
    def setUp(self):
        create_db_tables_sync(Employee)
        Employee.insert(
            *(
                Employee(
                    {
                        Employee.id: id_,
                        Employee.name: name,
                        Employee.manager_id: manager_id,
                    }
                )
                for id_, name, manager_id in (
                    (1, "ceo", None),
                    (2, "vp", 1),
                    (3, "lead", 2),
                    (4, "engineer", 3),
                    (5, "contractor", None),
                )
            )
        ).run_sync()

    def tearDown(self):
        drop_db_tables_sync(Employee)

    @staticmethod
    def reports() -> CTE:
        return CTE.recursive(
            "reports",
            base=QueryString(
                'SELECT "id", 0 FROM "employee" WHERE "id" = {}', 2
            ),
            recursive=QueryString(
                'SELECT "employee"."id", "reports"."depth" + 1 '
                'FROM "employee" JOIN "reports" '
                'ON "employee"."manager_id" = "reports"."id"'
            ),
            column_names=["id", "depth"],
        )

    def test_select(self):
        response = (
            Employee.select(Employee.name)
            .where(
                Employee.id.is_in(QueryString('SELECT "id" FROM "reports"'))
            )
            .order_by(Employee.id)
            .with_(self.reports())
            .run_sync()
        )
        self.assertEqual(
            response,
            [{"name": "vp"}, {"name": "lead"}, {"name": "engineer"}],
        )

    def test_select_multiple_ctes(self):
        ref = self.reports().ref()
        deep = CTE(
            "deep",
            QueryString(
                f"SELECT {ref.id} FROM {ref.from_clause()} WHERE "
                f"{ref.depth} > 0"
            ),
            column_names=["id"],
        )
        response = (
            Employee.select(Employee.name)
            .where(Employee.id.is_in(QueryString('SELECT "id" FROM "deep"')))
            .order_by(Employee.id)
            .with_(self.reports(), deep)
            .run_sync()
        )
        self.assertEqual(response, [{"name": "lead"}, {"name": "engineer"}])

    def test_update(self):
        Employee.update({Employee.name: "moved"}).where(
            Employee.id.is_in(QueryString('SELECT "id" FROM "reports"'))
        ).with_(self.reports()).run_sync()

        names = Employee.select(Employee.name).order_by(Employee.id).run_sync()
        self.assertEqual(
            [row["name"] for row in names],
            ["ceo", "moved", "moved", "moved", "contractor"],
        )

    def test_delete(self):
        Employee.delete().where(
            Employee.id.is_in(QueryString('SELECT "id" FROM "reports"'))
        ).with_(self.reports()).run_sync()

        names = Employee.select(Employee.name).order_by(Employee.id).run_sync()
        self.assertEqual([row["name"] for row in names], ["ceo", "contractor"])

    def test_insert(self):
        Employee.insert(
            Employee({Employee.id: 6, Employee.name: "intern"})
        ).with_(CTE("numbers", QueryString("SELECT 1"))).run_sync()

        self.assertEqual(
            Employee.count().where(Employee.name == "intern").run_sync(), 1
        )
