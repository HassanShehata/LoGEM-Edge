import flet as ft
import os
from configs_handler import ConfigsHandler

def output_config_tab():
    config_handler = ConfigsHandler()
    mapping_handler = ConfigsHandler(file_name="mapping.txt") 
    models_handler = ConfigsHandler(file_name="modelsmap.json")
    forwarder_handler = ConfigsHandler(file_name="forwarder_defaults.json")
    overrides_handler = ConfigsHandler(file_name="forwarder_overrides.json")
    states_handler = ConfigsHandler(file_name="button_states.json")
    counters_handler = ConfigsHandler(file_name="counters.json")

    # Load counters
    counters = counters_handler.get_saved_paths()
    if not counters:
        counters = {}
        counters_handler.save_mapping(counters)

    # Load forwarder defaults
    forwarder_defaults = forwarder_handler.get_saved_paths()
    if not forwarder_defaults:
        forwarder_defaults = {"ip": "127.0.0.1", "port": "514", "protocol": "TCP"}
        forwarder_handler.save_mapping(forwarder_defaults)
    
    # Forwarder config fields
    ip_field = ft.TextField(label="IP Address", width=200, value=forwarder_defaults["ip"])
    port_field = ft.TextField(label="Port", width=100, value=forwarder_defaults["port"])
    protocol_dropdown = ft.Dropdown(
        label="Protocol",
        width=100,
        value=forwarder_defaults["protocol"],
        options=[
            ft.dropdown.Option("TCP"),
            ft.dropdown.Option("UDP")
        ]
    )
    
    def save_forwarder_defaults(e=None):
        defaults = {
            "ip": ip_field.value,
            "port": port_field.value,
            "protocol": protocol_dropdown.value
        }
        forwarder_handler.save_mapping(defaults)
    
    ip_field.on_change = save_forwarder_defaults
    port_field.on_change = save_forwarder_defaults
    protocol_dropdown.on_change = save_forwarder_defaults
    
    hierarchy_view = ft.ListView(spacing=10, expand=True)
    
    def load_configs(e=None):
        hierarchy_view.controls.clear()
        
        # Load data
        saved_paths = config_handler.get_saved_paths()
        template_mapping = mapping_handler.get_saved_paths()  
        model_mapping = models_handler.get_saved_paths()
        overrides = overrides_handler.get_saved_paths()
        states = states_handler.get_saved_paths()
        
        # Build hierarchy
        for path in saved_paths:
            templates = template_mapping.get(path, [])
            path_key = os.path.basename(path)
            
            # Get override config for this file
            file_override = overrides.get(path_key, {
                "ip": ip_field.value,
                "port": port_field.value,
                "protocol": protocol_dropdown.value
            })
            
            # Create override config for this file
            file_ip = ft.TextField(label="IP Override", width=150, value=file_override["ip"])
            file_port = ft.TextField(label="Port Override", width=80, value=file_override["port"])
            file_protocol = ft.Dropdown(
                label="Protocol Override",
                width=120,
                value=file_override["protocol"],
                options=[
                    ft.dropdown.Option("TCP"),
                    ft.dropdown.Option("UDP")
                ]
            )
            
            def save_override(e, path_key=path_key, ip_field=file_ip, port_field=file_port, protocol_field=file_protocol):
                overrides = overrides_handler.get_saved_paths()
                overrides[path_key] = {
                    "ip": ip_field.value,
                    "port": port_field.value,
                    "protocol": protocol_field.value
                }
                overrides_handler.save_mapping(overrides)
            
            file_ip.on_change = save_override
            file_port.on_change = save_override
            file_protocol.on_change = save_override
    
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
                
                # Get button states
                state_key = f"{path_key}_{template}"
                template_state = states.get(state_key, {"enabled": False, "started": False})
                
                # Color based on model assignment
                model_color = "green" if model_name != "No model assigned" else "red"
                

                if model_name != "No model assigned":
                    # Create buttons with state
                    enable_text = "Disable" if template_state["enabled"] else "Enable"
                    enable_color = "red" if template_state["enabled"] else "green"
                    start_text = "Stop" if template_state["started"] else "Start"
                    start_color = "orange" if template_state["started"] else "blue"


                    enable_btn = ft.ElevatedButton(enable_text, color=enable_color, height=30)
                    start_btn = ft.ElevatedButton(start_text, color=start_color, height=30)
                    
                    def toggle_enable(e, btn=enable_btn, state_key=state_key):
                        states = states_handler.get_saved_paths()
                        current_state = states.get(state_key, {"enabled": False, "started": False})
                        current_state["enabled"] = not current_state["enabled"]
                        states[state_key] = current_state
                        states_handler.save_mapping(states)
                        
                        if btn.text == "Enable":
                            btn.text = "Disable"
                            btn.color = "red"
                        else:
                            btn.text = "Enable"
                            btn.color = "green"
                        btn.update()
                    
                    def toggle_start(e, btn=start_btn, state_key=state_key):
                        states = states_handler.get_saved_paths()
                        current_state = states.get(state_key, {"enabled": False, "started": False})
                        current_state["started"] = not current_state["started"]
                        states[state_key] = current_state
                        states_handler.save_mapping(states)
                        
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
                    passthrough_text = "Disable" if template_state["enabled"] else "Pass-through"
                    passthrough_color = "red" if template_state["enabled"] else "purple"
                    start_text = "Stop" if template_state["started"] else "Start"
                    start_color = "orange" if template_state["started"] else "blue"
                    
                    passthrough_btn = ft.ElevatedButton(passthrough_text, color=passthrough_color, height=30)
                    passthrough_start_btn = ft.ElevatedButton(start_text, color=start_color, height=30)
                    
                    def toggle_passthrough(e, btn=passthrough_btn, state_key=state_key):
                        states = states_handler.get_saved_paths()
                        current_state = states.get(state_key, {"enabled": False, "started": False})
                        current_state["enabled"] = not current_state["enabled"]
                        states[state_key] = current_state
                        states_handler.save_mapping(states)
                        
                        if btn.text == "Pass-through":
                            btn.text = "Disable"
                            btn.color = "red"
                        else:
                            btn.text = "Pass-through"
                            btn.color = "purple"
                        btn.update()
                    
                    def toggle_passthrough_start(e, btn=passthrough_start_btn, state_key=state_key):
                        states = states_handler.get_saved_paths()
                        current_state = states.get(state_key, {"enabled": False, "started": False})
                        current_state["started"] = not current_state["started"]
                        states[state_key] = current_state
                        states_handler.save_mapping(states)
                        
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
            
            # Get file-level counter
            file_count = counters.get(path_key, 0)

            # Create counter box for file header
            file_counter_box = ft.Container(
                content=ft.Text(f"Matches: {file_count}", color="yellow"),
                padding=5,
                border=ft.border.all(1, "yellow"),
                border_radius=3,
                width=100
            )

            # File level container
            file_container = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"📁 {os.path.basename(path)}", weight="bold", expand=True),
                        file_counter_box
                    ]),
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