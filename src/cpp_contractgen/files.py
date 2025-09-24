# cpp_contractgen/files.py

import sys
import hashlib
import re
import logging
from pathlib import Path
from typing import List, Optional, Union, TextIO
from contextlib import contextmanager

PathLike = Union[str, Path]
CONTRACT_EXT = ".hpp.contract"
SPECIAL_STREAMS = {"-", "stdout", "stderr"}

def file_exists(file: Optional[PathLike]) -> bool:
    if not file or str(file) in SPECIAL_STREAMS:
        return False
    return Path(file).exists()
    
def resolve_file(file: Optional[PathLike], strict=False) -> Optional[Path]:
    if not file:
        if strict:
            raise FileNotFoundError("No file path provided.")
        return None

    if str(file) in SPECIAL_STREAMS:
        return file  # Return the special string, as it's not a real path

    path = Path(file)
    if strict and not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path.resolve(strict=False) # Use resolve to get absolute path
    
def find_files(search_dirs: List[PathLike]) -> List[Path]:
    """Find all *.hpp.contract files in the given directories or single files."""
    results = []
    for d in search_dirs:
        p = Path(d)
        if p.is_dir():
            matches = list(p.glob(f"*{CONTRACT_EXT}"))
            if matches:
                logging.debug("Found %d contract(s) in %s", len(matches), p)
                results.extend(matches)
            else:
                logging.debug("No contracts found in %s", p)
        elif p.is_file() and p.suffix == ".contract":
            logging.debug("Adding single contract file: %s", p)
            results.append(p)
        else:
            logging.warning("Skipping invalid path: %s", p)

    return [f.resolve() for f in results]


def find_file(contract: PathLike) -> Optional[Path]:
    """Find a single contract file, or return None if missing."""
    p = Path(contract)
    if p.exists() and p.is_file():
        logging.debug("Discovered single contract file: %s", p)
        return p.resolve()
    else:
        logging.error("Contract file not found: %s", p)
        return None

def open_output(target: Optional[PathLike], use_stderr: bool = False) -> TextIO:
    """
    Open a writable output stream:
    - None → stdout (or stderr if requested)
    - "-" → stdout
    - "stdout" → stdout
    - "stderr" → stderr
    - Path/str → real file
    """
    if target is None:
        return sys.stderr if use_stderr else sys.stdout
    logging.debug("Write Target: %s", target)
    t = str(target).lower()
    if t in ("-", "stdout"):
        return sys.stdout
    if t == "stderr":
        return sys.stderr

    return open(target, "w", encoding="utf-8")

@contextmanager
def open_output(target: Optional[PathLike], use_stderr: bool = False) -> TextIO:
    """
    Open a writable output stream as a context manager.
    
    Args:
        target: A file path, '-' for stdout, or None/Path object.
        use_stderr: If True, uses stderr instead of stdout for default output.
    """
    if target is None:
        yield sys.stderr if use_stderr else sys.stdout
    elif isinstance(target, str):
        target_str = target.lower()
        if target_str in ("-", "stdout"):
            yield sys.stdout
        elif target_str == "stderr":
            yield sys.stderr
        else:
            f = open(target, "w", encoding="utf-8")
            try:
                yield f
            finally:
                f.close()
    elif isinstance(target, Path):
        f = open(target, "w", encoding="utf-8")
        try:
            yield f
        finally:
            f.close()
    else:
        raise TypeError(f"Invalid type for target: {type(target)}")

def write_file(target: Optional[PathLike], text: str, use_stderr: bool = False):
    """
    Write text to the given output destination.
    Handles stdout, stderr, or files transparently.
    """
    with open_output(target, use_stderr=use_stderr) as f:
        f.write(text)

def read_file_text(target: Optional[PathLike], strict: bool = False) -> str:
    if file_exists(target):
        return Path(target).read_text(encoding="utf-8")

    if strict:
        raise FileNotFoundError(f"File: {target} does not exist")
    else:
        return "" 


def hash_string(text: str) -> str:
    """Return a short hex digest of a string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def hash_file(path: Path) -> str:
    """Return a short hex digest of a file."""
    text = read_file_text(path, strict=True)
    return hash_string(text)

def extract_hash_from_text(text: str) -> str | None:
    """Find an embedded hash in a generated file string."""
    m = re.search(r"// cpp_contractgen:hash=([0-9a-f]+)", text)
    return m.group(1) if m else None
 
def extract_hash_from_file(path: Path|str) -> str | None:
    """Find an embedded hash in a generated file."""
    text = read_file_text(path, strict=True)
    return extract_hash_from_text(text)

