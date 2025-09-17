import flet as ft
import os
from configs_handler import ConfigsHandler

def output_config_tab():
    config_handler = ConfigsHandler()
    mapping_handler = ConfigsHandler(file_name="mapping.txt") 
    models_handler = ConfigsHandler(file_name="modelsmap.json")
    
    # Forwarder config fields
    ip_field = ft.TextField(label="IP Address", width=200, value="127.0.0.1")
    port_field = ft.TextField(label="Port", width=100, value="514")
    protocol_dropdown = ft.Dropdown(
        label="Protocol",
        width=100,
        value="TCP",
        options=[
            ft.dropdown.Option("TCP"),
            ft.dropdown.Option("UDP")
        ]
    )
    
    hierarchy_view = ft.ListView(spacing=10, expand=True)
    
    def load_configs(e=None):
        hierarchy_view.controls.clear()
        
        # Load data
        saved_paths = config_handler.get_saved_paths()
        template_mapping = mapping_handler.get_saved_paths()  
        model_mapping = models_handler.get_saved_paths()
        
        # Build hierarchy
        for path in saved_paths:
            templates = template_mapping.get(path, [])
            
            # Create override config for this file
            file_ip = ft.TextField(label="IP Override", width=150, value=ip_field.value)
            file_port = ft.TextField(label="Port Override", width=80, value=port_field.value)
            file_protocol = ft.Dropdown(
                label="Protocol Override",
                width=120,
                value=protocol_dropdown.value,
                options=[
                    ft.dropdown.Option("TCP"),
                    ft.dropdown.Option("UDP")
                ]
            )
    
            override_box = ft.Container(
                content=ft.Column([
                    ft.Text("Override Forwarding Config", size=12, weight="bold"),
                    ft.Row([file_ip, file_port, file_protocol])
                ]),
                padding=10,
                border=ft.border.all(1, "orange"),
                border_radius=5,
                margin=ft.margin.only(top=10, bottom=10)
            )
            
            # Template items for this file
            template_items = []
            for template in templates:
                model_info = model_mapping.get(template, ["No model assigned"])
                model_name = model_info[0] if isinstance(model_info, list) else model_info
                
                # Color based on model assignment
                model_color = "green" if model_name != "No model assigned" else "red"
                
                if model_name != "No model assigned":
                    # Create buttons with state
                    enable_btn = ft.ElevatedButton("Enable", color="green", height=30)
                    start_btn = ft.ElevatedButton("Start", color="blue", height=30)
                    
                    def toggle_enable(e, btn=enable_btn):
                        if btn.text == "Enable":
                            btn.text = "Disable"
                            btn.color = "red"
                        else:
                            btn.text = "Enable"
                            btn.color = "green"
                        btn.update()
                    
                    def toggle_start(e, btn=start_btn):
                        if btn.text == "Start":
                            btn.text = "Stop"
                            btn.color = "orange"
                        else:
                            btn.text = "Start"
                            btn.color = "blue"
                        btn.update()
                    
                    enable_btn.on_click = toggle_enable
                    start_btn.on_click = toggle_start
                    
                    template_items.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text(f"📄 {template} "),
                                ft.Text(f"({model_name})", color=model_color),
                                enable_btn,
                                start_btn
                            ]),
                            padding=ft.padding.only(left=20, top=5, bottom=5)
                        )
                    )
                else:
                    # Template without model - add pass-through buttons
                    passthrough_btn = ft.ElevatedButton("Pass-through", color="purple", height=30)
                    passthrough_start_btn = ft.ElevatedButton("Start", color="blue", height=30)
                    
                    def toggle_passthrough(e, btn=passthrough_btn):
                        if btn.text == "Pass-through":
                            btn.text = "Disable"
                            btn.color = "red"
                        else:
                            btn.text = "Pass-through"
                            btn.color = "purple"
                        btn.update()
                    
                    def toggle_passthrough_start(e, btn=passthrough_start_btn):
                        if btn.text == "Start":
                            btn.text = "Stop"
                            btn.color = "orange"
                        else:
                            btn.text = "Start"
                            btn.color = "blue"
                        btn.update()
                    
                    passthrough_btn.on_click = toggle_passthrough
                    passthrough_start_btn.on_click = toggle_passthrough_start
                    
                    template_items.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text(f"📄 {template} "),
                                ft.Text(f"({model_name})", color=model_color),
                                passthrough_btn,
                                passthrough_start_btn
                            ]),
                            padding=ft.padding.only(left=20, top=5, bottom=5)
                        )
                    )
            
            if not templates:
                template_items.append(
                    ft.Container(
                        content=ft.Text("  No templates assigned", color="orange"),
                        padding=ft.padding.only(left=20, top=5, bottom=5)
                    )
                )
            
            # File level container
            file_container = ft.Container(
                content=ft.Column([
                    ft.Text(f"📁 {os.path.basename(path)}", weight="bold"),
                    ft.Row([
                        # Left side - templates
                        ft.Container(
                            content=ft.Column(template_items),
                            expand=True
                        ),
                        # Right side - override box
                        ft.Container(
                            content=override_box,
                            width=400
                        )
                    ])
                ]),
                padding=10,
                border=ft.border.all(1, "blue"),
                border_radius=5
            )
            
            hierarchy_view.controls.append(file_container)
        
        if hierarchy_view.page:
            hierarchy_view.update()
    
    # Initial load
    load_configs()
    
    return ft.Container(
        content=ft.Column([
            # Forwarder defaults section
            ft.Container(
                content=ft.Column([
                    ft.Text("Forwarder Default Configs", size=14, weight="bold"),
                    ft.Row([
                        ip_field,
                        port_field,
                        protocol_dropdown
                    ])
                ]),
                padding=10,
                border=ft.border.all(1, "grey"),
                border_radius=5,
                margin=ft.margin.only(bottom=20)
            ),
            
            # Available configs section
            ft.Row([
                ft.Text("Available Configs", size=16, weight="bold"),
                ft.IconButton(
                    icon="refresh",
                    tooltip="Reload configs",
                    on_click=load_configs
                )
            ]),
            ft.Container(
                content=hierarchy_view,
                height=400,
                expand=True
            )
        ]),
        padding=20
    )








