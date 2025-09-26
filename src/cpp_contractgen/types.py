from dataclasses import dataclass, field
from typing import Optional, Dict, List
from pathlib import Path
from enum import Enum

# === Data Models ===
@dataclass
class BuildPolicy:
    onBuild: str
    diffAction: Optional[str] = None


@dataclass
class ContractOverride:
    input: str
    output: Optional[str] = None
    policy: Optional[BuildPolicy] = None
    aliases: Dict[str, str] = field(default_factory=dict)


@dataclass
class Config:
    searchDirs: List[str] = field(default_factory=list)
    outDir: Optional[str] = None
    embedContract: bool = True
    emitHeader: Optional[str] = None
    buildPolicy: Dict[str, BuildPolicy] = field(default_factory=dict)
    contracts: List[ContractOverride] = field(default_factory=list)

    # Metadata
    fileFound: bool = False
    filePath: Optional[Path] = None

class BuildMode(str, Enum):
    DEBUG = "debug"
    RELEASE = "release"


class DiffAction(str, Enum):
    WARN = "warn"
    ERROR = "error"


class OnBuildPolicy(str, Enum):
    NONE = "none"
    GENERATE_MISSING = "generate_missing"
    OVERWRITE = "overwrite"
    FORCE = "force"
    CHECK_DIFF = "check_diff"
    DETAIL_DIFF = "detail_diff"   # ← added because you mentioned it


class GenerationMode(str, Enum):
    EMIT_HEADER = "emit_header"
    SINGLE_FILE = "single_file"
    BATCH = "batch"



