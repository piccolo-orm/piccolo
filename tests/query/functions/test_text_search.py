from unittest import TestCase

from piccolo.query.functions.string import Similarity, WordSimilarity
from piccolo.query.functions.text_search import (
    PhrasetoTsquery,
    PlaintoTsquery,
    Setweight,
    ToTsquery,
    ToTsvector,
    TsHeadline,
    TsRank,
    TsRankCd,
    WebsearchToTsquery,
)
from piccolo.querystring import QueryString
from tests.base import postgres_only


@postgres_only
class TestToTsvector(TestCase):

    def test_without_config(self):
        """
        Make sure to_tsvector is generated without a config argument
        when none is provided.
        """
        qs = ToTsvector("some text")
        sql = str(qs)
        self.assertIn("to_tsvector", sql)
        self.assertNotIn(",", sql.split("(")[1].split(")")[0])

    def test_with_config(self):
        """
        Make sure to_tsvector is generated with the config as the first
        argument when provided.
        """
        qs = ToTsvector("some text", config="english")
        sql = str(qs)
        self.assertIn("to_tsvector", sql)
        self.assertIn("english", sql)

    def test_returns_querystring(self):
        """
        Make sure ToTsvector returns a QueryString instance.
        """
        self.assertIsInstance(ToTsvector("text"), QueryString)


@postgres_only
class TestToTsquery(TestCase):

    def test_without_config(self):
        """
        Make sure to_tsquery is generated without a config argument
        when none is provided.
        """
        qs = ToTsquery("python")
        sql = str(qs)
        self.assertIn("to_tsquery", sql)

    def test_with_config(self):
        """
        Make sure to_tsquery is generated with the config as the first
        argument when provided.
        """
        qs = ToTsquery("python", config="english")
        sql = str(qs)
        self.assertIn("to_tsquery", sql)
        self.assertIn("english", sql)


@postgres_only
class TestPlaintoTsquery(TestCase):

    def test_without_config(self):
        """
        Make sure plainto_tsquery is generated without a config argument
        when none is provided.
        """
        qs = PlaintoTsquery("python orm")
        sql = str(qs)
        self.assertIn("plainto_tsquery", sql)

    def test_with_config(self):
        """
        Make sure plainto_tsquery is generated with the config as the first
        argument when provided.
        """
        qs = PlaintoTsquery("python orm", config="english")
        sql = str(qs)
        self.assertIn("plainto_tsquery", sql)
        self.assertIn("english", sql)


@postgres_only
class TestPhrasetoTsquery(TestCase):

    def test_without_config(self):
        """
        Make sure phraseto_tsquery is generated without a config argument
        when none is provided.
        """
        qs = PhrasetoTsquery("python orm")
        sql = str(qs)
        self.assertIn("phraseto_tsquery", sql)


@postgres_only
class TestWebsearchToTsquery(TestCase):

    def test_without_config(self):
        """
        Make sure websearch_to_tsquery is generated without a config argument
        when none is provided.
        """
        qs = WebsearchToTsquery("python -java")
        sql = str(qs)
        self.assertIn("websearch_to_tsquery", sql)

    def test_with_config(self):
        """
        Make sure websearch_to_tsquery is generated with the config as the
        first argument when provided.
        """
        qs = WebsearchToTsquery("python -java", config="english")
        sql = str(qs)
        self.assertIn("websearch_to_tsquery", sql)
        self.assertIn("english", sql)


@postgres_only
class TestTsRank(TestCase):

    def test_basic(self):
        """
        Make sure ts_rank is generated with vector and query arguments.
        """
        qs = TsRank(ToTsvector("text"), ToTsquery("python"))
        sql = str(qs)
        self.assertIn("ts_rank", sql)

    def test_with_normalization(self):
        """
        Make sure ts_rank is generated with the normalization argument
        when provided.
        """
        qs = TsRank(ToTsvector("text"), ToTsquery("python"), normalization=1)
        sql = str(qs)
        self.assertIn("ts_rank", sql)

    def test_returns_querystring(self):
        """
        Make sure TsRank returns a QueryString instance.
        """
        self.assertIsInstance(
            TsRank(ToTsvector("t"), ToTsquery("q")), QueryString
        )


@postgres_only
class TestTsRankCd(TestCase):

    def test_basic(self):
        """
        Make sure ts_rank_cd is generated with vector and query arguments.
        """
        qs = TsRankCd(ToTsvector("text"), ToTsquery("python"))
        sql = str(qs)
        self.assertIn("ts_rank_cd", sql)

    def test_with_normalization(self):
        """
        Make sure ts_rank_cd is generated with the normalization argument
        when provided.
        """
        qs = TsRankCd(ToTsvector("text"), ToTsquery("python"), normalization=2)
        sql = str(qs)
        self.assertIn("ts_rank_cd", sql)


@postgres_only
class TestTsHeadline(TestCase):

    def test_without_config(self):
        """
        Make sure ts_headline is generated without a config argument
        when none is provided.
        """
        qs = TsHeadline("document text", ToTsquery("python"))
        sql = str(qs)
        self.assertIn("ts_headline", sql)

    def test_with_config(self):
        """
        Make sure ts_headline is generated with the config as the first
        argument when provided.
        """
        qs = TsHeadline("document text", ToTsquery("python"), config="english")
        sql = str(qs)
        self.assertIn("ts_headline", sql)
        self.assertIn("english", sql)


@postgres_only
class TestSimilarity(TestCase):

    def test_sql(self):
        """
        Make sure similarity() is generated with two arguments.
        """
        qs = Similarity("hello", "helo")
        sql = str(qs)
        self.assertIn("similarity", sql)

    def test_returns_querystring(self):
        """
        Make sure Similarity returns a QueryString instance.
        """
        self.assertIsInstance(Similarity("a", "b"), QueryString)

    def test_default_alias(self):
        """
        Make sure the default alias is 'similarity'.
        """
        qs = Similarity("a", "b")
        self.assertEqual(qs._alias, "similarity")


@postgres_only
class TestWordSimilarity(TestCase):

    def test_sql(self):
        """
        Make sure word_similarity() is generated with two arguments.
        """
        qs = WordSimilarity("hello world", "hello")
        sql = str(qs)
        self.assertIn("word_similarity", sql)

    def test_returns_querystring(self):
        """
        Make sure WordSimilarity returns a QueryString instance.
        """
        self.assertIsInstance(WordSimilarity("a", "b"), QueryString)


@postgres_only
class TestSetweight(TestCase):

    def test_sql_output(self):
        qs = Setweight(ToTsvector("some text"), "A")
        sql = str(qs)
        self.assertIn("setweight", sql)
        self.assertIn("to_tsvector", sql)

    def test_all_weights(self):
        for weight in ("A", "B", "C", "D"):
            qs = Setweight(ToTsvector("some text"), weight)
            self.assertIn(weight, str(qs))

    def test_returns_querystring(self):
        self.assertIsInstance(
            Setweight(ToTsvector("some text"), "A"), QueryString
        )
