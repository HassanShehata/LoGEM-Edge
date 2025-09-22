
from configs_handler import ConfigsHandler
from llm_handler import LLMHandler
from template_handler import TemplateHandler

handler = TemplateHandler(template_path)
# Check if log matches template type criteria
if handler.matches_log(logline):            
    prompt = handler.get_prompt()
    model_template = handler.get_model_template()
    model_params = handler.get_model_params()
    output_format = handler.get_output_format()                
    constructed_prompt = f"{prompt}\nRAW_LOG: {logline}"                
    full_prompt = model_template.replace("{{ .Prompt }}", constructed_prompt)
    print(full_prompt)