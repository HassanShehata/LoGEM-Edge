import flet as ft
import re
import os
from configs_handler import ConfigsHandler
from template_handler import TemplateHandler
from llm_handler import LLMHandler
import Evtx.Evtx as evtx
import xml.etree.ElementTree as ET


def sample_test_tab():
    config_handler = ConfigsHandler()
    template_map_handler = ConfigsHandler(file_name="mapping.txt")
    model_map_handler = ConfigsHandler(file_name="modelsmap.json")

    selected_path = ft.Ref[ft.Dropdown]()
    selected_template = ft.Ref[ft.Dropdown]()
    selected_model = ft.Ref[ft.Dropdown]()
    log_output = ft.Text()
    log_input = ft.TextField(
        label="Paste a log line manually or select below",
        multiline=True, min_lines=3, expand=True
    )
    result_box = ft.TextField(
        label="LLM Output",
        multiline=True, min_lines=3,
        expand=True, read_only=True
    )

    # Preload options for paths, templates and models at construction time
    _paths_options = [ft.dropdown.Option(p) for p in config_handler.get_saved_paths()]
    _template_files = [os.path.basename(p) for p in TemplateHandler.list_templates()]
    _template_options = [ft.dropdown.Option(t) for t in _template_files]
    _models_dir = os.path.abspath(os.path.join("..", "..", "models"))
    _models_files = [f for f in os.listdir(_models_dir) if f.endswith(".gguf")] if os.path.exists(_models_dir) else []
    _models_options = [ft.dropdown.Option(f) for f in _models_files]

    dropdown_paths = ft.Dropdown(
        ref=selected_path, width=800,
        hint_text="Select a saved path", options=_paths_options
    )
    dropdown_templates = ft.Dropdown(
        ref=selected_template, width=800,
        hint_text="Select assigned template", options=_template_options
    )
    dropdown_models = ft.Dropdown(
        ref=selected_model, width=800,
        hint_text="Select model (optional override)", options=_models_options
    )
    lines_list = ft.Dropdown(width=800, hint_text="Select a sample log line from file")


    def refresh_paths(e=None):
        paths = config_handler.get_saved_paths()
        dropdown_paths.options = [ft.dropdown.Option(p) for p in paths]
        dropdown_paths.update()


    def refresh_templates(e=None):
        # Always list all available templates; ignore any mapping
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
        template_name = selected_template.current.value
        if not path or not os.path.isfile(path):
            lines_list.options = [ft.dropdown.Option("No valid path selected")]
            lines_list.update()
            return
    
        options = []
        
        if path.lower().endswith('.evtx'):
            try:
                import Evtx.Evtx as evtx
                
                with evtx.Evtx(path) as log:
                    count = 0
                    for record in log.records():
                        if count >= 10:  # Limit to first 10 records
                            break
                        
                        xml_content = record.xml()
                        '''
                        # Extract readable text from XML
                        import xml.etree.ElementTree as ET
                        root = ET.fromstring(xml_content)
                        
                        # Try to find event data
                        event_data = ""
                        for elem in root.iter():
                            if elem.text and elem.text.strip():
                                event_data += elem.text.strip() + " "
                        
                        if event_data:
                            clean_data = event_data[:200]  # Limit length
                            options.append(ft.dropdown.Option(clean_data))
                        '''
                        options.append(ft.dropdown.Option(xml_content))
                        count += 1
                        

                        
            except Exception as e:
                options.append(ft.dropdown.Option(f"EVTX error: {str(e)[:100]}"))
        else:
            # Handle regular text files
            try:
                with open(path, "r", errors="ignore") as f:
                    lines = f.readlines()[:20]
                for line in lines:
                    if line.strip():
                        options.append(ft.dropdown.Option(line.strip()[:150]))
            except Exception as e:
                options.append(ft.dropdown.Option(f"File error: {str(e)[:100]}"))
        
        if not options:
            options.append(ft.dropdown.Option("No data found"))
            
        lines_list.options = options
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

        # Fallback to a mapped model if none selected
        if not model_name:
            model_name = model_map_handler.get_saved_paths().get(template_name, [None])[0]
        if not model_name:
            result_box.value = "Model not selected or mapped."
            result_box.update()
            return

        sanitized = log_line.strip()

        '''
        # Flatten the log line: remove tabs/newlines and collapse multiple spaces
        sanitized = log_line.replace("\t", " ").replace("\n", " ").replace("\n\t", " ")
        while "  " in sanitized:
            sanitized = sanitized.replace("  ", " ")
        '''

        template_path = os.path.join("..", "templates", template_name)
        handler = TemplateHandler(template_path)
        
        # Check if log matches template type criteria
        if not handler.matches_log(sanitized):
            result_box.value = "No logs match defined type in the template"
            result_box.update()
            return
        
        prompt = handler.get_prompt()
        model_template = handler.get_model_template()
        model_params = handler.get_model_params()
        output_format = handler.get_output_format()
        
        constructed_prompt = f"{prompt}\nRAW_LOG: {sanitized}"
        full_prompt = model_template.replace("{{ .Prompt }}", constructed_prompt)
        
        # Infer with sanitized log line
        llm = LLMHandler(model_name=model_name, n_ctx=2048)
        response, latency = llm.infer(
            full_prompt,
            model_params=model_params,
            max_tokens=model_params.get("max_tokens", 2048)
        )
        
        # Convert to SYSLOG format if needed
        if output_format.upper() == "SYSLOG":
            formatted_response = handler.json_to_syslog(response)
            result_box.value = f"{formatted_response}\n\nTime: {latency} sec"
        else:
            result_box.value = f"{response}\n\nTime: {latency} sec"
        
        result_box.update()

    # Refresh templates and sample lines when a new path is selected
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
            ft.ElevatedButton(text="Parse", icon="play_arrow", on_click=run_parser),
            result_box
        ], spacing=10, scroll="auto"),
        padding=20
    )
