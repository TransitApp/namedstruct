cmake_minimum_required (VERSION 3.6)

set(CMAKE_XCODE_GENERATE_SCHEME TRUE)

project(namedstruct LANGUAGES CXX C)

add_library(namedstruct include/namedstruct/bits.h include/namedstruct/bits.cpp include/namedstruct/shifts.h)

set_property(TARGET namedstruct PROPERTY CXX_STANDARD 17)
set_property(TARGET namedstruct PROPERTY CXX_STANDARD_REQUIRED ON)

target_include_directories(namedstruct PUBLIC ${PROJECT_SOURCE_DIR}/include)

find_package(XCTest)
if(APPLE AND ${CMAKE_VERSION} VERSION_GREATER 3.8.2016 AND XCTest_FOUND)

    enable_testing()

    xctest_add_bundle(namedstructTests namedstruct
        ${PROJECT_SOURCE_DIR}/localTestFiles
        include/namedstruct/namedStructTests.h
        include/namedstruct/namedStructTests.mm
        include/namedstruct/shiftTests.mm
        include/namedstruct/testBits.mm
    )

    set_property(TARGET namedstructTests PROPERTY CXX_STANDARD 17)
    set_property(TARGET namedstructTests PROPERTY CXX_STANDARD_REQUIRED ON)

    set_source_files_properties(${PROJECT_SOURCE_DIR}/localTestFiles PROPERTIES MACOSX_PACKAGE_LOCATION Resources)

     add_custom_command(
        OUTPUT ${PROJECT_SOURCE_DIR}/localTestFiles include/namedstruct/namedStructTests.h
        WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}
        COMMAND source reset_env.sh && cd ../ && pypy3 -m pytest namedstruct/namedstruct/tests.py
     )

    xctest_add_test(XCTest.namedstructTests namedstructTests)
    target_link_libraries(namedstructTests PUBLIC namedstruct)
    set_property(TARGET namedstructTests PROPERTY XCODE_ATTRIBUTE_FRAMEWORK_SEARCH_PATHS "\${DEVELOPER_FRAMEWORKS_DIR}")
endif()
