
import sys
import os

print(f"Python: {sys.version}")
print(f"CWD: {os.getcwd()}")

try:
    import llama_cpp
    from llama_cpp import Llama
    print(f"✅ llama_cpp imported successfully!")
    print(f"Version: {llama_cpp.__version__ if hasattr(llama_cpp, '__version__') else 'unknown'}")
    print(f"Llama class available: {Llama}")
except ImportError as e:
    print(f"❌ Failed to import llama_cpp: {e}")
except Exception as e:
    print(f"❌ An error occurred: {e}")
