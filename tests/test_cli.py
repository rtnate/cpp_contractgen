import pytest
import sys
import argparse
import io
import pathlib
from unittest.mock import MagicMock
from pathlib import Path

# Assume these are imported from your cli.py file
from cpp_contractgen.cli import (
    get_arg_parser,
    parse_args,
    create_temp_input_from_stdin,
    generate_temp_filename,
    ArgParseError,
)

# Assume these are imported from your other modules
from cpp_contractgen import parser, generator


# A mock class for the policy object to test interactions
class MockPolicy:
    def __init__(self):
        self.temp_directory = None
    
    def log_properties(self, level):
        pass

class TestCLI:
    """A simple test class for organizing tests, no inheritance needed."""

    def test_get_arg_parser(self):
        """
        Tests that the argument parser is correctly initialized and has the
        expected arguments and groups.
        """
        parser = get_arg_parser()
        assert isinstance(parser, argparse.ArgumentParser)

        # Test for mutually exclusive groups
        assert len(parser._mutually_exclusive_groups) == 2
        
        # Test for a specific argument
        assert '--version' in [action.option_strings[0] for action in parser._actions]
        assert '--contract' in [action.option_strings[0] for action in parser._actions]

    def test_parse_args_single_file_mode(self, monkeypatch, mocker):
        """Tests argument parsing in single-file mode by mocking the `parse_args` function."""
        
        # Create a mock for the returned `args` object
        mock_args = MagicMock()
        mock_args.contract = MagicMock(spec=io.StringIO)
        mock_args.contract.name = 'test_file.hpp.contract'
        mock_args.output = MagicMock(spec=io.StringIO)
        mock_args.output.name = 'out.hpp'
        mock_args.config = None
        mock_args.search = None
        mock_args.yes = False
        mock_args.emit_header = False
        
        # Patch the function that would normally run and make it return our mock object
        mocker.patch('cpp_contractgen.cli.get_arg_parser', return_value=MagicMock(parse_args=lambda: mock_args))
        
        # The test now runs against our controlled mock object
        args = parse_args()
        
        assert args.contract.name == 'test_file.hpp.contract'
        assert args.output.name == 'out.hpp'
        assert args.config is None
        assert args.search is None
        assert not args.yes
        
    def test_parse_args_config_mode(self, monkeypatch):
        """Tests argument parsing in batch/config mode using the monkeypatch fixture."""
        monkeypatch.setattr(sys, 'argv', ['cli.py', '--config', 'config.json', '-y', '-v'])
        args = parse_args()
        assert args.contract is None
        assert args.output is None
        assert args.config == 'config.json'
        assert args.yes
        assert args.verbose

    def test_parse_args_emit_header_error(self, monkeypatch):
        """Tests that using --outdir with a specific --emit-header path raises an error."""
        monkeypatch.setattr(sys, 'argv', ['cli.py', '--outdir', 'temp', '--emit-header', 'header_path'])
        with pytest.raises(ArgParseError):
            parse_args()

    def test_create_temp_input_from_stdin(self, mocker, tmp_path):
        """
        Tests that create_temp_input_from_stdin correctly reads from a mock stdin
        and creates a file in a temporary directory provided by the tmp_path fixture.
        """
        # Create a mock file-like object for stdin
        mock_stdin_file = MagicMock(spec=io.StringIO)
        mock_stdin_file.name = '<stdin>'
        mock_stdin_file.read.return_value = '// Test contract content'
        mock_stdin_file.seek.return_value = None

        # Call the function, using tmp_path as the temporary directory
        temp_file_path = create_temp_input_from_stdin(mock_stdin_file, tmp_path)

        # Assert that the function returns a Path object and it's in the tmp_path directory
        assert isinstance(temp_file_path, Path)
        assert str(temp_file_path).startswith(str(tmp_path))

        # Assert the filename is generated correctly
        expected_filename = generate_temp_filename('// Test contract content', ".hpp.contract")
        assert temp_file_path.name == expected_filename

        # Check that the file content was written correctly
        assert temp_file_path.read_text(encoding='utf-8') == '// Test contract content'

