from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TermDTO:
    text: str
    type: str
    # На самом деле PhraseType, но с enum возникли трудности...
    phrase_type: str
    tfidf: float
    hidden: bool = False
    id: Optional[int] = None


@dataclass
class ConnectionDTO:
    from_id: int
    to_id: int


@dataclass
class DictionaryDTO:
    name: str
    tfidfRange: float
    phrases: List[TermDTO]
    connections: List[ConnectionDTO]
    fileId: Optional[int] = None


@dataclass
class DictionaryShortDTO:
    id: int
    name: str
    created_at: float  # timestamp
    terms_count: int
    connections_count: int
