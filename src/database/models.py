from typing import List, Optional
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
    documents: List["Document"] = Relationship(back_populates="dictionary")

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
    dictionary_id: int = Field(foreign_key="dictionary.id")
    content: str

    dictionary: Dictionary = Relationship(back_populates="documents")


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
