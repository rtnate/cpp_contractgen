import pytest
import logging
from unittest.mock import MagicMock, call
from pathlib import Path
from cpp_contractgen.types import OnBuildPolicy, GenerationMode
# Assume these are imported from your core.py file
from cpp_contractgen.core import (
    Job,
    discover_files,
    determine_job_action,
    build_jobs,
    execute_job,
    build_and_execute_policy
)

# Mocking external dependencies
# We'll use these to simulate the behavior of other modules
class MockPolicy:
    def __init__(self, **kwargs):
        self.in_file = kwargs.get('in_file')
        self.search_dirs = kwargs.get('search_dirs', [])
        self.generation_mode = kwargs.get('generation_mode')
        self.emit_header = kwargs.get('emit_header')
        self.on_build = kwargs.get('on_build')
        self.embed_contract = kwargs.get('embed_contract', False)
        self.use_std_out = kwargs.get('use_std_out', False)

    def get_policy_for_file(self, file_path):
        return MockPolicy(
            on_build=self.on_build,
            embed_contract=self.embed_contract,
            use_std_out=self.use_std_out,
            in_file=file_path,
        )

    def resolve_output_file(self, file_path):
        if not file_path:
            return Path('mock_output_path')
        return Path(file_path).parent / f"{Path(file_path).stem.replace('.hpp', '.contract.hpp')}"

@pytest.fixture
def mock_logger(mocker):
    """Fixture to mock logging and prevent console output."""
    mocker.patch('logging.debug')
    mocker.patch('logging.info')
    mocker.patch('logging.warning')
    mocker.patch('logging.error')
    mocker.patch('logging.critical')

def test_discover_files_emit_header(mock_logger):
    """Test discover_files in EMIT_HEADER mode returns an empty list."""
    policy = MockPolicy(generation_mode=GenerationMode.EMIT_HEADER)
    files = discover_files(policy)
    assert files == []

def test_discover_files_single_file(mock_logger, mocker):
    """Test discover_files in SINGLE_FILE mode returns a single file."""
    mocker.patch('cpp_contractgen.core.find_file', return_value=Path('path/to/exists.hpp.contract'))
    policy = MockPolicy(generation_mode=GenerationMode.SINGLE_FILE, in_file='path/to/exists.hpp.contract')
    files = discover_files(policy)
    assert files == [Path('path/to/exists.hpp.contract')]

def test_discover_files_batch_mode(mock_logger, mocker):
    """Test discover_files in BATCH mode returns a list of files."""
    mocker.patch('cpp_contractgen.core.find_files', return_value=[Path('file1.hpp.contract'), Path('file2.hpp.contract')])
    policy = MockPolicy(generation_mode=GenerationMode.BATCH, search_dirs=['src'])
    files = discover_files(policy)
    assert files == [Path('file1.hpp.contract'), Path('file2.hpp.contract')]

@pytest.mark.parametrize("on_build, file_exists, expected_action", [
    (OnBuildPolicy.NONE, False, "skip"),
    (OnBuildPolicy.NONE, True, "skip"),
    (OnBuildPolicy.GENERATE_MISSING, False, "generate"),
    (OnBuildPolicy.GENERATE_MISSING, True, "skip"),
    (OnBuildPolicy.FORCE, False, "generate"),
    (OnBuildPolicy.FORCE, True, "generate"),
    (OnBuildPolicy.OVERWRITE, False, "generate"),
    (OnBuildPolicy.OVERWRITE, True, "generate"),
    (OnBuildPolicy.CHECK_DIFF, False, "check"),
    (OnBuildPolicy.CHECK_DIFF, True, "check"),
])
def test_determine_job_action(on_build, file_exists, expected_action, mocker):
    """Test determine_job_action for all policy combinations."""
    mocker.patch('cpp_contractgen.core.file_exists', return_value=file_exists)
    action = determine_job_action(on_build, "mock_path")
    assert action == expected_action

def test_build_jobs_emit_header(mock_logger, mocker):
    """Test building a job for EMIT_HEADER mode."""
    mocker.patch('cpp_contractgen.core.generate_header')
    policy = MockPolicy(generation_mode=GenerationMode.EMIT_HEADER, emit_header='output/header.hpp')
    jobs = build_jobs(policy, [])
    assert len(jobs) == 1
    job = jobs[0]
    assert job.action == 'emit_header'
    assert job.input_file is None
    assert job.output_file == Path('output/header.hpp').resolve()

def test_build_jobs_batch_mode(mock_logger, mocker):
    """Test building jobs for a batch of files."""
    mocker.patch('cpp_contractgen.core.find_files', return_value=[Path('file1.hpp.contract'), Path('file2.hpp.contract')])
    mocker.patch('cpp_contractgen.core.resolve_file', side_effect=lambda p: Path(p))
    policy = MockPolicy(generation_mode=GenerationMode.BATCH, on_build='FORCE')
    files = [Path('file1.hpp.contract'), Path('file2.hpp.contract')]
    jobs = build_jobs(policy, files)
    assert len(jobs) == 2
    assert all(isinstance(j, Job) for j in jobs)
    assert jobs[0].action == 'generate'
    assert jobs[0].input_file == Path('file1.hpp.contract')

