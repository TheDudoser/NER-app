from typing import Final

SINGLE_WORD: Final[str] = 'однословное'
ADJECTIVAL: Final[str] = 'адъективное'
GENITIVE: Final[str] = 'генитивное'
SUBSTANTIVE_WITH_PREPOSITION: Final[str] = 'субстантивное_с_предлогом'
ADVERBIAL: Final[str] = 'адвербиальное'
ADJECTIVAL_WORDY: Final[str] = 'адъективное_многословное'
GENITIVE_WORDY: Final[str] = 'генитивное_многословное'
ADJECTIVAL_GENITIVE: Final[str] = 'адъективно-генитивное'
GENITIVE_ADJECTIVAL: Final[str] = 'генитивно-адъективное'
ADJECTIVAL_WITH_PREPOSITION: Final[str] = 'адъективное_с_предлогом'
GENITIVE_WITH_PREPOSITION: Final[str] = 'генитивное_с_предлогом'
ADVERBIAL_COMBINATION: Final[str] = 'адвербиальное_сочетание'

PATTERNS = {
    SINGLE_WORD: [('С',)],
    ADJECTIVAL: [('П', 'С')],
    GENITIVE: [('С', 'С')],
    SUBSTANTIVE_WITH_PREPOSITION: [('С', 'предлог', 'С')],
    ADVERBIAL: [('Н', 'П')],
    ADJECTIVAL_WORDY: [('П', 'П', 'С')],
    GENITIVE_WORDY: [('С', 'С', 'С')],
    ADJECTIVAL_GENITIVE: [('С', 'П', 'С')],
    GENITIVE_ADJECTIVAL: [('П', 'С', 'С')],
    ADJECTIVAL_WITH_PREPOSITION: [
        [('П', 'С'), 'предлог', 'С'],
        ['С', 'предлог', ('П', 'С')]
    ],
    GENITIVE_WITH_PREPOSITION: [
        [('С', 'С'), 'предлог', 'С'],
        ['С', 'предлог', ('С', 'С')]
    ],
    ADVERBIAL_COMBINATION: [('Н', ('П', 'С'))]
}

# Подробное описание паттернов
PATTERN_DESCRIPTIONS = {
    SINGLE_WORD: "Сущ",
    ADJECTIVAL: "Прил + Сущ",
    GENITIVE: "Сущ + Сущ",
    SUBSTANTIVE_WITH_PREPOSITION: "Сущ + предлог + Сущ",
    ADVERBIAL: "Наречие + Прил",
    ADJECTIVAL_WORDY: "Прил + Прил + Сущ",
    GENITIVE_WORDY: "Сущ + Сущ + Сущ",
    ADJECTIVAL_GENITIVE: "Сущ + Прил + Сущ",
    GENITIVE_ADJECTIVAL: "Прил + Сущ + Сущ",
    ADJECTIVAL_WITH_PREPOSITION: [
        "(Прил+Сущ) + предлог + Сущ",
        "Сущ + предлог + (Прил+Сущ)"
    ],
    GENITIVE_WITH_PREPOSITION: [
        "(Сущ+Сущ) + предлог + Сущ",
        "Сущ + предлог + (Сущ+Сущ)"
    ],
    ADVERBIAL_COMBINATION: "Наречие + (Прил+Сущ)"
}

POS_TAGS = {
    'NOUN': 'С',
    'ADJF': 'П',
    'ADJS': 'П',
    'ADVB': 'Н',
    'PREP': 'предлог',
    'PRTF': 'П',
    'PRTS': 'П'
}

PATTERN_COLOR = {
    SINGLE_WORD: 'blue',
    ADJECTIVAL: 'green',
    GENITIVE: 'yellow',
    SUBSTANTIVE_WITH_PREPOSITION: 'magenta',
    ADVERBIAL: 'cyan',
    ADJECTIVAL_WORDY: 'lightgreen',
    GENITIVE_WORDY: 'lightyellow',
    ADJECTIVAL_GENITIVE: 'lightblue',
    GENITIVE_ADJECTIVAL: 'lightpurple',
    ADJECTIVAL_WITH_PREPOSITION: 'lightcyan',
    GENITIVE_WITH_PREPOSITION: 'lightred',
    ADVERBIAL_COMBINATION: 'white'
}