"""

import flet as ft
import os
from configs_handler import ConfigsHandler

def output_config_tab():
    config_handler = ConfigsHandler()
    mapping_handler = ConfigsHandler(file_name="mapping.txt") 
    models_handler = ConfigsHandler(file_name="modelsmap.json")
    
    # Forwarder config fields
    ip_field = ft.TextField(label="IP Address", width=200, value="127.0.0.1")
    port_field = ft.TextField(label="Port", width=100, value="514")
    protocol_dropdown = ft.Dropdown(
        label="Protocol",
        width=100,
        value="TCP",
        options=[
            ft.dropdown.Option("TCP"),
            ft.dropdown.Option("UDP")
        ]
    )
    
    hierarchy_view = ft.ListView(spacing=10, expand=True)
    
    def load_configs(e=None):
        hierarchy_view.controls.clear()
        
        # Load data
        saved_paths = config_handler.get_saved_paths()
        template_mapping = mapping_handler.get_saved_paths()  
        model_mapping = models_handler.get_saved_paths()
        
        # Build hierarchy
        for path in saved_paths:
            templates = template_mapping.get(path, [])
            
            # Template items for this file
            template_items = []
            for template in templates:
                model_info = model_mapping.get(template, ["No model assigned"])
                model_name = model_info[0] if isinstance(model_info, list) else model_info
                
                # Color based on model assignment
                model_color = "green" if model_name != "No model assigned" else "red"
                
                if model_name != "No model assigned":
                    # Create buttons with state
                    enable_btn = ft.ElevatedButton("Enable", color="green", height=30)
                    start_btn = ft.ElevatedButton("Start", color="blue", height=30)
                    
                    def toggle_enable(e, btn=enable_btn):
                        if btn.text == "Enable":
                            btn.text = "Disable"
                            btn.color = "red"
                        else:
                            btn.text = "Enable"
                            btn.color = "green"
                        btn.update()
                    
                    def toggle_start(e, btn=start_btn):
                        if btn.text == "Start":
                            btn.text = "Stop"
                            btn.color = "orange"
                        else:
                            btn.text = "Start"
                            btn.color = "blue"
                        btn.update()
                    
                    enable_btn.on_click = toggle_enable
                    start_btn.on_click = toggle_start
                    
                    template_items.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text(f"📄 {template} "),
                                ft.Text(f"({model_name})", color=model_color),
                                enable_btn,
                                start_btn
                            ]),
                            padding=ft.padding.only(left=20, top=5, bottom=5)
                        )
                    )
                else:
                    # Template without model - no buttons
                    template_items.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text(f"📄 {template} "),
                                ft.Text(f"({model_name})", color=model_color)
                            ]),
                            padding=ft.padding.only(left=20, top=5, bottom=5)
                        )
                    )
            
            if not templates:
                template_items.append(
                    ft.Container(
                        content=ft.Text("  No templates assigned", color="orange"),
                        padding=ft.padding.only(left=20, top=5, bottom=5)
                    )
                )
            
            # File level container
            file_container = ft.Container(
                content=ft.Column([
                    ft.Text(f"📁 {os.path.basename(path)}", weight="bold"),
                    *template_items
                ]),
                padding=10,
                border=ft.border.all(1, "blue"),
                border_radius=5
            )
            
            hierarchy_view.controls.append(file_container)
        
        if hierarchy_view.page:
            hierarchy_view.update()
    
    # Initial load
    load_configs()
    
    return ft.Container(
        content=ft.Column([
            # Forwarder defaults section
            ft.Container(
                content=ft.Column([
                    ft.Text("Forwarder Default Configs", size=14, weight="bold"),
                    ft.Row([
                        ip_field,
                        port_field,
                        protocol_dropdown
                    ])
                ]),
                padding=10,
                border=ft.border.all(1, "grey"),
                border_radius=5,
                margin=ft.margin.only(bottom=20)
            ),
            
            # Available configs section
            ft.Row([
                ft.Text("Available Configs", size=16, weight="bold"),
                ft.IconButton(
                    icon="refresh",
                    tooltip="Reload configs",
                    on_click=load_configs
                )
            ]),
            ft.Container(
                content=hierarchy_view,
                height=400,
                expand=True
            )
        ]),
        padding=20
    )

"""