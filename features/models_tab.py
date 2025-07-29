from turtle import heading
import flet as ft
import os
import yaml
from configs_handler import ConfigsHandler

def get_available_templates():
    """Scan ./templates directory for YAML files"""
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    options = []
    
    if os.path.exists(templates_dir):
        # List all files in directory
        try:
            files = os.listdir(templates_dir)
            # Filter for .yaml files
            yaml_files = [f for f in files if f.endswith('.yaml')]
            
            # Create options
            for filename in yaml_files:
                full_path = os.path.join(templates_dir, filename)
                options.append(ft.dropdown.Option(full_path, filename))
        except Exception as e:
            print(f"Error reading templates directory: {e}")
    
    return options

def get_available_models():
    """Scan models directory for GGUF files"""
    # Use relative path
    models_dir = os.path.join(os.path.dirname(__file__), "..", "..", "models")
    options = []
    
    if os.path.exists(models_dir):
        try:
            files = os.listdir(models_dir)
            # Filter for .gguf files
            gguf_files = [f for f in files if f.endswith('.gguf')]
            
            # Create options
            for filename in gguf_files:
                full_path = os.path.join(models_dir, filename)
                options.append(ft.dropdown.Option(full_path, filename))
        except Exception as e:
            print(f"Error reading models directory: {e}")
    
    return options

def models_tab():
    # Initialize config handlers
    config_handler = ConfigsHandler()
    models_config = ConfigsHandler(file_name="modelsmap.json")
    
    # Get current associations
    try:
        associations = models_config.get_saved_paths()
        if not isinstance(associations, dict):
            associations = {}
    except:
        associations = {}
    
    # Get available templates and models
    templates = [opt.key for opt in get_available_templates()]
    models = [opt.key for opt in get_available_models()]
    
    # Template selection dropdown
    template_dropdown = ft.Dropdown(
        label="Select Template",
        width=400,
        options=get_available_templates()
    )
    
    # Model selection dropdown
    model_dropdown = ft.Dropdown(
        label="Select Model",
        width=400,
        options=get_available_models()
    )
    
    # Model parameters
    temperature_slider = ft.Slider(
        min=0.1,
        max=1.0,
        divisions=9,
        value=0.2,
        label="{value}",
        width=400
    )
    
    top_k_slider = ft.Slider(
        min=0,
        max=10,
        divisions=10,
        value=5,
        label="{value}",
        width=400
    )
    
    top_p_slider = ft.Slider(
        min=0,
        max=10,
        divisions=10,
        value=5,
        label="{value}",
        width=400
    )
    
    # Association list
    associations_list = ft.ListView(spacing=5, expand=True)
    
    def save_mapping():
        models_config.save_mapping(associations)
    
    def refresh_associations():
        associations_list.controls.clear()
        for template, model_data in associations.items():
            model_filename = model_data[0] if isinstance(model_data, list) else model_data
            temp = model_data[1] if isinstance(model_data, list) and len(model_data) > 1 else "N/A"
            top_k = model_data[2] if isinstance(model_data, list) and len(model_data) > 2 else "N/A"
            top_p = model_data[3] if isinstance(model_data, list) and len(model_data) > 3 else "N/A"
            
            associations_list.controls.append(
                ft.Row([
                    ft.Text(template, expand=True),
                    ft.Text(" → "),
                    ft.Text(f"{model_filename} (T:{temp}, K:{top_k}, P:{top_p})", expand=True),
                    ft.IconButton(
                        icon="remove",
                        tooltip="Remove association",
                        icon_color="red",
                        on_click=lambda e, t=template: remove_association(t)
                    )
                ])
            )
        associations_list.update()
    
    def assign_model(template, model):
        # Get template filename only (not full path)
        template_filename = os.path.basename(template)
        model_filename = os.path.basename(model)
        
        # Store: {"template_filename": ["model_filename", temp, top_k, top_p]}
        associations[template_filename] = [
            model_filename,
            round(temperature_slider.value, 2),
            round(top_k_slider.value, 1),
            round(top_p_slider.value, 1)
        ]
        save_mapping()
        refresh_associations()
    
    def remove_association(template):
        if template in associations:
            del associations[template]
            save_mapping()
            refresh_associations()
    
    def reload_selections(e=None):
        # Reload templates and models only
        template_dropdown.options = get_available_templates()
        model_dropdown.options = get_available_models()
        template_dropdown.update()
        model_dropdown.update()
    
    def reload_associations(e=None):
        # Reload associations only
        refresh_associations()
    
    def reload_all(e=None):
        # Reload everything
        reload_selections()
        reload_associations()
    
    # Save association button
    save_button = ft.ElevatedButton(
        text="Associate Template with Model",
        icon="link",
        on_click=lambda e: assign_model(template_dropdown.value, model_dropdown.value) if template_dropdown.value and model_dropdown.value else None
    )
    
    return ft.Container(
        content=ft.Column([
            # Top row with two sections side by side
            ft.Row([
                # Section 1: Template/Model Selection + Association + Reload
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Template & Model Selection", size=14, weight="bold"),
                            ft.IconButton(
                                icon="refresh",
                                tooltip="Reload templates and models",
                                icon_color="blue",
                                on_click=reload_selections
                            )
                        ]),
                        ft.Divider(),
                        ft.Text("Template Selection:", size=12),
                        template_dropdown,
                        ft.Container(height=5),
                        ft.Text("Model Selection:", size=12),
                        model_dropdown,
                        ft.Container(height=5),
                        save_button,
                    ]),
                    width=490,
                    padding=10,
                    border=ft.border.all(1, "grey"),
                    border_radius=10,
                    height=345
                ),
                
                # Section 2: Model Parameters
                ft.Container(
                    content=ft.Column([
                        ft.Text("Model Parameters", size=14, weight="bold"),
                        ft.Divider(),
                        ft.Text("Temperature (0.1-1.0):", size=12),
                        temperature_slider,
                        ft.Container(height=5),
                        ft.Text("Top-K (0-10):", size=12),
                        top_k_slider,
                        ft.Container(height=5),
                        ft.Text("Top-P (0-10):", size=12),
                        top_p_slider,
                    ]),
                    width=490,
                    padding=10,
                    border=ft.border.all(1, "grey"),
                    border_radius=10,
                    height=345
                ),
            ], spacing=10),
            
            # Bottom section: Current Associations (full width, taller)
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Current Associations", size=14, weight="bold"),
                        ft.IconButton(
                            icon="refresh",
                            tooltip="Reload associations",
                            icon_color="blue",
                            on_click=reload_associations
                        )
                    ]),
                    ft.Divider(),
                    associations_list
                ]),
                padding=10,
                margin=ft.margin.only(top=10),
                border=ft.border.all(1, "lightgreen"),
                border_radius=10,
                height=220
            ),
        ], spacing=10),
        padding=10
    ) 