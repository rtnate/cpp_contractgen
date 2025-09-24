class ContractGenError(Exception):
    """Base exception for cpp_contractgen."""


class ArgParseError(ContractGenError):
    """Raised when CLI argument parsing fails."""

6
class ConfigError(ContractGenError):
    """Raised when configuration loading/validation fails."""


class ParseError(ContractGenError):
    """Raised when a contract file cannot be parsed."""

class PromptError(Exception):
    pass

class FileExistsError(ContractGenError):
    """Raised when a file already exists that shouldnt"""