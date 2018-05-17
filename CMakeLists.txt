cmake_minimum_required (VERSION 3.6)

set(RESET_IOS_ENV unset TARGET_DEVICE_MODEL && unset TARGET_DEVICE_OS_VERSION && unset SDKROOT && unset SDK_DIR && unset DEPLOYMENT_TARGET_CLANG_ENV_NAME && unset IPHONEOS_DEPLOYMENT_TARGET)
set(CMAKE_XCODE_GENERATE_SCHEME TRUE)

project(namedstruct LANGUAGES CXX C)

add_library(namedstruct src/bits.h src/bits.cpp)

set_property(TARGET namedstruct PROPERTY CXX_STANDARD 14)
set_property(TARGET namedstruct PROPERTY CXX_STANDARD_REQUIRED ON)

target_include_directories(namedstruct PUBLIC ${PROJECT_SOURCE_DIR})

find_package(XCTest)
if(APPLE AND ${CMAKE_VERSION} VERSION_GREATER 3.8.2016 AND XCTest_FOUND)

    enable_testing()

    xctest_add_bundle(namedstructTests namedstruct
        ${PROJECT_SOURCE_DIR}/src/localTestFiles
        src/namedStructTests.h
        src/namedStructTests.mm
        src/testBits.mm
    )

    set_property(TARGET namedstructTests PROPERTY CXX_STANDARD 14)
    set_property(TARGET namedstructTests PROPERTY CXX_STANDARD_REQUIRED ON)

    set_source_files_properties(${PROJECT_SOURCE_DIR}/src/localTestFiles PROPERTIES MACOSX_PACKAGE_LOCATION Resources)

     add_custom_command(
        OUTPUT ${PROJECT_SOURCE_DIR}/localTestFiles src/namedStructTests.h
        WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}
        COMMAND ${RESET_IOS_ENV} && pytest tests.py
     )

    xctest_add_test(XCTest.namedstructTests namedstructTests)
    target_link_libraries(namedstructTests PUBLIC namedstruct)
    set_property(TARGET namedstructTests PROPERTY XCODE_ATTRIBUTE_FRAMEWORK_SEARCH_PATHS "\${DEVELOPER_FRAMEWORKS_DIR}")
endif()
