from llm_handler import LLMHandler
from template_handler import TemplateHandler

# Sample Windows log
log_line = """An account failed to log on.

Subject:
    Security ID:        S-1-0-0
    Account Name:       -
    Account Domain:     -
    Logon ID:           0x0

Logon Type:            3

Account For Which Logon Failed:
    Security ID:        S-1-0-0
    Account Name:       bonaga
    Account Domain:     MicrosoftAccount

Failure Information:
    Failure Reason:     Unknown user name or bad password.
    Status:             0xC000006D
    Sub Status:         0xC0000064

Process Information:
    Caller Process ID:  0x0
    Caller Process Name:    -

Network Information:
    Workstation Name:   HASSANLAPTOP
    Source Network Address: 172.20.10.4
    Source Port:        0

Detailed Authentication Information:
    Logon Process:      NtLmSsp 
    Authentication Package: NTLM
    Transited Services: -
    Package Name (NTLM only): -
    Key Length:         0
"""

# Detect matching template
template_handler = TemplateHandler.detect_template(log_line)
if not template_handler:
    print("No matching template found.")
    exit(1)

instruction = template_handler.get_instruction().strip()
template = template_handler.get_output_template().strip()

# Initialize model
handler = LLMHandler(model_name="Qwen3-0.6B-Q3_K_S.gguf", n_ctx=1024)

# Run inference
response, latency = handler.infer(instruction, template, log_line, max_tokens=150, stop=["}"])
print("Output:", response)
print("Time:", latency, "sec")