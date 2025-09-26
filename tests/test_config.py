import pytest
from dataclasses import dataclass, field
from unittest.mock import MagicMock
from pathlib import Path
from cpp_contractgen import policy as policy_module
from cpp_contractgen.config import Config, ContractOverride, BuildPolicy
from cpp_contractgen.errors import ArgParseError
from cpp_contractgen.types import BuildMode, OnBuildPolicy, DiffAction, GenerationMode
from copy import deepcopy

# Mock Arg object for testing
@dataclass
class MockArgs:
    o: bool = False
    force: bool = False
    mode: str = ""
    diff: bool = False
    check: bool = False
    overwrite: bool = False
    search: list = field(default_factory=list)
    outdir: str = ""
    outfile: str = ""
    contract: str = ""
    debug: bool = False
    release: bool = False
    embed_contract: bool = None
    emit_header: bool = False

# Mock Config object for testing
@dataclass
class MockConfig:
    fileFound: bool = False
    filePath: Path = None
    buildPolicy: dict = field(default_factory=dict)
    searchDirs: list = field(default_factory=list)
    outDir: str = ""
    emitHeader: str = ""
    embedContract: bool = True
    contracts: list = field(default_factory=list)

@pytest.fixture
def base_args():
    return MockArgs()

@pytest.fixture
def base_config():
    return MockConfig()

# --- Test from_config ---

def test_from_config_default_behavior(base_config):
    """Test that from_config returns a default policy with no config."""
    p = policy_module.Policy.from_config()
    assert p.build_mode == BuildMode.DEBUG
    assert p.on_build == OnBuildPolicy.GENERATE_MISSING
    assert p.diff_action == DiffAction.WARN
    assert p.search_dirs == []

def test_from_config_with_debug_policy(base_config):
    """Test that from_config loads the correct debug policy."""
    base_config.buildPolicy["debug"] = BuildPolicy(onBuild="check_diff", diffAction="error")
    p = policy_module.Policy.from_config(config=base_config, build_mode=BuildMode.DEBUG)
    assert p.on_build == OnBuildPolicy.CHECK_DIFF
    assert p.diff_action == DiffAction.ERROR
    
def test_from_config_with_release_policy(base_config):
    """Test that from_config loads the correct release policy."""
    base_config.buildPolicy["release"] = BuildPolicy(onBuild="overwrite", diffAction="warn")
    p = policy_module.Policy.from_config(config=base_config, build_mode=BuildMode.RELEASE)
    assert p.on_build == OnBuildPolicy.OVERWRITE
    assert p.diff_action == DiffAction.WARN

def test_from_config_with_filesystem_options(base_config):
    """Test that from_config correctly sets filesystem-related properties."""
    base_config.searchDirs = ["src", "contracts"]
    base_config.outDir = "build"
    base_config.embedContract = False
    p = policy_module.Policy.from_config(config=base_config)
    assert p.search_dirs == ["src", "contracts"]
    assert p.out_dir == "build"
    assert p.embed_contract is False
    
# --- Test apply_args ---

def test_apply_args_on_build_overrides(base_args):
    """Test that CLI flags for OnBuildPolicy override the policy."""
    base_policy = policy_module.Policy(on_build=OnBuildPolicy.GENERATE_MISSING)
    
    base_args.diff = True
    p = policy_module.Policy.apply_args(base_policy, base_args)
    assert p.on_build == OnBuildPolicy.DETAIL_DIFF

    base_args.diff = False
    base_args.check = True
    p = policy_module.Policy.apply_args(base_policy, base_args)
    assert p.on_build == OnBuildPolicy.CHECK_DIFF
    
    base_args.check = False
    base_args.overwrite = True
    p = policy_module.Policy.apply_args(base_policy, base_args)
    assert p.on_build == OnBuildPolicy.OVERWRITE

def test_apply_args_filesystem_overrides(base_args, tmp_path):
    """Test that CLI file path arguments override policy values."""
    base_policy = policy_module.Policy(
        search_dirs=["config-src"], out_dir="config-out", out_file="config-file.hpp"
    )
    cli_search = ["cli-src"]
    cli_outdir = "cli-outdir"
    cli_outfile = "cli-outfile.hpp"
    
    base_args.search = cli_search
    base_args.outdir = cli_outdir
    base_args.outfile = cli_outfile
    
    p = policy_module.Policy.apply_args(base_policy, base_args)
    assert p.search_dirs == cli_search
    assert p.out_dir == cli_outdir
    assert p.out_file == cli_outfile

