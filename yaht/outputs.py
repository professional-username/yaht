import os
import importlib.util


OUTPUTS = {}


def register_output(output):
    """Decorator to register a output"""
    OUTPUTS[output.__name__] = output
    return output


def get_output(output_name):
    """Function to return a output by name"""
    return OUTPUTS[output_name]


def find_outputs():
    """Import files in current directory to find outputs"""
    for dirpath, dirnames, filenames in os.walk("."):
        for filename in [f for f in filenames if f.endswith(".py")]:
            # Construct the module name from the file path
            module_name = os.path.splitext(filename)[0]
            # Construct the full path to the .py file
            file_path = os.path.join(dirpath, filename)
            # Import the module
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
