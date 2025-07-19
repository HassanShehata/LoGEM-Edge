import os
import yaml

class TemplateHandler:
    VALID_FORMATS = {"JSON", "SYSLOG", "CEF"}

    def __init__(self, templates_dir="../../templates"):
        self.templates_dir = os.path.abspath(templates_dir)

    def list_templates(self):
        return [f for f in os.listdir(self.templates_dir) if f.endswith(".yaml")]

    def load_template(self, name):
        path = os.path.join(self.templates_dir, f"{name}.yaml")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Template '{name}' not found.")
        with open(path, "r") as file:
            data = yaml.safe_load(file)
        self._validate_template(data)
        return data["instruction"], data["output_template"], data["output_format"]

    def _validate_template(self, data):
        required_keys = {"name", "instruction", "output_template", "output_format"}
        if not isinstance(data, dict) or not required_keys.issubset(data):
            raise ValueError(f"Invalid template: missing required keys: {required_keys - data.keys()}")
        if data["output_format"].upper() not in self.VALID_FORMATS:
            raise ValueError(f"Invalid output_format '{data['output_format']}'. Must be one of {self.VALID_FORMATS}")
