from dataclasses import dataclass
from datetime import datetime
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
    head_noun: Optional[str] = None


@dataclass
class ConnectionDTO:
    from_id: int
    to_id: int


@dataclass
class DictionaryDTO:
    name: str
    tfidf_range: float
    phrases: List[TermDTO]
    connections: List[ConnectionDTO]
    id: Optional[int] = None
    analysis_result_id: Optional[int] = None


@dataclass
class DictionaryShortDTO:
    id: int
    name: str
    created_at: datetime | float
    terms_count: int
    connections_count: int
