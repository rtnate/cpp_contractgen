import re
import os
from dataclasses import dataclass
from typing import List

@dataclass
class Method:
    ret: str
    name: str
    args: str
    const: bool = False

@dataclass
class Contract:
    source: str
    name: str
    methods: List[Method]
    preamble: str
    postamble: str

def parse_contract(path: str) -> Contract:
    with open(path) as f:
        text = f.read()

    lines = [l.rstrip() for l in text.splitlines()]

    in_contract = False
    saw_marker = False
    contract_name = None
    methods: List[Method] = []
    preamble_lines: List[str] = []
    postamble_lines: List[str] = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith("#include <cpp_contractgen>"):
            saw_marker = True
            # Reset preamble to only what comes *after* the marker
            preamble_lines = []
            continue

        if stripped.startswith("define_contract"):
            if not saw_marker:
                raise SyntaxError(
                    f"{path}:{i+1}: found define_contract before #include <cpp_contractgen>"
                )
            in_contract = True
            contract_name = stripped.split()[1]
            continue

        if in_contract:
            if stripped.startswith("};"):
                in_contract = False
                continue

            if "(" in stripped and stripped.endswith(";"):
                m = re.match(r'(\w[\w\s\*&:<>]*)\s+(\w+)\(([^)]*)\)(.*);', stripped)
                if not m:
                    continue
                ret, mname, args, suffix = m.groups()
                methods.append(Method(
                    ret=ret.strip(),
                    name=mname.strip(),
                    args=args.strip(),
                    const="const" in suffix
                ))
        else:
            if contract_name is not None:
                # after contract closing
                postamble_lines.append(line)
            else:
                preamble_lines.append(line)

    if not saw_marker:
        raise SyntaxError(
            f"{path}: missing required '#include <cpp_contractgen>' marker"
        )

    if not contract_name:
        raise SyntaxError(
            f"{path}: missing define_contract block"
        )

    return Contract(
        source=os.path.basename(path),
        name=contract_name,
        methods=methods,
        preamble="\n".join(preamble_lines),
        postamble="\n".join(postamble_lines),
    )
