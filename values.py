from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from builtins import str
from builtins import range
from past.builtins import basestring
from past.utils import old_div
from builtins import object
import array
import numbers

from . import bithelper
from . import constants
from . import namedstruct
from . import stringhelper
from . import types


# given a python object, will return a reasonable Value for it
# Value   -> returns the argument
# int     -> int32 value
# string  -> string value
# None    -> Null value
# an iterable -> an array value, using getValue on the elements
def getValue(value):
    if isinstance(value, Value):
        return value
    elif isinstance(value, numbers.Integral):
        return Int(value)
    elif isinstance(value, basestring):
        return String(value)
    elif value is None:
        return Null()
    elif hasattr(value, "__iter__"):
        return getArrayValue(value)
    else:
        raise Exception("can't convert " + str(value) + " to a Value")


# given an array, will return a reasonable array value for it, i.e. makes a Value array by turning
# every element into a value using "getValue"
def getArrayValue(arrayValues, fixedSize=None):
    arrayValues = [getValue(v) for v in arrayValues]
    t = arrayValues[0].getType()
    for v in arrayValues[1:]:
        t = types.mergeTypes(t, v.getType())
    if isinstance(t, types.ReferenceType):
        raise Exception("can't build arrays out of references")
    if t.isImmediate():  # elements are immediate - just build simple array
        return SimpleArray(t, arrayValues, fixedSize)
    else:
        return ReferenceArray(arrayValues, fixedSize)  # build reference array


class Value(object):
    def __init__(self, valueType):
        self.type = valueType
    
    def getType(self):
        return self.type
    
    # returns a tuple of strings, the immediate data, and the offseted data, which is assumed to start at dataOffset
    # the caller has to ensure proper alignment of the immediate data 
    # but the function will ensure alignment of the offseted data
    def pack(self, dataOffset=None):
        raise Exception()
    
    def getPythonValue(self):  # will return a python value, basically what was used to create this
        raise Exception()
    
    def pretty(self):
        raise Exception("unimplemented for " + repr(self))
    
    def getLiteral(self):
        raise Exception("cannot get literal for " + repr(self))
    
    def getImmediateDataSize(self):
        return self.type.getWidth()


# primitve value
class PrimitiveValue(Value):
    def __init__(self, valueType, pythonValue):
        Value.__init__(self, valueType)
        self.pythonValue = pythonValue
        valueType.assertValueHasType(pythonValue)
    
    @staticmethod
    def hasFixedWidth():
        return True
    
    def getPythonValue(self):
        return self.pythonValue
    
    def pretty(self):
        return repr(self.pythonValue)
    
    def pack(self, dataOffset=None):
        return self.type.pack(self.pythonValue), b""


# integer value
class Int(PrimitiveValue):
    def __init__(self, intValue, unsigned=False, bitWidth=32):
        valueType = types.IntType(unsigned, bitWidth)
        valueType.assertValueHasType(intValue)
        PrimitiveValue.__init__(self, valueType, intValue)
    
    def getLiteral(self):
        return str(self.getPythonValue())


# padding byte
class Padding(Int):
    def __init__(self):
        Int.__init__(self, 0, True, 8)


# a single char
class Char(PrimitiveValue):
    def __init__(self, char):
        assert (isinstance(char, basestring))
        assert (len(char) == 1)
        charType = types.CharType()
        PrimitiveValue.__init__(self, charType, char)
    
    def getLiteral(self):
        return stringhelper.literalFromString(self.getPythonValue(), quote="'")


