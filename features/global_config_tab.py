import flet as ft
from configs_handler import ConfigsHandler

def global_config_tab():
    global_config_handler = ConfigsHandler(file_name="global_config.json")
    
    # Load existing config or set defaults
    config = global_config_handler.get_saved_paths()
    if not config:
        config = {
            "llm_timeout": 60,
            "max_log_size": 100,
            "tail_limit": 10,
            "file_access_rate": 1,
            "gpu_acceleration": False,
            "gpu_offload_ratio": 1.0,
            "dynamic_ctx": True
        }
        global_config_handler.save_mapping(config)
    
    def save_config():
        global_config_handler.save_mapping(config)
    
    # LLM Timeout field
    timeout_field = ft.TextField(
        label="LLM Response Timeout (seconds)",
        width=200,
        value=str(config["llm_timeout"]),
        on_change=lambda e: (config.update({"llm_timeout": int(e.control.value) if e.control.value.isdigit() else 60}), save_config())
    )

    # Max Log Size field
    log_size_field = ft.TextField(
        label="Max Log Size (characters)",
        width=200,
        value=str(config["max_log_size"]),
        on_change=lambda e: (config.update({"max_log_size": int(e.control.value) if e.control.value.isdigit() else 100}), save_config())
    )
    
    # Tail Limit field
    tail_limit_field = ft.TextField(
        label="Last N Logs to Match",
        width=200,
        value=str(config["tail_limit"]),
        on_change=lambda e: (config.update({"tail_limit": int(e.control.value) if e.control.value.isdigit() else 10}), save_config())
    )
    
    # File Access Rate field
    access_rate_field = ft.TextField(
        label="Log File Access Rate (seconds)",
        width=200,
        value=str(config["file_access_rate"]),
        on_change=lambda e: (config.update({"file_access_rate": int(e.control.value) if e.control.value.isdigit() else 1}), save_config())
    )

    # GPU Acceleration checkbox
    gpu_checkbox = ft.Checkbox(
        label="Enable GPU Acceleration (NVIDIA only)",
        value=config["gpu_acceleration"],
        on_change=lambda e: (config.update({"gpu_acceleration": e.control.value}), save_config())
    )
    
    # GPU Offload Ratio slider
    #gpu_ratio_text = ft.Text(f"{int(config['gpu_offload_ratio'] * 100)}%", size=14)
    
    gpu_ratio_container = ft.Container(
        content=ft.Text(f"{int(config['gpu_offload_ratio'] * 100)}%", size=14),
        width=50
    )

    def update_gpu_ratio(e):
        config["gpu_offload_ratio"] = e.control.value / 100
        gpu_ratio_container.content.value = f"{int(e.control.value)}%"
        gpu_ratio_container.update()
        save_config()
    
    gpu_ratio_slider = ft.Slider(
        min=0,
        max=100,
        divisions=10,
        value=config["gpu_offload_ratio"] * 100,
        width=300,
        on_change=update_gpu_ratio
    )
    
    return ft.Container(
        content=ft.Column([
            ft.Text("Global Configuration", size=16, weight="bold"),
            ft.Divider(),
            
            # Performance Settings
            ft.Container(
                content=ft.Column([
                    ft.Text("Performance Settings", size=14, weight="bold"),
                    ft.Container(height=10),  # Add spacing
                    ft.Row([timeout_field, log_size_field]),
                    ft.Row([tail_limit_field, access_rate_field])
                ]),
                padding=10,
                border=ft.border.all(1, "grey"),
                border_radius=10,
                margin=ft.margin.only(bottom=20)
            ),
            
            # GPU Settings
            ft.Container(
                content=ft.Column([
                    ft.Text("GPU Configuration", size=14, weight="bold"),
                    ft.Container(height=10),
                    gpu_checkbox,
                    ft.Row([
                        ft.Text("GPU Offload Ratio:", size=12),
                        gpu_ratio_container
                    ]),
                    gpu_ratio_slider
                ]),
                padding=10,
                border=ft.border.all(1, "grey"),
                border_radius=10
            )
        ]),
        padding=20
    )