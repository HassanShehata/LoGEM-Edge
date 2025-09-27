import os
import sys
import time
import multiprocessing
from contextlib import contextmanager
from llama_cpp import Llama
import json


class LLMHandler:
    def __init__(self, model_name, model_dir="../../models", n_ctx=2048, n_threads=None, n_batch=64, n_gpu_layers=-1):
        self.model_path = os.path.abspath(os.path.join(model_dir, model_name))
        self.n_ctx = n_ctx
        self.n_threads = min(2, multiprocessing.cpu_count())
        self.n_batch = n_batch
        self.n_gpu_layers = n_gpu_layers
        self.model = None
        self.call_count = 0


    @contextmanager
    def suppress_output(self):
        with open(os.devnull, 'w') as devnull:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = devnull
            sys.stderr = devnull
            try:
                yield
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

    def load_model(self):
        with self.suppress_output():
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                n_batch=self.n_batch,
                n_gpu_layers=self.n_gpu_layers,
                verbose=False,
                # NEW PERFORMANCE PARAMETERS
                #n_ubatch=512,        # Process tokens in larger micro-batches
                #flash_attn=True,     # Enable flash attention for speed
                #use_mmap=True,       # Memory mapping for faster loading
                use_mlock=True,      # Lock model in RAM
                rope_scaling_type=0,           # Disable RoPE scaling
                rope_freq_base=10000.0,        # Standard frequency base
                mul_mat_q=True,                # Enable quantized matrix multiplication
                logits_all=False,              # Don't compute all logits
                embedding=False,               # Disable embeddings
                offload_kqv=True,              # Offload K,Q,V to GPU
                flash_attn=True,               # Enable flash attention
                use_mmap=False,                # Disable memory mapping (try this)
            )
    
    def _reset_if_needed(self):
        """Reset model every 100 calls to prevent memory saturation"""
        if self.call_count > 0 and self.call_count % 100 == 0:
            print(f"[LLM] Resetting model after {self.call_count} calls")
            if self.model:
                del self.model
                self.model = None
            self.load_model()

    def infer(self, prompt, model_params=None, max_tokens=64):
        self._reset_if_needed()

        if self.model is None:
            self.load_model()
        
        # Use model_params if provided, otherwise use defaults
        if model_params:
            stop_tokens = model_params.get("stop", ["\n"])
            temperature = model_params.get("temperature", 0)
            top_p = model_params.get("top_p", 0.9)
            max_tokens = model_params.get("max_tokens", max_tokens)
        else:
            # Fallback defaults when no model_params provided
            stop_tokens = ["\n"]
            temperature = 0
            top_p = 0.9
        
        start = time.time()
        self.call_count += 1
        print(f"[LLM] Call #{self.call_count} starting inference with prompt length: {len(prompt)}")
        output = self.model(
            prompt, 
            max_tokens=max_tokens, 
            stop=stop_tokens, 
            temperature=temperature,
            top_p=top_p,
            echo=False
        )
        end = time.time()
        
        result = output["choices"][0]["text"].strip()
        return result, round(end - start, 3)


    @staticmethod
    def list_available_models(model_dir="../../models"):
        files = os.listdir(os.path.abspath(model_dir))
        return [f for f in files if f.endswith(".gguf")]