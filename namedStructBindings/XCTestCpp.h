//
//  XCTestCpp.h
//  namedstruct
//
//  Created by annaelle on 2018-04-04.
//

#ifndef XCTestCpp_h
#define XCTestCpp_h

#define _XCTPrimitiveAssertEqualCpp(test, expression1, expressionStr1, expression2, expressionStr2, ...) \
({ \
@try { \
auto expressionValue1 = (expression1); \
auto expressionValue2 = (expression2); \
if (expressionValue1 != expressionValue2) { \
std::ostringstream ss1; \
ss1 << expressionValue1; \
string expressionValueString1 = ss1.str(); \
std::ostringstream ss2; \
ss2 << expressionValue2; \
string expressionValueString2 = ss2.str(); \
_XCTRegisterFailure(test, _XCTFailureDescription(_XCTAssertion_Equal, 0, expressionStr1, expressionStr2, @(expressionValueString1.c_str()), @(expressionValueString2.c_str())), __VA_ARGS__); \
} \
} \
@catch (_XCTestCaseInterruptionException *interruption) { [interruption raise]; } \
@catch (NSException *exception) { \
_XCTRegisterUnexpectedFailure(test, _XCTFailureDescription(_XCTAssertion_Equal, 1, expressionStr1, expressionStr2, [exception reason]), __VA_ARGS__); \
} \
@catch (...) { \
_XCTRegisterUnexpectedFailure(test, _XCTFailureDescription(_XCTAssertion_Equal, 2, expressionStr1, expressionStr2), __VA_ARGS__); \
} \
})

/*!
 * @define XCTAssertEqualCpp(expression1, expression2, ...)
 * Generates a failure when ((\a expression1) != (\a expression2)).
 * @param expression1 An expression of C scalar type or cpp object.
 * @param expression2 An expression of C scalar type or cpp object.
 * @param ... An optional supplementary description of the failure. A literal NSString, optionally with string format specifiers. This parameter can be completely omitted.
 */
#define XCTAssertEqualCpp(expression1, expression2, ...) \
_XCTPrimitiveAssertEqualCpp(self, expression1, @#expression1, expression2, @#expression2, __VA_ARGS__)


#endif /* XCTestCpp_h */
