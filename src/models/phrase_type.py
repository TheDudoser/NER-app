import enum


class PhraseType(str, enum.Enum):
    phrase = "phrase"
    term = "term"
    synonym = "synonym"
    definition = "definition"
