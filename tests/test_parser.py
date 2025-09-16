import pathlib
from contractgen import parser

def test_parse_contract(tmp_path):
    file = tmp_path / "MyComb.hpp.contract"
    file.write_text("""
define_contract MyComb {
    bool setDelaySamples(uint32_t d);
    float readTail(uint32_t i) const;
    void writeTail(uint32_t i, float s);
    void advance();
};
""")
    contract = parser.parse_contract(file)
    assert contract.name == "MyComb"
    assert len(contract.methods) == 4
    assert contract.methods[0].name == "setDelaySamples"
