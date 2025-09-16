function(contractgen_generate_contracts SEARCH_DIRECTORY OUT_DIRECTORY)
    find_package(Python3 REQUIRED COMPONENTS Interpreter)

    # Make sure the output dir exists
    file(MAKE_DIRECTORY ${OUT_DIRECTORY})

    # Glob all .hpp.contract files
    file(GLOB CONTRACT_INPUTS "${SEARCH_DIRECTORY}/*.hpp.contract")

    set(GENERATED_HEADERS "")

    foreach(CONTRACT_FILE ${CONTRACT_INPUTS})
        # e.g. TestContract.hpp.contract -> TestContract.contract.hpp
        get_filename_component(NAME_WE ${CONTRACT_FILE} NAME_WE) # TestContract.hpp
        string(REPLACE ".hpp" "" CONTRACT_BASE ${NAME_WE})       # TestContract
        set(CONTRACT_OUTPUT ${OUT_DIRECTORY}/${CONTRACT_BASE}.contract.hpp)

        add_custom_command(
            OUTPUT ${CONTRACT_OUTPUT}
            COMMAND ${Python3_EXECUTABLE} -m contractgen
                    ${CONTRACT_FILE}
                    --outdir ${OUT_DIRECTORY}
            DEPENDS ${CONTRACT_FILE}
            WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
            COMMENT "Generating ${CONTRACT_OUTPUT}"
        )

        list(APPEND GENERATED_HEADERS ${CONTRACT_OUTPUT})
    endforeach()

    add_custom_target(generate_contracts ALL DEPENDS ${GENERATED_HEADERS})

    # Expose outputs to caller
    set(CONTRACT_GENERATED ${GENERATED_HEADERS} PARENT_SCOPE)
endfunction()
