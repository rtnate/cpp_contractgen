import argparse
import glob
import os
import pathlib
import logging
import tempfile
import sys
from .parser import parse_contract
from .generator import generate_contract
from cpp_contractgen import __version__, __program_name__, ExitCode
from .errors import ArgParseError, ConfigError, FileExistsError, ParseError, PromptError
from .config import load_config, generate_default_config_file
from .core import *
from .user_confirm import ConfirmManager
from .files import generate_temp_filename

# PARSE ARGUMENTS
def get_arg_parser():
    """
    Defines and returns the main argument parser.
    The primary goal is to have a safe default behavior (use config file)
    and a clear override for single-file mode.
    """
    parser = argparse.ArgumentParser(
        prog=__program_name__,
        description="Generate and validate C++ contract wrappers from .hpp.contract files"
    )

    # --- Global Switches ---
    parser.add_argument("--version", action="version", version=f"{__program_name__} {__version__}")
    parser.add_argument("--mode", choices=["debug", "release"], help="Select build policy mode")
    parser.add_argument("--debug", action="store_const", dest="mode", const="debug")
    parser.add_argument("--release", action="store_const", dest="mode", const="release")
    parser.add_argument("-y", "--yes", action="store_true", help="Assume yes to prompts")
    parser.add_argument("--no", action="store_true", help="Assume no to prompts")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress non-error output")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase logging verbosity")
    parser.add_argument("-f", "--force", action="store_true", help="When specified with --overwrite, forces overwriting of headers")
    
    # --- Action Flags (can be combined with single-file mode or batch mode) ---
    parser.add_argument("--check", action="store_true", help="Verify headers match contracts (exit code only)")
    parser.add_argument("--diff", action="store_true", help="Show diff between headers and contracts")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing headers")
    parser.add_argument("--emit-header", nargs="?", const=True, metavar="PATH",
                        help="Emit cpp_contractgen helper header.")

    # --- Input Mode Selection (Mutually Exclusive) ---
    # You can be in single-file mode OR batch/config mode, but not both.
    input_group = parser.add_mutually_exclusive_group()

    # Single-file mode
    input_group.add_argument(
        "--contract",
        type=argparse.FileType('r', encoding='utf-8'),
        help="Single contract file to process. Use '-' to read from stdin.",
    )

    # Batch/Config mode (default behavior)
    input_group.add_argument("--config", help="Path to cpp_contractgen.json to use for build configuration")
    input_group.add_argument("--search", nargs="+", help="Search directory or glob for .hpp.contract files")

    # --- Output Mode Selection (Mutually Exclusive) ---
    output_group = parser.add_mutually_exclusive_group()
    
    # Output single file (overrides all other output logic)
    output_group.add_argument(
        "-o",
        "--output",
        type=argparse.FileType('w', encoding='utf-8'),
        help="Explicit output file. Writes to stdout if no file is specified.",
    )

    # Output to a directory (for batch mode)
    output_group.add_argument(
        "--outdir",
        help="Output directory for generated headers."
    )
    
    # --- Special Init Mode ---
    parser.add_argument("--init", action="store_true", help="Generates cpp_contractgen.json and exits")
    
    return parser

# Original Arguments Referense
# def parse_args_og():
#     try:
#         parser = argparse.ArgumentParser(
#             prog=__program_name__,
#             description="Generate and validate C++ contract wrappers from .hpp.contract files"
#         )

#         # Global switches
#         parser.add_argument("--version", action="version", version=f"{__program_name__} {__version__}")

#         parser.add_argument("--mode", choices=["debug", "release"], default="debug",
#                             help="Select build policy mode (default: debug)")
#         parser.add_argument("--debug", action="store_const", dest="mode", const="debug")
#         parser.add_argument("--release", action="store_const", dest="mode", const="release")

#         parser.add_argument("-y", "--yes", action="store_true", help="Assume yes to prompts")
#         parser.add_argument("--no", action="store_true", help="Assume no to prompts")
#         parser.add_argument("-q", "--quiet", action="store_true", help="Suppress non-error output")
#         parser.add_argument("-v", "--verbose", action="store_true", help="Increase logging verbosity")

#         parser.add_argument("-f", "--force", action="store_true", help="When specified with --overwrite, forces overwriting of headers")
#         parser.add_argument("--check", action="store_true", help="Verify headers match contracts (exit code only)")
#         parser.add_argument("--diff", action="store_true", help="Show diff between headers and contracts")
#         parser.add_argument("--overwrite", action="store_true", help="Overwrite existing headers")
#         parser.add_argument("--config", help="Path to cpp_contractgen.json to use for build configuration")
#         # Emit cpp_contractgen.hpp helper
#         # Emit cpp_contractgen.hpp helper
#         parser.add_argument(
#             "--emit-header",
#             nargs="?",                # zero or one value
#             const=True,               # value if given without an arg
#             metavar="PATH",
#             help="Emit cpp_contractgen helper header. "
#                 "If PATH is supplied, directory, generates cpp_contractgen inside the provdied directory"
#                 "If omitted with --outdir, defaults to <outdir>/cpp_contractgen"
#                 "If omitted with --outfile, generates to <outfile>"
#         )


#         # Single file mode
#         parser.add_argument("--contract", help="Single contract file to process")
#         parser.add_argument("--outfile", help="Explicit output file (single file mode)")
#         parser.add_argument("-o", action="store_true",
#                             help="Write to stdout (single file mode or emit-header)")
#         parser.add_argument(
#             "--embed-contract",
#             dest="embed_contract",
#             action="store_true",
#             help="Embed full contract source into generated header"
#         )
#         parser.add_argument(
#             "--no-embed-contract",
#             dest="embed_contract",
#             action="store_false",
#             help="Do not embed full contract source"
#         )
#         parser.set_defaults(embed_contract=None)  # So config decides if CLI not set

