from __future__ import annotations

from typing import Any

from sqlmodel import Field, Session, SQLModel, create_engine, select


class Produto(SQLModel, table=True):
    """Define o modelo de dados para um Produto."""

    __tablename__ = "produto"
    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(index=True)
    categoria: str
    preco: float


class Database:
    """Gerencia a conexão e as operações CRUD com o banco de dados."""

    def __init__(self, db_url: str = "sqlite:///./app.db"):
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
            if not session.exec(select(Produto)).first():
                session.add_all(
                    [
                        Produto(nome="Teclado", categoria="Periférico", preco=199.9),
                        Produto(nome="Mouse", categoria="Periférico", preco=99.9),
                        Produto(nome="Monitor", categoria="Vídeo", preco=1299.0),
                    ]
                )
                session.commit()

    def get_all_products(self) -> list[dict[str, Any]]:
        """Busca todos os produtos e os retorna como dicionários."""
        with self.get_session() as session:
            produtos = session.exec(select(Produto)).all()
            return [p.model_dump() for p in produtos]

    def get_product(self, product_id: int) -> Produto | None:
        """Busca um produto pelo seu ID."""
        with self.get_session() as session:
            return session.get(Produto, product_id)

    def commit_session(self, session: Session):
        """Realiza o commit de uma sessão."""
        session.commit()