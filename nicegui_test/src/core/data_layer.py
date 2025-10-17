from __future__ import annotations

from datetime import datetime
from typing import Any, Type

from sqlalchemy import Column, DateTime
from sqlmodel import Field, Session, SQLModel, create_engine, select, text


class Bookmark(SQLModel, table=True):
    """Define o modelo de dados para um Bookmark."""

    __tablename__ = "bookmark"
    __table_args__ = {"extend_existing": True}

    nm_bookmark: str = Field(primary_key=True)
    ds_bookmark: str | None = Field(default=None)
    nm_grouping: str | None = Field(default=None, index=True)
    nm_group_bookmark: str | None = Field(default=None, index=True)
    nm_subgroup_bookmark: str | None = Field(default=None, index=True)
    nm_tag: str | None = Field(default=None, index=True)
    url_bookmark: str
    ts_created: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, server_default=text("CURRENT_TIMESTAMP")),
    )
    ts_updated: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(
            DateTime, server_default=text("CURRENT_TIMESTAMP"), onupdate=datetime.now
        ),
    )


class Database:
    """Gerencia a conexão e as operações CRUD com o banco de dados."""

    def __init__(self, db_url: str = "sqlite:///./wsorg.db"):
        self.engine = create_engine(
            db_url, connect_args={"check_same_thread": False}
        )
        self._enable_wal_mode()
        self._create_db_and_tables()

    def _enable_wal_mode(self):
        """Habilita o modo WAL para melhor concorrência."""
        with self.engine.connect() as conn:
            conn.exec_driver_sql("PRAGMA journal_mode=WAL;")

    def _create_db_and_tables(self):
        """Cria as tabelas no banco de dados se não existirem."""
        SQLModel.metadata.create_all(self.engine)

    def get_session(self):
        """Retorna uma nova sessão do banco de dados."""
        return Session(self.engine)

    def seed_if_empty(self):
        """Popula o banco com dados iniciais se estiver vazio."""
        with self.get_session() as session:
            if not session.exec(select(Bookmark)).first():
                session.add_all(
                    [
                        Bookmark(
                            nm_bookmark="NiceGUI",
                            ds_bookmark="Framework UI em Python",
                            nm_grouping="Framework",
                            nm_group_bookmark="Develop",
                            nm_subgroup_bookmark="Python",
                            nm_tag="UI",
                            url_bookmark="https://nicegui.io/",
                        ),
                        Bookmark(
                            nm_bookmark="SQLModel",
                            ds_bookmark="ORM Pythonic",
                            nm_grouping="ORM",
                            nm_group_bookmark="Develop",
                            nm_subgroup_bookmark="Python",
                            nm_tag="Database",
                            url_bookmark="https://sqlmodel.tiangolo.com/",
                        ),
                    ]
                )
                session.commit()

    def get_all(self, model: Type[SQLModel]) -> list[dict[str, Any]]:
        """Busca todos os registros de um modelo e os retorna como dicionários."""
        with self.get_session() as session:
            items = session.exec(select(model)).all()
            return [item.model_dump() for item in items]

    def commit_session(self, session: Session):
        """Realiza o commit de uma sessão."""
        session.commit()