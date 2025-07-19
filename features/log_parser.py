from llm_handler import LLMHandler

handler = LLMHandler(model_name="Qwen3-0.6B-Q3_K_S.gguf", n_ctx=1024)

instruction = "Extract fields from the log and return only JSON with keys: account_name, logon_type, failure_reason, status, Source_Network_Address, workstation, auth_package, logon_process."

template = (
    "Stick to the below output format please!!\n"
    "Output: {\"account_name\": \"usenames if any\", \"logon_type\": \"usually a number\", \"failure_reason\": \"Usually a description\", \"status\": \"usually a code\", \"Source_Network_Address\": \"usually source IP\", \"workstation\": \"Usually Workstation name\", \"auth_package\": \"usually NTLM ot Kerberos\", \"logon_process\": \"Usually a process name\"}"
)


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


response, latency = handler.infer(instruction, template, log_line, max_tokens=150, stop=["}"])
print("Output:", response)
print("Time:", latency, "sec")

#print("Available Models:", handler.list_available_models())