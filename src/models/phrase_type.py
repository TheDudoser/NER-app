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

    def get_desc(self) -> str:
        match self:
            case PhraseType.phrase:
                return "выделенное словосочетание"
            case PhraseType.term:
                return "термин"
            case PhraseType.synonym:
                return "синоним"
            case PhraseType.definition:
                return "значение"
