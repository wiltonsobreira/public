from __future__ import annotations

from nicegui import ui

from data_layer import Bookmark, Database
from ui_layer import create_catalog_ui


def main():
    """Inicializa o banco de dados, a UI e executa a aplicação."""
    db = Database()
    db.seed_if_empty()
    create_catalog_ui(db, Bookmark)
    ui.run(port=8080)


main()