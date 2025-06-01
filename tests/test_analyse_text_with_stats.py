import json
import os
import unittest
from unittest.mock import MagicMock

from src.analysis.analyser import Analyser


class TestAnalyseTextWithStats(unittest.TestCase):
    def setUp(self):
        self.analyser = Analyser()
        self.analyser.extract_top_ngrams_with_tfidf = MagicMock()

    @staticmethod
    def load_fixture(filename):
        fixtures_dir = os.path.join(
            os.path.dirname(__file__),
            "fixtures",
            "stats"
        )
        filepath = os.path.join(fixtures_dir, filename)

        with open(filepath, "r", encoding="utf-8") as f:
            return json.loads(f.read())

    def test_empty_text(self):
        self.analyser.extract_top_ngrams_with_tfidf.return_value = []

        result = self.analyser.analyze_text_with_stats("")
        expected = self.load_fixture("empty_result.json")
        self.assertEqual(result, expected)

    def test_single_phrase(self):
        self.analyser.extract_top_ngrams_with_tfidf.return_value = [("быстрый кот", 0.8)]

        result = self.analyser.analyze_text_with_stats("быстрый кот")
        expected = self.load_fixture("catflash.json")
        self.assertEqual(result, expected)

    def test_multiple_phrases(self):
        self.analyser.extract_top_ngrams_with_tfidf.return_value = [
            ("быстрый кот", 0.8),
            ("кот", 0.7),
            ("рыжий кот", 0.5),
        ]

        result = self.analyser.analyze_text_with_stats("быстрый кот, кот, рыжий кот")
        expected = self.load_fixture("catflash_jump.json")
        self.assertEqual(result, expected)
