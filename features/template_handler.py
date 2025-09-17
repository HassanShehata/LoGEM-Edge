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

    def get_prompt(self):
        return self.template.get("prompt", "").strip() if self.template else ""
    
    def get_model_params(self):
        return self.template.get("model_params", {}) if self.template else {}
    
    def get_model_template(self):
        return self.template.get("model_template", "").strip() if self.template else ""

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


    def json_to_syslog(self, json_response):
        """Convert JSON response to RFC3164 syslog format"""
        import json
        from datetime import datetime
        import socket
        
        try:
            # Parse JSON response
            data = json.loads(json_response)
            
            # Current timestamp in RFC3164 format
            timestamp = datetime.now().strftime("%b %d %H:%M:%S")
            
            # Get hostname
            hostname = socket.gethostname()
            
            # Facility 16 (local0), Severity 6 (info) = Priority 134
            priority = "<134>"
            
            # Create TAG from EventID if available
            tag = f"EventID{data.get('EventID', 'Unknown')}"
            
            # Flatten JSON to key=value pairs
            content_parts = []
            for key, value in data.items():
                if value:  # Skip empty values
                    content_parts.append(f"{key}={value}")
            
            content = " ".join(content_parts)
            
            # RFC3164 format: <PRI>TIMESTAMP HOSTNAME TAG: CONTENT
            syslog_message = f"{priority}{timestamp} {hostname} {tag}: {content}"
            
            return syslog_message
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return original response
            return json_response

 
    def matches_log(self, log_line):
        """Check if log matches template's type criteria"""
        type_regex = self.get_type_regex()
        types_list = self.get_types()
        
        # If no regex or types defined, accept any log
        if not type_regex and not types_list:
            return True
            
        # If no regex defined but types exist, skip matching
        if not type_regex:
            return False
            
        # Try to extract type from log using regex
        match = re.search(type_regex, log_line)
        if not match:
            return False
            
        # Get the extracted type (first capture group)
        extracted_type = match.group(1)
        
        # Check if extracted type is in accepted types list
        return extracted_type in types_list
    
    def get_match_info(self, log_line):
        """Get detailed match information for debugging"""
        type_regex = self.get_type_regex()
        types_list = self.get_types()
        
        info = {
            'has_regex': bool(type_regex),
            'has_types': bool(types_list),
            'extracted_type': None,
            'matches': False
        }
        
        if type_regex:
            match = re.search(type_regex, log_line)
            if match:
                info['extracted_type'] = match.group(1)
                info['matches'] = info['extracted_type'] in types_list if types_list else False
        
        return info


    @classmethod
    def detect_template(cls, log_line, preferred_order=None):
        if preferred_order is None:
            preferred_order = ["JSON"]  # default fallback
    
        matched_templates = []
    
        for path in cls.list_templates():
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                pattern = data.get("type_regex", "")
                accepted_types = data.get("types", [])
                output_format = data.get("output_format", "JSON").upper()
    
                if pattern:
                    match = re.search(pattern, log_line)
                    if match:
                        extracted_type = match.group(1)
                        if extracted_type in accepted_types:
                            matched_templates.append((output_format, path))
    
        if matched_templates:
            matched_templates.sort(
                key=lambda t: preferred_order.index(t[0]) if t[0] in preferred_order else len(preferred_order)
            )
            return TemplateHandler(matched_templates[0][1])
    
        return None

