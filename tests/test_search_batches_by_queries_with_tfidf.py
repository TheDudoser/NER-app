import unittest

from src.analysis.analyser import Analyser


class TestSearchBatchesByQueriesWithTfidf(unittest.TestCase):
    def setUp(self):
        self.analyser = Analyser()

    def test_found(self):
        batch_vectors = self.analyser.simple_vectorize(["Красная шапочка шла по дороге"])
        results = self.analyser.search_batches_by_queries_with_tfidf(
            ["шапочка"],
            batch_vectors
        )
        self.assertEqual(len(results), 1)

    def test_not_found(self):
        batch_vectors = self.analyser.simple_vectorize(["Красная шапочка шла по дороге"])
        results = self.analyser.search_batches_by_queries_with_tfidf(
            ["тест"],
            batch_vectors
        )
        self.assertEqual(len(results), 0)
