import os
import json

class ConfigsHandler:
    def __init__(self, conf_dir="../conf", file_name="saved_paths.txt"):
        self.conf_dir = conf_dir
        self.file_path = os.path.join(self.conf_dir, file_name)
        self.file_name = file_name
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        os.makedirs(self.conf_dir, exist_ok=True)
        if not os.path.isfile(self.file_path):
            with open(self.file_path, "w") as f:
                if self.file_name == "mapping.txt":
                    json.dump({}, f)
                else:
                    pass  # empty file for line-based

    def get_saved_paths(self):
        if self.file_name == "mapping.txt":
            with open(self.file_path, "r") as f:
                return json.load(f)
        with open(self.file_path, "r") as f:
            return [line.strip() for line in f if line.strip()]

    def save_path(self, path):
        if self.file_name == "mapping.txt":
            raise Exception("Use save_mapping() for mapping.txt")
        existing = self.get_saved_paths()
        if path not in existing:
            with open(self.file_path, "a") as f:
                f.write(path + "\n")

    def remove_path(self, path):
        if self.file_name == "mapping.txt":
            raise Exception("Use save_mapping() for mapping.txt")
        existing = self.get_saved_paths()
        if path in existing:
            updated = [p for p in existing if p != path]
            with open(self.file_path, "w") as f:
                f.write("\n".join(updated) + "\n")

    def save_mapping(self, mapping):
        if self.file_name != "mapping.txt":
            raise Exception("save_mapping is for mapping.txt only")
        with open(self.file_path, "w") as f:
            json.dump(mapping, f, indent=2)
