cmake_minimum_required(VERSION 3.16)

# Fetch GoogleTest
include(FetchContent)
FetchContent_Declare(
  googletest
  URL https://github.com/google/googletest/archive/03597a01ee50ed33e9dfd640b249b4be3799d395.zip
  DOWNLOAD_EXTRACT_TIMESTAMP true
)

FetchContent_MakeAvailable(googletest)

set(CMAKE_CXX_STANDARD 14)
# Add test sources
add_executable(contract_tests
    test_contracts.cpp
)

find_package(Python3 REQUIRED COMPONENTS Interpreter)

include(${CMAKE_SOURCE_DIR}/cmake/ContractGen.cmake)

contractgen_generate_contracts(
    ${CMAKE_CURRENT_LIST_DIR}
    ${CMAKE_BINARY_DIR}/generated
)

target_include_directories(contract_tests PRIVATE ${CMAKE_BINARY_DIR}/generated)
add_dependencies(contract_tests generate_contracts)


# Make the tests depend on generated contracts
add_dependencies(contract_tests generate_contracts)

target_link_libraries(contract_tests
    GTest::gtest_main
)

include(GoogleTest)
gtest_discover_tests(contract_tests)

