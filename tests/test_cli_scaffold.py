import os
import pytest
import shutil
import tempfile
import yaht.cli as cli


@pytest.fixture
def mock_working_directory():
    # Generate a temp directory to run test in
    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)
    return temp_dir


def test_scaffold(mock_working_directory):
    """Test generating the yaht scaffold"""
    cli.gen_scaffold()

    # Two files should be created
    assert os.path.isfile(cli.DEFAULT_CONFIG_FILE)
    assert os.path.exists(cli.DEFAULT_CACHE_DIR)


def test_git_scaffold(mock_working_directory):
    """Test that generates a gitignore if necessary"""
    os.mkdir("./.git/")
    cli.gen_scaffold()
    # If a .git directory exists with no gitignore, one should be created
    assert os.path.isfile("./.gitignore")
    with open("./.gitignore", "r") as f:
        gitgnore_text = f.readlines()
    assert gitgnore_text[-1] == cli.DEFAULT_CACHE_DIR


def test_not_git_scaffold(mock_working_directory):
    """Test that a gitignore is not generated when no git directory exists"""
    cli.gen_scaffold()
    # The .gitignore file should not have been created if no git directory exists
    assert not os.path.isfile("./.gitignore")


def test_existing_git_scaffold(mock_working_directory):
    """Test that scaffolding adds a line to an existing gitignore"""
    os.mkdir("./.git/")
    with open("./.gitignore", "w") as f:
        f.write("some_folder\nSomethingElse")

    cli.gen_scaffold()
    # If a .gitignore already exists, .yaht_cache should be added to it
    with open("./.gitignore", "r") as f:
        gitgnore_text = f.readlines()
    assert gitgnore_text[-1] == cli.DEFAULT_CACHE_DIR


def test_changing_environment_variables(mock_working_directory, monkeypatch):
    """Test that we can change the setup of the scaffold by changing env vars"""
    monkeypatch.setenv("YAHT_CONFIG_FILE", "mock_config.yaml")
    monkeypatch.setenv("YAHT_CACHE_DIR", "mock_cache")
    cli.gen_scaffold()

    # Two files should be created
    assert os.path.isfile("mock_config.yaml")
    assert os.path.exists("mock_cache/")


def test_changing_function_variables(mock_working_directory):
    """Test that we can change the setup of the scaffold by changing function vars"""
    cli.gen_scaffold(config_file="mock_config.yaml", cache_dir="mock_cache")

    # Two files should be created
    assert os.path.isfile("mock_config.yaml")
    assert os.path.exists("mock_cache/")
