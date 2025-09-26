import pathlib
from cpp_contractgen import parser, generator, files

def test_generate_contract(tmp_path):
    contract_file = tmp_path / "MyComb.hpp.contract"
    contract_file.write_text("""
#include <cpp_contractgen>
define_contract MyComb {
    bool setDelaySamples(uint32_t d);
};
""")
    parsed = parser.parse_contract(contract_file)
    hash_value = files.hash_file(contract_file)
    contract = generator.generate_contract(parsed, hash_value, False)
    text = contract
    assert "struct MyCombTraits" in text
    assert "setDelaySamples" in text
    assert "MyCombWrapper" in text
