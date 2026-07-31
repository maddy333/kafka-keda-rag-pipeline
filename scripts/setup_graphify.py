import os
import subprocess
import sys


def run_graphify_extraction():
    print("🕸️  Initializing Graphify Knowledge Graph extraction...")
    
    config_path = os.path.join(".graphify", "config.json")
    if not os.path.exists(config_path):
        print(f"❌ Graphify configuration file not found at {config_path}")
        sys.exit(1)

    print("Running graphify AST extraction across codebase...")
    try:
        # Executes graphify CLI command to generate AST and community cluster graphs
        cmd = ["graphify", ".", "--config", config_path]
        print(f"Executing: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Graphify extraction successful! Graph outputs generated in graphify-out/")
            print(result.stdout)
        else:
            print("⚠️  Graphify execution completed with output/warning:")
            print(result.stdout)
            print(result.stderr)
    except FileNotFoundError:
        print("ℹ️  'graphify' CLI is not installed in current environment. Install via 'pip install graphifyy'.")


if __name__ == "__main__":
    run_graphify_extraction()
