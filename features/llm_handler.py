import os
import sys
import time
import multiprocessing
from contextlib import contextmanager
from llama_cpp import Llama
import json


class LLMHandler:
    def __init__(self, model_name, model_dir="../../models", n_ctx=1024, n_threads=None, n_batch=64, n_gpu_layers=0):
        self.model_path = os.path.abspath(os.path.join(model_dir, model_name))
        self.n_ctx = n_ctx
        self.n_threads = n_threads or multiprocessing.cpu_count()
        self.n_batch = n_batch
        self.n_gpu_layers = n_gpu_layers
        self.model = None


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
                verbose=False
            )

    def infer(self, prompt, model_params=None, max_tokens=64):
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