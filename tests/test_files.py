import pytest
import sys
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
from your_project_name import files as files_module  # Replace with your actual module name

# --- Test file_exists ---

def test_file_exists_with_existing_file(tmp_path):
    """Test that file_exists returns True for an existing file."""
    p = tmp_path / "test.txt"
    p.touch()
    assert files_module.file_exists(p)

def test_file_exists_with_non_existing_file(tmp_path):
    """Test that file_exists returns False for a non-existing file."""
    p = tmp_path / "non_existent.txt"
    assert not files_module.file_exists(p)

@pytest.mark.parametrize("stream", files_module.SPECIAL_STREAMS)
def test_file_exists_with_special_streams(stream):
    """Test that file_exists returns False for special stream names."""
    assert not files_module.file_exists(stream)

def test_file_exists_with_none():
    """Test that file_exists returns False for None input."""
    assert not files_module.file_exists(None)


# --- Test resolve_file ---

def test_resolve_file_with_path(tmp_path):
    """Test resolve_file returns an absolute path for a valid Path object."""
    p = tmp_path / "test.txt"
    p.touch()
    resolved = files_module.resolve_file(p)
    assert resolved == p.resolve()

def test_resolve_file_with_strict_existing_file(tmp_path):
    """Test resolve_file with strict=True returns a resolved path."""
    p = tmp_path / "test.txt"
    p.touch()
    resolved = files_module.resolve_file(p, strict=True)
    assert resolved == p.resolve()

def test_resolve_file_with_strict_non_existent(tmp_path):
    """Test resolve_file with strict=True raises FileNotFoundError."""
    p = tmp_path / "non_existent.txt"
    with pytest.raises(FileNotFoundError):
        files_module.resolve_file(p, strict=True)

@pytest.mark.parametrize("stream", files_module.SPECIAL_STREAMS)
def test_resolve_file_with_special_streams(stream):
    """Test resolve_file returns the special stream string itself."""
    resolved = files_module.resolve_file(stream)
    assert resolved == stream

def test_resolve_file_with_none():
    """Test resolve_file returns None for None input."""
    assert files_module.resolve_file(None) is None


# --- Test find_files ---

def test_find_files(tmp_path):
    """Test find_files correctly discovers contract files in directories."""
    # Setup a directory structure
    dir1 = tmp_path / "dir1"
    dir1.mkdir()
    (dir1 / "a.hpp.contract").touch()
    (dir1 / "b.hpp.contract").touch()
    
    dir2 = tmp_path / "dir2"
    dir2.mkdir()
    (dir2 / "c.hpp.contract").touch()
    (dir2 / "d.cpp").touch() # Should be ignored

    search_dirs = [dir1, dir2]
    found = files_module.find_files(search_dirs)
    
    assert len(found) == 3
    assert (dir1 / "a.hpp.contract").resolve() in found
    assert (dir2 / "c.hpp.contract").resolve() in found

def test_find_files_with_single_file(tmp_path):
    """Test find_files correctly handles a single file path as input."""
    p = tmp_path / "single_contract.hpp.contract"
    p.touch()
    
    found = files_module.find_files([p])
    assert len(found) == 1
    assert found[0] == p.resolve()


# --- Test find_file ---

def test_find_file_existing(tmp_path):
    """Test find_file returns resolved path for an existing file."""
    p = tmp_path / "existing.hpp.contract"
    p.touch()
    found = files_module.find_file(p)
    assert found == p.resolve()

def test_find_file_non_existent(tmp_path):
    """Test find_file returns None for a non-existing file."""
    p = tmp_path / "non_existent.hpp.contract"
    found = files_module.find_file(p)
    assert found is None


# --- Test open_output (context manager) and write_file ---

def test_write_file_to_file(tmp_path):
    """Test that write_file correctly writes content to a file."""
    output_path = tmp_path / "output.txt"
    test_text = "Hello, world!"
    
    files_module.write_file(output_path, test_text)
    
    assert output_path.read_text() == test_text

def test_write_file_to_stdout(capsys):
    """Test that write_file correctly writes to stdout."""
    test_text = "stdout test\n"
    files_module.write_file("-", test_text)
    
    captured = capsys.readouterr()
    assert captured.out == test_text

def test_write_file_to_stderr(capsys):
    """Test that write_file correctly writes to stderr."""
    test_text = "stderr test\n"
    files_module.write_file("stderr", test_text)
    
    captured = capsys.readouterr()
    assert captured.err == test_text

def test_open_output_invalid_type():
    """Test that open_output raises a TypeError for an invalid target type."""
    with pytest.raises(TypeError):
        with files_module.open_output(123):
            pass


# --- Test read_file_text ---

def test_read_file_text_existing_file(tmp_path):
    """Test that read_file_text returns the correct content."""
    p = tmp_path / "read.txt"
    p.write_text("test content")
    assert files_module.read_file_text(p) == "test content"

def test_read_file_text_non_existent_file():
    """Test that read_file_text returns empty string for non-existent file."""
    assert files_module.read_file_text("does_not_exist.txt") == ""

def test_read_file_text_strict_raises_error():
    """Test that strict=True raises an error for a non-existent file."""
    with pytest.raises(FileNotFoundError):
        files_module.read_file_text("does_not_exist.txt", strict=True)


# --- Test hashing and hash extraction ---

def test_hash_string():
    """Test that hash_string returns a consistent hash."""
    text = "hello world"
    # Known SHA256 hash for "hello world"
    expected_hash = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert files_module.hash_string(text) == expected_hash

def test_extract_hash_from_text():
    """Test that extract_hash_from_text finds the hash."""
    text_with_hash = "// cpp_contractgen:hash=1a2b3c4d5e"
    assert files_module.extract_hash_from_text(text_with_hash) == "1a2b3c4d5e"

def test_extract_hash_from_text_no_hash():
    """Test that extract_hash_from_text returns None when no hash is found."""
    text_without_hash = "some text without a hash"
    assert files_module.extract_hash_from_text(text_without_hash) is None

# NOTE: The tests for hash_file and extract_hash_from_file are already implicitly covered
# by the read_file_text and hash_string tests, but explicit tests are good practice.

def test_hash_file(tmp_path):
    """Test that hash_file returns a hash of the file content."""
    p = tmp_path / "hash_me.txt"
    p.write_text("file content")
    expected_hash = hashlib.sha256("file content".encode()).hexdigest()
    assert files_module.hash_file(p) == expected_hash

def test_extract_hash_from_file(tmp_path):
    """Test that extract_hash_from_file finds an embedded hash."""
    p = tmp_path / "hash_file.txt"
    p.write_text("// cpp_contractgen:hash=deadbeef")
    assert files_module.extract_hash_from_file(p) == "deadbeef"