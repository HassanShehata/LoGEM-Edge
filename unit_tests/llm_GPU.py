from llama_cpp import Llama

llm = Llama(
    model_path="../../models/logem-win.gguf",
    n_gpu_layers=-1,    # put ALL layers on GPU
    n_threads=8,
    n_batch=512,
    verbose=True
)
print(llm("Q: 2+2=?\nA:"))



'''
import time
from llama_cpp import Llama

# Load GGUF model
llm = Llama(
    model_path="../../models/logem-win.gguf",
    n_ctx=4096,
    n_threads=4,
    n_gpu_layers=-1,
    verbose=True
)

# User log prompt
user_prompt = """Extract fields from the log and return only JSON with keys:
EventID, Computer, SystemTime, SubjectUserName, SubjectDomainName,
TargetName, ProcessName, LogonType, Status

RAW_LOG:
<Event xmlns='http://schemas.microsoft.com/win/2004/08/events/event'>
  <System>
    <Provider Name='Microsoft-Windows-Security-Auditing'/>
    <EventID>4625</EventID>
    <TimeCreated SystemTime='2024-11-29T08:31:52.123456Z'/>
    <Computer>WIN-SRV01.corp.local</Computer>
  </System>
  <EventData>
    <Data Name='SubjectUserName'>WIN-SRV01$</Data>
    <Data Name='SubjectDomainName'>CORP</Data>
    <Data Name='TargetUserName'>jdoe</Data>
    <Data Name='ProcessName'>-</Data>
    <Data Name='LogonType'>3</Data>
    <Data Name='Status'>0xC000006D</Data>
  </EventData>
</Event>
"""

# Chat-style template
prompt = f"""<|im_start|>system
You are a log parser. Return RAW JSON only. No <think>, no prose, no markdown.<|im_end|>
<|im_start|>user
{user_prompt}<|im_end|>
<|im_start|>assistant
"""

# Run inference
t0 = time.time()
out = llm(
    prompt,
    max_tokens=256,
    temperature=0.0,
    top_p=1.0,
    stop=["<|im_start|>", "<|im_end|>"],  # your stoppers
    echo=False
)
elapsed_ms = int((time.time() - t0) * 1000)

# Print model output
print(out["choices"][0]["text"].strip())
print(f"\n[elapsed: {elapsed_ms} ms]")
'''