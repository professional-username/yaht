#!/usr/bin/env python3


PROCESSES = {}


def register_process(proc):
    """Decorator to register a process"""
    PROCESSES[proc.__name__] = proc
    return proc


def get_process(proc_name):
    """Function to return a process by name"""
    return PROCESSES[proc_name]
