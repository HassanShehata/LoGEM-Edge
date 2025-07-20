import flet as ft
from log_files_handler import LogFilesHandler


def log_sources_tab():
    log_handler = LogFilesHandler()
    log_paths = log_handler.list_log_sources()

    available_list = ft.ListView(spacing=5, expand=True)
    saved_items = []  # Just strings
    saved_column = ft.ListView(spacing=5, expand=True)
    custom_input = ft.TextField(label="Add custom log path", expand=True)
    def add_custom_path(e):
        path = custom_input.value.strip()
        if not path:
            return  # Ignore empty input
    
        row = ft.Row([
            ft.Text(path, expand=True),
            ft.IconButton(
                icon="remove",
                tooltip="Remove from saved",
                icon_color="red",
                on_click=lambda ev: (
                    saved_column.controls.remove(ev.control.parent),
                    saved_column.update()
                )
            )
        ])
    
        saved_column.controls.append(row)
        saved_column.update()
        custom_input.value = ""
        custom_input.update()
    
    add_custom_button = ft.IconButton(
        icon="add",
        tooltip="Add custom path",
        icon_color="blue",
        on_click=add_custom_path
    )



    # Populate available items
    for path in log_paths:
        available_list.controls.append(
            ft.Row([
                ft.Text(path, expand=True),
                ft.IconButton(
                    icon="add",
                    tooltip="Add to saved",
                    on_click=lambda e, p=path: (
                        (
                            lambda row: (
                                saved_column.controls.append(row),
                                available_list.controls.remove(e.control.parent),
                                saved_column.update(),
                                available_list.update()
                            )
                        )(
                            ft.Row([
                                ft.Text(p, expand=True),
                                ft.IconButton(
                                    icon="remove",
                                    tooltip="Remove from saved",
                                    icon_color="red",
                                    on_click=lambda ev: (
                                        saved_column.controls.remove(ev.control.parent),
                                        available_list.controls.append(
                                            ft.Row([
                                                ft.Text(p, expand=True),
                                                ft.IconButton(
                                                    icon="add",
                                                    tooltip="Add to saved",
                                                    on_click=e.control.on_click  # reuse original add
                                                )
                                            ])
                                        ),
                                        saved_column.update(),
                                        available_list.update()
                                    )
                                )
                            ])
                        )
                    )

                )

            ])
        )

        

    return ft.Row(
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Text("Detected Log Paths:", size=16, weight="bold"),
                    ft.Container(
                        content=available_list,
                        height=400,
                        expand=True
                    )
                ]),
                width=500,
                padding=10,
                margin=ft.margin.only(top=10),
                border=ft.border.all(2, "yellow"),
                border_radius=10
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Saved Paths", size=16, weight="bold"),
                    ft.Container(
                        content=saved_column,
                        height=400,
                        expand=True
                    ),
                    ft.Container(
                        content=ft.Row([custom_input, add_custom_button]),
                        bgcolor="lightblue",
                        padding=10,
                        margin=ft.margin.only(top=10)
                    )
                ]),
                width=500,
                padding=10,
                margin=ft.margin.only(top=10),
                border=ft.border.all(2, "green"),
                border_radius=10
            )
        ]
    )
