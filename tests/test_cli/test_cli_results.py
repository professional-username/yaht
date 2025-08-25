import os
import pytest
import tempfile
import yaht.cli as cli


@pytest.fixture
def mock_working_directory():
    # Generate a temp directory to run test in
    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)
    return temp_dir


# @pytest.fixture
# def mock_file_path():
#     # Create an example source file
#     file_dir = tempfile.mkdtemp()
#     file_name = "mock_file"
#     file_path = os.path.join(file_dir, file_name)
#     with open(file_path, "w") as f:
#         f.write("EXAMPLE_DATA")
#     return file_path


@pytest.fixture
def mock_all_outputs(mocker):
    RESULTS = []

    # Mock output functions to just print the result value
    def mock_get_output(proc_name):
        return lambda x, y: RESULTS.append({"value": x, "metadata": y})

    mocker.patch("yaht.outputs.get_output", mock_get_output)
    # Return a list that keeps track of all results
    return RESULTS


def test_output_default_config(mock_all_outputs, mock_working_directory):
    """
    Initialize and run the default config,
    and check that outputs were given
    """
    result_list = mock_all_outputs
    cli.gen_scaffold()
    cli.run_experiments()
    cli.output_experiment_results()

    # Check the structure of one of the results
    some_result = result_list[0]
    assert list(some_result.keys()) == ["value", "metadata"]
    assert list(some_result["metadata"].keys()) == [
        "experiment",
        "trial",
        "process",
        "name",
        "hash",
    ]
