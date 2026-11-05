from unittest import TestCase

from piccolo.columns import ForeignKey, Integer, Varchar
from piccolo.query.methods.objects import prefetch_related
from piccolo.table import Table
from piccolo.testing.test_case import AsyncTableTest


class Retailer(Table):
    name = Varchar()


class Product(Table):
    name = Varchar()
    retailer = ForeignKey(Retailer)
    price = Integer(default=0)


class Trade(Table):
    """
    Has two foreign keys pointing at the same table.
    """

    buyer = ForeignKey(Retailer)
    seller = ForeignKey(Retailer)


class Rating(Table):
    product = ForeignKey(Product)
    stars = Integer(default=0)


class TestReverseRelations(TestCase):

    def test_names(self):
        """
        Each relation should have a name which includes the column, and a
        shorter one which doesn't.
        """
        self.assertEqual(
            Product._meta.reverse_relations,
            {
                "rating_product_set": Rating.product,
                "rating_set": Rating.product,
            },
        )

    def test_ambiguous_names(self):
        """
        If a table has two foreign keys pointing at this one, then only the
        names which include the column should be available for them.
        """
        self.assertEqual(
            Retailer._meta.reverse_relations,
            {
                "product_retailer_set": Product.retailer,
                "product_set": Product.retailer,
                "trade_buyer_set": Trade.buyer,
                "trade_seller_set": Trade.seller,
            },
        )

    def test_no_reverse_relations(self):
        """
        A table which nothing points at should have no reverse relations.
        """
        self.assertEqual(Rating._meta.reverse_relations, {})


class TestGetRelatedObjects(AsyncTableTest):

    tables = [Retailer, Product]

    async def asyncSetUp(self):
        await super().asyncSetUp()

        self.retailer = Retailer({Retailer.name: "Acme"})
        await self.retailer.save()

        self.other_retailer = Retailer({Retailer.name: "Globex"})
        await self.other_retailer.save()

        await Product.insert(
            Product(
                {
                    Product.name: "Anvil",
                    Product.retailer: self.retailer,
                    Product.price: 100,
                }
            ),
            Product(
                {
                    Product.name: "Rocket",
                    Product.retailer: self.retailer,
                    Product.price: 10,
                }
            ),
            Product(
                {
                    Product.name: "Widget",
                    Product.retailer: self.other_retailer,
                    Product.price: 50,
                }
            ),
        )

    async def test_get_related_objects(self):
        products = await self.retailer.get_related_objects(Product.retailer)

        self.assertListEqual(
            sorted(product.name for product in products),
            ["Anvil", "Rocket"],
        )

    async def test_accessor_name(self):
        """
        Passing in the accessor name should be the same as passing in the
        column.
        """
        products = await self.retailer.get_related_objects("product_set")

        self.assertListEqual(
            sorted(product.name for product in products),
            ["Anvil", "Rocket"],
        )

    async def test_attribute_access(self):
        """
        The accessor names should also work as attributes.
        """
        for products in (
            await self.retailer.product_set,
            await self.retailer.product_retailer_set,
        ):
            self.assertListEqual(
                sorted(product.name for product in products),
                ["Anvil", "Rocket"],
            )

    async def test_query_is_lazy(self):
        """
        A query should be returned, so it can be narrowed down.
        """
        products = await self.retailer.product_set.where(Product.price > 50)

        self.assertListEqual([product.name for product in products], ["Anvil"])

    async def test_unknown_attribute(self):
        with self.assertRaises(AttributeError):
            self.retailer.abc123

    async def test_unknown_accessor_name(self):
        with self.assertRaises(ValueError):
            self.retailer.get_related_objects("abc123")

    async def test_not_a_foreign_key(self):
        with self.assertRaises(ValueError):
            self.retailer.get_related_objects(Product.name)  # type: ignore

    async def test_wrong_table(self):
        """
        The foreign key has to point at this table.
        """
        with self.assertRaises(ValueError):
            self.retailer.get_related_objects(Rating.product)

    async def test_not_in_database(self):
        """
        A row which hasn't been saved has no primary key to match on.
        """
        with self.assertRaises(ValueError):
            Retailer({Retailer.name: "Initech"}).get_related_objects(
                Product.retailer
            )