#         # Batch mode
#         parser.add_argument("--search", nargs="+", help="Search directory or glob for .hpp.contract files")
#         parser.add_argument("--outdir", help="Output directory for generated headers")

#         # Special Init Mode 
#         parser.add_argument("--init",  action="store_true", help="Generates cpp_contractgen.json and exit")
#         return parser.parse_args()
#     except Exception as e:
#         raise ArgParseError(e)

# Helper function to configure logging
def setup_logging(is_verbose, is_quiet):
    level = logging.INFO
    if is_verbose:
        level = logging.DEBUG
    elif is_quiet:
        level = logging.ERROR
    logging.basicConfig(level=level, format="[%(levelname)s]: %(message)s")

def handle_init_mode():
    """Handles --init mode: generates a default config file and exits."""
    configFile = generate_default_config_file()
    write_file(Path.cwd() / "cpp_contractgen.json", configFile)
    logging.info("Generated cpp_contractgen.json.")
    return ExitCode.SUCCESS

# New function that handles the parsing step
def parse_args():
    parser = get_arg_parser()
    try:
        args = parser.parse_args()
        # A check for the --emit-header option, which is a special single-file case
        if args.outdir and args.emit_header:
            # Note: This check is needed because --emit-header is not in an input group
            # If emit-header has a value (a path), it is also a single-file operation
            if args.emit_header is not True:
                raise ArgParseError("Cannot use --outdir with a specific --emit-header path.")
        
        return args
    except argparse.ArgumentError as e:
        # Catch the argparse exception and re-raise it as your custom error
        raise ArgParseError(e) from e
    
def create_temp_input_from_stdin(contract_arg, output_dir):
    """
    Handles --contract if input is stdin (<stdin> or '-')
    and returns a path to a temporary file.
    """
    try:
        content = contract_arg.read()
        contract_arg.seek(0)
        filename = generate_temp_filename(content, ".hpp.contract")
        
        # Use a temporary directory to store the file
        temp_file_path = Path(output_dir) / filename
        
        # Write the content to the file
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logging.debug(f"Wrote stdin content to temporary file: {temp_file_path}")
        return temp_file_path
    except Exception as e:
        raise ArgParseError(f"Failure reading input from stdin: {e}")


def main():
    """Main function to run the CLI application."""
    # Use a temporary directory for all temporary file needs
    with tempfile.TemporaryDirectory() as temp_directory:
        args = parse_args()

        setup_logging(args.verbose, args.quiet)
        logging.debug("Running cpp_contractgen...")

        if args.init:
            return handle_init_mode()
        # Resolve special cases before calling the rest of the application.
        if args.contract and args.contract.name == '<stdin>':
            # Create a temporary file to store the stdin content for later processing
            temp_file_path = create_temp_input_from_stdin(args.contract, temp_directory)
            # Update the args to use the temporary file
            args.contract = temp_file_path

        config_path = Path(args.config) if args.config else Path.cwd()
        logging.debug("Attempting to load config file from path: `%s`" %(config_path))
        config = load_config(config_path)

        if config.fileFound:
            logging.debug(f"Using configuration file {config.filePath}")
        else:
            logging.debug("Configuration file not found, using default configuration")
        
        policy = create_policy_from_args_and_config(args, config)
        policy.temp_directory = temp_directory
        logging.debug("====== Current Policy ====== ")
        policy.log_properties(logging.DEBUG)
        logging.debug("====== End Policy ========== ")
        
        confirm_manager = ConfirmManager(args.yes, args.no, sys.stderr)
        return build_and_execute_policy(policy, confirm_manager)

def run_cli():
    try:
        sys.exit(main())
    except ArgParseError as e:
        logging.error("Argument error: %s", e)
        sys.exit(ExitCode.BAD_ARGS)
    except ConfigError as e:
        logging.error("Configuration error: %s", e)
        sys.exit(ExitCode.CONFIG_ERROR)
    except ParseError as e:
        logging.error("Parse error: %s", e)
        sys.exit(ExitCode.PARSE_ERROR)
    except FileExistsError as e:
        logging.error("File Exists error: %s", e)
        sys.exit(ExitCode.FILE_EXISTS_ERROR)
    except FileNotFoundError as e:
        logging.error(e)
        sys.exit(ExitCode.FILE_NOT_FOUND_ERROR)
    except Exception as e:
        # Only show stack trace if verbose mode is on
        log = logging.getLogger()
        logLevel = log.getEffectiveLevel()
        if logLevel <= logging.DEBUG:
            logging.critical("Unexpected error", exc_info=True)
        else:
            logging.critical("Unexpected error: %s", e)
        sys.exit(ExitCode.INTERNAL_ERROR)

# Run The CLI - ORIGINAL VERSION
# def run_cli_og():
#     # First Parse Arguments
#     args = parse_args()
#     # Then Setup Logging
#     setup_logging(args.verbose, args.quiet)
#     # If --init: generate the config file and then exit
#     if args.init:
#         output_init_config_file(args, Path.cwd())
#         return ExitCode.SUCCESS
#     # Hello Message - May Remove Later
#     logging.debug("Running cpp_contractgen...")
#     # Load Configuration
#     config =load_config_file_or_default(args)
#     # Create the policy
#     policy = create_policy_from_args_and_config(args, config)
#     logging.debug("====== Current Policy ====== ")
#     policy.log_properties(logging.DEBUG)
#     logging.debug("====== End Policy ========== ")
#     # Execute the policy 
#     confirmManager = create_confirm_manager(args)
#     return build_and_execute_policy(policy, confirmManager)

