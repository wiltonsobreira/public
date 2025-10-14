from __future__ import annotations

from nicegui import ui

from data_layer import Database, Produto
from ui_layer import ProductCatalogUI


def main():
    """Inicializa o banco de dados, a UI e executa a aplicação."""
    db = Database()
    db.seed_if_empty()
    ProductCatalogUI(db, Produto)
    ui.run(port=8080)

main()