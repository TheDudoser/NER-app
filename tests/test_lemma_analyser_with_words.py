import unittest

from src.analysis.analyser import Analyser


class TestLemmaAnalyserWithWords(unittest.TestCase):
    def setUp(self):
        self.analyser = Analyser()

    def test_single_word(self):
        result = self.analyser.lemma_analyzer_with_numbers(text="test")
        self.assertCountEqual(result, ["test"])

    def test_hyphen(self):
        result = self.analyser.lemma_analyzer_with_numbers(text="test-test")
        self.assertCountEqual(result, ["test-test"])

    def test_numbers(self):
        # Пока поддерживается только unsigned integer
        result = self.analyser.lemma_analyzer_with_numbers(text="123 5.0")
        self.assertCountEqual(result, ["123"])

        result = self.analyser.lemma_analyzer_with_numbers(text="2024 год")
        self.assertEqual(result[0], "2024")

    def test_punctuation_ignored(self):
        result = self.analyser.lemma_analyzer_with_numbers("Привет, мир!")
        self.assertEqual(result, ["привет", "мир"])

    def test_max_n_parameter(self):
        result = self.analyser.lemma_analyzer_with_numbers("один два три", max_n=2)
        self.assertEqual(sorted(result), sorted(["один", "два", "один два", "три", "два три"]))

    def test_single_symbol(self):
        result = self.analyser.lemma_analyzer_with_numbers("а")
        self.assertEqual(result, [])

    def test_empty(self):
        result = self.analyser.lemma_analyzer_with_numbers("")
        self.assertEqual(result, [])
