# policy.py
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Union
from enum import Enum
from .config import Config, ContractOverride
from .errors import ArgParseError
from copy import deepcopy
from pathlib import Path
from .types import BuildMode, BuildPolicy, OnBuildPolicy, DiffAction, GenerationMode
from .files import resolve_file


@dataclass
class Policy:
    # Core
    build_mode: BuildMode = BuildMode.DEBUG
    on_build: OnBuildPolicy = OnBuildPolicy.CHECK_DIFF
    diff_action: DiffAction = DiffAction.WARN
    generation_mode: GenerationMode = GenerationMode.BATCH

    # Filesystem
    search_dirs: List[str] = field(default_factory=list)
    out_dir: Optional[str] = None
    emit_header: Optional[str] = None
    out_file: Optional[str] = None
    in_file: Optional[str] = None
    # Per-contract context
    input: Optional[str] = None
    aliases: Dict[str, str] = field(default_factory=dict)
    # Embedding behavior
    embed_contract: bool = True
    # To Std Out Sticky Flag
    use_std_out: bool = False 
    # Force Sticky Flag 
    force_flag: bool = False
    # Temporary Directory - Provided For Future Use If Necessary
    temp_directory: Optional[str] = None
    # Attached overrides
    contract_overrides: List[ContractOverride] = field(default_factory=list)

    # ------------------------------------------------------------------

    @classmethod
    def from_config(
        cls, config: Optional[Config] = None, 
        build_mode: BuildMode = BuildMode.DEBUG,
        generation_mode: GenerationMode = GenerationMode.BATCH
    ) -> "Policy":
        """
        Create a base Policy object from a Config object.
        Uses the specified build_mode to select the correct policy.
        """
        if config is None:
            config = Config(fileFound=False, filePath=None)
        
        config_policy = config.buildPolicy.get(build_mode.value)

        on_build = (
            OnBuildPolicy(config_policy.onBuild)
            if config_policy and config_policy.onBuild
            else OnBuildPolicy.GENERATE_MISSING
        )
        diff_action = (
            DiffAction(config_policy.diffAction)
            if config_policy and config_policy.diffAction
            else DiffAction.WARN
        )

        return cls(
            build_mode=build_mode,
            on_build=on_build,
            diff_action=diff_action,
            generation_mode=generation_mode,
            search_dirs=config.searchDirs or [],
            out_dir=config.outDir,
            emit_header=config.emitHeader, # This is now the string value
            embed_contract=config.embedContract,
            contract_overrides=deepcopy(config.contracts) or []
        )

    @classmethod
    def from_args_and_config(cls, args, config: Config) -> "Policy":
        """Orchestrates the merging of CLI args and Config."""
        
        # 1. Determine build mode from CLI flags (highest precedence)
        if args.mode:
            try:
                build_mode = BuildMode(args.mode.lower())
            except ValueError:
                raise ArgParseError("--mode must be debug or release")
        elif getattr(args, "debug", False):
            build_mode = BuildMode.DEBUG
        elif getattr(args, "release", False):
            build_mode = BuildMode.RELEASE
        else:
            build_mode = BuildMode.DEBUG

        # 2. Determine generation mode and emit path
        emit_path = None
        if args.contract and args.search:
            raise ArgParseError("Cannot use --contract and --search together")
        if args.emit_header:
            generation_mode = GenerationMode.EMIT_HEADER
            if args.emit_header is True:
                 emit_path = Path(args.outdir or ".") / "cpp_contractgen"
            else:
                 emit_path = Path(args.emit_header) / "cpp_contractgen"
        elif args.contract:
            generation_mode = GenerationMode.SINGLE_FILE
        else:
            generation_mode = GenerationMode.BATCH

        # 3. Create the baseline policy from the config, with determined fundamental modes
        base_policy = cls.from_config(config=config, build_mode=build_mode, generation_mode=generation_mode)
        base_policy.emit_header = emit_path  # Set here for consistency

        # 4. Apply the remaining CLI arguments to the baseline policy
        final_policy = cls.apply_args(base_policy, args)

        return final_policy
    
    @classmethod
    def apply_args(cls, policy: "Policy", args) -> "Policy":
        """
        Apply CLI arguments to an existing Policy object.
        """
        p = deepcopy(policy)

        # OnBuild and DiffAction overrides (CLI flags override any policy from config)
        if getattr(args, "diff", False):
            p.on_build = OnBuildPolicy.DETAIL_DIFF
        elif getattr(args, "check", False):
            p.on_build = OnBuildPolicy.CHECK_DIFF
        elif getattr(args, "overwrite", False):
            p.on_build = OnBuildPolicy.OVERWRITE
        
        # Filesystem overrides
        p.search_dirs = args.search or p.search_dirs
        p.out_dir = args.outdir or p.out_dir
        p.out_file = args.outfile or p.out_file
        p.in_file = args.contract or p.in_file

        # Embedding override
        if getattr(args, "embed_contract", None) is not None:
            p.embed_contract = args.embed_contract

        # Sticky flags
        p.use_std_out = bool(args.o)
        p.force_flag = bool(args.force)

        return p
    
    # Original method - provided for context and first source of truth
    # @classmethod
    # def from_args_and_config_og(cls, args, config: Config) -> "Policy":
    #     """Merge CLI args and Config into a normalized Policy."""

    #     # === Generation mode ===
    #     if args.contract and args.search:
    #         raise ArgParseError("Cannot use --contract and --search together")

    #     emit_path = None
    #     if args.emit_header:
    #         generation_mode = GenerationMode.EMIT_HEADER
    #         if args.emit_header is True:
    #             # no path given, must rely on --outdir
    #             if args.outfile:
    #                 emit_path = Path(args.outfile)
    #             if args.outdir:
    #                 emit_path = Path(args.outdir) / "cpp_contractgen"
    #             else:
    #                 emit_path = Path("./cpp_contractgen") #use cwd
    #         else:
    #             path = Path(args.emit_header)
    #             emit_path = path / "cpp_contractgen"
    #     elif args.contract:
    #         generation_mode = GenerationMode.SINGLE_FILE
    #     else:
    #         generation_mode = GenerationMode.BATCH

        

    #     # === Build mode ===
    #     if args.mode:
    #         mode_str = args.mode.lower()
    #         if mode_str == "debug":
    #             build_mode = BuildMode.DEBUG
    #         elif mode_str == "release":
    #             build_mode = BuildMode.RELEASE
    #         else:
    #             raise ArgParseError("--mode must be debug or release")
    #     elif getattr(args, "debug", False):
    #         build_mode = BuildMode.DEBUG
    #     elif getattr(args, "release", False):
    #         build_mode = BuildMode.RELEASE
    #     else:
    #         build_mode = BuildMode.DEBUG

    #     # Load build policy from config (per mode)
    #     config_policy = None
    #     if config.buildPolicy and build_mode.value in config.buildPolicy:
    #         config_policy = config.buildPolicy[build_mode.value]

    #     # === OnBuild ===
    #     if getattr(args, "diff", False):
    #         on_build = OnBuildPolicy.DETAIL_DIFF
    #     elif getattr(args, "check", False):
    #         on_build = OnBuildPolicy.CHECK_DIFF
    #     elif getattr(args, "overwrite", False):
    #         on_build = OnBuildPolicy.OVERWRITE
    #     elif config_policy:
    #         on_build = OnBuildPolicy(config_policy.onBuild)
    #     else:
    #         on_build = OnBuildPolicy.GENERATE_MISSING

    #     # === Diff action ===
    #     if config_policy and config_policy.diffAction:
    #         diff_action = DiffAction(config_policy.diffAction)
    #     else:
    #         diff_action = DiffAction.WARN

    #     # === Filesystem options ===
    #     search_dirs = args.search or config.searchDirs or []
    #     out_dir = args.outdir or config.outDir
    #     #emit_header = args.emit_header or config.emitHeader
    #     out_file = args.outfile

    #     # Embed contract option
    #     if getattr(args, "embed_contract", None) is not None:
    #         embed_contract = args.embed_contract
    #     else:
    #         embed_contract = config.embedContract

    #     #Sticky flags 
    #     force_flag = True if args.force else False
    #     use_std_out = True if args.o else False
    #     # === Build final policy ===
    #     return cls(
    #         build_mode=build_mode,
    #         on_build=on_build,
    #         diff_action=diff_action,
    #         generation_mode=generation_mode,
    #         search_dirs=search_dirs,
    #         out_dir=out_dir,
    #         emit_header=emit_path,
    #         out_file=out_file,
    #         in_file = args.contract or None,
    #         embed_contract=embed_contract,
    #         contract_overrides=config.contracts or [],
    #         use_std_out = use_std_out,
    #         force_flag = force_flag
    #     )
    
    def get_policy_for_file(self, file: Path) -> "Policy":
        """
        Return a *new Policy object* customized for this file.
        Looks up overrides by input filename, else uses baseline.
        """
        file_resolved = file.resolve()
        
        for override in self.contract_overrides:
            override_path = Path(override.input).resolve()
            
            if override_path == file_resolved:
                p = deepcopy(self)
                p.input = str(file_resolved)
                if override.output:
                    p.out_file = override.output
                if override.policy:
                    p.on_build = OnBuildPolicy(override.policy.onBuild)
                    if override.policy.diffAction:
                        p.diff_action = DiffAction(override.policy.diffAction)
                if override.aliases:
                    p.aliases = dict(override.aliases)
                return p

        # fallback -> just return a copy of baseline
        p = deepcopy(self)
        p.input = str(file_resolved)
        return p

    def resolve_output_file(cls, in_file: Optional[Union[Path, str]]) -> Optional[Union[Path, str]]:
        if cls.use_std_out:
            return "stdout"
        elif cls.out_file:
            return resolve_file(cls.out_file)
        elif cls.out_dir:
            out_file = Path(cls.out_dir) / in_file.with_suffix("").name
            out_file = out_file.with_suffix(".contract.hpp")
            return resolve_file(out_file)
        else:
            # Default: alongside contract file
            return resolve_file(in_file.with_suffix("").with_suffix(".contract.hpp"))

    def log_properties(self, logLevel: int = logging.INFO):
        """Log all policy properties at debug level."""
        for name, value in self.__dict__.items():
            logging.log(logLevel, "Policy.%s = %r", name, value)