def test_apply_args_sticky_flags(base_args):
    """Test that sticky flags (force, stdout) are set correctly."""
    base_policy = policy_module.Policy()
    
    base_args.o = True
    base_args.force = True
    
    p = policy_module.Policy.apply_args(base_policy, base_args)
    assert p.use_std_out is True
    assert p.force_flag is True

# --- Test from_args_and_config (Orchestrator) ---

def test_full_orchestration_cli_precedence(base_args, base_config):
    """Test the full flow with CLI args overriding config."""
    base_args.mode = "release"
    base_args.outdir = "cli-build"
    base_args.overwrite = True
    
    base_config.buildPolicy["release"] = BuildPolicy(onBuild="check_diff", diffAction="error")
    base_config.outDir = "config-build"

    p = policy_module.Policy.from_args_and_config(base_args, base_config)
    
    assert p.build_mode == BuildMode.RELEASE
    assert p.on_build == OnBuildPolicy.OVERWRITE
    assert p.diff_action == DiffAction.ERROR
    assert p.out_dir == "cli-build"

def test_full_orchestration_generation_modes(base_args, base_config, tmp_path):
    """Test that generation modes are correctly determined."""
    # Test SINGLE_FILE mode
    base_args.contract = "my-file.contract"
    p = policy_module.Policy.from_args_and_config(base_args, base_config)
    assert p.generation_mode == GenerationMode.SINGLE_FILE
    assert p.in_file == "my-file.contract"

    # Test BATCH mode
    base_args.contract = ""
    p = policy_module.Policy.from_args_and_config(base_args, base_config)
    assert p.generation_mode == GenerationMode.BATCH
    
    # Test EMIT_HEADER mode with no path
    base_args.emit_header = True
    base_args.outdir = "some/dir"
    p = policy_module.Policy.from_args_and_config(base_args, base_config)
    assert p.generation_mode == GenerationMode.EMIT_HEADER
    assert p.emit_header == Path("some/dir") / "cpp_contractgen"

    # Test EMIT_HEADER mode with a path
    base_args.emit_header = "lib/path"
    p = policy_module.Policy.from_args_and_config(base_args, base_config)
    assert p.generation_mode == GenerationMode.EMIT_HEADER
    assert p.emit_header == Path("lib/path") / "cpp_contractgen"

def test_full_orchestration_mutually_exclusive_args(base_args, base_config):
    """Test that mutually exclusive args raise an error."""
    base_args.contract = "test.contract"
    base_args.search = ["src"]
    with pytest.raises(ArgParseError):
        policy_module.Policy.from_args_and_config(base_args, base_config)

# --- Test get_policy_for_file with resolved paths ---

def test_get_policy_for_file_with_resolved_override(base_config, tmp_path):
    """Test that get_policy_for_file correctly applies a resolved override."""
    # Setup
    file = tmp_path / "contracts/test.hpp.meta"
    file.parent.mkdir()
    file.touch()

    # Create policy with a resolved override
    override_path_str = str(file.resolve())
    base_config.contracts = [
        ContractOverride(input=override_path_str, output="build/test.gen.hpp")
    ]
    p = policy_module.Policy.from_config(config=base_config)

    # Test
    file_policy = p.get_policy_for_file(file)

    assert file_policy.out_file == "build/test.gen.hpp"
    assert file_policy.input == override_path_str

def test_get_policy_for_file_no_resolved_override(base_config, tmp_path):
    """Test that no override is applied if paths don't match."""
    # Setup
    file = tmp_path / "contracts/unlisted.hpp.meta"
    file.parent.mkdir()
    file.touch()
    
    base_config.contracts = [
        ContractOverride(input="contracts/other.hpp.meta", output="build/other.gen.hpp")
    ]
    p = policy_module.Policy.from_config(config=base_config)
    
    # Test
    file_policy = p.get_policy_for_file(file)
    assert file_policy.out_file is None