import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from .types import Config, ContractOverride, BuildPolicy

# TODO: Enforce JSON schema eventually when the schema is locked
# try:
#     import jsonschema
# except ImportError:
#     jsonschema = None


# === Config Parsing ===

def _parse_config_data(data: dict) -> Config:
    """Internal function to parse a raw dict into a Config object."""
    # Build policies
    build_policy = {}
    for key in ("debug", "release"):
        if key in data.get("buildPolicy", {}):
            bp = data["buildPolicy"][key]
            build_policy[key] = BuildPolicy(
                onBuild=bp["onBuild"],
                diffAction=bp.get("diffAction")
            )
            
    # Contracts
    contracts = []
    for c in data.get("contracts", []):
        pol = None
        if "policy" in c:
            pol = BuildPolicy(
                onBuild=c["policy"]["onBuild"],
                diffAction=c["policy"].get("diffAction")
            )
        contracts.append(
            ContractOverride(
                input=c["input"],
                output=c.get("output"),
                policy=pol,
                aliases=c.get("aliases", {})
            )
        )
    
    return Config(
        searchDirs=data.get("searchDirs", []),
        outDir=data.get("outDir"),
        embedContract=data.get("embedContract", True),
        emitHeader=data.get("emitHeader"),
        buildPolicy=build_policy,
        contracts=contracts,
        fileFound=True
    )

# === Loader ===

def load_config(path: str) -> Config:
    """Load a Config object from a JSON file at the given path."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _parse_config_data(data)

def load_config_from_text(text: str) -> Config:
    """Load a Config object from a JSON-encoded string."""
    data = json.loads(text)
    return _parse_config_data(data)

def generate_default_config_file(path: Path):
    """
    Create a default cpp_contractgen.json config file at the given path.

    Args:
        path (Path): Either a directory (file will be created inside)
                     or a file path (must end with .json).
    """
    # If a directory is given, place config file inside
    if path.is_dir():
        config_path = path / "cpp_contractgen.json"
    else:
        config_path = path

    # Default configuration content
    default_config = {
        "searchDirs": ["./include", "./src"],
        "outDir": "./build/contracts",
        "embedContract": True,
        "emitHeader": None,  # or "./include" if user wants a default
        "buildPolicy": {
            "debug": {
                "onBuild": "check_diff",
                "diffAction": "warn"
            },
            "release": {
                "onBuild": "generate_missing",
                "diffAction": "error"
            }
        },
        "contracts": [
            {
                "input": "examples/MyContract.hpp.contract",
                "output": None,
                "policy": {
                    "onBuild": "force",
                    "diffAction": "warn"
                },
                "aliases": {}
            }
        ]
    }

    return json.dumps(default_config, indent=4)