# an integer that acts as a bit field
class BitField(Value):
    def __init__(self, name, bitWidth=32):
        super(BitField, self).__init__(types.BitFieldType(name, bitWidth))
        self.values = []
    
    def add(self, name, value, bitWidth=1):
        if not (0 <= value < 2 ** bitWidth):
            raise Exception("bitfield %s cannot store unsigned (%s, %d, bitWidth=%d)"
                            % (self.type.name, name, value, bitWidth))
        self.type.add(name, bitWidth)
        self.values.append(value)
        return self
    
    def addSigned(self, name, value, bitWidth):
        if not (bithelper.zigZagEncode(value) < 2 ** bitWidth):
            raise Exception("bitfield %s cannot store signed (%s, %d, bitWidth=%d)"
                            % (self.type.name, name, value, bitWidth))
        self.type.addSigned(name, bitWidth)
        self.values.append(value)
        return self
    
    def addEnum(self, name, enumValue):  # TODO: ,numBits=None,signed=None):
        self.type.addEnum(name, enumValue.getType())
        self.values.append(enumValue)
        return self
    
    @staticmethod
    def hasFixedWidth():
        return True
    
    def getPythonValue(self):
        return self
    
    def get(self, fieldName):  # returns the value of the field name
        return self.values[self.getType().fields[fieldName]]
    
    def pretty(self):
        result = "bitField{bitWidth}({name}){{".format(bitWidth=self.type.bitWidth, name=self.type.name)
        nameLen = max(len(field.name) for field in self.type.fieldArray) if len(self.values) > 0 else 0
        for _, _ in enumerate(self.values):
            result += ("\n{name:" + str(nameLen) + "}:{type}{separator}{bitWidth:<2} = {value}")
        result = result.replace("\n", "\n" + stringhelper.indent)
        result += "\n}"
        return result
    
    # packs this bietfield into an integer
    def packToInt(self):
        value = 0
        shift = 0
        for i, v in enumerate(self.values):
            field = self.type.fieldArray[i]
            if field.type == 'u':
                storeValue = v
            elif field.type == 'i':
                storeValue = bithelper.zigZagEncode(v)
            else:
                storeValue = v.getPythonValue()
                if field.type.hasNegativeValues():
                    storeValue = bithelper.zigZagEncode(storeValue)
            value |= storeValue << shift
            shift = shift + field.bitWidth
        return value
    
    def pack(self, dataOffset=None):
        intPacked = self.packToInt()
        return Int(intPacked, True, self.type.bitWidth).pack(dataOffset)
    
    def __repr__(self):
        return (
            self.pretty()
                .replace("\n" + stringhelper.indent, ",")
                .replace(" ", "")
                .replace("\n", "")
                .replace("{,", "{")
                .replace(",", ", ")
        )
        
        # null value


class Null(Value):
    def __init__(self):
        Value.__init__(self, types.NullType())
    
    def pretty(self):
        return "<NULL>"
    
    def getPythonValue(self):
        return None


# reference value
class Reference(Value):
    # a target of None is allowed - in that case (and only that case) target type may be set
    def __init__(self, targetValue, referenceBitWidth=32, targetType=None):
        """:type targetValue: any"""

        if targetValue is not None and targetType is not None:
            raise Exception("cannot set target type for non-null reference")
        if targetValue is None:
            targetValue = Null()
        targetValue = getValue(targetValue)
        Value.__init__(self, types.ReferenceType(targetValue.type, referenceBitWidth=referenceBitWidth))
        self.targetValue = targetValue
    
    def pretty(self):
        return ("->" +
                (self.targetValue.pretty().replace("\n", stringhelper.indent + "\n")
                 if self.targetValue is not None else
                 "None"))
    
    def getPythonValue(self):
        return self.targetValue.getPythonValue()
    
    def pack(self, dataOffset=None):
        if dataOffset is None:
            raise Exception("cannot pack reference without a data offset (is the reference not contained in a struct?)")
        if self.targetValue.getPythonValue() is None:
            return self.type.referenceType.pack(0), b""
        else:
            # add padding bytes until data offset is aligned with target type
            padding = ((-dataOffset) % self.type.targetType.getAlignment())
            packedReference = self.type.referenceType.pack(dataOffset + padding)
            packedData = b"\x00" * padding + namedstruct.pack(self.targetValue, addPadding=False)
            return packedReference, packedData


