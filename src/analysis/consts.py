from typing import Final

SINGLE_WORD: Final[str] = 'однословное'
ADJECTIVAL: Final[str] = 'адъективное'
GENITIVE: Final[str] = 'генитивное'
ADJECTIVAL_WORDY: Final[str] = 'адъективное_многословное'
GENITIVE_WORDY: Final[str] = 'генитивное_многословное'
ADJECTIVAL_GENITIVE: Final[str] = 'адъективно-генитивное'
GENITIVE_ADJECTIVAL: Final[str] = 'генитивно-адъективное'

# Виды ниже не используем, так как они не информативны в качестве именованных сущностей
ADVERBIAL: Final[str] = 'адвербиальное'
ADJECTIVAL_WITH_PREPOSITION: Final[str] = 'адъективное_с_предлогом'
GENITIVE_WITH_PREPOSITION: Final[str] = 'генитивное_с_предлогом'
ADVERBIAL_COMBINATION: Final[str] = 'адвербиальное_сочетание'
SUBSTANTIVE_WITH_PREPOSITION: Final[str] = 'субстантивное_с_предлогом'

PATTERNS = {
    SINGLE_WORD: [('С',)],
    ADJECTIVAL: [('П', 'С')],
    GENITIVE: [('С', 'С')],
    ADJECTIVAL_WORDY: [('П', 'П', 'С')],
    GENITIVE_WORDY: [('С', 'С', 'С')],
    ADJECTIVAL_GENITIVE: [('С', 'П', 'С')],
    GENITIVE_ADJECTIVAL: [('П', 'С', 'С')],
}

# Подробное описание паттернов
PATTERN_DESCRIPTIONS = {
    SINGLE_WORD: "Сущ",
    ADJECTIVAL: "Прил + Сущ",
    GENITIVE: "Сущ + Сущ",
    ADJECTIVAL_WORDY: "Прил + Прил + Сущ",
    GENITIVE_WORDY: "Сущ + Сущ + Сущ",
    ADJECTIVAL_GENITIVE: "Сущ + Прил + Сущ",
    GENITIVE_ADJECTIVAL: "Прил + Сущ + Сущ",
}

POS_TAGS = {
    'NOUN': 'С',    # существительное
    'ADJF': 'П',    # прилагательное (полное)
    'ADJS': 'П',    # прилагательное (краткое)
    # 'ADVB': 'Н',    # наречие
    'PRTF': 'П',    # причастие (полное)
    'PRTS': 'П'     # причастие (краткое)
}

PATTERN_COLOR = {
    SINGLE_WORD: 'blue',
    ADJECTIVAL: 'green',
    GENITIVE: 'yellow',
    ADJECTIVAL_WORDY: 'lightgreen',
    GENITIVE_WORDY: 'lightyellow',
    ADJECTIVAL_GENITIVE: 'lightblue',
    GENITIVE_ADJECTIVAL: 'lightpurple',
}

TYPE_COLOR = {
    'term': 'black',
    'synonym': 'green',
    'definition': 'orange',
}
