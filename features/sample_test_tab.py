import flet as ft
import os

from configs_handler import ConfigsHandler
from template_handler import TemplateHandler
from llm_handler import LLMHandler

def sample_test_tab():
    config_handler = ConfigsHandler()
    # We still initialise these for fallback model lookup, but mapping doesn’t
    # restrict the lists shown in the dropdowns.
    template_map_handler = ConfigsHandler(file_name="mapping.txt")
    model_map_handler = ConfigsHandler(file_name="modelsmap.json")

    selected_path = ft.Ref[ft.Dropdown]()
    selected_template = ft.Ref[ft.Dropdown]()
    selected_model = ft.Ref[ft.Dropdown]()

    log_input = ft.TextField(label="Paste a log line manually or select below",
                             multiline=True, min_lines=3, expand=True)
    result_box = ft.TextField(label="LLM Output", multiline=True,
                              min_lines=3, expand=True, read_only=True)

    # Preload available options for paths, templates and models. Doing this
    # at construction time avoids calling update() on unmounted controls.
    _paths_options = [ft.dropdown.Option(p) for p in config_handler.get_saved_paths()]
    _template_files = [os.path.basename(p) for p in TemplateHandler.list_templates()]
    _template_options = [ft.dropdown.Option(t) for t in _template_files]
    _models_dir = os.path.abspath(os.path.join("..", "..", "models"))
    _models_files = [f for f in os.listdir(_models_dir) if f.endswith(".gguf")] if os.path.exists(_models_dir) else []
    _models_options = [ft.dropdown.Option(f) for f in _models_files]

    dropdown_paths = ft.Dropdown(ref=selected_path, width=800,
                                 hint_text="Select a saved path",
                                 options=_paths_options)
    dropdown_templates = ft.Dropdown(ref=selected_template, width=800,
                                     hint_text="Select assigned template",
                                     options=_template_options)
    dropdown_models = ft.Dropdown(ref=selected_model, width=800,
                                  hint_text="Select model (optional override)",
                                  options=_models_options)
    lines_list = ft.Dropdown(width=800, hint_text="Select a sample log line from file")

    def refresh_paths(e=None):
        paths = config_handler.get_saved_paths()
        dropdown_paths.options = [ft.dropdown.Option(p) for p in paths]
        dropdown_paths.update()

    def refresh_templates(e=None):
        # In the test tab we ignore any mapping and simply list all templates.
        template_files = [os.path.basename(p) for p in TemplateHandler.list_templates()]
        dropdown_templates.options = [ft.dropdown.Option(t) for t in template_files]
        dropdown_templates.update()

    def refresh_models(e=None):
        models_dir = os.path.abspath(os.path.join("..", "..", "models"))
        models = [f for f in os.listdir(models_dir) if f.endswith(".gguf")] if os.path.exists(models_dir) else []
        dropdown_models.options = [ft.dropdown.Option(f) for f in models]
        dropdown_models.update()

    def load_sample_lines(e=None):
        path = selected_path.current.value
        if not path or not os.path.isfile(path):
            lines_list.options = []
        else:
            with open(path, "r", errors="ignore") as f:
                lines = [line.strip() for line in f.readlines()]
            limited = lines[:100] if len(lines) > 100 else lines
            lines_list.options = [ft.dropdown.Option(line) for line in limited if line.strip()]
        lines_list.update()

    def select_line(e):
        log_input.value = lines_list.value
        log_input.update()

    def run_parser(e):
        log_line = log_input.value.strip()
        if not log_line:
            result_box.value = "No log line provided."
            result_box.update()
            return

        template_name = selected_template.current.value
        model_name = selected_model.current.value
        if not template_name:
            result_box.value = "Template not selected."
            result_box.update()
            return

        # Fallback to mapped model if none selected
        if not model_name:
            model_name = model_map_handler.get_saved_paths().get(template_name, [None])[0]
        if not model_name:
            result_box.value = "Model not selected or mapped."
            result_box.update()
            return

        template_path = os.path.join("..", "templates", template_name)
        handler = TemplateHandler(template_path)
        instruction = handler.get_instruction()
        template_text = handler.get_output_template()
        output_format = handler.get_output_format()

        llm = LLMHandler(model_name=model_name, n_ctx=1024)
        response, latency = llm.infer(instruction, template_text,
                                      log_line, output_format=output_format, max_tokens=256)
        result_box.value = f"{response}\n\nTime: {latency} sec"
        result_box.update()

    # Refresh available templates and sample lines whenever a new path is selected.
    dropdown_paths.on_change = lambda e: (refresh_templates(), load_sample_lines())

    return ft.Container(
        content=ft.Column([
            ft.Row([dropdown_paths,
                    ft.IconButton(icon="refresh", tooltip="Refresh Paths",
                                  on_click=refresh_paths)]),
            ft.Row([dropdown_templates,
                    ft.IconButton(icon="refresh", tooltip="Refresh Templates",
                                  on_click=refresh_templates)]),
            ft.Row([dropdown_models,
                    ft.IconButton(icon="refresh", tooltip="Refresh Models",
                                  on_click=refresh_models)]),
            ft.Row([lines_list,
                    ft.IconButton(icon="download", tooltip="Load log lines",
                                  on_click=load_sample_lines),
                    ft.IconButton(icon="select_all", tooltip="Use selected line",
                                  on_click=select_line)]),
            log_input,
            ft.ElevatedButton(text="Parse", icon="play_arrow",
                              on_click=run_parser),
            result_box
        ], spacing=10, scroll="auto"),
        padding=20
    )
