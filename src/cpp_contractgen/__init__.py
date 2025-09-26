from enum import IntEnum, unique

@unique
class ExitCode(IntEnum):
    SUCCESS = 0
    ONE_MISMATCH = 1
    MULTIPLE_MISMATCHES = 2
    BAD_ARGS = 10
    CONFIG_ERROR = 11
    IO_ERROR = 12
    PARSE_ERROR = 13
    FILE_EXISTS_ERROR = 14
    FILE_NOT_FOUND_ERROR = 15
    INTERNAL_ERROR = 99

__version__ = "0.1.0"
__program_name__ = "cpp_contractgen"