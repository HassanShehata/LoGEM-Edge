import os
import re
import yaml

class TemplateHandler:
    TEMPLATE_DIR = "../templates"

    def __init__(self, template_path=None):
        self.template = None
        self.template_path = template_path
        if template_path:
            self.template = self._load_template(template_path)

    def _load_template(self, path):
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def get_instruction(self):
        return self.template.get("instruction", "").strip() if self.template else ""

    def get_output_template(self):
        return self.template.get("output_template", "").strip() if self.template else ""

    def get_output_format(self):
        return self.template.get("output_format", "JSON").strip() if self.template else "JSON"

    def get_name(self):
        return self.template.get("name", "Unnamed") if self.template else "Unnamed"

    def get_type_regex(self):
        return self.template.get("type_regex", "") if self.template else ""

    def get_types(self):
        return self.template.get("types", []) if self.template else []

    def get_path(self):
        return self.template_path

    @classmethod
    def list_templates(cls):
        return [
            os.path.join(cls.TEMPLATE_DIR, f)
            for f in os.listdir(cls.TEMPLATE_DIR)
            if f.endswith(".yaml") or f.endswith(".yml")
        ]

    @classmethod
    def detect_template(cls, log_line):
        for path in cls.list_templates():
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                pattern = data.get("type_regex", "")
                accepted_types = data.get("types", [])

                if pattern:
                    match = re.search(pattern, log_line)
                    if match:
                        extracted_type = match.group(1)
                        if extracted_type in accepted_types:
                            return TemplateHandler(path)

        return None  # No match
