from llama_cpp import Llama

llm = Llama(
    model_path="./models/logem-win.gguf",
    temperature=0,
    top_p=0.9,
    n_ctx=40960,
    stop=["<|im_start|>", "<|im_end|>"],
)

def format_prompt(raw_log):
    return f"""<|im_start|>system
You are a log parser. Return RAW JSON only. No <think>, no prose, no markdown.<|im_end|>
<|im_start|>user
Extract fields from the log and return only JSON with keys:Name,Guid,Qualifiers,EventID,Version,Level,Task,Opcode,Keywords,SystemTime,EventRecordID,ActivityID,RelatedActivityID,ProcessID,ThreadID,Channel,Computer,UserID,SubjectUserSid,SubjectUserName,SubjectDomainName,SubjectLogonId
RAW_LOG: {raw_log}<|im_end|>
<|im_start|>assistant
"""

# Real Windows failed logon attempt (Event ID 4625)
test_log = """Name="Microsoft-Windows-Security-Auditing" Guid="{54849625-5478-4994-a5ba-3e3b0328c30d}" Qualifiers="" EventID="4625" Version="0" Level="0" Task="12544" Opcode="0" Keywords="0x8010000000000000" SystemTime="2024-09-17 14:23:17.445123+00:00" EventRecordID="892471" ActivityID="" RelatedActivityID="" ProcessID="628" ThreadID="5832" Channel="Security" Computer="DC01.contoso.com" UserID="" SubjectUserSid="S-1-5-18" SubjectUserName="DC01$" SubjectDomainName="CONTOSO" SubjectLogonId="0x3e7" TargetUserName="administrator" TargetDomainName="CONTOSO" FailureReason="%%2313" Status="0xc000006d" SubStatus="0xc000006a" LogonType="3" LogonProcessName="NtLmSsp" AuthenticationPackageName="NTLM" WorkstationName="LAPTOP-USER01" TransmittedServices="-" LmPackageName="-" KeyLength="0" ProcessName="NtLmSsp" IpAddress="192.168.10.155" IpPort="52341\""""

response = llm.create_completion(
    prompt=format_prompt(test_log),
    max_tokens=2048,
)

print("JSON Response:")
print(response['choices'][0]['text'])