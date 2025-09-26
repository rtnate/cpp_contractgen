import os
import sys
from .parser import Contract
# from jinja2 import Environment, FileSystemLoader

# def generate_contract(contract, outfile):
#     from jinja2 import Environment, FileSystemLoader
#     import pathlib

#     template_dir = pathlib.Path(__file__).parent.parent.parent / "templates"
#     env = Environment(
#         loader=FileSystemLoader(str(template_dir)),
#         trim_blocks=True,
#         lstrip_blocks=True,
#     )
#     template = env.get_template("contract.hpp.j2")
#     rendered = template.render(contract=contract)

#     if outfile:
#     # Ensure parent dir exists, not "outfile" itself
#         outfile = pathlib.Path(outfile)
#         outfile.parent.mkdir(parents=True, exist_ok=True)

#         # Write the file
#         outfile.write_text(rendered)
#     return rendered

from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# Setup Jinja2 environment
env = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent.parent.parent / "templates")),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)

def generate_contract(contract: Contract, contract_hash: str = "", embed: bool = True):
    template = env.get_template("contract.hpp.j2")
    rendered = template.render(
        contract=contract,
        contract_hash=contract_hash,
        embed_contract=embed
    )
    return rendered

