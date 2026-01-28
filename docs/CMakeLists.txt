cmake_minimum_required(VERSION 4.2)

find_program(PANDOC_EXECUTABLE pandoc REQUIRED)
find_program(QHELPGENERATOR_EXECUTABLE qhelpgenerator REQUIRED)

file(GLOB WIKI_FILES "${CMAKE_CURRENT_SOURCE_DIR}/wiki/*.md")
message(STATUS "Found wiki files: ${WIKI_SOURCES}")

foreach(md_file ${WIKI_FILES})
    get_filename_component(name ${md_file} NAME_WE)
    set(html_file "${CMAKE_CURRENT_BINARY_DIR}/help_html/${name}.html")

    add_custom_command(
        OUTPUT ${html_file}
        COMMAND ${CMAKE_COMMAND} -E make_directory "${CMAKE_CURRENT_BINARY_DIR}/help_html"
        COMMAND ${PANDOC_EXECUTABLE} -f gfm -t html5 ${md_file} -o ${html_file} --standalone
        DEPENDS ${md_file}
    )
    list(APPEND HTML_OUTPUTS ${html_file})
endforeach()

add_custom_command(
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/help.qch
    COMMAND ${QHELPGENERATOR_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/help.qhp -o ${CMAKE_CURRENT_BINARY_DIR}/help.qch
    DEPENDS ${HTML_OUTPUTS} ${CMAKE_CURRENT_SOURCE_DIR}/help.qhp
)

set(WIKI_IMAGE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/wiki/img")
set(OUTPUT_IMAGE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/help_html/img")

add_custom_command(
    OUTPUT "${OUTPUT_IMAGE_DIR}"
    COMMAND ${CMAKE_COMMAND} -E copy_directory "${WIKI_IMAGE_DIR}" "${OUTPUT_IMAGE_DIR}"
    DEPENDS "${WIKI_IMAGE_DIR}"
    COMMENT "Copying wiki images to build directory"
)

add_custom_target(help_docs ALL DEPENDS
    "${CMAKE_CURRENT_BINARY_DIR}/help.qch"
    "${OUTPUT_IMAGE_DIR}"
)