from __future__ import annotations

from nicegui import ui

from data_layer import Bookmark, Database
from ui_layer import GenericCatalogUI


def main():
    """Inicializa o banco de dados, a UI e executa a aplicação."""
    db = Database()
    db.seed_if_empty()
    GenericCatalogUI(db, Bookmark)
    ui.run(port=8080)


main()