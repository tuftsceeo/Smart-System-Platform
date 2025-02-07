from config import config

print("Running boot.py")

def run_config_module(module_name):
    try:
        with open(module_name + ".py") as f:
            code = f.read()
        exec(code)
    except Exception as e:
        print(f"Error running {module_name}: {e}")

