import argparse
import glob
import os
import pathlib
from .parser import parse_contract
from .generator import generate_contract

DUMMY_HEADER = """\
// cpp_contractgen dummy header
#pragma once

#ifndef CPP_CONTRACTGEN_DEFINED
#define CPP_CONTRACTGEN_DEFINED

#define define_contract struct

#endif // CPP_CONTRACTGEN_DEFINED
"""

def emit_header(outdir: str):
    path = pathlib.Path(outdir) / "cpp_contractgen"
    with open(path, "w") as f:
        f.write(DUMMY_HEADER)
    print(f"[OK] Generated dummy header at {path}")

def main():
    parser = argparse.ArgumentParser(description="Generate C++ contracts from .hpp.contract files")
    parser.add_argument("file", nargs="?", help="Single .hpp.contract file")
    parser.add_argument("--search-dir", help="Directory to search for .hpp.contract files")
    parser.add_argument("--outdir", help="Output directory (optional)")
    parser.add_argument("-r", "--recursive", action="store_true", help="Search recursively")
    parser.add_argument("--emit-header", action="store_true")
    args = parser.parse_args()

    files = []
    if args.emit_header:
        outdir = args.outdir if args.outdir else "."
        emit_header(outdir)
        return
    if args.search_dir:
        pattern = "**/*.hpp.contract" if args.recursive else "*.hpp.contract"
        files = glob.glob(os.path.join(args.search_dir, pattern), recursive=args.recursive)
    elif args.file:
        files = [args.file]
    else:
        parser.error("You must provide either a file or --search-dir")

    if not files:
        print("No contract files found")
        return

    base_search = pathlib.Path(args.search_dir).resolve() if args.search_dir else None

    for f in files:
        infile = pathlib.Path(f).resolve()
        contract = parse_contract(infile)

        if args.outdir:
            outdir = pathlib.Path(args.outdir).resolve()
            if args.search_dir and args.recursive:
                # Mirror relative path under outdir
                relpath = infile.parent.relative_to(base_search)
                outdir = outdir / relpath
            outdir.mkdir(parents=True, exist_ok=True)
            outfile = outdir / (infile.stem.replace(".hpp", "") + ".contract.hpp")
        else:
            # In-place: replace .hpp.contract with .contract.hpp
            outfile = infile.with_suffix("").with_suffix(".contract.hpp")

        generate_contract(contract, outfile)
        print(f"Generated {outfile}")
