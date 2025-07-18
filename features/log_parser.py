from llama_cpp import Llama

# Path to your downloaded GGUF model (e.g., TinyLlama, Phi-2, etc.)
MODEL_PATH = "models/tinyllama-1.1b-chat.gguf"

# Initialize model (keep n_ctx small for low memory)
llm = Llama(model_path=MODEL_PATH, n_ctx=512)

# Define a simple prompt
prompt = "Extract the source IP and destination port from this log: src=192.168.1.1 dst_port=443 action=allow"

# Run inference (stop after first return or max tokens)
output = llm(prompt, max_tokens=64, stop=["\n"], echo=False)

# Print model response
print("LLM Output:", output["choices"][0]["text"].strip())
