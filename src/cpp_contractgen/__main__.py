from .cli import run_cli
from cpp_contractgen import ExitCode
import sys
import logging
from .errors import ArgParseError, ConfigError, ParseError

if __name__ == "__main__":
    run_cli()
    # try:
    #     exit_code = run_cli()
    #     sys.exit(exit_code)
    # except ArgParseError as e:
    #     logging.error("Argument error: %s", e)
    #     sys.exit(ExitCode.BAD_ARGS)
    # except ConfigError as e:
    #     logging.error("Configuration error: %s", e)
    #     sys.exit(ExitCode.CONFIG_ERROR)
    # except ParseError as e:
    #     logging.error("Parse error: %s", e)
    #     sys.exit(ExitCode.PARSE_ERROR)
    # except FileExistsError as e:
    #     logging.error("File Exists error: %s", e)
    #     sys.exit(ExitCode.FILE_EXISTS_ERROR)
    # except Exception as e:
    #     # Only show stack trace if verbose mode is on
    #     log = logging.getLogger()
    #     logLevel = log.getEffectiveLevel()
    #     if logLevel <= logging.DEBUG:
    #         logging.critical("Unexpected error", exc_info=True)
    #     else:
    #         logging.critical("Unexpected error: %s", e)
    #     sys.exit(ExitCode.INTERNAL_ERROR)
