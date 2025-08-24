import pytest
from yaht.processes import get_process


def test_default_process_return_true():
    """Test the default 'test' process, return_true"""
    proc = get_process("return_true")

    assert proc() == True


def test_default_process_return_inverse():
    """Test the default 'test' process, return_inverse"""

    proc = get_process("return_inverse")
    # Should return 0 - the input
    assert proc(1) == -1
    assert proc(-9) == 9


def test_default_process_return_n():
    """Test the default 'test' process, return_n"""
    proc = get_process("return_n")

    assert proc() == 0
    assert proc(n=12) == 12
