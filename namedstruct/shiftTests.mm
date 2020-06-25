//
//  shiftTests.mm
//  namedstruct
//
//  Created by Rodrigo Hausen on 2020-06-23.
//  Copyright © 2020 The Transit App. All rights reserved.
//

#import <XCTest/XCTest.h>
#include "XCTestCpp.h"
#include <namedstruct/shifts.h>
#include <cstdint>
#include <limits>
#include <utility>

@interface shiftTests : XCTestCase {
}

@end

@implementation shiftTests

#pragma mark - setup

- (void)setUp {
}

#pragma mark - tests

- (void)testClamp {
    using namedstruct::NonNegative;

    constexpr auto x = NonNegative(std::numeric_limits<uint64_t>::max());

    XCTAssertEqual(x.clamped<std::int8_t>(), 7);
    XCTAssertEqual(x.clamped<std::uint8_t>(), 7);

    XCTAssertEqual(x.clamped<std::int16_t>(), 15);
    XCTAssertEqual(x.clamped<std::uint16_t>(), 15);

    XCTAssertEqual(x.clamped<std::int32_t>(), 31);
    XCTAssertEqual(x.clamped<std::uint32_t>(), 31);

    XCTAssertEqual(x.clamped<std::int64_t>(), 63);
    XCTAssertEqual(x.clamped<std::uint64_t>(), 63);
}

- (void)testArithmeticShiftLeftPositive {
    using namedstruct::NonNegative;
    using namedstruct::MaybeNegative;

    constexpr auto positiveNumber = MaybeNegative<std::int16_t>(43);

    static_assert(std::is_same<decltype(positiveNumber.value), std::int16_t>::value);

    std::pair<int, std::int16_t> samples[] = {
        {0, positiveNumber.value},      // 0000 0000 0010 1011
        {1, 2*positiveNumber.value},
        {8, 256*positiveNumber.value},
        {9, 512*positiveNumber.value},
        {10, -21504},                   // 1010 1100 0000 0000
        {11,  22528},                   // 0101 1000 0000 0000
        {12, -20480},                   // 1011 0000 0000 0000
        {13,  24576},                   // 0110 0000 0000 0000
        {14, -16384},                   // 1100 0000 0000 0000
        {15, -32768},                   // 1000 0000 0000 0000
        {16, positiveNumber.value},     // shift exponent clamped to 0
        {17, 2*positiveNumber.value}    // shift exponent clamped to 1
    };

    for (const auto [shift, expected] : samples) {
        std::int16_t result = positiveNumber << NonNegative(shift);
        XCTAssertEqual(result, expected);
    }
}

- (void)testArithmeticShiftLeftNegative {
    using namedstruct::NonNegative;
    using namedstruct::MaybeNegative;

    constexpr auto negativeNumber = MaybeNegative<std::int16_t>(-43);

    static_assert(std::is_same<decltype(negativeNumber.value), std::int16_t>::value);

    std::pair<int, std::int16_t> samples[] = {
        {0, negativeNumber.value},     // 1111 1111 1101 0101
        {1, 2*negativeNumber.value},   // 1111 1111 1010 1010
        {8, 256*negativeNumber.value}, // 1101 0101 0000 0000
        {9, 512*negativeNumber.value}, // 1010 1010 0000 0000
        {10,  21504},                  // 0101 0100 0000 0000
        {11, -22528},                  // 1010 1000 0000 0000
        {12,  20480},                  // 0101 0000 0000 0000
        {13, -24576},                  // 1010 0000 0000 0000
        {14,  16384},                  // 0100 0000 0000 0000
        {15, -32768},                  // 1000 0000 0000 0000
        {16, negativeNumber.value},    // shift exponent clamped to 0
        {17, 2*negativeNumber.value}   // shift exponent clamped to 1
    };

    for (const auto [shift, expected] : samples) {
        std::int16_t result = negativeNumber << NonNegative(shift);
        XCTAssertEqual(result, expected, "shift=%d", shift);
    }
}

- (void)testArithmeticShiftRightPositive {
    using namedstruct::NonNegative;
    using namedstruct::MaybeNegative;

    constexpr auto positiveNumber = MaybeNegative<std::int16_t>(43);
    
    std::pair<int, std::int16_t> samples[] = {
        {0, positiveNumber.value}, // 0000 0000 0010 1011
        {1, 21},
        {2, 10},
        {3,  5},
        {4,  2},
        {5,  1},
        {6,  0},
        {15, 0},
        {16, positiveNumber.value}, // shift exponent clamped to 0
        {17, 21}                    // shift exponent clamped to 1
    };
    
    for (const auto [shift, expected] : samples) {
        std::int16_t result = positiveNumber >> NonNegative(shift);
        XCTAssertGreaterThanOrEqual(result, 0, "shift=%d", shift);
        XCTAssertEqual(result, expected, "shift=%d", shift);
    }
}

- (void)testArithmeticShiftRightNegative {
    using namedstruct::NonNegative;
    using namedstruct::MaybeNegative;

    constexpr auto negativeNumber = MaybeNegative<std::int16_t>(-43);
    
    std::pair<int, std::int16_t> samples[] = {
        {0, negativeNumber.value},  // 1111 1111 1101 0101
        {1, -22},                   // 1111 1111 1110 1010
        {2, -11},                   // 1111 1111 1111 0101
        {3,  -6},                   // 1111 1111 1111 1010
        {4,  -3},                   // 1111 1111 1111 1101
        {5,  -2},                   // 1111 1111 1111 1110
        {6,  -1},                   // 1111 1111 1111 1111
        {7,  -1},                   // 1111 1111 1111 1111
        {15, -1},                   // 1111 1111 1111 1111
        {16, negativeNumber.value}, // shift exponent clamped to 0
        {17, -22}                   // shift exponent clamped to 1
    };
    
    for (const auto [shift, expected] : samples) {
        std::int16_t result = negativeNumber >> NonNegative(shift);
        XCTAssertLessThanOrEqual(result, 0, "shift=%d", shift);
        XCTAssertEqual(result, expected, "shift=%d", shift);
    }
}

@end