class TestPrefetchRelated(AsyncTableTest):

    tables = [Retailer, Product]

    async def asyncSetUp(self):
        await super().asyncSetUp()

        self.retailer = Retailer({Retailer.name: "Acme"})
        await self.retailer.save()

        self.other_retailer = Retailer({Retailer.name: "Globex"})
        await self.other_retailer.save()

        await Product.insert(
            Product(
                {
                    Product.name: "Anvil",
                    Product.retailer: self.retailer,
                    Product.price: 100,
                }
            ),
            Product(
                {
                    Product.name: "Rocket",
                    Product.retailer: self.retailer,
                    Product.price: 10,
                }
            ),
            Product(
                {
                    Product.name: "Widget",
                    Product.retailer: self.other_retailer,
                    Product.price: 50,
                }
            ),
        )

    async def get_response(self, retailers) -> dict:
        return {
            retailer.name: sorted(
                product.name for product in await retailer.product_set
            )
            for retailer in retailers
        }

    async def test_prefetch_related(self):
        retailers = await Retailer.objects().prefetch_related(Product.retailer)

        self.assertDictEqual(
            await self.get_response(retailers),
            {"Acme": ["Anvil", "Rocket"], "Globex": ["Widget"]},
        )

    async def test_no_extra_queries(self):
        """
        Once prefetched, accessing the relation shouldn't hit the database.
        """
        retailers = await Retailer.objects().prefetch_related(Product.retailer)

        # If the database is queried again, we'll get an empty response.
        await Product.delete(force=True)

        self.assertDictEqual(
            await self.get_response(retailers),
            {"Acme": ["Anvil", "Rocket"], "Globex": ["Widget"]},
        )

    async def test_narrowing_bypasses_the_cache(self):
        """
        Any change to the query means the prefetched rows can no longer
        answer it.
        """
        retailers = await Retailer.objects().prefetch_related(Product.retailer)
        retailer = [i for i in retailers if i.name == "Acme"][0]

        products = await retailer.product_set.where(Product.price > 50)
        self.assertListEqual([product.name for product in products], ["Anvil"])

        await Product.delete(force=True)

        products = await retailer.product_set.where(Product.price > 50)
        self.assertListEqual(products, [])

    async def test_no_related_rows(self):
        """
        A row with no related rows should get an empty list, rather than an
        error.
        """
        retailer = Retailer({Retailer.name: "Initech"})
        await retailer.save()

        retailers = await Retailer.objects().prefetch_related(Product.retailer)
        initech = [i for i in retailers if i.name == "Initech"][0]

        self.assertListEqual(await initech.product_set, [])

    async def test_standalone_function(self):
        """
        ``prefetch_related`` can also be called with rows we already have.
        """
        retailers = await Retailer.objects()
        await prefetch_related(retailers, Product.retailer)

        await Product.delete(force=True)

        self.assertDictEqual(
            await self.get_response(retailers),
            {"Acme": ["Anvil", "Rocket"], "Globex": ["Widget"]},
        )

    async def test_no_rows(self):
        """
        Prefetching with no rows shouldn't run any queries.
        """
        await prefetch_related([], Product.retailer)


class TestPrefetchMultipleRelations(AsyncTableTest):

    tables = [Retailer, Trade]

    async def test_multiple_relations(self):
        """
        More than one relation can be prefetched at a time, including two
        which come from the same table.
        """
        buyer = Retailer({Retailer.name: "Acme"})
        await buyer.save()

        seller = Retailer({Retailer.name: "Globex"})
        await seller.save()

        await Trade({Trade.buyer: buyer, Trade.seller: seller}).save()

        retailers = await Retailer.objects().prefetch_related(
            Trade.buyer, Trade.seller
        )

        await Trade.delete(force=True)

        response = {
            retailer.name: (
                len(await retailer.trade_buyer_set),
                len(await retailer.trade_seller_set),
            )
            for retailer in retailers
        }

        self.assertDictEqual(response, {"Acme": (1, 0), "Globex": (0, 1)})
