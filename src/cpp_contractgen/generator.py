import os
from jinja2 import Environment, FileSystemLoader

def generate_contract(contract, outfile):
    from jinja2 import Environment, FileSystemLoader
    import pathlib

    template_dir = pathlib.Path(__file__).parent.parent.parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("contract.hpp.j2")
    rendered = template.render(contract=contract)

    # Ensure parent dir exists, not "outfile" itself
    outfile = pathlib.Path(outfile)
    outfile.parent.mkdir(parents=True, exist_ok=True)

    # Write the file
    outfile.write_text(rendered)