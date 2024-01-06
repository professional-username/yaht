#!/usr/bin/env python3
import os
import importlib.util


PROCESSES = {}


def register_process(proc):
    """Decorator to register a process"""
    PROCESSES[proc.__name__] = proc
    return proc


def get_process(proc_name):
    """Function to return a process by name"""
    return PROCESSES[proc_name]


def find_processes():
    """Import files in current directory to find processes"""
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
