# services_handler.py
import threading
import os
import time
from typing import Dict, Tuple, Optional, List
from configs_handler import ConfigsHandler

class ServicesHandler:
    def __init__(self):
        self._lock = threading.Lock()
        self.active_services: Dict[str, Dict[str, object]] = {}
        self.states_handler = ConfigsHandler(file_name="button_states.json")
        self.paths_handler = ConfigsHandler()  # ../conf/saved_paths.txt
        self.positions_handler = ConfigsHandler(file_name="positions.json")


    def _key(self, file_path: str, template: str) -> str:
        return f"{os.path.basename(file_path)}_{template}"

    def _split_key(self, key: str) -> Tuple[str, str]:
        # returns (basename, template)
        parts = key.split("_", 1)
        return (parts[0], parts[1] if len(parts) > 1 else "")

    def _find_full_path(self, basename: str) -> Optional[str]:
        candidates: List[str] = self.paths_handler.get_saved_paths()
        for p in candidates:
            if os.path.basename(p) == basename:
                return p
        return None

    # ---------- CRUD from UI ----------
    def create_service(self, file_path: str, template: str) -> bool:
        print(f"[create] {self._key(file_path, template)}")
        return True

    def delete_service(self, file_path: str, template: str) -> bool:
        key = self._key(file_path, template)
        with self._lock:
            if key in self.active_services:
                self._stop_locked(key)
        print(f"[delete] {key}")
        return True

    def start_service(self, file_path: str, template: str) -> bool:
        key = self._key(file_path, template)
        with self._lock:
            if key in self.active_services:
                print(f"[start] already running: {key}")
                return True
            stop_flag = threading.Event()
            t = threading.Thread(
                target=self._monitor_loop,
                args=(file_path, template, stop_flag),
                name=f"Monitor-{key}",
                daemon=True,
            )
            self.active_services[key] = {"thread": t, "stop_flag": stop_flag}
            t.start()
        print(f"[start] {key}")
        return True

    def stop_service(self, file_path: str, template: str) -> bool:
        key = self._key(file_path, template)
        with self._lock:
            if key not in self.active_services:
                print(f"[stop] not running: {key}")
                return True
            self._stop_locked(key)
        print(f"[stop] {key}")
        return True

    def _stop_locked(self, key: str) -> None:
        entry = self.active_services.get(key)
        if not entry:
            return
        entry["stop_flag"].set()
        entry["thread"].join(timeout=5)
        self.active_services.pop(key, None)

    def stop_all(self) -> None:
        with self._lock:
            keys = list(self.active_services.keys())
        for k in keys:
            with self._lock:
                self._stop_locked(k)
        print("[stop_all] all services stopped")

    # ---------- Auto-restore on app start ----------
    def autostart_from_states(self) -> None:
        """
        Read ../conf/button_states.json and start services for entries
        with {"enabled": true, "started": true}.
        """
        try:
            states: Dict[str, Dict[str, bool]] = self.states_handler.get_saved_paths()
        except Exception as ex:
            print(f"[autostart] failed to read states: {ex}")
            return

        for key, st in (states or {}).items():
            if not isinstance(st, dict):
                continue
            if not (st.get("enabled") and st.get("started")):
                continue

            basename, template = self._split_key(key)
            full_path = self._find_full_path(basename)
            if not full_path:
                print(f"[autostart] path not found for {basename}, skip")
                continue
            self.start_service(full_path, template)

    def _monitor_loop(self, file_path: str, template: str, stop_flag: threading.Event):
        key = self._key(file_path, template)
        if not file_path.lower().endswith(".evtx"):
            while not stop_flag.wait(0.5): pass
            return
    
        from Evtx.Evtx import Evtx
        from xml.etree import ElementTree as ET
        from datetime import datetime
    
        def parse_iso(s):
            try:
                return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None
            except Exception:
                return None
    
        pos = self.positions_handler.get_saved_paths() or {}
        state = pos.get(key) or {}
        last_id = int(state.get("last_id", 0))
        last_ts = state.get("last_ts")
        last_dt = parse_iso(last_ts)
    
        # 1) init once: use latest-by-timestamp
        if last_ts is None:
            try:
                with Evtx(file_path) as log:
                    rec = max(log.records(), key=lambda r: r.timestamp())  # latest
                    root = ET.fromstring(rec.xml())
                    ns = {"e": "http://schemas.microsoft.com/win/2004/08/events/event"}
                    last_id = int(root.findtext("./e:System/e:EventRecordID", namespaces=ns) or 0)
                    tc = root.find("./e:System/e:TimeCreated", namespaces=ns)
                    last_ts = tc.get("SystemTime") if tc is not None else None
                    last_dt = parse_iso(last_ts)
                pos[key] = {"last_id": last_id, "last_ts": last_ts}
                self.positions_handler.save_mapping(pos)
                print(f"[evtx][{key}] init last_id={last_id} last_ts={last_ts}")
            except ValueError:
                # empty log
                pos[key] = {"last_id": 0, "last_ts": None}
                self.positions_handler.save_mapping(pos)
    
        # 2) tail: emit events after (ts,id)
        while not stop_flag.is_set():
            new_id, new_ts, new_dt = last_id, last_ts, last_dt
            try:
                with Evtx(file_path) as log:
                    for rec in log.records():
                        xml_str = rec.xml()
                        root = ET.fromstring(xml_str)
                        ns = {"e": "http://schemas.microsoft.com/win/2004/08/events/event"}
                        rid = int(root.findtext("./e:System/e:EventRecordID", namespaces=ns) or 0)
                        tcel = root.find("./e:System/e:TimeCreated", namespaces=ns)
                        ts = tcel.get("SystemTime") if tcel is not None else None
                        dt = parse_iso(ts)
    
                        if (last_dt is None) or (dt and (dt > last_dt or (dt == last_dt and rid > last_id))):
                            print(f"[evtx][{key}] NEW id={rid} ts={ts}")
                            print(xml_str)  # << debug: print full XML of new event
                            new_id, new_ts, new_dt = rid, ts, dt
            except Exception as e:
                print(f"[evtx][{key}] error: {e}")
    
            if new_id != last_id or new_ts != last_ts:
                last_id, last_ts, last_dt = new_id, new_ts, new_dt
                pos[key] = {"last_id": last_id, "last_ts": last_ts}
                self.positions_handler.save_mapping(pos)
    
            if stop_flag.wait(0.5): break




# Global instance
services_handler = ServicesHandler()

#last_10 = [record.xml() for record in sorted(log.records(), key=lambda r: r.timestamp())[-10:]]