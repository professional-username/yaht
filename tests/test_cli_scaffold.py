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
    assert os.path.isfile("./yaht.yaml")
    assert os.path.exists("./.yaht_cache/")


def test_git_scaffold(mock_working_directory):
    """Test that generates a gitignore if necessary"""
    os.mkdir("./.git/")
    cli.gen_scaffold()
    # If a .git directory exists with no gitignore, one should be created
    assert os.path.isfile("./.gitignore")
    with open("./.gitignore", "r") as f:
        gitgnore_text = f.readlines()
    assert gitgnore_text[-1] == ".yaht_cache"


def test_not_git_scaffold(mock_working_directory):
    """Test that a gitignore is not generated when no git directory exists"""
    cli.gen_scaffold()
    # The .gitignore file should not have been created if no git directory exists
    assert not os.path.isfile("./.gitignore")


def test_existing_git_scaffold(mock_working_directory):
    """Test that scaffolding adds a line to an existing gitignore"""
    os.mkdir("./.git/")
    with open("./.gitignore", "w") as f:
        f.write("some_folder\n")

    cli.gen_scaffold()
    # If a .gitignore already exists, .yaht_cache should be added to it
    with open("./.gitignore", "r") as f:
        gitgnore_text = f.readlines()
    assert gitgnore_text[-1] == ".yaht_cache"
