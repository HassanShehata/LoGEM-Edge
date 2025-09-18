import threading
import os
import time
from configs_handler import ConfigsHandler

class ServicesHandler:
    def __init__(self):
        self.active_services = {}
        self.load_config_handlers()
    
    def load_config_handlers(self):
        self.states_handler = ConfigsHandler(file_name="button_states.json")
    
    def create_service(self, file_path, template):
        """Create service when user clicks Enable - just mark it as created"""
        service_key = f"{os.path.basename(file_path)}_{template}"
        print(f"Service created: {service_key}")
        return True
    
    def delete_service(self, file_path, template):
        """Delete service when user clicks Disable"""
        service_key = f"{os.path.basename(file_path)}_{template}"
        
        # Stop if running
        if service_key in self.active_services:
            self.stop_service(file_path, template)
            del self.active_services[service_key]
        
        print(f"Service deleted: {service_key}")
        return True
    
    def start_service(self, file_path, template):
        """Start service when user clicks Start"""
        service_key = f"{os.path.basename(file_path)}_{template}"
        
        # Don't start if already running
        if service_key in self.active_services:
            print(f"Service {service_key} already running")
            return True
        
        # Create a stop flag for this service
        stop_flag = threading.Event()
        
        # Create background thread
        monitor_thread = threading.Thread(
            target=self._monitor_file,
            args=(file_path, template, stop_flag),
            daemon=True,
            name=f"Monitor-{service_key}"
        )
        
        # Start the thread
        monitor_thread.start()
        
        # Store it so we can stop it later
        self.active_services[service_key] = {
            'thread': monitor_thread,
            'stop_flag': stop_flag
        }
        
        print(f"Service started: {service_key}")
        return True
    
    def stop_service(self, file_path, template):
        """Stop service when user clicks Stop"""
        service_key = f"{os.path.basename(file_path)}_{template}"
        
        if service_key in self.active_services:
            # Signal the thread to stop
            self.active_services[service_key]['stop_flag'].set()
            # Wait for thread to finish
            self.active_services[service_key]['thread'].join(timeout=5)
            print(f"Service stopped: {service_key}")
        else:
            print(f"Service {service_key} was not running")
        
        return True
    
    def _monitor_file(self, file_path, template, stop_flag):
        """Background thread that monitors the file for new content"""
        service_key = f"{os.path.basename(file_path)}_{template}"
        print(f"Monitoring thread started for {service_key}")
        
        # Load position tracker
        position_handler = ConfigsHandler(file_name="file_positions.json")
        positions = position_handler.get_saved_paths()
        file_key = os.path.basename(file_path)
        
        # Set initial position to end of file (skip old logs)
        if file_key not in positions:
            if file_path.lower().endswith('.evtx'):
                # For EVTX, get the latest record ID
                try:
                    import Evtx.Evtx as evtx
                    with evtx.Evtx(file_path) as log:
                        records = list(log.records())
                        if records:
                            latest_record = records[-1]
                            latest_id = self._extract_record_id(latest_record.xml())
                            positions[file_key] = {"last_record_id": latest_id}
                        else:
                            positions[file_key] = {"last_record_id": 0}
                except:
                    positions[file_key] = {"last_record_id": 0}
            else:
                # For text files, set to end of file
                try:
                    file_size = os.path.getsize(file_path)
                    positions[file_key] = {"byte_offset": file_size}
                except:
                    positions[file_key] = {"byte_offset": 0}
            
            position_handler.save_mapping(positions)
            print(f"Set initial position for {service_key}")
        
        # Monitor loop
        while not stop_flag.is_set():
            try:
                if file_path.lower().endswith('.evtx'):
                    self._check_evtx_file(file_path, service_key, position_handler)
                else:
                    self._check_text_file(file_path, service_key, position_handler)
            except Exception as e:
                print(f"Monitor error for {service_key}: {e}")
            
            time.sleep(2)  # Check every 2 seconds
        
        print(f"Monitoring thread stopped for {service_key}")
    
    def _extract_record_id(self, xml_content):
        """Extract EventRecordID from EVTX XML"""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            for elem in root.iter():
                if elem.tag.endswith('EventRecordID'):
                    return int(elem.text)
            return 0
        except:
            return 0
    
    def _check_evtx_file(self, file_path, service_key, position_handler):
        """Check EVTX file for new records"""
        # TODO: Implement EVTX checking
        pass
    
    def _check_text_file(self, file_path, service_key, position_handler):
        """Check text file for new lines"""
        # TODO: Implement text file checking  
        pass

# Global instance
services_handler = ServicesHandler()