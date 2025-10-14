# app.py
from __future__ import annotations

import json
from typing import Any

from nicegui import ui
from sqlmodel import SQLModel, Field, Session, create_engine, select

# =========================
#   MODELO & BANCO (SQLite)
# =========================

class Produto(SQLModel, table=True):
    __tablename__ = "produto"
    # Evita erro "Table 'produto' is already defined..." em cenários de hot-reload
    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    nome: str
    categoria: str
    preco: float


engine = create_engine("sqlite:///./app.db", connect_args={"check_same_thread": False})

# Habilita WAL para melhorar leituras concorrentes em apps web
with engine.connect() as conn:
    conn.exec_driver_sql("PRAGMA journal_mode=WAL;")

SQLModel.metadata.create_all(engine)


def seed_if_empty() -> None:
    with Session(engine) as s:
        if not s.exec(select(Produto)).first():
            s.add_all(
                [
                    Produto(nome="Teclado", categoria="Periférico", preco=199.9),
                    Produto(nome="Mouse", categoria="Periférico", preco=99.9),
                    Produto(nome="Monitor", categoria="Vídeo", preco=1299.0),
                ]
            )
            s.commit()


def fetch_all() -> list[dict[str, Any]]:
    with Session(engine) as s:
        produtos = s.exec(select(Produto)).all()
        # Se estiver com Pydantic v2 (SQLModel recente), use model_dump(); caso contrário, pode usar .dict()
        return [p.model_dump() for p in produtos]


seed_if_empty()

# ================
#   UI (NiceGUI)
# ================

ui.dark_mode().enable()  # opcional

with ui.row().classes("items-center justify-between w-full"):
    ui.label("Catálogo de Produtos").classes("text-2xl font-bold")
    status = ui.label("").classes("text-sm opacity-80")

# Definição de colunas da AG Grid
col_defs = [
    {"headerName": "ID", "field": "id", "sortable": True, "filter": True, "editable": False, "width": 90},
    {"headerName": "Nome", "field": "nome", "sortable": True, "filter": True, "editable": True},
    {"headerName": "Categoria", "field": "categoria", "sortable": True, "filter": True, "editable": True},
    {
        "headerName": "Preço",
        "field": "preco",
        "sortable": True,
        "filter": "agNumberColumnFilter",
        "editable": True,
        # Validação visual básica no front pode ser feita com valueParser/formatter se quiser
    },
]

grid_options = {
    "columnDefs": col_defs,
    "rowData": fetch_all(),
    "rowSelection": "multiple",
    "animateRows": True,
    "defaultColDef": {
        "resizable": True,
        "sortable": True,
        "filter": True,
        "enableRowGroup": True,
    },
}

grid = ui.aggrid(grid_options).classes("w-full")

# -----------------------------
#   Funções de suporte (CRUD)
# -----------------------------

def refresh_grid() -> None:
    grid.options["rowData"] = fetch_all()
    grid.update()
    status.set_text("Dados atualizados")

async def notify_ok(msg: str) -> None:
    ui.notify(msg, color="positive")

async def notify_err(msg: str) -> None:
    ui.notify(msg, color="negative")

# Handler de edição inline: persiste a alteração no SQLite
async def on_cell_value_changed(e):
    """
    Evento do AG Grid: 'cellValueChanged'
    Espera-se um payload com as chaves:
      - data: dict da linha inteira (inclui 'id')
      - colDef: dict com 'field'
      - newValue: novo valor
      - oldValue: valor antigo
    """
    try:
        payload = e.args
        if isinstance(payload, str):
            payload = json.loads(payload)

        row = payload.get("data") or {}
        field = (payload.get("colDef") or {}).get("field")
        new_value = payload.get("newValue")
        old_value = payload.get("oldValue")

        if not field or "id" not in row:
            await notify_err("Evento inválido: campo ou id ausente")
            return

        # Curto-circuito: nada mudou
        if new_value == old_value:
            return

        # Conversão de tipo simples para 'preco'
        if field == "preco":
            try:
                new_value = float(new_value)
            except Exception:
                await notify_err("Preço inválido (use número). Alteração revertida.")
                # Força refresh para reverter no grid
                refresh_grid()
                return

        with Session(engine) as s:
            produto = s.get(Produto, row["id"])
            if not produto:
                await notify_err("Registro não encontrado.")
                refresh_grid()
                return

            # Seta o atributo dinamicamente
            setattr(produto, field, new_value)
            s.add(produto)
            s.commit()

        await notify_ok(f"Salvo: {field} = {new_value}")
        # Opcional: manter sem refresh total para preservar posição/foco.
        # Se preferir consistência total com o DB (gatilhos, arredondamentos, etc.), descomente:
        # refresh_grid()

    except Exception as ex:
        await notify_err(f"Erro ao salvar: {ex}")
        refresh_grid()

# Vincula o handler ao evento do grid
grid.on("cellValueChanged", on_cell_value_changed)

# Botões CRUD
with ui.row().classes("gap-2 my-2"):
    nome_in = ui.input(label="Nome").classes("w-56")
    cat_in = ui.input(label="Categoria").classes("w-56")
    preco_in = ui.input(label="Preço").classes("w-40")

    async def add_row():
        try:
            nome = (nome_in.value or "").strip()
            categoria = (cat_in.value or "").strip()
            preco_str = (preco_in.value or "").strip()

            if not nome or not categoria or not preco_str:
                await notify_err("Preencha Nome, Categoria e Preço.")
                return

            preco = float(preco_str)

            with Session(engine) as s:
                p = Produto(nome=nome, categoria=categoria, preco=preco)
                s.add(p)
                s.commit()

            refresh_grid()
            await notify_ok("Produto adicionado.")
            nome_in.value = ""
            cat_in.value = ""
            preco_in.value = ""
        except Exception as ex:
            await notify_err(f"Erro ao adicionar: {ex}")

    async def delete_selected():
        try:
            # NiceGUI fornece método utilitário para pegar linhas selecionadas
            selected_rows = await grid.get_selected_rows()
            if not selected_rows:
                await notify_err("Selecione ao menos um registro.")
                return

            ids = [r.get("id") for r in selected_rows if r.get("id") is not None]
            if not ids:
                await notify_err("Seleção sem IDs válidos.")
                return

            with Session(engine) as s:
                for _id in ids:
                    obj = s.get(Produto, _id)
                    if obj:
                        s.delete(obj)
                s.commit()

            refresh_grid()
            await notify_ok(f"Excluídos: {ids}")
        except Exception as ex:
            await notify_err(f"Erro ao excluir: {ex}")

    ui.button("Adicionar", on_click=add_row, color="primary")
    ui.button("Excluir selecionados", on_click=delete_selected, color="negative")
    ui.button("Recarregar", on_click=refresh_grid)

ui.run(port=8080)
