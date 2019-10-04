from builtins import str
from builtins import range
from builtins import bytes
from builtins import ord
import math
import struct
import unittest
import sys


if sys.version_info.major >= 3:
    unicode = str


# returns the number of bits required to store the number
# 0 -> 0, 255 -> 8, 256 -> 9
def requiredBits(number):
    if number == 0:
        return 0
    return int(math.log(number, 2)) + 1


# returns a postive number as an array of bits
# numBits forces 0-bits to be added so that the len of the result is numBits
# if the number of required bits is longer than numBits, throws an exception
def toBits(number, numBits=None):
    theNumber = number
    if number < 0:
        raise Exception("received negative number " + str(number))
    if int(number) != number:
        raise Exception("received non int-number " + str(number))
    bits = []
    while number > 0:
        bits.append(number & 1)
        number >>= 1
    if numBits is None:
        return bits
    if len(bits) > numBits:
        raise Exception("number %d doesn't fit in %d bits" % (theNumber, numBits))
    return bits + [0] * (numBits - len(bits))  # add 0 bits


# takes an array of bits, and returns them as a string (i.e. char array)
# this operation should be indemptotent, i.e. a string will be returned as is
def packBitsToChars(bits):
    if isinstance(bits, (str, unicode, bytes)):
        for c in bits:
            if ord(c) < 0 or ord(c) > 255:
                raise Exception("blob strings myst be made of 8-bit chars, but found " + repr(c))
        return bits
    c = 0
    numBits = 0
    result = []
    for b in bits:
        if not (b == 0 or b == 1):
            raise Exception("blobs can only be made from sequences of 0,1 values")
        if numBits == 8:
            result.append(c)
            c = 0
            numBits = 0
        c += b << numBits
        numBits += 1
    if numBits > 0:
        result.append(c)
    bitsToChar = struct.pack("<" + str(len(result)) + "B", *bytes(result))
    if sys.version_info.major >= 3:
        arrayOfIndividualBytes = [bytes([charValue]) for charValue in bitsToChar]
    else:
        arrayOfIndividualBytes = [bytes([ord(charValue)]) for charValue in bitsToChar]

    return arrayOfIndividualBytes


def zigZagEncode(v):
    if v < 0:
        return ~int(v) * 2 + 1
    else:
        return 2 * v


def zigZagDecode(v):
    if v & 1:
        return ~(v >> 1)
    else:
        return v >> 1


class TestBitHelper(unittest.TestCase):
    def testZigZag(self):
        values = [
            (0, 0),
            (-1, 1),
            (1, 2),
            (-2, 3),
            (2147483647, 4294967294),
            (-2147483648, 4294967295),
        ]
        for s, d in values:
            self.assertEqual(zigZagEncode(s), d)
            self.assertEqual(s, zigZagDecode(d))
    
    def testZigZag2(self):
        for shift in range(40):
            for v in [1 << shift, (1 << shift) - 1, - (1 << shift), -((1 << shift) - 1)]:
                self.assertEqual(zigZagDecode(zigZagEncode(v)), v)


def runTests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBitHelper)
    unittest.TextTestRunner(verbosity=2).run(suite)
