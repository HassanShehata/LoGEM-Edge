import os
import platform
import glob

class LogFilesHandler:
    def __init__(self, base_dirs=None):
        self.system_type = self.detect_system_type()
        self.base_dirs = base_dirs or self.default_log_dirs()

    def detect_system_type(self):
        return platform.system().lower()

    def default_log_dirs(self):
        if self.system_type == "windows":
            return [
                r"C:\Windows\System32\winevt\Logs",  # EVTX
                r"C:\Windows\System32\config",       # Registry hives
            ]
        elif self.system_type == "linux":
            return ["/var/log"]
        elif self.system_type == "darwin":
            return ["/var/log"]
        else:
            return []

    def list_log_sources(self):
        sources = []
        for base_dir in self.base_dirs:
            if os.path.exists(base_dir):
                for path in glob.glob(os.path.join(base_dir, "*")):
                    sources.append(path)
        return sources