# all the array-like values
class Array(Value):
    def __init__(self, arrayType, values):
        Value.__init__(self, arrayType)
        # check correctness on values - either incoming values are python values or Value objects
        self.elementsAreValueObjects = (len(values) > 0 and isinstance(values[0], Value))
        for v in values:
            if self.elementsAreValueObjects:
                assert (isinstance(v, Value))
                arrayType.getElementType().merge(v.getType())
            else:
                arrayType.getElementType().assertValueHasType(v)
        self.values = values
    
    def getPythonValue(self):
        return self.values
    
    # will pack the elements
    def pack(self, dataOffset=None, elementOffsetsRelativeToElement=True):
        if dataOffset is None:
            dataOffset = self.getImmediateDataSize()
        immediateData = []
        offsetedData = []
        immediateLen = 0
        for value in self.values:
            if self.elementsAreValueObjects:
                immediate, referred = value.pack(dataOffset -
                                                 (immediateLen
                                                  if elementOffsetsRelativeToElement else
                                                  0))  # offset is relative to element
                dataOffset += len(referred)
                immediateData.append(immediate)
                offsetedData.append(referred)
                immediateLen += len(immediateData[-1])
            else:
                immediateData.append(self.type.getElementType().pack(value))
                immediateLen += len(immediateData[-1])
        immediateString = b"".join(bytes(immediateData))
        offsetedString = b"".join(bytes(offsetedData))
        return immediateString, offsetedString
    
    def pretty(self):
        maxChars = 500
        minResults = 2
        results = [v.pretty() if self.elementsAreValueObjects else str(v) for v in self.values]
        chars = 0
        i = 0
        while (chars <= maxChars or i < minResults) and i < len(results):
            chars += len(results[i])
            i += 1
        return "[" + ", ".join(results[:i]) + (",..." if i < len(results) else "") + "]"


# c array - either variable length, or fixed length
class SimpleArray(Array):
    def __init__(self, elementType, values, fixedSize=None, byteAlignment=None):
        if isinstance(elementType, types.ReferenceType):
            raise Exception("simple arrays cannot store references")
        if fixedSize is not None:
            assert (len(values) <= fixedSize)
        self.fixedSize = fixedSize

        Array.__init__(self, types.SimpleArrayType(elementType, fixedSize, byteAlignment), values)
    
    def getImmediateDataSize(self):
        return (self.type.getElementType().getWidth()
                * (len(self.values) if self.fixedSize is None else self.fixedSize))
    
    def pack(self, dataOffset=None, elementOffsetsRelativeToElement=True):
        immediateData, offsetData = Array.pack(self, dataOffset)  # call super pack
        if self.fixedSize is not None:
            # fill the data with zero bytes 
            immediateData = (immediateData
                             + b"\x00" * (self.getImmediateDataSize() - len(immediateData)))
        if dataOffset is None:
            return immediateData + offsetData, b""
        else:
            return immediateData, offsetData


# c array of chars - arbitrary strings get converted to utf-8
class String(SimpleArray):
    def __init__(self, string="", fixedSize=None, omitTerminal=False):
        chars = stringhelper.stringToChars(string)
        if omitTerminal:
            chars = chars[:-1]
        SimpleArray.__init__(self, types.CharType(), chars, fixedSize)
        self.string = string
    
    def pretty(self):
        return stringhelper.cutStringIfTooLong(repr(self.string))
    
    def getPythonValue(self):
        return self.string
    
    def getLiteral(self):
        return stringhelper.literalFromString(self.string)


# c array of chars - but inputs as arrays of 0/1 (bit) values, packed into 8 bits per char
blobStrings = []


class Blob(SimpleArray):
    # the alignment is 4 bytes by default, which can be overriden
    def __init__(self, blob, fixedSize=None, byteAlignment=4):
        global blobStrings
        blobStrings.append(blob)
        if isinstance(blob, basestring):
            bitArrays = [bithelper.toBits(ord(c), numBits=8) for c in blob]
            blob = []
            for bitArray in bitArrays:
                blob.extend(bitArray)
        blob = array.array('B', blob)  # turn blob into an actual binary array - if it's not a string
        SimpleArray.__init__(self, types.CharType(), str(bithelper.packBitsToChars(blob)), fixedSize, byteAlignment)
        self.blob = blob
    
    def pretty(self):
        return stringhelper.cutStringIfTooLong("[" + ''.join(str(b) for b in self.blob[0:200]) + "]",
                                               length=len(self.blob))
    
    def getPythonValue(self):
        return self.blob


