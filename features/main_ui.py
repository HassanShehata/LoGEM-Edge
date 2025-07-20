import flet as ft
from log_sources_tab import log_sources_tab

def main(page: ft.Page):
    page.title = "LoGEM - Log Intelligence"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = "none"
    page.window_width = 800
    page.window_height = 500

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        expand=True,
        tabs=[
            ft.Tab(text="Log Sources", content=log_sources_tab()),
            ft.Tab(text="Templates", content=ft.Text("Templates Tab Coming Soon")),
            ft.Tab(text="Models", content=ft.Text("Model Selector Coming Soon")),
            ft.Tab(text="Sample Test", content=ft.Text("Sample Test Tab Coming Soon")),
            ft.Tab(text="Output Config", content=ft.Text("Output Config Coming Soon")),
        ]
    )

    page.add(tabs)

ft.app(target=main)