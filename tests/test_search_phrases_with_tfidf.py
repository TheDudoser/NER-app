import unittest

from src.analysis.analyser import Analyser
from src.database.models import Term


class TestSearchPhrasesWithTfidf(unittest.TestCase):
    def setUp(self):
        self.analyzer = Analyser()

    def test_empty_phrases(self):
        """Тест на пустой список фраз."""
        result = self.analyzer.search_phrases_with_tfidf("query", [])
        self.assertEqual(result, [])

    def test_not_found(self):
        phrases = [Term(text="фраза 1"), Term(text="фраза 2"), Term(text="фраза 3")]
        result = self.analyzer.search_phrases_with_tfidf("запрос", phrases)

        self.assertEqual(len(result), 0)

    def test_found(self):
        phrases = [Term(text="фраза 1"), Term(text="фраза 2"), Term(text="фраза 3")]
        result = self.analyzer.search_phrases_with_tfidf("фраза", phrases)

        self.assertEqual(len(result), 3)