# reference array
class ReferenceArray(Array):
    # construct reference array from a sequence of values - those may be values, or will be turned into values
    def __init__(self, values, fixedSize=None, referenceBitWidth=32):
        if len(values) == 0:
            raise Exception("reference array values cannot be empty")
        if fixedSize is not None:
            assert (len(values) <= fixedSize)
        self.fixedSize = fixedSize
        # turn all values into references
        targetValues = []
        elementType = getValue(values[0]).getType()
        for v in values:
            v = getValue(v)
            if not isinstance(v, Value):
                raise Exception("reference array needs to be constructed from Value elements")
            if isinstance(v, Reference):
                raise Exception("cannot store references in reference array")
            elementType = types.mergeTypes(v.getType(), elementType)
            targetValues.append(v)
        referenceValues = [Reference(v, referenceBitWidth) for v in targetValues]
        Array.__init__(self, types.ReferenceArrayType(elementType, fixedSize, referenceBitWidth), referenceValues)
    
    def getImmediateDataSize(self):
        return (self.type.getElementType().getWidth()
                * (len(self.values) if self.fixedSize is None else self.fixedSize))
    
    def pack(self, dataOffset=None, elementOffsetsRelativeToElement=True):
        if dataOffset is None:
            dataOffset = self.getImmediateDataSize()
            combine = True
        else:
            combine = False
        immediateData, offsetData = Array.pack(self, dataOffset, elementOffsetsRelativeToElement=False)
        if self.fixedSize is not None:
            # fill the data with zero bytes 
            immediateData = (immediateData
                             + "\x00" * (self.getImmediateDataSize() - len(immediateData)))
        if combine:
            return immediateData + offsetData, ""
        else:
            return immediateData, offsetData


# reserved is just a set of bytes reserved for future use
class ReservedValue(SimpleArray):
    pass  # TODO?


class EnumValue(Value):
    def __init__(self, enumType, name):
        assert isinstance(enumType, types.EnumType)
        assert name in enumType.mapping
        super(EnumValue, self).__init__(enumType)
        self.name = name
    
    @staticmethod
    def hasFixedWidth():
        return True
    
    def getPythonValue(self):  # will return a python value, basically what was used to create this
        return self.type.mapping[self.name].getPythonValue()
    
    def pretty(self):
        return self.type.getName() + "." + self.name
    
    def getLiteral(self):
        raise self.type.values[self.name].getLiteral()
    
    def getImmediateDataSize(self):
        return self.type.getEnumType().getWidth()
    
    def pack(self, dataOffset=None):
        return self.type.mapping[self.name].pack(dataOffset=dataOffset)
    
    def __repr__(self):
        return "%s.%s" % (self.type, self.name)


