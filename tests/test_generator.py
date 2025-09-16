import pathlib
from contractgen import parser, generator

def test_generate_contract(tmp_path):
    contract_file = tmp_path / "MyComb.hpp.contract"
    contract_file.write_text("""
define_contract MyComb {
    bool setDelaySamples(uint32_t d);
};
""")
    contract = parser.parse_contract(contract_file)
    outfile = tmp_path / "MyComb.contract.hpp"
    generator.generate_contract(contract, outfile)

    text = outfile.read_text()
    assert "struct MyComb_Traits" in text
    assert "setDelaySamples" in text
    assert "MyCombWrapper" in text
