import time; start = time.time(); 
import subprocess; result = subprocess.run(['ollama', 'run', 'qwen2.5:14b', 'Hello'], capture_output=True, text=True, timeout=30)
print(f'Response time: {time.time() - start:.2f}s')
