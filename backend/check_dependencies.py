import sys
import subprocess
import os
from importlib.util import find_spec

def check_package(pkg_name, import_name=None):
    if import_name is None:
        import_name = pkg_name
    spec = find_spec(import_name)
    if spec is not None:
        print(f"[OK] {pkg_name} is installed.")
        return True
    else:
        print(f"[ERROR] {pkg_name} is missing.")
        return False

def check_ollama_model(model_name):
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)
        if model_name in result.stdout:
            print(f"[OK] Ollama model '{model_name}' is available.")
            return True
        else:
            print(f"[ERROR] Ollama model '{model_name}' is missing. Run: ollama run {model_name}")
            return False
    except FileNotFoundError:
         print(f"[ERROR] Ollama is not installed or not in PATH.")
         return False
    except Exception as e:
        print(f"[ERROR] Failed to run Ollama: {e}")
        return False

def check_env():
    if os.path.exists(".env"):
        print("[OK] .env file found.")
        with open(".env", "r") as f:
            content = f.read()
            if "GEMINI_API_KEY" in content:
                print("[OK] GEMINI_API_KEY found in .env.")
            else:
                print("[WARNING] GEMINI_API_KEY is missing in .env.")
    else:
        print("[ERROR] .env file is missing.")
        
def main():
    print("========================================")
    print("  Netran AI Dependency & Setup Checker  ")
    print("========================================")
    
    print("\n--- Python Packages ---")
    packages = {
        "kivy": "kivy",
        "google-genai": "google.genai",
        "ollama": "ollama",
        "sounddevice": "sounddevice",
        "numpy": "numpy",
        "faster-whisper": "faster_whisper",
        "kokoro": "kokoro",
        "speechbrain": "speechbrain",
        "torch": "torch",
        "torchaudio": "torchaudio",
        "pypdf": "pypdf",
        "python-docx": "docx",
        "tavily-python": "tavily"
    }
    
    all_pkgs_ok = True
    for pkg, imp in packages.items():
        if not check_package(pkg, imp):
            all_pkgs_ok = False
            
    print("\n--- Ollama Models ---")
    ollama_ok = True
    for model in ["qwen2.5:3b", "qwen2.5:1.5b"]:
        if not check_ollama_model(model):
            ollama_ok = False
            
    print("\n--- Environment Variables ---")
    check_env()
    
    print("\n========================================")
    if all_pkgs_ok and ollama_ok:
        print("[SUCCESS] All crucial dependencies appear to be met!")
        print("          If you face issues with models (e.g. Silero/Faster-Whisper), they will auto-download on first run.")
    else:
        print("[FAILED]  Some dependencies are missing. Please review the errors above.")
        print("          Use setup options in run.bat to install python packages.")

if __name__ == "__main__":
    main()
