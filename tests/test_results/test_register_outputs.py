from yaht.outputs import register_output, get_output


def test_register_output():
    """Test that we can register and retrieve a function as an output"""

    @register_output
    def foo():
        return "bar"

    proc = get_output("foo")
    assert proc == foo
