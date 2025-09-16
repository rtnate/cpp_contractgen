#include <stdint.h>
#include "TestContract.contract.hpp"
#include <gtest/gtest.h>

// Positive case
struct ValidContractImplementation {
    bool setOffset(uint32_t d){ offset = d; return true; };
    float readTail(uint32_t i) const { return 0.1f; };
    void writeTail(uint32_t i, float s){};
    void advance(){};
    uint32_t getOffset() const { return offset; };
    uint32_t offset = 0;
};

TEST(TestContractImpl, GoodImplementationCompiles) {
    IMPLEMENTS_CONTRACT_TestContract(ValidContractImplementation);
    SUCCEED();
}

// Negative case would normally break the build, so
// handle it as a WILL_FAIL target instead of gtest.
