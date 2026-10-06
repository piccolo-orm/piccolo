from unittest import TestCase

from piccolo.columns import Integer, Varchar
from piccolo.constraints import Check, Unique
from piccolo.table import Table


class TestUniqueConstraint(TestCase):
    def test_default_name(self):
        class Album(Table):
            name = Varchar()
            code = Integer()
            unique_name_code = Unique(columns=[name, code])

        self.assertEqual(
            Album.unique_name_code._meta.name, "unique_name_code"
        )
        self.assertEqual(
            Album._meta.constraints[0]._meta.name, "unique_name_code"
        )
        self.assertEqual(
            Album.unique_name_code._meta.params,
            {"columns": ["name", "code"], "nulls_distinct": True},
        )
        self.assertNotIn(
            "prefix_tablename", Album.unique_name_code._meta.params
        )

    def test_explicit_name(self):
        class Album(Table):
            name = Varchar()
            code = Integer()
            unique_name_code = Unique(
                columns=[name, code], name="custom_album_unique"
            )

        self.assertEqual(
            Album.unique_name_code._meta.name, "custom_album_unique"
        )
        self.assertEqual(
            Album._meta.constraints[0]._meta.name, "custom_album_unique"
        )

    def test_prefix_tablename(self):
        class Album(Table):
            name = Varchar()
            code = Integer()
            unique_name_code = Unique(
                columns=[name, code], prefix_tablename=True
            )

        self.assertEqual(
            Album.unique_name_code._meta.name, "album_unique_name_code"
        )
        self.assertEqual(
            Album._meta.constraints[0]._meta.name, "album_unique_name_code"
        )
        self.assertEqual(
            Album.unique_name_code._meta.params,
            {
                "columns": ["name", "code"],
                "nulls_distinct": True,
                "prefix_tablename": True,
            },
        )

    def test_prefix_tablename_with_explicit_name(self):
        class Album(Table):
            name = Varchar()
            code = Integer()
            unique_name_code = Unique(
                columns=[name, code],
                name="custom_idx",
                prefix_tablename=True,
            )

        self.assertEqual(Album.unique_name_code._meta.name, "album_custom_idx")
        self.assertEqual(
            Album._meta.constraints[0]._meta.name, "album_custom_idx"
        )

    def test_mixin_inheritance_with_prefix(self):
        class IdentifierMixin:
            external_id = Integer()
            version_no = Integer()

            unique_identifier = Unique(
                columns=[external_id, version_no],
                prefix_tablename=True,
            )

        class Order(IdentifierMixin, Table, tablename="orders"):
            title = Varchar()

        class Invoice(IdentifierMixin, Table, tablename="invoices"):
            title = Varchar()

        # Both tables have distinct constraint names prefixed by tablename:
        self.assertEqual(
            Order.unique_identifier._meta.name, "orders_unique_identifier"
        )
        self.assertEqual(
            Invoice.unique_identifier._meta.name, "invoices_unique_identifier"
        )

        # Both tables have distinct Constraint instances:
        self.assertIsNot(Order.unique_identifier, Invoice.unique_identifier)
        self.assertIsNot(
            Order.unique_identifier, IdentifierMixin.unique_identifier
        )

        # Columns in constraint point to respective table's cloned columns:
        self.assertIs(Order.unique_identifier.columns[0], Order.external_id)
        self.assertIs(
            Invoice.unique_identifier.columns[0], Invoice.external_id
        )

        # DDL includes properly prefixed constraint names:
        order_ddl = [str(x) for x in Order.create_table().ddl]
        expected_order_sql = (
            'ADD CONSTRAINT orders_unique_identifier '
            'UNIQUE ("external_id", "version_no")'
        )
        self.assertTrue(
            any(expected_order_sql in stmt for stmt in order_ddl)
        )

        invoice_ddl = [str(x) for x in Invoice.create_table().ddl]
        expected_invoice_sql = (
            'ADD CONSTRAINT invoices_unique_identifier '
            'UNIQUE ("external_id", "version_no")'
        )
        self.assertTrue(
            any(expected_invoice_sql in stmt for stmt in invoice_ddl)
        )

    def test_mixin_inheritance_without_prefix(self):
        class IdentifierMixin:
            external_id = Integer()
            version_no = Integer()

            unique_identifier = Unique(
                columns=[external_id, version_no],
                prefix_tablename=False,
            )

        class Order(IdentifierMixin, Table, tablename="orders"):
            title = Varchar()

        class Invoice(IdentifierMixin, Table, tablename="invoices"):
            title = Varchar()

        # Without prefix, both keep the base attribute name:
        self.assertEqual(
            Order.unique_identifier._meta.name, "unique_identifier"
        )
        self.assertEqual(
            Invoice.unique_identifier._meta.name, "unique_identifier"
        )
        # Instances remain isolated:
        self.assertIsNot(Order.unique_identifier, Invoice.unique_identifier)

    def test_table_str(self):
        class Album(Table):
            name = Varchar()
            unique_name = Unique(columns=[name], prefix_tablename=True)

        self.assertIn("prefix_tablename=True", Album.unique_name._table_str())


class TestCheckConstraint(TestCase):
    def test_check_default_name(self):
        class Ticket(Table):
            price = Integer()
            valid_price = Check(price >= 0)

        self.assertEqual(Ticket.valid_price._meta.name, "valid_price")
        self.assertNotIn("prefix_tablename", Ticket.valid_price._meta.params)

    def test_check_prefix_tablename(self):
        class Ticket(Table):
            price = Integer()
            valid_price = Check(price >= 0, prefix_tablename=True)

        self.assertEqual(Ticket.valid_price._meta.name, "ticket_valid_price")
        self.assertTrue(
            Ticket.valid_price._meta.params.get("prefix_tablename")
        )

    def test_check_mixin_inheritance(self):
        class PriceMixin:
            price = Integer()
            valid_price = Check(price >= 0, prefix_tablename=True)

        class ConcertTicket(PriceMixin, Table, tablename="concert_tickets"):
            pass

        class CinemaTicket(PriceMixin, Table, tablename="cinema_tickets"):
            pass

        self.assertEqual(
            ConcertTicket.valid_price._meta.name, "concert_tickets_valid_price"
        )
        self.assertEqual(
            CinemaTicket.valid_price._meta.name, "cinema_tickets_valid_price"
        )
        self.assertIsNot(
            ConcertTicket.valid_price, CinemaTicket.valid_price
        )

    def test_check_table_str(self):
        class Ticket(Table):
            price = Integer()
            valid_price = Check(price >= 0, prefix_tablename=True)

        self.assertIn("prefix_tablename=True", Ticket.valid_price._table_str())
