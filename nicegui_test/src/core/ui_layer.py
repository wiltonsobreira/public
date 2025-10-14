from __future__ import annotations

from typing import Any, cast

from nicegui import ui, events
from sqlmodel import SQLModel

from data_layer import Database, Produto


class ProductCatalogUI:
    """Constrói e gerencia a interface do usuário para o catálogo de produtos."""

    def __init__(self, db: Database, model: type[SQLModel]):
        self.db = db
        self.model = model
        self.input_fields: dict[str, ui.input] = {}

        self._setup_ui()

    def _setup_ui(self):
        """Configura todos os elementos da interface."""
        ui.dark_mode().enable()

        with ui.row().classes("items-center justify-between w-full"):
            ui.label("Catálogo de Produtos").classes("text-2xl font-bold")
            self.status_label = ui.label("").classes("text-sm opacity-80")

        self.grid = self._create_grid()
        self._create_crud_buttons()

    def _create_grid(self) -> ui.aggrid:
        """Cria e configura a AG Grid dinamicamente a partir do modelo."""
        col_defs = self._generate_col_defs()
        grid_options = {
            "columnDefs": col_defs,
            "rowData": self.db.get_all_products(),
            "rowSelection": "multiple",
            "animateRows": True,
            "defaultColDef": {"resizable": True, "sortable": True, "filter": True},
        }
        grid = ui.aggrid(grid_options).classes("w-full")
        grid.on(
            "cellValueChanged",
            self._on_cell_value_changed,
            # Passamos explicitamente os argumentos que queremos do evento.
            # Isso garante que o payload (e.args) seja um dicionário com essas chaves.
            args=["data", "colId", "newValue", "oldValue"],
        )
        return grid

    def _generate_col_defs(self) -> list[dict[str, Any]]:
        """Gera definições de coluna para a AG Grid a partir dos campos do modelo."""
        col_defs = []
        for name, field_info in self.model.model_fields.items():
            col_def = {
                "headerName": name.capitalize(),
                "field": name,
                "editable": name != "id",  # O campo 'id' não é editável
            }
            if name == "id":
                col_def["width"] = 90
            if field_info.annotation == float or field_info.annotation == int:
                col_def["filter"] = "agNumberColumnFilter"
            col_defs.append(col_def)
        return col_defs

    def _create_crud_buttons(self):
        """Cria os campos de entrada e botões para as operações CRUD."""
        with ui.row().classes("gap-2 my-2"):
            # Gera campos de input dinamicamente, exceto para 'id'
            for name, field_info in self.model.model_fields.items():
                if name != "id":
                    self.input_fields[name] = ui.input(label=name.capitalize()).classes(
                        "w-56"
                    )

            ui.button("Adicionar", on_click=self._add_row, color="primary")
            ui.button(
                "Excluir selecionados", on_click=self._delete_selected, color="negative"
            )
            ui.button("Recarregar", on_click=self.refresh_grid)

    def refresh_grid(self):
        """Atualiza os dados da grid buscando do banco."""
        self.grid.options["rowData"] = self.db.get_all_products()
        self.grid.update()
        self.status_label.set_text("Dados atualizados")

    async def _add_row(self):
        """Adiciona um novo produto ao banco de dados."""
        try:
            product_data = {}
            for name, field in self.input_fields.items():
                value = cast(str, field.value or "").strip()
                if not value:
                    await ui.notify(f"O campo '{name}' é obrigatório.", color="negative")
                    return

                # Converte o tipo se necessário
                field_type = self.model.model_fields[name].annotation
                product_data[name] = field_type(value)

            with self.db.get_session() as session:
                new_product = self.model(**product_data)
                session.add(new_product)
                self.db.commit_session(session)

            self.refresh_grid()
            await ui.notify("Produto adicionado.", color="positive")
            for field in self.input_fields.values():
                field.value = ""
        except (ValueError, TypeError):
            await ui.notify("Verifique os valores. Preço deve ser um número.", color="negative")
        except Exception as ex:
            await ui.notify(f"Erro ao adicionar: {ex}", color="negative")

    async def _delete_selected(self):
        """Exclui os produtos selecionados na grid."""
        try:
            selected_rows = await self.grid.get_selected_rows()
            if not selected_rows:
                await ui.notify("Selecione ao menos um registro.", color="negative")
                return

            ids_to_delete = [row["id"] for row in selected_rows if "id" in row]
            if not ids_to_delete:
                return

            with self.db.get_session() as session:
                for product_id in ids_to_delete:
                    product = session.get(self.model, product_id)
                    if product:
                        session.delete(product)
                self.db.commit_session(session)

            self.refresh_grid()
            await ui.notify(f"Excluídos: {len(ids_to_delete)} produto(s).", color="positive")
        except Exception as ex:
            await ui.notify(f"Erro ao excluir: {ex}", color="negative")

    async def _on_cell_value_changed(self, e: events.GenericEventArguments):
        """Manipula a edição de uma célula na grid e persiste a alteração."""
        try:
            # Graças ao `args=[...]` no `grid.on`, o payload é previsível.
            row = e.args["data"]
            field = e.args["colId"]
            new_value = e.args["newValue"]
            old_value = e.args["oldValue"]

            if not field or "id" not in row:
                await ui.notify("Evento inválido: campo ou id ausente.", color="negative")
                return

            if new_value == old_value:
                return

            # Converte o tipo se necessário
            field_type = self.model.model_fields[field].annotation
            try:
                new_value = field_type(new_value)
            except (ValueError, TypeError):
                await ui.notify(f"Valor inválido para '{field}'. Alteração revertida.", color="negative")
                self.refresh_grid()
                return

            with self.db.get_session() as session:
                product = session.get(self.model, row["id"])
                if not product:
                    await ui.notify("Registro não encontrado.", color="negative")
                    self.refresh_grid()
                    return

                setattr(product, field, new_value)
                session.add(product)
                self.db.commit_session(session)

            await ui.notify(f"Salvo: {field} = {new_value}", color="positive")
        except Exception as ex:
            await ui.notify(f"Erro ao salvar: {ex}", color="negative")
            self.refresh_grid()