import threading
import os
import socket
import time
from configs_handler import ConfigsHandler
from template_handler import TemplateHandler
from llm_handler import LLMHandler
import Evtx.Evtx as evtx

class ServicesHandler:
    def __init__(self):
        self.active_services = {}  # {service_key: {'thread': thread, 'stop_flag': Event}}
        self.load_config_handlers()
    
    def load_config_handlers(self):
        self.overrides_handler = ConfigsHandler(file_name="forwarder_overrides.json") 
        self.forwarder_handler = ConfigsHandler(file_name="forwarder_defaults.json")
        self.counters_handler = ConfigsHandler(file_name="counters.json")
        self.models_handler = ConfigsHandler(file_name="modelsmap.json")
        self.states_handler = ConfigsHandler(file_name="button_states.json")
    
    def create_service(self, file_path, template):
        """Create service when user clicks Enable"""
        service_key = f"{os.path.basename(file_path)}_{template}"
        print(f"Service created: {service_key}")
        return True
    
    def delete_service(self, file_path, template):
        """Delete service when user clicks Disable"""
        service_key = f"{os.path.basename(file_path)}_{template}"
        self.stop_service(file_path, template)  # Stop first
        if service_key in self.active_services:
            del self.active_services[service_key]
        print(f"Service deleted: {service_key}")
        return True
    
    def start_service(self, file_path, template):
        """Start service when user clicks Start"""
        service_key = f"{os.path.basename(file_path)}_{template}"
        
        if service_key in self.active_services and self.active_services[service_key]['thread'].is_alive():
            return True  # Already running
        
        # Create stop flag and thread
        stop_flag = threading.Event()
        service_thread = threading.Thread(
            target=self._run_service,
            args=(file_path, template, stop_flag),
            daemon=True
        )
        service_thread.start()
        
        self.active_services[service_key] = {
            'thread': service_thread,
            'stop_flag': stop_flag
        }
        print(f"Service started: {service_key}")
        return True
    
    def stop_service(self, file_path, template):
        """Stop service when user clicks Stop"""
        service_key = f"{os.path.basename(file_path)}_{template}"
        
        if service_key in self.active_services:
            self.active_services[service_key]['stop_flag'].set()
            self.active_services[service_key]['thread'].join(timeout=3)
            print(f"Service stopped: {service_key}")
        return True
    
    def _run_service(self, file_path, template, stop_flag):
        """Main service logic"""
        service_key = f"{os.path.basename(file_path)}_{template}"
        
        # Load configurations
        overrides = self.overrides_handler.get_saved_paths()
        defaults = self.forwarder_handler.get_saved_paths()
        model_mapping = self.models_handler.get_saved_paths()
        states = self.states_handler.get_saved_paths()
        
        # Get forwarding config
        file_key = os.path.basename(file_path)
        config = overrides.get(file_key, defaults)
        
        # Get model info
        model_info = model_mapping.get(template, ["No model assigned"])
        model_name = model_info[0] if isinstance(model_info, list) else model_info
        
        # Check if this is pass-through mode based on button states
        template_state = states.get(service_key, {"enabled": False, "started": False})
        is_passthrough_mode = (model_name == "No model assigned")
        
        # Initialize LLM only if NOT pass-through
        llm = None
        template_handler = None
        if not is_passthrough_mode:
            try:
                template_path = os.path.join("..", "templates", template)
                template_handler = TemplateHandler(template_path)
                llm = LLMHandler(model_name=model_name, n_ctx=2048)
                print(f"LLM initialized for {service_key} with model {model_name}")
            except Exception as e:
                print(f"LLM initialization error: {e}")
                return
        else:
            print(f"Pass-through mode for {service_key}")
        
        # Process logs with mode info
        try:
            if file_path.lower().endswith('.evtx'):
                self._process_evtx(file_path, template_handler, llm, config, service_key, stop_flag, is_passthrough_mode)
            else:
                self._process_text_file(file_path, template_handler, llm, config, service_key, stop_flag, is_passthrough_mode)
        except Exception as e:
            print(f"Service {service_key} error: {e}")


    def _process_initial_records(self, file_path, template_handler, llm, config, service_key, stop_flag, is_passthrough_mode, count):
        """Process last N records on initial startup for EVTX files"""
        try:
            with evtx.Evtx(file_path) as log:
                records = list(log.records())
                
                # Process last N records
                for record in records[-count:]:
                    if stop_flag.is_set():
                        return
                    
                    xml_content = record.xml()
                    record_id = self._extract_record_id(xml_content)
                    
                    # Process the record
                    self._process_and_forward(xml_content, template_handler, llm, config, is_passthrough_mode)
                    self._increment_counter(service_key)
                    
                    # Update position tracking
                    position_handler = ConfigsHandler(file_name="file_positions.json")
                    positions = position_handler.get_saved_paths()
                    file_key = os.path.basename(file_path)
                    positions[file_key] = {"last_record_id": record_id, "last_timestamp": ""}
                    position_handler.save_mapping(positions)
                    
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"Initial EVTX processing error: {e}")


    def _process_evtx(self, file_path, template_handler, llm, config, service_key, stop_flag, is_passthrough_mode):
        """Use Windows Event Log API for efficient real-time monitoring"""
        import win32evtlog
        import win32evtlogutil
        
        # Extract log name from path (Security.evtx -> Security)  
        log_name = os.path.splitext(os.path.basename(file_path))[0]
        
        position_handler = ConfigsHandler(file_name="file_positions.json")
        positions = position_handler.get_saved_paths()
        file_key = os.path.basename(file_path)
        last_position = positions.get(file_key, {"last_record_id": 0})
        
        print(f"DEBUG: Monitoring {log_name} from record ID: {last_position['last_record_id']}")
        
        while not stop_flag.is_set():
            try:
                # Open event log
                handle = win32evtlog.OpenEventLog(None, log_name)
                
                # Read newest events first
                events = win32evtlog.ReadEventLog(
                    handle, 
                    win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ,
                    0
                )
                
                new_events = []
                for event in events[:500]:  # Only check newest 500
                    if event.RecordNumber > last_position["last_record_id"]:
                        new_events.append(event)
                    else:
                        break  # Stop when we hit old records
                
                win32evtlog.CloseEventLog(handle)
                
                # Process new events (reverse to process oldest first)
                for event in reversed(new_events):
                    if stop_flag.is_set():
                        return
                        
                    # Convert to XML format like your existing code expects
                    xml_content = self._event_to_xml(event)
                    self._process_and_forward(xml_content, template_handler, llm, config, is_passthrough_mode)
                    self._increment_counter(service_key)
                    
                    last_position["last_record_id"] = event.RecordNumber
                    positions[file_key] = last_position
                    position_handler.save_mapping(positions)
                
                if new_events:
                    print(f"Processed {len(new_events)} new events")
                
            except Exception as e:
                print(f"Event monitoring error: {e}")
            
            time.sleep(5)


    def _event_to_xml(self, event):
        """Convert Windows Event object to XML format"""
        import xml.etree.ElementTree as ET
        
        # Create basic XML structure similar to EVTX format
        root = ET.Element("Event", xmlns="http://schemas.microsoft.com/win/2004/08/events/event")
        
        # System section
        system = ET.SubElement(root, "System")
        ET.SubElement(system, "EventID").text = str(event.EventID)
        ET.SubElement(system, "EventRecordID").text = str(event.RecordNumber)
        ET.SubElement(system, "Computer").text = event.ComputerName
        ET.SubElement(system, "TimeCreated").text = str(event.TimeGenerated)
        
        # Convert to XML string
        return ET.tostring(root, encoding='unicode')

    
    def _extract_record_id(self, xml_content):
        """Extract EventRecordID from XML"""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            for elem in root.iter():
                if elem.tag.endswith('EventRecordID'):
                    return int(elem.text)
            return 0
        except:
            return 0
    
    def _process_text_file(self, file_path, template_handler, llm, config, service_key, stop_flag, is_passthrough_mode):
        """Process text file with robust position tracking"""
        position_handler = ConfigsHandler(file_name="file_positions.json")
        positions = position_handler.get_saved_paths()
        
        file_key = os.path.basename(file_path)
        last_position = positions.get(file_key, {"byte_offset": 0, "file_size": 0})
        
        # Handle first run or file rotation
        try:
            current_size = os.path.getsize(file_path)
            
            # If file is smaller than last position, file was rotated/truncated
            if current_size < last_position["byte_offset"]:
                print(f"File rotation detected for {file_key}")
                last_position = {"byte_offset": 0, "file_size": current_size}
            
            # If first run, set position to end of file to avoid processing entire backlog
            if last_position["byte_offset"] == 0 and current_size > 0:
                print(f"Setting initial position to end of file: {current_size}")
                last_position["byte_offset"] = current_size
                last_position["file_size"] = current_size
                positions[file_key] = last_position
                position_handler.save_mapping(positions)
            
        except Exception as e:
            print(f"File size check error: {e}")
        
        # Monitor for new lines
        while not stop_flag.is_set():
            try:
                with open(file_path, "r", errors="ignore") as f:
                    # Seek to last known position
                    f.seek(last_position["byte_offset"])
                    
                    new_lines = []
                    for line in f:
                        if line.strip():
                            new_lines.append(line.strip())
                    
                    # Process new lines
                    for line in new_lines:
                        if stop_flag.is_set():
                            return
                        
                        self._process_and_forward(line, template_handler, llm, config, is_passthrough_mode)
                        self._increment_counter(service_key)
                        time.sleep(0.1)
                    
                    # Update position
                    current_position = f.tell()
                    current_size = os.path.getsize(file_path)
                    
                    if current_position > last_position["byte_offset"]:
                        last_position["byte_offset"] = current_position
                        last_position["file_size"] = current_size
                        positions[file_key] = last_position
                        position_handler.save_mapping(positions)
                    
                    if new_lines:
                        print(f"Processed {len(new_lines)} new lines")
                    
            except Exception as e:
                print(f"Text file monitoring error: {e}")
            
            time.sleep(5)
    
    def _process_initial_text_lines(self, file_path, template_handler, llm, config, service_key, stop_flag, is_passthrough_mode, count):
        """Process last N lines on initial startup"""
        try:
            with open(file_path, "r", errors="ignore") as f:
                lines = f.readlines()
                for line in lines[-count:]:
                    if stop_flag.is_set():
                        return
                    if line.strip():
                        self._process_and_forward(line.strip(), template_handler, llm, config, is_passthrough_mode)
                        self._increment_counter(service_key)
                        time.sleep(0.1)
        except Exception as e:
            print(f"Initial text processing error: {e}")
    
    def _process_and_forward(self, content, template_handler, llm, config, is_passthrough_mode):
        """Process content and forward"""
        try:
            if is_passthrough_mode:
                print("Pass-through mode - forwarding raw content")
                processed_content = content
            elif llm and template_handler:
                print("LLM mode - checking template match...")
                
                # Use exact same logic as test tab
                if not template_handler.matches_log(content):
                    print("Template didn't match - skipping log")
                    return
                
                print("Template matched - processing with LLM")
                
                prompt = template_handler.get_prompt()
                model_template = template_handler.get_model_template()
                model_params = template_handler.get_model_params()
                output_format = template_handler.get_output_format()
                
                constructed_prompt = f"{prompt}\nRAW_LOG: {content}"
                full_prompt = model_template.replace("{{ .Prompt }}", constructed_prompt)
                
                # Use same inference call as test tab
                response, latency = llm.infer(
                    full_prompt,
                    model_params=model_params,
                    max_tokens=model_params.get("max_tokens", 2048)
                )
                
                # Convert to SYSLOG format if needed - exact same as test tab
                if output_format.upper() == "SYSLOG":
                    processed_content = template_handler.json_to_syslog(response)
                else:
                    processed_content = response
                
                print(f"LLM processing completed in {latency}s")
            else:
                print("ERROR: No LLM configured but not in pass-through mode")
                return
            
            # Forward to destination
            print(f"Forwarding {len(processed_content)} chars to {config['ip']}:{config['port']}")
            self._forward_log(processed_content, config)
            
        except Exception as e:
            print(f"Processing error: {e}")
            return

    def _forward_log(self, content, config):
        """Send to destination"""
        try:
            if config["protocol"] == "TCP":
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((config["ip"], int(config["port"])))
                sock.send(content.encode() + b'\n')
                sock.close()
            else:  # UDP
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(content.encode() + b'\n', (config["ip"], int(config["port"])))
                sock.close()
            print(f"Successfully forwarded to {config['ip']}:{config['port']} via {config['protocol']}")
        except Exception as e:
            print(f"Forwarding error: {e}")
    
    def _increment_counter(self, service_key):
        """Update counter"""
        try:
            counters = self.counters_handler.get_saved_paths()
            file_key = service_key.split('_')[0]
            counters[file_key] = counters.get(file_key, 0) + 1
            self.counters_handler.save_mapping(counters)
        except Exception as e:
            print(f"Counter update error: {e}")

# Global instance
services_handler = ServicesHandler()