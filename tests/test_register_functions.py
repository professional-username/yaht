#!/usr/bin/env python3
from yaht.processes import register_process, get_process


def test_register_process():
    """Test that we can register and retrieve a function as a process"""

    @register_process
    def foo():
        return "bar"

    proc = get_process("foo")
    assert proc == foo


def test_default_process_return_true():
    """Test the default 'test' process, return_true"""
    proc = get_process("return_true")

    assert proc() == True


def test_default_process_return_inverse():
    """Test the default 'test' process, not"""

    proc = get_process("return_inverse")
    assert proc(1) == -1
    assert proc(-9) == 9


def test_default_process_return_n():
    """Test the default 'test' process, return_n"""
    proc = get_process("return_n")

    assert proc() == 0
    assert proc(n=12) == 12
