import flet as ft
import os
from configs_handler import ConfigsHandler

TEMPLATES_DIR = "../templates"

def load_templates():
    return [f for f in os.listdir(TEMPLATES_DIR) if f.endswith(".yaml")]

def template_mapper_tab():
    config_handler = ConfigsHandler()
    map_handler = ConfigsHandler(file_name="mapping.txt")
    templates = load_templates()

    try:
        mapping = map_handler.get_saved_paths()
        if not isinstance(mapping, dict):
            mapping = {}
    except Exception:
        mapping = {}

    selected_path = ft.Ref[ft.Dropdown]()
    available_list = ft.ListView(spacing=5, expand=True)
    assigned_list = ft.ListView(spacing=5, expand=True)

    def save_mapping():
        map_handler.save_mapping(mapping)

    def reload_paths(e=None):
        paths = config_handler.get_saved_paths()
    
        # Remove mappings for deleted paths
        removed_keys = [k for k in list(mapping.keys()) if k not in paths]
        for k in removed_keys:
            del mapping[k]
    
        save_mapping()
    
        # Update dropdown with only valid paths
        valid_paths = [p for p in paths if p in mapping or p not in removed_keys]
        selected_path.current.options = [ft.dropdown.Option(p) for p in valid_paths]
        selected_path.current.update()
    
        # Clear selection if it's gone
        if selected_path.current.value not in valid_paths:
            selected_path.current.value = None
            available_list.controls.clear()
            assigned_list.controls.clear()
            available_list.update()
            assigned_list.update()


    def refresh_lists(e=None):
        path = selected_path.current.value
        if not path:
            available_list.controls.clear()
            assigned_list.controls.clear()
            return

        assigned = mapping.get(path, [])
        available = [t for t in templates if t not in assigned]

        available_list.controls.clear()
        for tmpl in available:
            available_list.controls.append(
                ft.Row([
                    ft.Text(tmpl, expand=True),
                    ft.IconButton(icon="add", tooltip="Assign", on_click=lambda e, t=tmpl: assign_template(path, t))
                ])
            )

        assigned_list.controls.clear()
        for tmpl in assigned:
            assigned_list.controls.append(
                ft.Row([
                    ft.Text(tmpl, expand=True),
                    ft.IconButton(icon="remove", tooltip="Unassign", icon_color="red", on_click=lambda e, t=tmpl: remove_template(path, t))
                ])
            )

        available_list.update()
        assigned_list.update()

    def assign_template(path, template_name):
        mapping.setdefault(path, [])
        if template_name not in mapping[path]:
            mapping[path].append(template_name)
            save_mapping()
            refresh_lists()

    def remove_template(path, template_name):
        if template_name in mapping.get(path, []):
            mapping[path].remove(template_name)
            if not mapping[path]:
                del mapping[path]
            save_mapping()
            refresh_lists()

    dropdown = ft.Dropdown(
        ref=selected_path,
        options=[ft.dropdown.Option(p) for p in config_handler.get_saved_paths()],
        on_change=refresh_lists,
        on_focus=reload_paths,  # also handled from button
        hint_text="Select a saved log path",
        width=800
    )

    return ft.Container(
        content=ft.Column([
            ft.Row([
                dropdown,
                ft.IconButton(
                    icon="refresh",
                    tooltip="Reload paths and sync mapping",
                    icon_color="blue",
                    on_click=reload_paths
                )
            ]),
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("Available Templates", size=14, weight="bold"),
                        available_list
                    ]),
                    border=ft.border.all(1, "grey"),
                    margin=ft.margin.only(top=10),
                    border_radius=10,
                    padding=10,
                    width=475,
                    height=475
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Assigned Templates", size=14, weight="bold"),
                        assigned_list
                    ]),
                    border=ft.border.all(1, "lightgreen"),
                    margin=ft.margin.only(top=10),
                    border_radius=10,
                    padding=10,
                    width=475,
                    height=475
                )
            ])
        ], spacing=20, scroll="auto"),
        padding=20
    )
