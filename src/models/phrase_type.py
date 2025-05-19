import enum


class PhraseType(str, enum.Enum):
    phrase = "phrase"
    term = "term"
    synonym = "synonym"
    definition = "definition"

    @classmethod
    def from_value(cls, value: str) -> 'PhraseType':
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"'{value}' is not a valid {cls.__name__} value")
