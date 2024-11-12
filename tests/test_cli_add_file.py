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
    cli.add_file(mock_file_path)

    mock_file_name = os.path.basename(mock_file_path)
    # Read the config and check that it specifies the file
    with open(cli.DEFAULT_CONFIG_FILE, "r") as config_stream:
        updated_config = yaml.safe_load(config_stream)
    assert updated_config["SOURCES"][mock_file_name] == "file:%s" % mock_file_name


def test_add_file_to_cache(mock_file_path, mock_working_dir):
    """Test that the relevant file is added to the cache"""
    cli.add_file(mock_file_path)

    mock_file_name = os.path.basename(mock_file_path)
    expected_file = os.path.join(cli.DEFAULT_CACHE_DIR, mock_file_name)
    # Check that the file is in the cache, and the original is still there
    assert os.path.isfile(expected_file)
    assert os.path.isfile(mock_file_path)


def test_move_initial_file(mock_file_path, mock_working_dir):
    """Test that supplying the move=true option deletes the original file"""
    cli.add_file(mock_file_path, move=True)

    mock_file_name = os.path.basename(mock_file_path)
    expected_file = os.path.join(cli.DEFAULT_CACHE_DIR, mock_file_name)
    # Original file should be gone, cached file should be there
    assert os.path.isfile(expected_file)
    assert not os.path.isfile(mock_file_path)


def test_set_environment_variables(mock_file_path, monkeypatch):
    """Test that add_file works with environment variables"""
    # Set the env vars and create the working dir
    monkeypatch.setenv("YAHT_CONFIG_FILE", "mock_config.yaml")
    monkeypatch.setenv("YAHT_CACHE_DIR", "mock_cache")
    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)
    cli.gen_scaffold()

    cli.add_file(mock_file_path)

    mock_file_name = os.path.basename(mock_file_path)
    expected_file = os.path.join("mock_cache", mock_file_name)
    # Check the target file as well as the config change
    assert os.path.isfile(expected_file)
    with open("mock_config.yaml", "r") as config_stream:
        updated_config = yaml.safe_load(config_stream)
    assert updated_config["SOURCES"][mock_file_name] == "file:%s" % mock_file_name


def test_set_function_variables(mock_file_path):
    """Test that we can add variables directly"""
    # Create the working dir with the new vars
    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)
    cli.gen_scaffold(config_file="mock_config.yaml", cache_dir="mock_cache")

    cli.add_file(
        mock_file_path,
        config_file="mock_config.yaml",
        cache_dir="mock_cache",
    )

    mock_file_name = os.path.basename(mock_file_path)
    expected_file = os.path.join("mock_cache", mock_file_name)
    # Check the target file as well as the config change
    assert os.path.isfile(expected_file)
    with open("mock_config.yaml", "r") as config_stream:
        updated_config = yaml.safe_load(config_stream)
    assert updated_config["SOURCES"][mock_file_name] == "file:%s" % mock_file_name
