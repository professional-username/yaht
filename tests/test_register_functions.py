#!/usr/bin/env python3
from yaht.processes import register_process, get_process


def test_register_process():
    """Test that we can register and retrieve a function as a process"""

    @register_process
    def foo():
        return "bar"

    proc = get_process("foo")
    assert proc == foo