# struct value
# structs don't have fixed width unless they are closed/finished
class Struct(Value, constants.AddConstantFunctions):
    def __init__(self, name):
        structType = types.StructType(name)
        Value.__init__(self, structType)
        self.values = []  # list of member values
    
    def __repr__(self):
        structType = self.type
        numMembers = len(structType.members)
        return ("<Struct:" + str(structType.name)
                + " with " + str(numMembers)
                + " member%s>" % ("" if numMembers == 1 else "s"))
    
    def getName(self):
        return self.type.name
    
    def addConstant(self, name, value):
        self.getType().addConstant(name, value)
        return self
    
    def getPythonValue(self):
        return self  # struct is a container, so it's not a python value
    
    def get(self, key):  # returns the python value associated with the given key
        if key in self.type.members:
            index = self.type.members[key]
            return self.values[index].getPythonValue()
        constantPool = self.getType().getConstantPool()
        return constantPool.get(key).getPythonValue()
    
    def getImmediateDataSize(self):
        return sum(v.getImmediateDataSize() for v in self.values)
    
    # will add a new value to the struct.
    # if value is a dictionary, will add value[name]
    # if the value is a Value, will add the value with the type
    # otherwise it will attempt to turn the value into a value using "getValue"
    def add(self, name, value):
        value = getValue(dictGet(value, name))
        if value.getType().isImmediate():
            self.addImmediate(name, value)
        else:
            self.addReference(name, value)
        return self
    
    # will add a reference to the given value to this struct
    # if the type is defined, and value=None allows adding a typed reference even if the value is Null
    def addReference(self, name, value, referenceBitWidth=32, targetType=None):
        if targetType is not None:
            if value is not None:
                raise Exception("can only override reference type for Null Value")
            return self.addImmediate(name, Reference(None, referenceBitWidth, targetType=targetType))
        return self.addImmediate(name, Reference(value, referenceBitWidth))
    
    # short hand for addReference(name,None,referenceBitWidth,targetType)
    def addNullReference(self, name, targetType, referenceBitWidth=32):
        return self.addImmediate(name, Reference(None, referenceBitWidth, targetType=targetType))
    
    # shorthand for addReference(name,value,referenceBitWidth=8,targetType=targetType)
    def addRef8(self, name, value, targetType=None):
        referenceBitWidth = 8
        return self.addReference(name, value, referenceBitWidth=referenceBitWidth, targetType=targetType)
    
    # shorthand for addReference(name,value,referenceBitWidth=16,targetType=targetType)
    def addRef16(self, name, value, targetType=None):
        referenceBitWidth = 16
        return self.addReference(name, value, referenceBitWidth=referenceBitWidth, targetType=targetType)
    
    # shorthand for addReference(name,value,referenceBitWidth=32,targetType=targetType)
    def addRef32(self, name, value, targetType=None):
        referenceBitWidth = 32
        return self.addReference(name, value, referenceBitWidth=referenceBitWidth, targetType=targetType)
    
    # will add the value
    def addImmediate(self, name, value):
        value = getValue(dictGet(value, name))
        padBytes = self.getType().addMember(name, value.getType())
        self.values.extend([Padding()] * padBytes)
        self.values.append(value)
        return self
    
    # add an int32 to the struct. if 'anInt' is a dictionary d, will add d[name]
    # if the name exists, will throw an error
    # returns self
    def addInt8(self, name, anInt):
        return self.add(name, Int(dictGet(anInt, name), False, 8))
    
    def addInt16(self, name, anInt):
        return self.add(name, Int(dictGet(anInt, name), False, 16))
    
    def addInt32(self, name, anInt):
        return self.add(name, Int(dictGet(anInt, name), False, 32))
    
    def addInt64(self, name, anInt):
        return self.add(name, Int(dictGet(anInt, name), False, 64))
    
    def addUInt8(self, name, anInt):
        return self.add(name, Int(dictGet(anInt, name), True, 8))
    
    def addUInt16(self, name, anInt):
        return self.add(name, Int(dictGet(anInt, name), True, 16))
    
    def addUInt32(self, name, anInt):
        return self.add(name, Int(dictGet(anInt, name), True, 32))
    
    def addUInt64(self, name, anInt):
        return self.add(name, Int(dictGet(anInt, name), True, 64))
    
    def addChar(self, name, aChar):
        return self.add(name, Char(dictGet(aChar, name)))
    
    # will reference add a binary blob, either an array of 0/1 values, or a string, to the struct.
    # if 'aBlob' is a dictionary d, will add d[name] will store the the byte offset in the C struct,
    # using the name <name>+ByteOffset. If the name exists, will throw an error.
    # Blobs will be word aligned by default, but that can be overriden.
    # Blobs are stored little endian, i.e. [0,1,0,0,1,0,0,1]=0x92=146.
    # returns self
    def addBlob(self, name, blob, referenceBitWidth=32):
        self.addReference(name, Blob(dictGet(blob, name)), referenceBitWidth=referenceBitWidth)
        return self
    
    # will add a string to the struct. if 'aString' is a dictionary d, will add d[name]
    # will store the byte offset in the C struct, using the name <name>+ByteOffset
    # if the name exists, will throw an error
    # if the string is None (or d[name] is None), will add a string-reference to None
    # if fixed with is True, will add a fixed width string inside the the struct, otherwise a 
    # a reference to a variable length string.
    # If omit terminal is true, will omit the '\0' terminal character at the end of the string.
    # reference bit width allows overriding the bit widh of the reference (byte offset) used,
    # if the string is not stored as an immediate value.
    # returns self
    def addString(self, name, string, fixedWidth=None, omitTerminal=False, referenceBitWidth=32):
        string = dictGet(string, name)
        if string is None:
            if fixedWidth is not None:
                raise Exception("cannot add fixed with string as a null-reference")
            self.addImmediate(name, Reference(None, targetType=types.SimpleArrayType(types.CharType())))
        else:
            self.addReference(name, String(string, fixedWidth, omitTerminal), referenceBitWidth)
        return self
    
    # will add an array of values to the struct.
    # if value is a dictionary, will add value[name]
    # if the value is an array of Value objects, will add an array with the val
    # otherwise it will attempt to turn the value into a value using "getValue"
    def addArray(self, name, arrayValues, fixedSize=None):
        arrayValues = dictGet(arrayValues, name)
        value = getArrayValue(arrayValues, fixedSize)
        if value.getType().isImmediate():
            self.addImmediate(name, value)
        else:
            self.addReference(name, value)
        return self
    
    # will add a reference array to the struct.
    # if value is a dictionary, will add value[name]
    # if the value is an array of Value objects, will add an array with the val
    # otherwise it will attempt to turn the value into a value using "getValue"
    def addReferenceArray(self, name, arrayValues, fixedSize=None, referenceBitWidth=32):
        arrayValues = dictGet(arrayValues, name)
        arrayValues = [getValue(v) for v in arrayValues]
        array = ReferenceArray(arrayValues, fixedSize, referenceBitWidth)
        if array.getType().isImmediate():
            self.addImmediate(name, array)
        else:
            self.addReference(name, array)
        return self
    
    # this will finalize type of this struct. The Struct may never grow in size from this point on.
    # returns self.
    def finalize(self, byteAlignment=4):
        padBytes = self.getType().finalize(byteAlignment)
        self.values.extend([Padding()] * padBytes)
        return self
    
    def pretty(self):
        result = "struct " + self.type.getName() + " {"
        length = max([0] + [len(repr(self.type.getMember(i)[1])) for i in range(len(self.values))])
        for i, memberValue in enumerate(self.values):
            offset, memberType, name = self.type.getMember(i)
            typeName = repr(memberType)
            result += ("\n{pos:02}: {type} " + (" " * (length - len(typeName))) + "{name}=")
        result = result.replace("\n", "\n" + stringhelper.indent)
        result += "\n}"
        return result
    
    def pack(self, dataOffset=None):
        if True:  # try:
            if dataOffset is None:
                dataOffset = self.getImmediateDataSize()
                combine = True
            else:
                combine = False
            immediateData = b""
            offsetedData = b""
            for i, value in enumerate(self.values):
                immediate, referred = value.pack(dataOffset)
                dataOffset += len(referred)
                immediateData = immediateData + immediate
                offsetedData = offsetedData + referred
            padding = self.getImmediateDataSize() - len(immediateData)
            immediateData += b"\x00" * padding
            if combine:
                return immediateData + offsetedData, b""
            else:
                return immediateData, offsetedData
                # except Exception as e:
                #    print "error when packing struct %s, member %s" % (self.getName(),repr(currentMember))
                #    raise e
    
    # prints the sizes of every member
    # indent allows indenting the printing result by 'indent' spaces
    def printSizes(self, indent=0):
        # collect names/sizes
        names = []
        sizes = []
        dataOffset = self.getImmediateDataSize()
        for i, value in enumerate(self.values):
            immediate, referred = value.pack(dataOffset)
            names.append(self.type.getMember(i)[2])
            sizes.append(len(immediate) + len(referred))
            dataOffset += len(referred)
        total = "total:"
        maxNameLen = max([len(total)] + [len(name) for name in names]) + 1
        numLen = len(str(sum(sizes)))
        numFormat = "%" + str(numLen) + "d"
        # print name, sizes, total
        print(" " * indent + "struct %s:" % self.type.getName())
        print(" " * indent + "-" * (maxNameLen + numLen))
        for i, name in enumerate(names):
            print(" " * indent + name + (" " * (maxNameLen - len(name))) + (numFormat % sizes[i]))
        print(" " * indent + "-" * (maxNameLen + numLen))
        print(" " * indent + total + (" " * (maxNameLen - len(total))) + (numFormat % sum(sizes)))


