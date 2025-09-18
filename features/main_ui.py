import flet as ft
from log_sources_tab import log_sources_tab
from template_mapper_tab import template_mapper_tab
from models_tab import models_tab
from sample_test_tab import sample_test_tab
from output_config_tab import output_config_tab
from log_service_manager import start_service_manager, stop_service_manager

def main(page: ft.Page):
    page.title = "LoGEM - Log Intelligence"
    page.window.width = 1050
    page.window.height = 700
    page.window.resizable = False
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = "none"
    
    # Start the background service manager
    start_service_manager()
    
    # Handle app close
    def on_window_event(e):
        if e.data == "close":
            stop_service_manager()
            page.window.destroy()
    
    page.window.on_event = on_window_event
    page.update()
    
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        expand=True,
        tabs=[
            ft.Tab(text="Log Sources", content=log_sources_tab()),
            ft.Tab(text="Templates", content=template_mapper_tab()),
            ft.Tab(text="Models", content=models_tab()),
            ft.Tab(text="Sample Test", content=sample_test_tab()),
            ft.Tab(text="Output Config", content=output_config_tab())
        ]
    )
    page.add(tabs)

ft.app(target=main, view=ft.AppView.FLET_APP)