def test_execute_job_emit_header(mock_logger, mocker):
    """Test executing a job to emit a helper header."""
    mock_write_file = mocker.patch('cpp_contractgen.core.write_file')
    mock_generate_header = mocker.patch('cpp_contractgen.core.generate_header', return_value='generated_header_code')

    job = Job(
        input_file=None,
        output_file=Path('path/to/header.hpp'),
        action='emit_header',
        policy=MockPolicy(generation_mode=GenerationMode.EMIT_HEADER)
    )
    result = execute_job(job)
    assert result == 0
    mock_generate_header.assert_called_once()
    mock_write_file.assert_called_once_with(Path('path/to/header.hpp').resolve(), 'generated_header_code')

def test_execute_job_generate_missing(mock_logger, mocker):
    """Test generating a file that doesn't exist."""
    mocker.patch('cpp_contractgen.core.file_exists', return_value=False)
     # Save the mock object for later assertion
    mock_write_file = mocker.patch('cpp_contractgen.core.write_file')
    mocker.patch('cpp_contractgen.core.parse_contract')
    mocker.patch('cpp_contractgen.core.hash_file')
    mocker.patch('cpp_contractgen.core.generate_contract')
    mocker.patch('cpp_contractgen.core.resolve_file', side_effect=lambda p: Path(p))
    
    job = Job(
        input_file=Path('path/to/contract.hpp.contract'),
        output_file=Path('path/to/contract.contract.hpp'),
        action='generate',
        policy=MockPolicy(on_build=OnBuildPolicy.GENERATE_MISSING, use_std_out=False)
    )
    result = execute_job(job)
    assert result == 0
    mock_write_file.assert_called_once()

def test_execute_job_check_diff_match(mock_logger, mocker):
    """Test check-diff when hashes match."""
    mocker.patch('cpp_contractgen.core.file_exists', return_value=True)
    mocker.patch('cpp_contractgen.core.hash_file', return_value='test_hash')
    mocker.patch('cpp_contractgen.core.parse_contract')
    mocker.patch('cpp_contractgen.core.generate_contract')
    mocker.patch('cpp_contractgen.core.read_file_text')
    mocker.patch('cpp_contractgen.core.extract_hash_from_text', return_value='test_hash')
    
    job = Job(
        input_file=Path('path/to/contract.hpp.contract'),
        output_file=Path('path/to/exists.contract.hpp'),
        action='check',
        policy=MockPolicy(on_build='CHECK_DIFF')
    )
    result = execute_job(job)
    assert result == 0

def test_execute_job_check_diff_mismatch(mock_logger, mocker):
    """Test check-diff when hashes mismatch."""
    mocker.patch('cpp_contractgen.core.file_exists', return_value=True)
    mocker.patch('cpp_contractgen.core.hash_file', return_value='test_hash')
    mocker.patch('cpp_contractgen.core.parse_contract')
    mocker.patch('cpp_contractgen.core.generate_contract')
    mocker.patch('cpp_contractgen.core.read_file_text')
    mocker.patch('cpp_contractgen.core.extract_hash_from_text', return_value='mismatched_hash')
    
    job = Job(
        input_file=Path('path/to/contract.hpp.contract'),
        output_file=Path('path/to/exists.contract.hpp'),
        action='check',
        policy=MockPolicy(on_build='CHECK_DIFF')
    )
    result = execute_job(job)
    assert result == 1

def test_execute_job_handles_missing_input_file(mock_logger, mocker):
    """Test that a job with a missing input file raises a FileNotFoundError."""
    mocker.patch('cpp_contractgen.core.resolve_file', return_value=None)

    job = Job(
        input_file=None,
        output_file=Path('path/to/output.hpp'),
        action='generate',
        policy=MockPolicy(on_build='FORCE')
    )
    with pytest.raises(FileNotFoundError):
        execute_job(job)

def test_build_and_execute_policy_success(mock_logger, mocker):
    """Test a full run with all jobs succeeding."""
    mocker.patch('cpp_contractgen.core.discover_files', return_value=[Path('file1.hpp.contract')])
    mocker.patch('cpp_contractgen.core.build_jobs', return_value=[
        Job(Path('file1.hpp.contract'), Path('file1.contract.hpp'), 'generate', MagicMock())
    ])
    mocker.patch('cpp_contractgen.core.execute_job', return_value=0)

    policy = MockPolicy(
        generation_mode=GenerationMode.BATCH,
        search_dirs=['src'],
        on_build=OnBuildPolicy.GENERATE_MISSING
    )
    result = build_and_execute_policy(policy, MagicMock())
    assert result == 0

def test_build_and_execute_policy_failure(mock_logger, mocker):
    """Test a full run where one job returns a failure code."""
    mocker.patch('cpp_contractgen.core.discover_files', return_value=[Path('exists.hpp.contract')])
    mocker.patch('cpp_contractgen.core.build_jobs', return_value=[
        Job(Path('exists.hpp.contract'), Path('exists.contract.hpp'), 'check', MagicMock())
    ])
    mocker.patch('cpp_contractgen.core.execute_job', return_value=1)

    policy = MockPolicy(
        generation_mode=GenerationMode.BATCH,
        search_dirs=['src'],
        on_build=OnBuildPolicy.CHECK_DIFF
    )
    result = build_and_execute_policy(policy, MagicMock())
    assert result == 1
