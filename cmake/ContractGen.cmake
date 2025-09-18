# Generate contracts using contractgen Python tool
# Signature:
# contractgen_generate_contracts(
#     TARGET <target>
#     SEARCH_DIR <dir>
#     OUT_DIR <dir>
#     [GEN_TARGET <name>]   # optional override for the custom target name
#     [INCLUDE_VISIBILITY <PUBLIC|PRIVATE|INTERFACE|NONE> #optional
# )
function(contractgen_generate_contracts)
    cmake_parse_arguments(
        CG "" "TARGET;SEARCH_DIR;OUT_DIR;GEN_TARGET;INCLUDE_VISIBILITY" "" ${ARGN}
    )

    if(NOT CG_TARGET)
        message(FATAL_ERROR "contractgen_generate_contracts: TARGET is required")
    endif()
    if(NOT TARGET ${CG_TARGET})
        message(FATAL_ERROR "contractgen_generate_contracts: TARGET ${CG_TARGET} does not exist")
    endif()

    if(NOT CG_SEARCH_DIR)
        message(FATAL_ERROR "contractgen_generate_contracts: SEARCH_DIR is required")
    endif()
    if(NOT CG_OUT_DIR)
        message(FATAL_ERROR "contractgen_generate_contracts: OUT_DIR is required")
    endif()

    # Default visibility = PUBLIC
    if(NOT CG_INCLUDE_VISIBILITY)
        set(CG_INCLUDE_VISIBILITY "PUBLIC")
    endif()

    # Validate INCLUDE_VISIBILITY
    set(_valid_visibilities PUBLIC PRIVATE INTERFACE NONE)
    if(NOT CG_INCLUDE_VISIBILITY IN_LIST _valid_visibilities)
        message(FATAL_ERROR "INCLUDE_VISIBILITY must be PUBLIC, PRIVATE, INTERFACE, or NONE")
    endif()

    find_package(Python3 REQUIRED COMPONENTS Interpreter)

    file(MAKE_DIRECTORY ${CG_OUT_DIR})

    file(GLOB CONTRACT_INPUTS "${CG_SEARCH_DIR}/*.hpp.contract")

    set(GENERATED_HEADERS "")
    foreach(CONTRACT_FILE ${CONTRACT_INPUTS})
        get_filename_component(NAME_WE ${CONTRACT_FILE} NAME_WE) # e.g. TestContract.hpp
        string(REPLACE ".hpp" "" CONTRACT_BASE ${NAME_WE})       # TestContract
        set(CONTRACT_OUTPUT ${CG_OUT_DIR}/${CONTRACT_BASE}.contract.hpp)

        add_custom_command(
            OUTPUT ${CONTRACT_OUTPUT}
            COMMAND ${Python3_EXECUTABLE} -m cpp_contractgen
                    ${CONTRACT_FILE}
                    --outdir ${CG_OUT_DIR}
            DEPENDS ${CONTRACT_FILE}
            WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
            COMMENT "Generating ${CONTRACT_OUTPUT}"
            VERBATIM
        )

        list(APPEND GENERATED_HEADERS ${CONTRACT_OUTPUT})
    endforeach()

    # Pick target name
    if(CG_GEN_TARGET)
        set(GEN_TARGET_NAME ${CG_GEN_TARGET})
    else()
        set(GEN_TARGET_NAME ${CG_TARGET}_contracts)
    endif()

    # Custom target for codegen
    add_custom_target(${GEN_TARGET_NAME} DEPENDS ${GENERATED_HEADERS})

    # Ensure build order: contracts -> target
    add_dependencies(${CG_TARGET} ${GEN_TARGET_NAME})

    # Add include path if requested
    if(NOT CG_INCLUDE_VISIBILITY STREQUAL "NONE")
        target_include_directories(${CG_TARGET} ${CG_INCLUDE_VISIBILITY} ${CG_OUT_DIR})
    endif()

    # Expose outputs to caller
    set(CONTRACT_GENERATED ${GENERATED_HEADERS} PARENT_SCOPE)
endfunction()
