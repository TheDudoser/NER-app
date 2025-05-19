import enum
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship, Column, Enum
from pgvector.sqlalchemy import Vector
from datetime import datetime

from database import engine
from src.models.phrase_type import PhraseType


class Dictionary(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    tfidf_range: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    terms: List["Term"] = Relationship(back_populates="dictionary")
    connections: List["Connection"] = Relationship(back_populates="dictionary")


class Term(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    dictionary_id: int = Field(foreign_key="dictionary.id")
    text: str
    type: str
    phrase_type: PhraseType = Field(sa_column=Column(Enum(PhraseType), index=True))
    tfidf: float
    hidden: bool = False
    embedding: List[float] = Field(
        sa_column=Column(
            # Обычно за dim берут число уникальных слов в тексте, поэтому задал большой порог
            Vector(10000),
            nullable=True
        )
    )

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
