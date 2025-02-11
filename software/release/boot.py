from config import config
import time

print("Running boot.py")

try:
    time.sleep(2)
except Exception as e:
    print(f"Error running {module_name}: {e}")

def run_config_module(module_name):
    try:
        with open(module_name + ".py") as f:
            code = f.read()
        exec(code)
    except Exception as e:
        print(f"Error running {module_name}: {e}")