# an array of bitfield values, with variable number of bits
class BitFieldArray(Value):
    def __init__(self, name, *fields):
        super(BitFieldArray, self).__init__(types.BitFieldArrayType(name, fields))
        self.entries = []  # each entry is an array of (isBlob,value)
    
    def __repr__(self):
        return "<BitFieldArray:%s with %d fields>" % (self.type.getName(), len(self.type.getFields()))
    
    def __len__(self):
        return len(self.entries)
    
    # adds a new entry to the bit field array
    # the fieldValues may be a dictionary of field-value, or a sequence of values in the same order as the fields
    # the values themselves may be (positive) integers, or Blob objects
    def add(self, fieldValues=None, **fieldValuesDict):
        if fieldValues is None:
            fieldValues = fieldValuesDict
        fields = self.type.getFields()
        if len(fields) != len(fieldValues):
            raise Exception("expecting %d field values, received %s" % (len(fields), fieldValues))
        if isinstance(fieldValues, dict):
            fieldValues = [fieldValues[field] for field in fields]
        entry = []
        for value in fieldValues:
            if isinstance(value, Blob):
                entry.append((True, value))
            else:
                if not isinstance(value, numbers.Integral):
                    raise Exception(
                            "attempting to add " + repr(value) + ", but bitFieldArray only supports int or blobValue.")
                if not (0 <= value < 2 ** 31):
                    raise Exception(
                            "bitFieldArray only supports values between 0 (incl) and 2^31 (excl), received " + repr(value))
                entry.append((False, value))
        self.entries.append(entry)
        return self
    
    # calls add on all elements of a sequence, returns self
    def addAll(self, entries):
        for entry in entries:
            self.add(entry)
        return self
    
    @staticmethod
    def hasFixedWidth():
        return False
    
    def getPythonValue(self):
        return self
    
    def get(self, fieldName, index):  # returns the value of the field name at the given index
        return self.entries[index][self.type.getFields().index(fieldName)][1]
    
    # for every field, returns the bit length of it
    def getFieldLengths(self):
        fields = self.type.getFields()
        if len(self.entries) == 0:
            return [0] * len(fields)
        return [
            max(len(entry[fieldIndex][1].getPythonValue())
                if entry[fieldIndex][0] else
                bithelper.requiredBits(entry[fieldIndex][1])
                for entry in self.entries)
            for fieldIndex in range(len(fields))]
    
    def pretty(self):
        fields = self.type.getFields()
        fieldLengths = self.getFieldLengths()
        result = "bitFieldArray[{length}x{numBits}]{{".format(length=len(self.entries), numBits=sum(fieldLengths))
        rows = [stringhelper.indent + s + ":" for s in stringhelper.getColumn(fields)]
        rows = [rows[i] + s + " = [" for i, s in enumerate(stringhelper.getColumn(fieldLengths))]
        maxColumnWidth = 80
        maxEntryWidth = 12
        numEntries = len(self.entries)
        for i, entry in enumerate(self.entries):
            # build column values
            values = []
            for isBlob, value in entry:
                if isBlob:
                    blob = ''.join(str(v) for v in value.getPythonValue())
                    if len(blob) > maxEntryWidth:
                        blob = blob[0:maxEntryWidth - 2] + ".."
                    values.append(blob)
                else:
                    values.append(value)
            strings = stringhelper.getColumn(values)
            # stop if rows grow too big
            if len(rows[0]) + 1 + len(strings[0]) > maxColumnWidth:
                if i < numEntries:
                    rows = [row + ".." for row in rows]
                break
            # add row
            delim = ("" if (i == numEntries - 1) else ",")
            rows = [rows[j] + s + delim for j, s in enumerate(strings)]
        rows = [row + "]" for row in rows]
        result += "\n" + "\n".join(rows)
        result += "\n}"
        return result
    
    def getImmediateDataSize(self):
        fieldLengths = self.getFieldLengths()
        return (len(fieldLengths) + 2) * 2 + old_div((sum(fieldLengths) * len(self.entries) + 7), 8)
    
    def pack(self, dataOffset=None):
        fieldLengths = self.getFieldLengths()
        offset = (len(fieldLengths) + 2) * 16
        headerValues = [sum(fieldLengths)] + [offset + sum(fieldLengths[:i]) for i in range(len(fieldLengths) + 1)]
        header = namedstruct.pack(SimpleArray(types.UINT16, headerValues), addPadding=False)
        # create data blob
        blob = array.array('B', [])
        for entry in self.entries:
            for i, (isBlob, value) in enumerate(entry):
                if isBlob:
                    b = value.getPythonValue()
                    blob.extend(b)
                    blob.extend((fieldLengths[i] - len(b)) * array.array('B', ['0']))
                else:
                    blob.extend(array.array('B', bithelper.toBits(value, fieldLengths[i])))
        data = namedstruct.pack(Blob(blob), addPadding=False)
        assert (len(blob) == sum(fieldLengths) * len(self.entries))
        return header + data, ""


# if value is a dictionary, returns value[name], otherwise returns value
def dictGet(value, name):
    if isinstance(value, dict):
        # Help pycharm figuring it out it's a dict
        """:type :dict"""
        dictionnary = value
        return dictionnary[name]
    else:
        return value
