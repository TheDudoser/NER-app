from analysis.phrase_extractor import PhraseExtractor
from printer.cli_printer import print_report as cli_print_report
from input_text_worker.functions import read_file

if __name__ == "__main__":
    # text = """
    # В лесу растёт старая сосна. Сосна высокая и зелёная.
    # Под сосной лежит большой камень. Камень серый и холодный.
    # Утром на камне сидит мудрая сова. Сова смотрит в лес.
    # Вечером в лесу тихо. Тишина нарушается только шумом листьев.
    # Лес, сосна, камень - вот главные герои этой истории.
    # """

    phrase_extractor = PhraseExtractor()
    file_content = read_file('redhead.txt')

    analysis = phrase_extractor.analyze_text_with_stats(file_content)
    cli_print_report(analysis)
