from typing import Final

SINGLE_WORD: Final[str] = 'однословное'
ADJECTIVAL: Final[str] = 'адъективное'
GENITIVE: Final[str] = 'генитивное'
SUBSTANTIVE_WITH_PREPOSITION: Final[str] = 'субстантивное_с_предлогом'
ADJECTIVAL_WORDY: Final[str] = 'адъективное_многословное'
GENITIVE_WORDY: Final[str] = 'генитивное_многословное'
ADJECTIVAL_GENITIVE: Final[str] = 'адъективно-генитивное'
GENITIVE_ADJECTIVAL: Final[str] = 'генитивно-адъективное'
ADVERBIAL_COMBINATION: Final[str] = 'адвербиальное_сочетание'

# Адвербиальное, адъективное с предлогом и генитивное с предлогом не используем,
#   т.к. для нашей задачи не информативно (предлоги)
ADVERBIAL: Final[str] = 'адвербиальное'
ADJECTIVAL_WITH_PREPOSITION: Final[str] = 'адъективное_с_предлогом'
GENITIVE_WITH_PREPOSITION: Final[str] = 'генитивное_с_предлогом'

PATTERNS = {
    SINGLE_WORD: [('С',)],
    ADJECTIVAL: [('П', 'С')],
    GENITIVE: [('С', 'С')],
    SUBSTANTIVE_WITH_PREPOSITION: [('С', 'предлог', 'С')],
    ADJECTIVAL_WORDY: [('П', 'П', 'С')],
    GENITIVE_WORDY: [('С', 'С', 'С')],
    ADJECTIVAL_GENITIVE: [('С', 'П', 'С')],
    GENITIVE_ADJECTIVAL: [('П', 'С', 'С')],
    ADVERBIAL_COMBINATION: [('Н', ('П', 'С'))],
}

# Подробное описание паттернов
PATTERN_DESCRIPTIONS = {
    SINGLE_WORD: "Сущ",
    ADJECTIVAL: "Прил + Сущ",
    GENITIVE: "Сущ + Сущ",
    ADVERBIAL: "Наречие + Прил",
    ADJECTIVAL_WORDY: "Прил + Прил + Сущ",
    GENITIVE_WORDY: "Сущ + Сущ + Сущ",
    ADJECTIVAL_GENITIVE: "Сущ + Прил + Сущ",
    GENITIVE_ADJECTIVAL: "Прил + Сущ + Сущ",
    ADVERBIAL_COMBINATION: "Наречие + (Прил+Сущ)",
}

POS_TAGS = {
    'NOUN': 'С',
    'ADJF': 'П',
    'ADJS': 'П',
    'ADVB': 'Н',
    'PRTF': 'П',
    'PRTS': 'П'
}

PATTERN_COLOR = {
    SINGLE_WORD: 'blue',
    ADJECTIVAL: 'green',
    GENITIVE: 'yellow',
    SUBSTANTIVE_WITH_PREPOSITION: 'magenta',
    ADJECTIVAL_WORDY: 'lightgreen',
    GENITIVE_WORDY: 'lightyellow',
    ADJECTIVAL_GENITIVE: 'lightblue',
    GENITIVE_ADJECTIVAL: 'lightpurple',
    ADVERBIAL_COMBINATION: 'white',
}
