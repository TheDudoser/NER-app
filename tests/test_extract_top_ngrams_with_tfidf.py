import unittest

from src.analysis.analyser import Analyser


class TestExtractTopNgramsWithTfidf(unittest.TestCase):
    def setUp(self):
        self.analyser = Analyser(ngram_count=1)

    def test_empty_text(self):
        self.assertRaises(
            Exception,
            self.analyser.extract_top_ngrams_with_tfidf,
            ""
        )

    def test_single_word(self):
        result = self.analyser.extract_top_ngrams_with_tfidf("hello")
        expected = [("hello", 1.0)]
        self.assertEqual(result, expected)

    def test_repeated_words(self):
        result = self.analyser.extract_top_ngrams_with_tfidf("hello hello world")
        expected = [("hello", 0.8944271909999159), ("world", 0.4472135954999579)]
        self.assertEqual(result, expected)

    def test_single_symbol(self):
        self.assertRaises(
            Exception,
            self.analyser.extract_top_ngrams_with_tfidf,
            "a b c d"
        )

    def test_top_k_parameter(self):
        result = self.analyser.extract_top_ngrams_with_tfidf("he she it", top_k=2)
        self.assertEqual(len(result), 2)
