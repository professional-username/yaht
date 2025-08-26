import os
import yaml
import pytest
import shutil
import tempfile
import yaht.cli as cli


@pytest.fixture
def mock_file_path():
    # Create an example source file
    file_dir = tempfile.mkdtemp()
    file_name = "mock_file"
    file_path = os.path.join(file_dir, file_name)
    with open(file_path, "w") as f:
        f.write("EXAMPLE_DATA")
    return file_path


@pytest.fixture
def mock_working_dir():
    # Generate a temp directory to run test in
    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)
    cli.gen_scaffold()  # Scaffold it for yaht
    return temp_dir


def test_add_file_to_config(mock_file_path, mock_working_dir):
    """Test that the relevant file is added to the config"""
    # Add the file, then clear the cache
    cli.add_file(mock_file_path)
    cli.clear_cache()

    # Check that there is a cache folder, but it's empty
    assert os.path.exists(cli.DEFAULT_CACHE_DIR)
    assert len(os.listdir(cli.DEFAULT_CACHE_DIR)) == 0
