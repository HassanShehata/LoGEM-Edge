# services_handler.py
import threading
import os
import time
from configs_handler import ConfigsHandler

class ServicesHandler:
    def __init__(self):
        self._lock = threading.Lock()
        self.active_services = {}  # key -> {"thread": Thread, "stop_flag": Event}
        self.states_handler = ConfigsHandler(file_name="button_states.json")

    def _key(self, file_path, template) -> str:
        return f"{os.path.basename(file_path)}_{template}"

    def create_service(self, file_path, template):
        # logical registration only; UI already persists states
        service_key = self._key(file_path, template)
        print(f"[create] {service_key}")
        return True

    def delete_service(self, file_path, template):
        service_key = self._key(file_path, template)
        with self._lock:
            if service_key in self.active_services:
                # ensure stopped before delete
                self._stop_locked(service_key)
        print(f"[delete] {service_key}")
        return True

    def start_service(self, file_path, template):
        service_key = self._key(file_path, template)
        with self._lock:
            if service_key in self.active_services:
                print(f"[start] already running: {service_key}")
                return True
            stop_flag = threading.Event()
            t = threading.Thread(
                target=self._monitor_loop,
                args=(file_path, template, stop_flag),
                name=f"Monitor-{service_key}",
                daemon=True,
            )
            self.active_services[service_key] = {"thread": t, "stop_flag": stop_flag}
            t.start()
        print(f"[start] {service_key}")
        return True

    def stop_service(self, file_path, template):
        service_key = self._key(file_path, template)
        with self._lock:
            if service_key not in self.active_services:
                print(f"[stop] not running: {service_key}")
                return True
            self._stop_locked(service_key)
        print(f"[stop] {service_key}")
        return True

    def _stop_locked(self, service_key: str):
        entry = self.active_services.get(service_key)
        if not entry:
            return
        entry["stop_flag"].set()
        # join outside long loops; small timeout to avoid UI hang
        thr = entry["thread"]
        thr.join(timeout=5)
        # cleanup
        self.active_services.pop(service_key, None)

    def stop_all(self):
        with self._lock:
            keys = list(self.active_services.keys())
        for k in keys:
            with self._lock:
                self._stop_locked(k)
        print("[stop_all] all services stopped")

    # --- monitoring stub (will implement real logic later) ---
    def _monitor_loop(self, file_path, template, stop_flag: threading.Event):
        # minimal cooperative loop for start/stop testing
        while not stop_flag.is_set():
            time.sleep(0.2)
        # allow graceful exit
        return

# Global instance
services_handler = ServicesHandler()
