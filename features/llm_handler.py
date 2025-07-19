import os
import sys
import time
import multiprocessing
from contextlib import contextmanager
from llama_cpp import Llama

class LLMHandler:
    def __init__(self, model_name, model_dir="../../models", n_ctx=256, n_threads=None, n_batch=64, n_gpu_layers=0):
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


    def infer(self, instruction, template, log_line, output_format="JSON", max_tokens=64, stop=None):
        if self.model is None:
            self.load_model()
    
        output_format = output_format.upper()
    
        # Define prefix, suffix, and stop token based on format
        if output_format == "JSON":
            prefix = "{"
            suffix = "}"
            stop = stop or ["}"]
        elif output_format == "CEF":
            prefix = ""
            suffix = "\n"
            stop = stop or ["\n"]
        else:  # Default for unsupported/custom formats
            prefix = ""
            suffix = ""
            stop = stop or ["\n"]
    
        prompt = f"{instruction}\n{template}\nLog: {log_line}\nOutput:\n{prefix}"
    
        print(f"""
        ----------------------------------
        {prompt}
        ----------------------------------
        """)
    
        start = time.time()
        output = self.model(prompt, max_tokens=max_tokens, stop=stop, echo=False)
        end = time.time()
    
        result = output["choices"][0]["text"].strip()
    
        if output_format == "JSON":
            if result and not result.startswith("{"):
                result = "{" + result
            if result and not result.endswith("}"):
                result = result + "}"
    
        return result, round(end - start, 3)


    @staticmethod
    def list_available_models(model_dir="../../models"):
        files = os.listdir(os.path.abspath(model_dir))
        return [f for f in files if f.endswith(".gguf")]