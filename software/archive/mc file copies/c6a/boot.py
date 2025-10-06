from config import config
import time

print("Running boot.py")

try:
    time.sleep(3)
except Exception as e:
    print(f"Error {e}")
    
module_name = config["configuration"].lower()
try:
    with open(module_name + ".py") as f:
        code = f.read()
    exec(code)
except Exception as e:
    print(f"Error running {module_name}: {e}")


