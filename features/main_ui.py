import flet as ft
from log_sources_tab import log_sources_tab
from template_mapper_tab import template_mapper_tab


def main(page: ft.Page):
    page.title = "LoGEM - Log Intelligence"
    page.window.width = 1050        # window's width is 200 px
    page.window.height = 700       # window's height is 200 px
    page.window.resizable = False  # window is not resizable
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = "none"
    page.update()


    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        expand=True,
        tabs=[
            ft.Tab(text="Log Sources", content=log_sources_tab()),
            ft.Tab(text="Templates", content=template_mapper_tab()),
            ft.Tab(text="Models", content=ft.Text("Model Selector Coming Soon")),
            ft.Tab(text="Sample Test", content=ft.Text("Sample Test Tab Coming Soon")),
            ft.Tab(text="Output Config", content=ft.Text("Output Config Coming Soon")),
        ]
    )

    page.add(tabs)

ft.app(target=main, view=ft.AppView.FLET_APP)  # force local no-cloud
