from yaht.outputs import register_output, get_output, default_output


def test_register_output():
    """Test that we can register and retrieve a function as an output"""

    @register_output
    def foo():
        return "bar"

    out = get_output("foo")
    assert out == foo


def test_default_output():
    """Test what happens when we retrieve 'None' as the output name"""
    out = get_output(None)
    assert out == default_output
