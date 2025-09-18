import time
import threading
import os
import json
from configs_handler import ConfigsHandler
from template_handler import TemplateHandler
from llm_handler import LLMHandler
import socket
import Evtx.Evtx as evtx

class LogServiceManager:
    def __init__(self):
        self.running = True
        self.services = {}  # {service_key: {'thread': thread, 'stop_flag': threading.Event()}}
        self.load_config_handlers()
        
    def load_config_handlers(self):
        self.states_handler = ConfigsHandler(file_name="button_states.json")
        self.overrides_handler = ConfigsHandler(file_name="forwarder_overrides.json") 
        self.forwarder_handler = ConfigsHandler(file_name="forwarder_defaults.json")
        self.counters_handler = ConfigsHandler(file_name="counters.json")
        self.mapping_handler = ConfigsHandler(file_name="mapping.txt")
        self.models_handler = ConfigsHandler(file_name="modelsmap.json")
        self.config_handler = ConfigsHandler()
        
    def create_forwarding_service(self, file_path, template):
        """Creates a forwarding service but doesn't start it"""
        service_key = f"{os.path.basename(file_path)}_{template}"
        print(f"Creating service: {service_key}")
        
    def delete_forwarding_service(self, file_path, template):
        """Stops and deletes a forwarding service"""
        service_key = f"{os.path.basename(file_path)}_{template}"
        self.stop_forwarding_service(file_path, template)
        if service_key in self.services:
            del self.services[service_key]
        print(f"Deleted service: {service_key}")
        
    def start_forwarding_service(self, file_path, template):
        """Starts a forwarding service"""
        service_key = f"{os.path.basename(file_path)}_{template}"
        
        if service_key in self.services and self.services[service_key]['thread'].is_alive():
            return
            
        # Create stop flag for clean shutdown
        stop_flag = threading.Event()
        
        service_thread = threading.Thread(
            target=self._run_forwarding_service,
            args=(file_path, template, stop_flag),
            daemon=True
        )
        service_thread.start()
        
        self.services[service_key] = {
            'thread': service_thread,
            'stop_flag': stop_flag
        }
        print(f"Started service: {service_key}")
        
    def stop_forwarding_service(self, file_path, template):
        """Stops a forwarding service"""
        service_key = f"{os.path.basename(file_path)}_{template}"
        
        if service_key in self.services:
            # Signal thread to stop
            self.services[service_key]['stop_flag'].set()
            # Wait for thread to finish
            self.services[service_key]['thread'].join(timeout=5)
            print(f"Stopped service: {service_key}")
            
    def _run_forwarding_service(self, file_path, template, stop_flag):
        """Main service logic for processing and forwarding logs"""
        service_key = f"{os.path.basename(file_path)}_{template}"
        
        # Load configs
        overrides = self.overrides_handler.get_saved_paths()
        defaults = self.forwarder_handler.get_saved_paths()
        model_mapping = self.models_handler.get_saved_paths()
        
        # Get forwarding config (override or default)
        file_key = os.path.basename(file_path)
        config = overrides.get(file_key, defaults)
        
        # Get model info
        model_info = model_mapping.get(template, ["No model assigned"])
        model_name = model_info[0] if isinstance(model_info, list) else model_info
        
        # Initialize LLM if model assigned
        llm = None
        template_handler = None
        if model_name != "No model assigned":
            template_path = os.path.join("..", "templates", template)
            template_handler = TemplateHandler(template_path)
            llm = LLMHandler(model_name=model_name, n_ctx=2048)
        
        # Process last 10 lines then monitor for new ones
        processed_count = 0
        
        try:
            if file_path.lower().endswith('.evtx'):
                processed_count = self._process_evtx_file(
                    file_path, template, llm, template_handler, config, service_key, stop_flag
                )
            else:
                processed_count = self._process_text_file(
                    file_path, template, llm, template_handler, config, service_key, stop_flag
                )
        except Exception as e:
            print(f"Service {service_key} error: {e}")
            
    def _process_evtx_file(self, file_path, template, llm, template_handler, config, service_key, stop_flag):
        """Process EVTX file - last 10 records then monitor"""
        count = 0
        
        with evtx.Evtx(file_path) as log:
            records = list(log.records())
            # Process last 10 records
            for record in records[-10:]:
                if stop_flag.is_set():
                    break
                xml_content = record.xml()
                self._process_and_forward(xml_content, template, llm, template_handler, config)
                count += 1
                self._update_counter(service_key)
                time.sleep(0.1)
                
            # Monitor for new records (simplified - in reality you'd need file watching)
            while not stop_flag.is_set():
                time.sleep(2)  # Check every 2 seconds for new records
                
        return count
        
    def _process_text_file(self, file_path, template, llm, template_handler, config, service_key, stop_flag):
        """Process text file - last 10 lines then monitor"""
        count = 0
        
        try:
            with open(file_path, "r", errors="ignore") as f:
                lines = f.readlines()
                # Process last 10 lines
                for line in lines[-10:]:
                    if stop_flag.is_set():
                        break
                    if line.strip():
                        self._process_and_forward(line.strip(), template, llm, template_handler, config)
                        count += 1
                        self._update_counter(service_key)
                        time.sleep(0.1)
                        
            # Monitor for new lines (simplified - in reality you'd need file watching)
            while not stop_flag.is_set():
                time.sleep(2)  # Check every 2 seconds for new lines
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            
        return count
        
    def _process_and_forward(self, log_content, template, llm, template_handler, config):
        """Process log content and forward to destination"""
        try:
            if llm and template_handler:
                # LLM processing
                if template_handler.matches_log(log_content):
                    prompt = template_handler.get_prompt()
                    model_template = template_handler.get_model_template()
                    model_params = template_handler.get_model_params()
                    
                    constructed_prompt = f"{prompt}\nRAW_LOG: {log_content}"
                    full_prompt = model_template.replace("{{ .Prompt }}", constructed_prompt)
                    
                    response, _ = llm.infer(full_prompt, model_params=model_params)
                    
                    # Convert to SYSLOG if needed
                    output_format = template_handler.get_output_format()
                    if output_format.upper() == "SYSLOG":
                        processed_content = template_handler.json_to_syslog(response)
                    else:
                        processed_content = response
                else:
                    return  # Skip if doesn't match template
            else:
                # Pass-through mode
                processed_content = log_content
                
            # Forward to destination
            self._forward_log(processed_content, config)
            
        except Exception as e:
            print(f"Processing error: {e}")
            
    def _forward_log(self, content, config):
        """Send log to configured destination"""
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
                
        except Exception as e:
            print(f"Forwarding error: {e}")
            
    def _update_counter(self, service_key):
        """Update counter for service"""
        counters = self.counters_handler.get_saved_paths()
        file_key = service_key.split('_')[0]  # Extract file part
        counters[file_key] = counters.get(file_key, 0) + 1
        self.counters_handler.save_mapping(counters)
        
    def monitor_configs(self):
        """Main monitoring loop - checks configs every 2 seconds"""
        while self.running:
            try:
                states = self.states_handler.get_saved_paths()
                saved_paths = self.config_handler.get_saved_paths()
                template_mapping = self.mapping_handler.get_saved_paths()
                
                # Check each path and template combination
                for path in saved_paths:
                    templates = template_mapping.get(path, [])
                    file_key = os.path.basename(path)
                    
                    for template in templates:
                        state_key = f"{file_key}_{template}"
                        template_state = states.get(state_key, {"enabled": False, "started": False})
                        
                        # Create service if enabled
                        if template_state["enabled"]:
                            self.create_forwarding_service(path, template)
                        
                        # Start service if started
                        if template_state["started"]:
                            self.start_forwarding_service(path, template)
                        else:
                            self.stop_forwarding_service(path, template)
                            
                        # Delete service if disabled
                        if not template_state["enabled"]:
                            self.delete_forwarding_service(path, template)
                            
            except Exception as e:
                print(f"Config monitoring error: {e}")
                
            time.sleep(2)
            
    def start(self):
        """Start the service manager"""
        monitor_thread = threading.Thread(target=self.monitor_configs, daemon=True)
        monitor_thread.start()
        print("Log Service Manager started")
        
    def stop(self):
        """Stop the service manager"""
        self.running = False
        # Stop all services
        for service_key, service_data in self.services.items():
            service_data['stop_flag'].set()
            service_data['thread'].join(timeout=5)
        print("Log Service Manager stopped")

# Global service manager instance
service_manager = None

def start_service_manager():
    global service_manager
    if service_manager is None:
        service_manager = LogServiceManager()
        service_manager.start()

def stop_service_manager():
    global service_manager
    if service_manager:
        service_manager.stop()
        service_manager = None