from typing import List, Optional

from sqlalchemy import JSON, ARRAY, String
from sqlmodel import SQLModel, Field, Relationship, Column, Enum
from datetime import datetime, UTC

from config import VL_TIMEZONE
from database import engine
from src.models.phrase_type import PhraseType


def _get_current_time():
    return datetime.now(UTC)


class Dictionary(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    tfidf_range: float
    created_at: datetime = Field(
        default_factory=_get_current_time,
    )
    updated_at: Optional[datetime] = Field(
        default_factory=_get_current_time,
        sa_column_kwargs={"onupdate": _get_current_time},
    )

    terms: List["Term"] = Relationship(back_populates="dictionary")
    connections: List["Connection"] = Relationship(back_populates="dictionary")
    dictionary_analysis_results: List["DictionaryAnalysisResult"] = Relationship(back_populates="dictionary")

    @property
    def created_at_local(self) -> datetime | None:
        if self.created_at is None:
            return None
        return self.created_at.astimezone(VL_TIMEZONE)

    @property
    def updated_at_local(self) -> datetime | None:
        if self.updated_at is None:
            return None
        return self.updated_at.astimezone(VL_TIMEZONE)


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hash_key: Optional[str] = Field(index=True)
    content: str

    analysis_result: Optional["AnalysisResult"] = Relationship(  # Изменили на единственное число
        back_populates="document",
        sa_relationship_kwargs={"uselist": False}  # Указываем, что связь 1:1
    )


class AnalysisResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: Optional[int] = Field(foreign_key="document.id")
    content: Optional[dict] = Field(default={}, sa_column=Column(JSON))
    document_batches: List[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String))
    )

    document: Document = Relationship(back_populates="analysis_result")

    dictionary_analysis_results: List["DictionaryAnalysisResult"] = Relationship(back_populates="analysis_result")


class DictionaryAnalysisResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    dictionary_id: int = Field(foreign_key="dictionary.id")
    analysis_result_id: int = Field(foreign_key="analysisresult.id")

    dictionary: Dictionary = Relationship(back_populates="dictionary_analysis_results")
    analysis_result: AnalysisResult = Relationship(back_populates="dictionary_analysis_results")


class Term(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    dictionary_id: int = Field(foreign_key="dictionary.id")
    text: str
    type: str
    phrase_type: PhraseType = Field(sa_column=Column(Enum(PhraseType), index=True))
    tfidf: float
    hidden: bool = False

    dictionary: Dictionary = Relationship(back_populates="terms")
    from_connections: List["Connection"] = Relationship(
        back_populates="from_term",
        sa_relationship_kwargs={"foreign_keys": "[Connection.from_term_id]"}
    )
    to_connections: List["Connection"] = Relationship(
        back_populates="to_term",
        sa_relationship_kwargs={"foreign_keys": "[Connection.to_term_id]"}
    )


class Connection(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    dictionary_id: int = Field(foreign_key="dictionary.id")
    from_term_id: int = Field(foreign_key="term.id")
    to_term_id: int = Field(foreign_key="term.id")

    dictionary: Dictionary = Relationship(back_populates="connections")
    from_term: Term = Relationship(
        back_populates="from_connections",
        sa_relationship_kwargs={"foreign_keys": "[Connection.from_term_id]"}
    )
    to_term: Term = Relationship(
        back_populates="to_connections",
        sa_relationship_kwargs={"foreign_keys": "[Connection.to_term_id]"}
    )


def create_all():
    SQLModel.metadata.create_all(engine)
