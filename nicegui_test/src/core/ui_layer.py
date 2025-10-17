from __future__ import annotations

from typing import Any, cast, get_args, get_origin

from nicegui import events, ui
from sqlmodel import SQLModel, Field

from data_layer import Database


class GenericCatalogUI:
    """Constrói e gerencia uma interface de usuário genérica para um modelo SQLModel."""

    def __init__(self, db: Database, model: type[SQLModel]):
        self.db = db
        self.model = model
        self.input_fields: dict[str, ui.input] = {}

        # Acessa os metadados da tabela para encontrar a(s) chave(s) primária(s)
        pk_cols = self.model.__table__.primary_key.columns
        if not pk_cols:
            raise ValueError(f"O modelo {model.__name__} não possui chave primária.")
        # Pega o nome da primeira coluna da chave primária
        self.primary_key_field = list(pk_cols)[0].name

        self._setup_ui()

    def _setup_ui(self):
        """Configura todos os elementos da interface."""
        # Obtém o objeto dark_mode para registrar um callback.
        dark = ui.dark_mode()
        dark.enable()

        self._create_crud_buttons()
        self.grid = self._create_grid()

    def _create_grid(self) -> ui.aggrid:
        """Cria e configura a AG Grid dinamicamente a partir do modelo."""
        # Prepara as definições de coluna e os dados.
        col_defs = self._generate_col_defs()
        rows = self._get_formatted_rows()

        # Encontra o índice da coluna de URL para passar para html_columns.
        try:
            url_col_index = next(i for i, col in enumerate(col_defs) if col["field"] == "url_bookmark")
        except StopIteration:
            url_col_index = -1 # Coluna não encontrada

        grid_options = {
            "columnDefs": col_defs,
            "rowData": rows,
            "rowSelection": "multiple",
            "animateRows": True,
            "defaultColDef": {"resizable": True, "sortable": True, "filter": True},
        }

        # Usa o argumento `html_columns` para instruir a grade a renderizar HTML.
        html_columns = [url_col_index] if url_col_index != -1 else []
        grid = ui.aggrid(grid_options, html_columns=html_columns).classes("w-full h-[83vh]") # 90vh é valor percentual da tela verticalmente 
        
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
        pk_name = self.primary_key_field
        for name, field_info in self.model.model_fields.items():
            col_def = {
                "headerName": name.replace("_", " ").capitalize(),
                "field": name,
                "editable": "ts_" not in name,  # Torna todos os campos, exceto timestamps, editáveis
            }
            if name == pk_name:
                col_def["width"] = 150
            # A renderização do link agora é tratada por `html_columns`, não precisamos mais de cellRenderer.

            if field_info.annotation in (float, int):
                col_def["filter"] = "agNumberColumnFilter"
            col_defs.append(col_def)
        return col_defs

    def _create_crud_buttons(self):
        """Cria os campos de entrada e botões para as operações CRUD."""
        # Busca as opções para os comboboxes de tipo e subtipo.
        # O modelo é importado dinamicamente para evitar dependência circular.
        from data_layer import TypeBookmark, SubtypeBookmark
        type_options = self.db.get_all_from_column(TypeBookmark, "nm_type_bookmark")
        subtype_options = self.db.get_all_from_column(SubtypeBookmark, "nm_subtype_bookmark")

        with ui.row().classes("gap-2 my-4 items-center w-full flex-nowrap overflow-x-auto"):
            # Gera campos de input dinamicamente, exceto para timestamps
            for name, _ in self.model.model_fields.items():
                if "ts_" not in name:
                    label = name.replace("_", " ").capitalize()
                    if name == "nm_type_bookmark":
                        self.input_fields[name] = ui.select(
                            options=type_options, label=label
                        ).classes("w-48")
                    elif name == "nm_subtype_bookmark":
                        self.input_fields[name] = ui.select(
                            options=subtype_options, label=label
                        ).classes("w-48")
                    else:
                        self.input_fields[name] = ui.input(label=label).classes("w-48")

            ui.button("Add", on_click=self._add_row, color="primary")
            ui.button(
                "Delete", on_click=self._delete_selected, color="negative"
            )
            # ui.button("Recarregar", on_click=self.refresh_grid)
            ui.space()
            self.status_label = ui.label("").classes("text-sm opacity-80")

    def refresh_grid(self):
        """Atualiza os dados da grid buscando do banco."""
        self.grid.options["rowData"] = self._get_formatted_rows()
        self.grid.update()
        self.status_label.set_text("Dados atualizados")

    def _get_formatted_rows(self) -> list[dict[str, Any]]:
        """Busca os dados e formata a coluna de URL para conter uma tag HTML."""
        rows = self.db.get_all(self.model)
        for row in rows:
            # Verifica se a linha tem a chave 'url_bookmark' e se o valor não é nulo.
            if url := row.get("url_bookmark"):
                # Substitui a URL pura pela tag <a> completa.
                row["url_bookmark"] = f'<a href="{url}" target="_blank" rel="noopener noreferrer">{url}</a>'
        return rows

    async def _add_row(self):
        """Adiciona um novo registro ao banco de dados."""
        try:
            data = {}
            for name, field in self.input_fields.items():
                value = cast(str, field.value or "").strip()
                field_info = self.model.model_fields[name]

                # Permite valores vazios para campos opcionais
                if not value and not field_info.is_required():
                    data[name] = None
                    continue

                if not value and field_info.is_required():
                    await ui.notify(f"O campo '{name}' é obrigatório.", color="negative")
                    return

                # Converte o tipo se necessário
                data[name] = self._convert_type(value, field_info.annotation)

            with self.db.get_session() as session:
                new_item = self.model(**data)
                session.add(new_item)
                self.db.commit_session(session)

            for field in self.input_fields.values():
                field.value = ""
            self.refresh_grid()
            await ui.notify("Registro adicionado.", color="positive")
        except (ValueError, TypeError) as e:
            await ui.notify(f"Verifique os valores. Erro: {e}", color="negative") # type: ignore
        except Exception as ex:
            await ui.notify(f"Erro ao adicionar: {ex}", color="negative")

    async def _delete_selected(self):
        """Exclui os registros selecionados na grid."""
        try:
            selected_rows = await self.grid.get_selected_rows()
            if not selected_rows:
                await ui.notify("Selecione ao menos um registro.", color="negative")
                return

            ids_to_delete = [
                row[self.primary_key_field]
                for row in selected_rows
                if self.primary_key_field in row
            ]
            if not ids_to_delete:
                return

            with self.db.get_session() as session:
                for item_id in ids_to_delete:
                    item = session.get(self.model, item_id)
                    if item:
                        session.delete(item)
                self.db.commit_session(session)

            self.refresh_grid()
            await ui.notify(f"Excluídos: {len(ids_to_delete)} registro(s).", color="positive")
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

            if not field or self.primary_key_field not in row:
                await ui.notify("Evento inválido: campo ou id ausente.", color="negative")
                return

            if new_value == old_value:
                return

            # Converte o tipo se necessário
            field_type = self.model.model_fields[field].annotation
            new_value = self._convert_type(new_value, field_type)

            # Lógica para lidar com a atualização da chave primária
            if field == self.primary_key_field:
                with self.db.get_session() as session:
                    # Exclui o registro antigo
                    old_item = session.get(self.model, old_value)
                    if old_item:
                        session.delete(old_item)

                    # Cria um novo registro com a nova PK
                    new_data = row.copy()
                    new_data[self.primary_key_field] = new_value
                    # Remove os campos de timestamp, pois eles serão gerados automaticamente
                    # pelo banco de dados para o novo registro.
                    new_data.pop("ts_created", None)
                    new_data.pop("ts_updated", None)
                    new_item = self.model(**new_data)
                    session.add(new_item)
                    self.db.commit_session(session)
                await ui.notify(f"Chave primária atualizada para: {new_value}", color="positive")
                self.refresh_grid()
            else:
                # Lógica para atualizar outros campos
                with self.db.get_session() as session:
                    item = session.get(self.model, row[self.primary_key_field])
                    if not item:
                        await ui.notify("Registro não encontrado.", color="negative")
                        self.refresh_grid()
                        return

                    setattr(item, field, new_value)
                    session.add(item)
                    self.db.commit_session(session)
                await ui.notify(f"Salvo: {field} = {new_value}", color="positive")
        except Exception as ex:
            await ui.notify(f"Erro ao salvar: {ex}", color="negative")
            self.refresh_grid()

    @staticmethod
    def _convert_type(value: Any, target_type: Any) -> Any:
        """Converte um valor para o tipo de destino, lidando com tipos Union (opcionais)."""
        if value is None:
            return None

        # Se o tipo for uma união (ex: str | None), extrai os tipos base
        if get_origin(target_type) is not None:
            # Pega os tipos dentro da Union, ex: (str, NoneType)
            base_types = [t for t in get_args(target_type) if t is not type(None)]
            if base_types:
                # Usa o primeiro tipo não-None para a conversão
                return base_types[0](value)
            return value  # Se não houver tipo base, retorna o valor como está

        # Se não for uma união, converte diretamente
        return target_type(value)