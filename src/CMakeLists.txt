cmake_minimum_required (VERSION 3.6)

project(namedstruct LANGUAGES CXX C)

add_library(namedstruct bits.h bits.cpp)

set_property(TARGET namedstruct PROPERTY CXX_STANDARD 14)
set_property(TARGET namedstruct PROPERTY CXX_STANDARD_REQUIRED ON)

target_include_directories(namedstruct PUBLIC ${PROJECT_SOURCE_DIR})

find_package(XCTest)
if(APPLE AND ${CMAKE_VERSION} VERSION_GREATER 3.8.2016 AND XCTest_FOUND)

    enable_testing()

    xctest_add_bundle(namedstructTests namedstruct
        ${PROJECT_SOURCE_DIR}/localTestFiles
        namedStructTests.h
        namedStructTests.mm
        testBits.mm
    )

    set_property(TARGET namedstructTests PROPERTY CXX_STANDARD 14)
    set_property(TARGET namedstructTests PROPERTY CXX_STANDARD_REQUIRED ON)

    set_source_files_properties(${PROJECT_SOURCE_DIR}/localTestFiles PROPERTIES MACOSX_PACKAGE_LOCATION Resources)

    # add_custom_command(
    #    OUTPUT ${PROJECT_SOURCE_DIR}/localTestFiles
    #    COMMAND ${RESET_IOS_ENV} && pwd && ${PROJECT_SOURCE_DIR}/copy_test_if_not_up_to_date.sh
    # )

    xctest_add_test(XCTest.namedstructTests namedstructTests)
    target_link_libraries(namedstructTests PUBLIC namedstruct)
    set_property(TARGET namedstructTests PROPERTY XCODE_ATTRIBUTE_FRAMEWORK_SEARCH_PATHS "\${DEVELOPER_FRAMEWORKS_DIR}")
endif()
