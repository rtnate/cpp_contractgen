import argparse
import glob
import os
import pathlib
import logging
import sys
from .parser import parse_contract
from .generator import generate_contract
from cpp_contractgen import __version__, __program_name__, ExitCode
from .errors import ArgParseError
from .config import load_config, generate_default_config_file
from .core import *
from .user_confirm import ConfirmManager

# PARSE ARGUMENTS
def parse_args():
    try:
        parser = argparse.ArgumentParser(
            prog=__program_name__,
            description="Generate and validate C++ contract wrappers from .hpp.contract files"
        )

        # Global switches
        parser.add_argument("--version", action="version", version=f"{__program_name__} {__version__}")

        parser.add_argument("--mode", choices=["debug", "release"], default="debug",
                            help="Select build policy mode (default: debug)")
        parser.add_argument("--debug", action="store_const", dest="mode", const="debug")
        parser.add_argument("--release", action="store_const", dest="mode", const="release")

        parser.add_argument("-y", "--yes", action="store_true", help="Assume yes to prompts")
        parser.add_argument("--no", action="store_true", help="Assume no to prompts")
        parser.add_argument("-q", "--quiet", action="store_true", help="Suppress non-error output")
        parser.add_argument("-v", "--verbose", action="store_true", help="Increase logging verbosity")

        parser.add_argument("-f", "--force", action="store_true", help="When specified with --overwrite, forces overwriting of headers")
        parser.add_argument("--check", action="store_true", help="Verify headers match contracts (exit code only)")
        parser.add_argument("--diff", action="store_true", help="Show diff between headers and contracts")
        parser.add_argument("--overwrite", action="store_true", help="Overwrite existing headers")
        parser.add_argument("--config", help="Path to cpp_contractgen.json to use for build configuration")
        # Emit cpp_contractgen.hpp helper
        # Emit cpp_contractgen.hpp helper
        parser.add_argument(
            "--emit-header",
            nargs="?",                # zero or one value
            const=True,               # value if given without an arg
            metavar="PATH",
            help="Emit cpp_contractgen helper header. "
                "If PATH is supplied, directory, generates cpp_contractgen inside the provdied directory"
                "If omitted with --outdir, defaults to <outdir>/cpp_contractgen"
                "If omitted with --outfile, generates to <outfile>"
        )


        # Single file mode
        parser.add_argument("--contract", help="Single contract file to process")
        parser.add_argument("--outfile", help="Explicit output file (single file mode)")
        parser.add_argument("-o", action="store_true",
                            help="Write to stdout (single file mode or emit-header)")
        parser.add_argument(
            "--embed-contract",
            dest="embed_contract",
            action="store_true",
            help="Embed full contract source into generated header"
        )
        parser.add_argument(
            "--no-embed-contract",
            dest="embed_contract",
            action="store_false",
            help="Do not embed full contract source"
        )
        parser.set_defaults(embed_contract=None)  # So config decides if CLI not set

        # Batch mode
        parser.add_argument("--search", nargs="+", help="Search directory or glob for .hpp.contract files")
        parser.add_argument("--outdir", help="Output directory for generated headers")

        # Special Init Mode 
        parser.add_argument("--init",  action="store_true", help="Generates cpp_contractgen.json and exit")
        return parser.parse_args()
    except Exception as e:
        raise ArgParseError(e)

#Setup Logging
def setup_logging(is_verbose, is_quiet):
  level = logging.INFO
  if is_verbose:
    level = logging.DEBUG
  elif is_quiet:
    level = logging.ERROR
  logging.basicConfig(level=level, format="[%(levelname)s]: %(message)s")

def load_config_file_or_default(args):
    configPath = args.config or Path.cwd()
    logging.debug("Attempting to load config file from path: `%s`" %(configPath))
    config = load_config(configPath)
    if (config.fileFound):
        logging.debug("Using configuration file %s" %(config.filePath))
    else:
        logging.debug("Configuration file not found, using default configuration")
    return config

def create_confirm_manager(args):
    return ConfirmManager(args.yes, args.no, sys.stderr)

def output_init_config_file(args, path: PathLike):
    configFile = generate_default_config_file()
    write_file(path, configFile)
    logging.info("Generated cpp_contractgen.json.")

#Run The CLI
def run_cli():
    # First Parse Arguments
    args = parse_args()
    # Then Setup Logging
    setup_logging(args.verbose, args.quiet)
    # If --init: generate the config file and then exit
    if args.init:
        output_init_config_file(args, Path.cwd())
        return ExitCode.SUCCESS
    # Hello Message - May Remove Later
    logging.debug("Running cpp_contractgen...")
    # Load Configuration
    config =load_config_file_or_default(args)
    # Create the policy
    policy = create_policy_from_args_and_config(args, config)
    logging.debug("====== Current Policy ====== ")
    policy.log_properties(logging.DEBUG)
    logging.debug("====== End Policy ========== ")
    # Execute the policy 
    confirmManager = create_confirm_manager(args)
    return build_and_execute_policy(policy, confirmManager)

