from __future__ import print_function
from __future__ import absolute_import

import unittest
from builtins import str
from builtins import range

import os

import sys

from .namedstruct import pack
from .values import *


# TODO
# - test equality operators:
#     bitfields

class NamedstructTestCase(unittest.TestCase):
    def test_namedstruct(self):
        genDir = os.path.dirname(
            os.path.realpath(__file__)) + \
                 '/../../../submodules/bgtfs-lib/bgtfsLib/localTestFiles/'
        sys.setrecursionlimit(10000000)

        os.system("echo .")
        os.system("pwd")
        os.system("mkdir -p " + genDir)
        os.system("rm -f -r " + genDir + "/*")  # delete everything in gen
        print("generate tests in directory:")
        os.system("pwd")

        # struct tests
        structs = generateTests(True)
        for struct in structs:
            filename = genDir + "/" + struct.getName() + ".bin"
            print("writing struct", struct.getName(), "in", filename)
            with open(filename, "wb") as f:
                f.write(pack(struct))


def generateTests(quiet=False):
    testStructs = []
    
    def add(s):
        if not quiet:
            print("**************************************")
            print("Test", ("s%d" % len(testStructs)) + ":", s)
            print("pretty:")
            print(s.pretty())
            print("packed:")
            print(repr(pack(s)))
        testStructs.append(s)
    
    add(Struct("testStruct0"))
    
    add(Struct("testStruct1")
        .addInt32("bla", 234))
    
    add(Struct("testStruct2")
        .addInt8("woot", 59))
    
    add(Struct('testStruct3')
        .addInt8('four', 4)
        .add("nestedMember",
             Struct("testNestedStruct0")
             .addInt8("bla", 23)))
    
    add(Struct("testStruct4")
        .addString("hello", "hello world!"))
    
    add(Struct("testStruct5")
        .addString("unicodeString", u'Soci\xe9t\xe9 de transport de Montr\xe9al'))
    
    add(Struct("testStruct6")
        .addBlob("myBlob", [0, 1, 0, 0, 1, 0, 0, 1]))
    
    d = {
        "anInt8": 8,
        "anInt32": -32,
        "anUint32": 32,
        "aString": "hello world",
        "aBlob": [0, 1, 1, 0, 0, 0, 1],
    }
    add(Struct("testStruct7")
        .addInt8("anInt8", d)
        .addInt32("anInt32", d)
        .addUInt32("anUint32", d)
        .addString("aString", d)
        .addBlob("aBlob", d))
    
    blob = []
    for i in range(1000):
        number = i
        while number > 0:
            blob.append(number & 1)
            number >>= 1
    add(Struct("testStruct8")
        .addBlob("longBlob", blob))
    
    add(Struct("testStruct9")
        .addString("longString",
                   '-'.join(str(i) for i in range(100))))
    
    add(Struct("testStruct10")
        .addInt32Constant("EVERYTHING", 43)
        .addConstant("FOO", 0)
        .addConstant("LABEL", "this is a label")
        .addConstant("QUOTE", '"'))
    
    add(Struct("testStruct11")
        .addInt32("value", 1)
        .add("next",
             Struct("testStruct11")
             .addInt32("value", 2)
             .add("next", None)))
    
    add(Struct("testStruct12")
        .add("anotherStruct",
             Struct("testNestedStruct1")
             .addInt8("anotherValue", 123))
        .addInt8("aValue", 4))
    
    add(Struct("testStruct13")
        .addInt8("x", 4)
        .addImmediate("immediateStruct",
                      Struct("testNestedStruct2")
                      .addInt32("y", -123)))
    
    add(Struct("testStruct14")
        .add("number", 23)
        .add("string", "helluWorld")
        .add("ref", None))
    
    add(Struct("testStruct15")
        .addImmediate("immedateString", "something something..."))
    
    add(Struct("testStruct16")
        .add("fixedString", String("yet another", 30))
        .addImmediate("nonFixedString", "fooBar"))
    
    add(Struct("testStruct17")
        .addArray("structArray", [Struct("elementStruct0").add("name", "John").addInt8("x", 7).finalize(),
                                  Struct("elementStruct0").add("name", "Jane").addInt8("x", 13).finalize(),
                                  Struct("elementStruct0").add("name", "Bob").addInt8("x", 37).finalize()]))
    
    add(Struct("testStruct18")
        .addArray("structArray", [Struct("elementStruct1").addInt8("foo", 7).finalize(),
                                  Struct("elementStruct1").addInt8("foo", 9).finalize()],
                  3)
        .add("x", 234))
    
    add(Struct("testStruct19")
        .addArray("structArray", [Struct("elementStruct2").add("aname", "Blob").finalize(),
                                  Struct("elementStruct2").add("aname", "Blubb").finalize()],
                  2)
        .add("xyz", 34))
    
    add(Struct("testStruct20")
        .addChar("aChar", "!")
        .addChar("bChar", "'")
        .addChar("cChar", '"')
        .addChar("dChar", "\n"))
    
    add(Struct("testStruct21")
        .addCharConstant("a", "!")
        .addCharConstant("b", "'")
        .addCharConstant("c", '"')
        .addCharConstant("d", "\n")
        .addCharConstant("e", "\x00"))
    
    add(Struct("testStruct22")
        .add("magic", String("abcd", 4, True))
        .addChar("end", "!"))
    
    add(Struct("testStruct23")
        .addString("noString", None))
    
    add(Struct("testStruct24")
        .addArray("structArray", [Struct("elementStruct3").add("maybeString", None).finalize(),
                                  Struct("elementStruct3").add("maybeString", "omg yes!").finalize()],
                  2))
    
    add(Struct("testStruct25")
        .addReference("a", String("this is a string"), 8)
        .addString("b", "this is another string", referenceBitWidth=8)
        .addReference("c", String("aaand another"), 16)
        .addReference("d", String("this is the last"), 32))
    
    add(Struct("testStruct26")
        .addArray("refArray", ["test", "foo", "bar"]))
    
    add(Struct("testStruct27")
        .addArray("bRefArray", [None, "foo", None]))
    
    add(Struct("testStruct28")
        .addArray("cRefArray", [Null()]))
    
    add(Struct("testStruct29")
        .addReferenceArray("rArray",
                           [Struct("elementStruct4").add("age", 56).addImmediate("name", "Vader"),
                            Struct("elementStruct4").add("age", 22).addImmediate("name", "Luc"),
                            Struct("elementStruct4").add("age", 22).addImmediate("name", "Lea")]))
    
    add(Struct("testStruct30")
        .addReferenceArray("strings",
                           ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", None],
                           referenceBitWidth=8))
    
    add(Struct("testStruct31")
        .addReferenceArray("array",
                           [[4, 5, 6], [2, 3], [5, 6, 7, 7]],
                           referenceBitWidth=16)
        .add("sizes", [3, 2, 4]))
    
    add(Struct("testStruct32")
        .addReferenceArray("fixedArray", [None, "foo", "bar"], fixedSize=4)
        .add("terminal", 12345))
    
    add(Struct("testStruct33")
        .addReferenceArray("refsrefsrefs",
                           [ReferenceArray([ReferenceArray(["foo", "bar"], 2),
                                            ReferenceArray([None, None], 2),
                                            ReferenceArray(["abcdefghijklmnopqrstuvwxyz"], 2)],
                                           referenceBitWidth=16),
                            ReferenceArray([ReferenceArray(["2_foo", "bar_2"], 2),
                                            ReferenceArray([None, "some!"], 2),
                                            ReferenceArray(["not again"], 2)],
                                           referenceBitWidth=16)])
        .add("terminal", 123456))
    
    add(Struct("testStruct34")
        .add("flags",
             BitField("bitField1", 8)
             .add("aFlag", 1)
             .add("bFlag", 0)
             .add("cFlag", 1)
             .add("values", 3, 2))
        .add("smallInts",
             BitField("bitField2", 16)
             .add("aFlag", 0)
             .add("b", 127, 7)
             .add("c", 0, 3)
             .add("d", 7, 5))
        .add("terminal", 567))
    
    struct35 = Struct("testStruct35")
    firstTime = (BitField("timeBitField")
                 .add("year", 2011, 11)
                 .add("month", 11, 4)
                 .add("day", 11, 5)
                 .add("hour", 9, 5)
                 .add("minute", 23, 6))
    secondTime = (BitField("timeBitField")
                  .add("year", 2012, 11)
                  .add("month", 12, 4)
                  .add("day", 12, 5)
                  .add("hour", 10, 5)
                  .add("minute", 24, 6))
    struct35.addArray("dates", [firstTime, secondTime])
    add(struct35)
    
    add(Struct("testStruct36")
        .add("s0", Struct("testNestedStruct3").addUInt8("x", 0xab).addUInt8("y", 0xab))
        .add("s1", Struct("testNestedStruct4").addUInt16("x", 0xacac))
        .add("s2", Struct("testNestedStruct5").addUInt32("x", 0xadadadad))
        .add("s3", Struct("testNestedStruct6").addUInt64("x", 0xaeaeaeaeafafafaf).addUInt64("y", 0x8182838485868788))
        .addUInt8("terminal", 0xff))
    
    add(Struct("testStruct37")
        .addReference("stringRef", None, targetType=String().getType())
        .addNullReference("bitFieldReference", BitField("bitField2").add("aField", 0, 13).getType())
        .addNullReference("int8ArrayRef", SimpleArray(types.INT8, [], 16), referenceBitWidth=16)
        .addReference("uint8Ref", None, referenceBitWidth=8, targetType=types.INT8))
    
    add(Struct("testStruct38")
        .add("bitArray",
             BitFieldArray("BitBitArray", "bit")
             .add([0]).add([1]).add([1]).add([0]).add([0]).add([1]).add([0]).add([1])))
    
    add(Struct("testStruct39")
        .add("pairArray",
             BitFieldArray("PairBitArray", "a", "b")
             .add([0, 12]).add([0, 4]).add([0, 0]).add([0, 63])))
    
    add(Struct("testStruct40")
        .addImmediate("bitArray",
                      BitFieldArray("ABFooBitArray", "a", "b", "foo")
                      .add([3, 4, 5])
                      .add([10, 0, 3])
                      .add([Blob([0, 0, 1, 0, 0, 1]), Blob([0] * 50), 0])
                      .add([0, 0, 0])
                      .add([2 ** 30, 0, 0])
                      .add([2 ** 30, 0, 0])
                      .add([2 ** 30, 0, 0])
                      .add([2 ** 30, 0, 1])
                      .add([2 ** 30, 0, 2])))
    
    add(Struct("testStruct41A")
        .addImmediate("bitArray",
                      BitFieldArray("VarBitArrayA", "a", "b")
                      .add([1, 0])
                      .add([1, 0])
                      .add([0, 0])))
    
    add(Struct("testStruct41B")
        .addImmediate("bitArray",
                      BitFieldArray("VarBitArrayB", "a", "b", "c")
                      .add([1, 0, 32])
                      .add([1, 0, 17])
                      .add([0, 0, 42])))
    
    add(Struct("testStruct41C")
        .addImmediate("bitArray",
                      BitFieldArray("VarBitArrayC", "a", "b", "c", "d")
                      .add([1, 0, 32, 23])
                      .add([1, 0, 17, 53])
                      .add([0, 0, 42, 59])))
    
    GenderEnum = namedstruct.types.EnumType("GenderEnum", namedstruct.types.UINT8, {'MALE': 0, 'FEMALE': 1, 'OTHER': 2})
    NationEnum = namedstruct.types.EnumType("NationEnum", namedstruct.types.CHAR,
                                            {'ENGLISH': 'e', 'FRENCH': 'f', 'OTHER': 'a'})
    PartyEnum = namedstruct.types.IntEnumType("PartyEnum", {"CONSERVATIVE": -1, "LIBERAL": -2, "NDP": -3, "GREEN": -4})
    add(Struct("testStruct42")
        .add("gender", GenderEnum.OTHER)
        .add("party", PartyEnum.GREEN)
        .add("nation", NationEnum.OTHER))
    
    # trivial enums
    YesEnum = namedstruct.types.EnumType("YesEnum", namedstruct.types.UINT16, {"yes": 0})
    NoEnum = namedstruct.types.IntEnumType("NoEnum", {"no": -1})
    
    add(Struct("testStruct43")
        .add("bitfield",
             BitField("bitField43", 16)
             .addSigned("s1", 1, 2)
             .addSigned("s2", -2, 2)
             .addSigned("s3", -127, 8)
             .add("empty", 0, 0))
        )
    
    add(Struct("testStruct44")
        .add("bitfield",
             BitField("BitField44")
             .addSigned("field", -2147483648, 32))
        )
    
    add(Struct("testStruct45")
        .add("bitfield",
             BitField("BitField45")
             .addEnum("gender", GenderEnum.OTHER)
             .addEnum("party", PartyEnum.GREEN)
             .addEnum("yes", YesEnum.yes)
             .addEnum("no", NoEnum.no)
             .addSigned("signedEmpty", 0, 0)
             .add("other", 1))
        )
    
    add(Struct("testStruct46")
        .add("bitfield",
             BitField("BitField46")
             .add("a", 0, 3)
             .addSigned("b", 0, 4)
             .add("c", 0, 4)
             .add("d", 0, 4)
             )
        )
    
    add(Struct("testStruct47")
        .add("bitfield",
             BitField("BitField47")
             .addSigned("number", 0, 32)
             )
        )
    
    pool = generateConstantPool()
    
    if not quiet:
        print("**** all pretties ********************")
        for s in testStructs:
            print(s.pretty())
        
        print("**** all headers *********************")
        print(namedstruct.generateHeader(testStructs, pool, namespace="namedStructTest", define="__NAMEDSTRUCTTEST__",
                                         headText="/* Testing structs generated by namedstructpy */"))
    return testStructs


def generateConstantPool():
    pool = constants.ConstantPool().addConstant("THREE", 3)
    return pool


def generateHeader():
    structs = generateTests(quiet=True)
    pool = generateConstantPool()
    header = namedstruct.generateHeader(structs, pool, namespace="namedStructTest", define="__NAMEDSTRUCTTEST__",
                                        headText="/* Testing structs generated by namedstructpy */")
    with open("../bgtfsLib/bgtfsLib Tests/namedStructTest.h", "w") as f:
        f.write(header)
