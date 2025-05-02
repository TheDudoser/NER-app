from typing import Dict
from colorama import Fore, Style

from src.analysis.consts import (
    SINGLE_WORD,
    ADJECTIVAL,
    GENITIVE,
    ADVERBIAL,
    SUBSTANTIVE_WITH_PREPOSITION,
    ADJECTIVAL_WORDY,
    GENITIVE_WORDY,
    ADJECTIVAL_GENITIVE,
    GENITIVE_ADJECTIVAL,
    ADJECTIVAL_WITH_PREPOSITION,
    GENITIVE_WITH_PREPOSITION,
    ADVERBIAL_COMBINATION
)

# Расширенная цветовая схема для всех типов паттернов
COLOR_MAPPING = {
    SINGLE_WORD: Fore.BLUE,
    ADJECTIVAL: Fore.GREEN,
    GENITIVE: Fore.YELLOW,
    ADVERBIAL: Fore.MAGENTA,
    SUBSTANTIVE_WITH_PREPOSITION: Fore.CYAN,
    ADJECTIVAL_WORDY: Fore.LIGHTGREEN_EX,
    GENITIVE_WORDY: Fore.LIGHTYELLOW_EX,
    ADJECTIVAL_GENITIVE: Fore.LIGHTBLUE_EX,
    GENITIVE_ADJECTIVAL: Fore.LIGHTMAGENTA_EX,
    ADJECTIVAL_WITH_PREPOSITION: Fore.LIGHTCYAN_EX,
    GENITIVE_WITH_PREPOSITION: Fore.LIGHTRED_EX,
    ADVERBIAL_COMBINATION: Fore.LIGHTWHITE_EX
}


def print_report(analysis: Dict):
    """Выводит отчёт об анализе с цветовой дифференциацией паттернов."""
    # Шапка отчёта
    print(f"\n{Fore.CYAN}{'=' * 100}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}{'АНАЛИЗ КЛЮЧЕВЫХ СЛОВОСОЧЕТАНИЙ':^80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 100}{Style.RESET_ALL}")

    # Общая статистика
    print(f"{'Всего фраз:':<25} {analysis['total_phrases']:>10}")
    print(f"{'Уникальных типов сочетаний:':<25} {analysis['unique_patterns']:>10}")
    print(f"{Fore.CYAN}{'-' * 100}{Style.RESET_ALL}")

    # Заголовки таблицы
    headers = [
        ("ТИП", 25),
        ("ОПИСАНИЕ ТИПА", 30),
        ("СЛОВОСОЧЕТАНИЕ", 30),
        ("TF-IDF", 10)
    ]
    header_line = " | ".join(f"{h[0]:<{h[1]}}" for h in headers)
    print(f"{Fore.YELLOW}{header_line}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'-' * 100}{Style.RESET_ALL}")

    # Данные
    for item in analysis['phrases']:
        color = COLOR_MAPPING.get(item['pattern_type'], Fore.WHITE)
        tfidf = f"{item['tfidf_score']:.3f}" if isinstance(item['tfidf_score'], float) else "N/A"

        # Обрезаем длинные строки для красивого вывода
        pattern_desc = item['pattern_description'][:30] + "..." if len(item['pattern_description']) > 30 else item[
            'pattern_description']
        phrase = item['phrase'][:30] + "..." if len(item['phrase']) > 30 else item['phrase']

        print(
            f"{color}{item['pattern_type'][:25]:<25}{Style.RESET_ALL} | "
            f"{pattern_desc:<30} | "
            f"{phrase:<30} | "
            f"{Fore.LIGHTWHITE_EX}{tfidf:^10}{Style.RESET_ALL}"
        )

    print(f"{Fore.CYAN}{'=' * 100}{Style.RESET_ALL}")
