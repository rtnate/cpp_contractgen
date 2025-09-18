import re
import os 
from dataclasses import dataclass
from typing import List

@dataclass
class Method:
    ret: str
    name: str
    args: str
    arg_names: List[str]
    arg_types: List[str]
    const: bool = False

@dataclass
class Contract:
    name: str
    methods: List[Method]
    source: str


def parse_contract(path: str) -> Contract:
    with open(path) as f:
        text = f.read()

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    name = None
    methods: List[Method] = []
    for line in lines:
        if line.startswith("define_contract"):
            name = line.split()[1]
        elif "(" in line and line.endswith(";"):
            m = re.match(r'(\w[\w\s\*&:<>]*)\s+(\w+)\(([^)]*)\)(.*);', line)
            if not m:
                continue
            ret, mname, args, suffix = m.groups()
            ret = ret.strip()
            args = args.strip()
            const = "const" in suffix

            arg_names, arg_types = [], []
            if args:
                parts = [a.strip() for a in args.split(",")]
                for p in parts:
                    tokens = p.split()
                    if len(tokens) > 1:
                        arg_types.append(" ".join(tokens[:-1]))
                        arg_names.append(tokens[-1])
                    else:
                        arg_types.append(tokens[0])
                        arg_names.append("")
            method = Method(
                ret=ret,
                name=mname,
                args=args,
                arg_names=arg_names,
                arg_types=arg_types,
                const=const,
            )
            methods.append(method)

    return Contract(
        source=os.path.basename(path),
        name=name,
        methods=methods
    )