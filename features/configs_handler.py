import os

class ConfigsHandler:
    def __init__(self, conf_dir="../conf", file_name="saved_paths.txt"):
        self.conf_dir = conf_dir
        self.file_path = os.path.join(self.conf_dir, file_name)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        os.makedirs(self.conf_dir, exist_ok=True)
        if not os.path.isfile(self.file_path):
            with open(self.file_path, "w") as f:
                pass  # create empty file

    def get_saved_paths(self):
        with open(self.file_path, "r") as f:
            return [line.strip() for line in f if line.strip()]

    def save_path(self, path):
        # Prevent duplicates
        existing = self.get_saved_paths()
        if path not in existing:
            with open(self.file_path, "a") as f:
                f.write(path + "\n")

    def remove_path(self, path):
        existing = self.get_saved_paths()
        if path in existing:
            updated = [p for p in existing if p != path]
            with open(self.file_path, "w") as f:
                f.write("\n".join(updated) + "\n")