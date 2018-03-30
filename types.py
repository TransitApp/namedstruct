from __future__ import absolute_import
from __future__ import division
from builtins import str
from past.builtins import basestring
from past.utils import old_div
from builtins import object
import collections
import numbers
import struct

from . import bithelper
from . import constants
from . import stringhelper
from . import values


# given two types, merges them, but if one of them is NullType, returns the other type
def mergeTypes(typeA, typeB):
    if isinstance(typeA, NullType):
        return typeB
    if isinstance(typeB, NullType):
        return typeA
    return typeA.merge(typeB)


# given two types, will ensure that
# the python type of typeA and typeB are the same,
# and that all given keys are the same
def _typeEqualAssert(typeA, typeB, *keys):
    if not type(typeA) == type(typeB):
        raise Exception("can't merge types " + repr(typeA) + " and " + repr(typeB))
    for key in keys:
        valueA = typeA.__getattribute__(key)
        valueB = typeB.__getattribute__(key)
        if valueA != valueB:
            raise Exception(
                    "can't merge types " + repr(typeA) + " and " + repr(typeB) + ", attribute " + key + " doesn't match, "
                    + repr(valueA) + " vs " + repr(valueB))


class Type(object):
    # the type name that is used in C to represent this type
    def __init__(self):
        self.name = None
    
    def getName(self):
        return self.name
    
    # a unique name to refer to the type, for most types it's just the c name
    def getUniqueName(self):
        return self.getName()
    
    # returns all the types that are directly referred/stored in this type (i.e. returns child types)
    def getContainedTypes(self):
        return []
    
    # returns, a generater of all the types that are referred/stored in this type (i.e. returns the whole type tree)
    def getAllContainedTypes(self):
        for t in self.getContainedTypes():
            for t2 in t.getAllContainedTypes():
                yield t2
        yield self
    
    # returns a c++ declaration of the type. If the type does not need to be declared (e.g. int32_t), returns None
    def getDeclaration(self, indent=stringhelper.indent, includeSetters=False):
        return None
    
    def getForwardDeclaration(self):
        return None
    
    def getAccessorFunction(self, memberName, indent=stringhelper.indent):
        return None
    
    def getDeclarationNameSuffix(self):  # for example [] for arrays, [24] for fixed arrays
        return ""
    
    def getNameSuffix(self):  # a suffix for the name - e.g. "ByteOffset" for references
        return ""
    
    def getAlignment(self):
        raise Exception("unimplemented for " + repr(self))
    
    def getWidth(self):
        raise Exception("unimplemented for " + repr(self))
    
    def hasEqualMethod(self):
        return False
    
    def assertValueHasType(self, aValue):
        raise Exception("cannot verify whether " + repr(aValue) + " matches type " + repr(self))
    
    def __repr__(self):
        return self.getUniqueName()
    
    # returns whether the type may change (width) - this will ignore contained types
    def isMutable(self):
        return False
    
    # try if the data type is usually stored directly in a struct, rather than stored via a reference
    # this is not a strict requirement.
    def isImmediate(self):
        return False
    
    # merge the other type with this -
    # will throw an error if the types are inconsistent (starting with their name)
    # the merge is to resolve unknown members
    def merge(self, other):
        raise Exception("unimplemented for " + repr(self))
    
    def dotGraph(self, parent=None):
        result = ""
        if parent is None:
            result += "graph {\n"
        else:
            result += "%s -- %s;\n" % (parent.getName(), self.getName())
        for childType in self.getContainedTypes():
            result += childType.dotGraph(self)
        if parent is None:
            result += "}"
        return result


class PrimitiveType(Type):
    def getAlignment(self):  # by default the primtive type width=alignment
        return self.getWidth()
    
    def isImmediate(self):
        return True
    
    def getFormatChar(self):
        return ""  # overwritten by subclass
    
    def pack(self, aPythonValue):
        # returns a string representing the primitive
        f = "<"  # format prefix defining little endian, standard encoding
        formatChar = self.getFormatChar()
        return struct.pack(f + formatChar, aPythonValue)

    def hasEqualMethod(self):
        return True
    
    def assertValueHasType(self, aValue):
        self.pack(aValue)
    
    # turns a python value into a namedstruct.Value of this primitive type
    def makeValue(self, aValue):
        raise Exception("unimplemented for " + repr(self))


class IntType(PrimitiveType):
    formats = {8: 'b', 16: 'h', 32: 'i', 64: 'q'}  # map from bit width -> format chars
    
    def __init__(self, unsigned, bitWidth):
        super(IntType, self).__init__()
        assert bitWidth in IntType.formats
        self.name = ('u' if unsigned else '') + "int" + str(bitWidth) + "_t"
        self.unsigned = unsigned
        self.bitWidth = bitWidth
    
    def getName(self):
        return self.name
    
    def assertValueHasType(self, aValue):
        if not isinstance(aValue, numbers.Integral):
            raise Exception(str(aValue) + " is not integral")
        if not ((0 <= aValue < 2 ** self.bitWidth)
                if self.unsigned else
                (2 ** (self.bitWidth - 1) > aValue >= -2 ** (self.bitWidth - 1))):
            raise Exception(str(aValue) + " does not fit in " + self.name)
        self.pack(aValue)
    
    def getWidth(self):
        return old_div(self.bitWidth, 8)
    
    def merge(self, other):
        _typeEqualAssert(self, other, "name")
        return self
    
    def getFormatChar(self):
        f = IntType.formats[self.bitWidth]
        return f.upper() if self.unsigned else f.lower()
    
    def makeValue(self, aValue):
        return values.Int(aValue, self.unsigned, self.bitWidth)


INT8 = IntType(False, 8)
INT16 = IntType(False, 16)
INT32 = IntType(False, 32)
INT64 = IntType(False, 64)
UINT8 = IntType(True, 8)
UINT16 = IntType(True, 16)
UINT32 = IntType(True, 32)
UINT64 = IntType(True, 64)
PADDING = INT8


# chars are used to represent strings and blobs, and are unsigned 1 byte values
class CharType(IntType):
    def __init__(self):
        IntType.__init__(self, False, 8)
        self.name = "char"
    
    def getFormatChar(self):
        return "s"
    
    def assertValueHasType(self, aValue):
        if not isinstance(aValue, basestring) or len(aValue) != 1:
            raise Exception(str(aValue) + " is not a char")
        self.pack(bytes(aValue, 'utf-8'))
    
    def makeValue(self, aChar):
        return values.Char(aChar)


CHAR = CharType()


# bit fields
class BitFieldType(Type):
    Field = collections.namedtuple("FieldType", ["name", "type", "bitWidth"])
    
    def __init__(self, name, totalBitWidth=32):
        super(BitFieldType, self).__init__()
        self.dataType = IntType(True, totalBitWidth)
        self.name = name
        self.fields = {}  # field name -> member index
        # self.fieldWidths = []
        self.fieldArray = []
        # self.fieldNames = []
        self.bitWidth = totalBitWidth
    
    def getContainedTypes(self):
        return [field.type for field in self.fieldArray if field.type not in {'i', 'u'}]
    
    def addField(self, field):
        if field.bitWidth + self.getNumUsedBits() > self.bitWidth:
            raise Exception("not enough bits to add field " + field.name + " to bit field " + self.name
                            + " (%d + %d > %d)" % (field.bitWidth, self.getNumUsedBits(), self.bitWidth))
        if field.name in self.fields:
            raise Exception(
                    "cannot use existing field name " + field.name + " as field name for bit field " + self.name)
        stringhelper.assertIsValidIdentifier(field.name)
        self.fieldArray.append(field)
        self.fields[field.name] = len(self.fields)
    
    # adds an int field to the bit field
    def add(self, name, bitWidth=1, signed=False):
        self.addField(BitFieldType.Field(name, "i" if signed else "u", bitWidth))
    
    def addSigned(self, name, bitWidth):
        self.addField(BitFieldType.Field(name, "i", bitWidth))
    
    def addEnum(self, name, enumType):  # TODO - signed, numBits?
        assert isinstance(enumType, EnumType)
        assert isinstance(enumType.enumType, IntType)
        self.addField(BitFieldType.Field(name, enumType, BitFieldType.getRequiredBitsForEnum(enumType)))
    
    @staticmethod
    def getRequiredBitsForEnum(enumType):
        pythonValues = enumType.getPythonValues()
        if not enumType.hasNegativeValues():
            numBits = bithelper.requiredBits(max(pythonValues))
        else:
            numBits = bithelper.requiredBits(max(bithelper.zigZagEncode(max(pythonValues)),
                                                 bithelper.zigZagEncode(min(pythonValues))))
        return numBits
    
    def getUniqueName(self):
        return (self.name + "("
                + (','.join(str(field.bitWidth)
                            for field in self.fieldArray))
                + ")%d" % self.bitWidth)
    
    def getAlignment(self):
        return self.dataType.getAlignment()
    
    def isImmediate(self):
        return True
    
    def getWidth(self):
        return self.dataType.getWidth()
    
    def getNumUsedBits(self):
        return sum(f.bitWidth for f in self.fieldArray)
    
    def hasEqualMethod(self):
        return True
    
    def getForwardDeclaration(self):
        return "struct " + self.getName() + ";"
    
    def getDeclaration(self, indent=stringhelper.indent, includeSetters=False):
        result = "typedef struct __attribute__((packed)) %s {\n" % self.getName()
        # add member
        result = result + indent + self.dataType.getName() + " bits;\n"
        # add accessor functions
        shift = 0
        
        def getTypeName(field):
            return "int" if field.type in {"i", "u"} else field.type.getUniqueName()
        
        setters = ""
        if len(self.fieldArray) > 0:
            fieldNameWidth = max(len(field.name) + len(getTypeName(field)) for field in self.fieldArray)
            maskChars = old_div((max(field.bitWidth for field in self.fieldArray) + 3), 4)
            for field in self.fieldArray:
                fieldName = field.name
                fieldWidth = field.bitWidth
                mask = ("0x%0" + str(maskChars) + "x") % ((1 << fieldWidth) - 1)
                s = "s" if fieldWidth != 1 else " "
                fieldType = getTypeName(field)
                space = " " * (fieldNameWidth - len(fieldName) - len(fieldType))
                useZigZag = (field.type == 'i') if field.type in {'i', 'u'} else field.type.hasNegativeValues()
                
                formatDict = dict(fieldType=fieldType,
                                  indent=stringhelper.indent, fieldName=stringhelper.capitalizeFirst(fieldName),
                                  shift=shift, mask=mask, s=s, space=space, bitWidth=fieldWidth,
                                  fieldNameWidthSpaces=' ' * fieldNameWidth)
                result += (
                    "{indent}/** {bitWidth:2} bit{s} */ inline {fieldType} get{fieldName}() {space}const {{" +
                    " auto v = " + (
                        "(bits >> {shift:2}) & {mask}" if fieldWidth > 0 else ' ' * (16 + maskChars) + "0") + "; "
                                                                                                              " return static_cast<{fieldType}>(" +
                    ("(v >> 1) ^ (-(v & 1))" if useZigZag else "v") +
                    "); " +
                    "}}\n").format(**formatDict)
                storageType = self.dataType.getName()
                intType = (IntType(unsigned=False, bitWidth=self.dataType.bitWidth).getName() + " ") if useZigZag else storageType
                setters += ("{indent}\n"
                            "{indent}inline void set{fieldName}({fieldType} v) {{\n"
                            "{indent}{indent}{intType} intValue = static_cast<{intType}>(v);\n"
                            "{indent}{indent}{storageType} bitValue = " +
                            (
                                "(intValue << 1)^(intValue>>{bitfieldBitsMinus1})" if useZigZag else "intValue") + ";\n"
                                                                                                                   "{indent}{indent}bits = (bits & ~({mask} << {shift:2})) | ((bitValue & {mask}) << {shift:2});\n"
                                                                                                                   "{indent}}}\n").format(
                        intType=intType,
                        storageType=storageType,
                        bitfieldBitsMinus1=self.dataType.bitWidth - 1,
                        **formatDict)
                shift = shift + fieldWidth
                
            if includeSetters:
                result += setters
            mask = "0x%X" % ((1 << self.getNumUsedBits()) - 1)
            result += """{indent}
{indent}inline bool operator==(const {name} other) const {{
{indent}{indent}return (bits & {mask}) == (other.bits & {mask});
{indent}}}
{indent}
{indent}inline bool operator!=(const {name} other) const {{
{indent}{indent}return not (*this == other);
{indent}}}
}} {name};
""".format(name=self.getName(), indent=indent, mask=mask)
            return result
    
    def merge(self, other):
        _typeEqualAssert(self, other, "name", "fieldArray")
        return self


# a type that represents null/none values
class NullType(Type):
    def __init__(self):
        super(NullType, self).__init__()
    
    def getName(self):
        return "void"
    
    def isImmediate(self):
        return False
    
    def merge(self, other):
        _typeEqualAssert(self, other)
        return self


# represents references - they are stored as integer byte offsets to another object, so contain that target type
# the target type may be None, if it is unknown.
# A reference type to None may be merged with any other reference type, if the reference bit width is the same.
# if the reference bit width is 8, will use unsigned references, otherwise the references are signed.
class ReferenceType(Type):
    formats = {8: True, 16: False, 32: False}  # bit width -> isUnsigned?
    
    def __init__(self, targetType, referenceBitWidth=32):
        super(ReferenceType, self).__init__()
        self.referenceBitWidth = referenceBitWidth
        self.targetType = targetType
        self.referenceType = IntType(ReferenceType.formats[referenceBitWidth], referenceBitWidth)
        self.name = self.referenceType.name
    
    def __repr__(self):
        return self.getUniqueName()
    
    #    def __repr__(self):
    #        return "ref"+str(self.referenceType.bitWidth) #+"->"+repr(self.targetType);
    def getContainedTypes(self):
        return [] if self.targetType is None else [self.targetType]
    
    def getAlignment(self):
        return self.referenceType.getAlignment()
    
    def getWidth(self):
        return self.referenceType.getWidth()
    
    def isImmediate(self):
        return True
    
    def getNameSuffix(self):
        return "ByteOffset"
    
    def merge(self, other):
        _typeEqualAssert(self, other)
        self.referenceType.merge(other.referenceType)
        return ReferenceType(mergeTypes(self.targetType, other.targetType),
                             self.referenceBitWidth)
    
    def getUniqueName(self):
        return ("ref" + str(self.referenceBitWidth)
                + "->"
                + (self.targetType.getUniqueName() if self.targetType is not None else "0"))
    
    def getAccessorFunction(self, memberName, indent=stringhelper.indent):
        memberTypeName = self.targetType.getName() if self.targetType is not None else "void"
        functionName = "get" + stringhelper.capitalizeFirst(memberName)
        functionCode = (
            "/** Returns {memberTypeName}-pointer to member {memberName}.\n" +
            " *  If {memberName} is null/void then the result is undefined. */\n" +
            "inline {memberTypeName}* {functionName}() const {{\n" +
            "{indent}return ({memberTypeName}*)(uintptr_t(this)+this->{memberName}{suffix});\n" +
            "}}").format(indent=stringhelper.indent, functionName=functionName, suffix=self.getNameSuffix(),
                         memberName=memberName, memberTypeName=memberTypeName)
        return functionCode


class ArrayType(Type):
    def __init__(self, elementType):
        super(ArrayType, self).__init__()
        if elementType.isMutable():
            raise Exception("cannot use type " + elementType + " for elements in array - it's not finalized")
        if elementType.getWidth() is None:  # may raise exception if width is undefined
            raise Exception("cannot use type " + elementType + " for elements in array - width undefined")
        assert ((-elementType.getWidth()) % elementType.getAlignment() == 0)
        self.elementType = elementType
    
    def getElementType(self):
        return self.elementType
    
    def getContainedTypes(self):
        return [self.elementType]


# array types
# simple arrays are c arrays
class SimpleArrayType(ArrayType):
    # a fixed size of None means array type doesn't have a fixed size
    # we can override alignment (in bytes)
    def __init__(self, elementType, fixedSize=None, byteAlignment=None):
        ArrayType.__init__(self, elementType)
        self.fixedSize = fixedSize
        self.suffix = ""
        self.name = elementType.getName()
        if fixedSize is not None:
            self.suffix = "[" + str(fixedSize) + "]"
        else:
            self.suffix = "[]"
        self.alignment = byteAlignment if byteAlignment is not None else elementType.getAlignment()
        if byteAlignment is not None:
            if byteAlignment < elementType.getAlignment():
                raise Exception("simple array type alignment has to be larger or equal the alignment of the elements")
    
    def getUniqueName(self):
        name = self.elementType.getUniqueName() + self.suffix
        if self.alignment != self.elementType.getAlignment():
            name += "@" + str(self.alignment)
        return name
    
    def getDeclarationNameSuffix(self):
        return self.suffix
    
    def isImmediate(self):
        return self.fixedSize is not None
    
    def getAlignment(self):
        return self.alignment
    
    def getWidth(self):
        if self.fixedSize is not None:
            return self.fixedSize * self.elementType.getWidth()
        else:
            raise Exception("non-fixed array has no width")
    
    def hasEqualMethod(self):
        # TODO - allow overriding the equality test expression, thus allowing equal where self.fixedSize != None
        return False
    
    def merge(self, other):
        _typeEqualAssert(self, other, "fixedSize", "alignment")
        t1 = self.elementType
        t2 = other.elementType
        if t1.getUniqueName() != t2.getUniqueName():
            return SimpleArrayType(t1.merge(t2),  # we only have to merge if the unique type names mismatch
                                   self.fixedSize)
        return self


# array of references - modelled as a struct
class ReferenceArrayType(ArrayType):
    infix = {8: "8", 16: "16", 32: ""}  # infix used to denote the array
    
    def __init__(self, elementType, fixedSize=None, referenceBitWidth=32):
        ArrayType.__init__(self, ReferenceType(elementType, referenceBitWidth))
        self.referenceBitWidth = referenceBitWidth
        self.fixedSize = fixedSize
        arraySuffix = "Ref" + ReferenceArrayType.infix[referenceBitWidth] + "Array"
        if fixedSize is not None:
            arraySuffix = "Size" + str(fixedSize) + arraySuffix
        self.name = elementType.getName() + arraySuffix
        self.uniqueName = elementType.getUniqueName() + arraySuffix
    
    def getCointainedTypes(self):
        return [self.elementType.targetType]
    
    def getUniqueName(self):
        return self.uniqueName
    
    def isImmediate(self):
        return self.fixedSize
    
    def getWidth(self):
        if self.fixedSize is not None:
            return self.fixedSize * self.elementType.getWidth()
        else:
            raise Exception("non-fixed array has no width")
    
    def merge(self, other):
        _typeEqualAssert(self, other, "fixedSize", "referenceBitWidth")
        t1 = self.elementType.targetType
        t2 = other.elementType.targetType
        if t1.getUniqueName() != t2.getUniqueName():
            return ReferenceArrayType(mergeTypes(t1, t2),  # we only have to merge if the unique type names mismatch
                                      self.fixedSize)
        return self
    
    def getAlignment(self):
        return min(self.elementType.getAlignment(), 4)
    
    def getForwardDeclaration(self):
        return "struct " + self.getName() + ";"
    
    def getDeclaration(self, indent=stringhelper.indent, includeSetters=False):
        result = "typedef struct __attribute__((packed)) %s {\n" % self.getName()
        # add member
        result = (result + indent + self.elementType.referenceType.getName() + " elementByteOffsets"
                  + "[" + (str(self.fixedSize) if self.fixedSize is not None else "") + "]"
                  + ";\n" + indent + "\n")
        
        # add accessor function
        elementTypeName = self.elementType.targetType.getName()
        result += (
            "{indent}/** Returns {elementTypeName}-pointer to the element at the given index.\n" +
            "{indent} *  If the element at the given index is null/void, then the result is undefined. */\n" +
            "{indent}inline {elementTypeName}* get(const int index) const {{\n" +
            "{indent}{indent}return ({elementTypeName}*)(uintptr_t(this)+this->elementByteOffsets[index]);\n" +
            "{indent}}}").format(indent=stringhelper.indent, elementTypeName=elementTypeName)
        
        # finish
        result = result + "\n} " + self.getName() + ";"
        return result


# Create an integer enum with the given name and mapping. Just calls the constructor of EnumType
def IntEnumType(name, mapping, bitWidth=32, unsigned=False):
    return EnumType(name, IntType(unsigned=unsigned, bitWidth=bitWidth), mapping)


class EnumType(Type):
    # Create an enum with the given type name, underlying type and name->value mapping.
    # The underlying type should be a primitive type (integer, char)
    # the mapping should either be a dictionary (names will be sorted), or a list of name->value pairs
    def __init__(self, name, enumType, mapping):
        super(EnumType, self).__init__()
        assert isinstance(enumType, PrimitiveType)
        self.enumType = enumType
        self.name = enumType.name
        self.mapping = collections.OrderedDict()  # name -> namedstructValue that represents the value
        self.values = collections.OrderedDict()  # name -> EnumValue
        self.uniqueName = name
        self._hasNegativeValues = False
        # turn dictionaries into list of pairs
        try:
            mapping = sorted(mapping.items())
        except AttributeError:
            pass
        for name, value in mapping:
            stringhelper.assertIsValidIdentifier(name)
            namedstructValue = enumType.makeValue(value)
            # for py3 compatibility
            if isinstance(value, int):
                is_negative_value = value < 0
            else:
                is_negative_value = False
            self._hasNegativeValues = self._hasNegativeValues or is_negative_value
            self.mapping[name] = namedstructValue
            enumValue = values.EnumValue(self, name)  # the enum value constructor requres the self.mapping value
            self.values[name] = enumValue
            setattr(self, name, enumValue)
    
    def __getitem__(self, key):
        return self.values[key]
    
    def __getattr__(self, item):
        return self.values[item]
    
    def getEnumType(self):
        return self.enumType
    
    def getUniqueName(self):
        return self.uniqueName
    
    def getContainedTypes(self):
        return [self.getEnumType()]
    
    def getDeclaration(self, indent=stringhelper.indent, includeSetters=False):
        header = "enum class {uniqueName} : {valueType} {{".format(uniqueName=self.uniqueName, valueType=self.name)
        members = [
            "{indent}{name} = {value}".format(indent=indent, name=name, value=value.getLiteral())
            for name, value in list(self.mapping.items())
            ]
        return header + "\n" + ",\n".join(members) + "\n};"
    
    def getForwardDeclaration(self):
        return "enum class {name} : {type};".format(name=self.uniqueName, type=self.name)
    
    def getAccessorFunction(self, memberName, indent=stringhelper.indent):
        functionName = "get" + stringhelper.capitalizeFirst(memberName)
        functionCode = (
            "/** Returns {memberName} as a {type} enum */\n" +
            "inline {type} {functionName}() const {{\n" +
            "{indent}return static_cast<{type}>(this->{memberName}{suffix});\n" +
            "}}").format(indent=stringhelper.indent, functionName=functionName, suffix=self.getNameSuffix(),
                         memberName=memberName, type=self.uniqueName)
        return functionCode
    
    def getDeclarationNameSuffix(self):  # for example [] for arrays, [24] for fixed arrays
        return ""
    
    def getNameSuffix(self):  # a suffix for the name - e.g. "ByteOffset" for references
        return "EnumValue"
    
    def getAlignment(self):
        return self.getEnumType().getAlignment()
    
    def getWidth(self):
        return self.getEnumType().getAlignment()
    
    def hasEqualMethod(self):
        return True
    
    def assertValueHasType(self, aValue):
        raise Exception("cannot verify whether " + repr(aValue) + " matches type " + repr(self))
    
    def __repr__(self):
        return self.getUniqueName()
    
    def isMutable(self):
        return False
    
    def isImmediate(self):
        return True
    
    # merge the other type with this -
    # will throw an error if the types are inconsistent (starting with their name)
    # the merge is to resolve unknown members
    def merge(self, other):
        _typeEqualAssert(self, other, "name", "enumType", "mapping")
        return self
    
    # returns the set of values used by theis enum
    def getPythonValues(self):
        return set(v.getPythonValue() for v in list(self.mapping.values()))
    
    def hasNegativeValues(self):
        return self._hasNegativeValues
        
        # this is the only type that is mutable


class StructType(Type, constants.AddConstantFunctions):
    def __init__(self, name):
        super(StructType, self).__init__()
        self.constantPool = constants.ConstantPool()
        self.mutable = True
        self.name = name
        self.alignment = 1
        self.members = {}  # member name -> member index
        self.names = []  # list of member names
        self.offsets = []  # list of member offsets
        self.types = []  # list of member types
        self.numPadBytes = 0  # the total number of padding bytes in struct
    
    def addConstant(self, name, value):  # should return self
        self.constantPool.addConstant(name, value)
        return self
    
    def getConstantPool(self):
        return self.constantPool
    
    # will add padding bytes until the current struct is aligned to the given byte alignment
    # returns how many padding bytes were added
    def addPadding(self, byteAlignment):
        # perform alignment
        padding = 0
        currentWidth = self.getCurrentWidth()
        if currentWidth > 0:
            while (-currentWidth) % byteAlignment != 0:
                self.addMember("paddingByte" + str(self.numPadBytes), PADDING)
                self.numPadBytes += 1
                currentWidth += 1
                padding += 1
        return padding
    
    # returns how many padding bytes were added before adding the member
    def addMember(self, name, memberType):
        if not self.mutable:
            raise Exception("cannot add member to finalized struct " + self.name)
        # check validity
        if name in self.members:
            raise Exception("name %s already in struct %s" % (name, self.name))
        assert (isinstance(memberType, Type))
        stringhelper.assertIsValidIdentifier(name)
        padding = self.addPadding(memberType.getAlignment())
        # actually add member
        self.members[name] = len(self.offsets)
        self.names.append(name)
        self.offsets.append(self.getCurrentWidth())
        self.types.append(memberType)
        self.alignment = max(self.alignment, memberType.getAlignment())
        return padding
    
    # returns the byte offset,type,name for the member at the given index
    def getMember(self, index):
        return self.offsets[index], self.types[index], self.names[index]
    
    def getWidth(self):
        if self.mutable:
            raise Exception("cannot ask the width of non-finished struct type " + repr(self))
        return self.getCurrentWidth()
    
    def hasEqualMethod(self):
        return len(self.members) > 0 and all(t.hasEqualMethod() for t in self.types)
    
    def getCurrentWidth(self):
        if len(self.offsets) == 0:
            return 0
        return self.offsets[-1] + self.types[-1].getWidth()
    
    # this will finalize the definition of this struct. The Struct may never grow in size
    # from this point on, otherwise it will become incompatible. Reserved elements may be added
    # to reserve space for future additions. After finalizing, the struct may have a fixed
    # width, depending on whether the last member is fixed. returns the number of padding bytes
    def finalize(self, byteAlignment=4):
        if self.getCurrentWidth() == 0:
            raise Exception("cannot finalize empty struct")
        paddingBytes = self.addPadding(byteAlignment)
        self.mutable = False
        return paddingBytes
    
    def isImmediate(self):
        return not self.mutable
    
    # alignment of the struct is the max of all the members
    def getAlignment(self):
        return self.alignment
    
    def getContainedTypes(self):
        return list(self.types)
    
    def merge(self, other):
        _typeEqualAssert(self, other, "name", "mutable", "names")
        # TODO - merge constant pools
        # go through and check if the unique names are the same - in that case we can just return self
        equal = True
        for i, name in enumerate(self.names):
            t1 = self.types[i]
            t2 = other.types[i]
            if t1.getUniqueName() != t2.getUniqueName():
                equal = False
                break
        if equal:
            return self
        result = StructType(self.name)
        for i, name in enumerate(self.names):
            t1 = self.types[i]
            t2 = other.types[i]
            if t1.getUniqueName != t2.getUniqueName():
                result.addMember(name, t1.merge(t2))  # we only have to merge if the unique type names mismatch
            else:
                result.addMember(name, t1)
        result.mutable = self.mutable
        result.constantPool = self.constantPool  # FIXME - This is a hack! Properly deal with cosntant pools!
        return result
    
    def getForwardDeclaration(self):
        return "struct " + self.getName() + ";"
    
    def getDeclaration(self, indent=stringhelper.indent, includeSetters=False):
        result = "typedef struct __attribute__((packed)) %s {\n" % self.getName()
        
        # add constants
        if self.constantPool.getNumConstants() > 0:
            result = (result
                      + indent
                      + self.constantPool.getConstantDeclarations().replace("\n", "\n" + indent) + "\n")
        
        # add members
        typeWidth = max([0] + [len(memberType.getName()) for memberType in self.types])
        for i, memberName in enumerate(self.names):
            memberType = self.types[i]
            memberName = memberName + memberType.getNameSuffix()
            space = " " * (typeWidth + 1 - len(memberType.getName()))
            comment = ""  # comment comes from struct or from type
            result = (result
                      + indent
                      + memberType.getName() + space
                      + memberName + memberType.getDeclarationNameSuffix() + ";"
                      + comment
                      + "\n")
        
        # add accessor functions
        functions = ""
        for i, memberName in enumerate(self.names):
            memberType = self.types[i]
            function = memberType.getAccessorFunction(memberName, indent=stringhelper.indent)
            if function is not None:
                function = ("\n" + function + "\n").replace("\n", "\n" + indent)
                functions += function
        if len(functions) > 0:
            result = result + functions[:-len(indent)]
        
        # add equal
        if self.hasEqualMethod():
            result += """{indent}
            {indent}bool operator==(const {name}& other) const {{
            {indent}{indent}return {prefix}{comparisonExpression}{postfix};
            {indent}}}
            {indent}
            {indent}bool operator!=(const {name}& other) const {{
            {indent}{indent}return not (*this == other);
            {indent}}}
            """.format(name=self.getName(),
                       indent=indent,
                       prefix="(    " if len(self.names) > 1 else "",
                       postfix=")" if len(self.names) > 1 else "",
                       comparisonExpression=(("\n{i}{i}        and ".format(i=indent))
                                             .join("{name}{suffix} == other.{name}{suffix}"
                                                   .format(name=n, suffix=self.types[i].getNameSuffix())
                                                   for i, n in enumerate(self.names))))
        # finish
        result = result + "} " + self.getName() + ";"
        return result


# a special struct type, an array of bitfield values
class BitFieldArrayType(Type):
    def __init__(self, name, fields):
        super(BitFieldArrayType, self).__init__()
        self.name = name
        if len(fields) == 0:
            raise Exception("BitFieldArrayType needs at least one field")
        for field in fields:
            stringhelper.assertIsValidIdentifier(field)
            assert (field != 'bitFieldArrayEntryBits')
        self.fields = fields
    
    def getFields(self):
        return self.fields
    
    def getUniqueName(self):
        return "BitFieldArray:" + self.name
    
    def getAlignment(self):
        return 4
    
    def getForwardDeclaration(self):
        return "struct " + self.getName() + ";"
    
    def getDeclaration(self, indent=stringhelper.indent, includeSetters=False):
        result = "typedef struct __attribute__((packed)) %s {\n" % self.getName()
        
        # add members
        result += indent + "uint16_t bitFieldArrayEntryBits;\n"
        for i, field in enumerate(self.fields):
            result += indent + "uint16_t %sBitOffset;\n" % field
        result += indent + "uint16_t endOffset;"
        
        # add accessor functions
        # by index accessors:
        result += """{indent}
{indent}
{indent}/** returns the number of fields stored in this. Incoming data may have fewer
{indent}    or more than the defined number of fields, in which case it's still valid to
{indent}    access members, but only where fieldIndex < numFields. */
{indent}inline int getNumFields() const {{
{indent}{indent}return ((((uint16_t*)(this))[1]) >> 4) - 2;
{indent}}}
{indent}
{indent}/** returns the bit offset of field with the given index at the given element index */
{indent}inline int getBitOffsetByFieldIndex(int fieldIndex, int elementIndex) const {{
{indent}{indent}return ((uint16_t*)(this))[1+fieldIndex] + elementIndex*bitFieldArrayEntryBits;
{indent}}}
{indent}
{indent}
{indent}/** returns the number of bits used by the field with the given field index. */
{indent}inline int getNumBitsByFieldIndex(int fieldIndex) const {{
{indent}{indent}return ((uint16_t*)(this))[2+fieldIndex] - ((uint16_t*)(this))[1+fieldIndex];
{indent}}}
{indent}
{indent}/** returns the value of a field with given field index at the given element index, assuming it has <=31 bits. */
{indent}inline uint32_t getByFieldIndex(int fieldIndex, int elementIndex) const {{
{indent}{indent}const int thisBitOffset = ((uint16_t*)(this))[1+fieldIndex];
{indent}{indent}const int nextBitOffset = ((uint16_t*)(this))[2+fieldIndex];
{indent}{indent}const int bitOffset = thisBitOffset + elementIndex*bitFieldArrayEntryBits;
{indent}{indent}return namedstruct::readBits(this, bitOffset, nextBitOffset-thisBitOffset);
{indent}}}""".format(indent=stringhelper.indent)
        # by name accessors:
        for i, field in enumerate(self.fields):
            if i == len(self.fields) - 1:
                nextBitOffset = "endOffset"
            else:
                nextBitOffset = self.fields[i + 1] + "BitOffset"
            result += """{indent}
{indent}
{indent}/** returns the bit offset of field {field} at the given index, assuming it is present */
{indent}inline int get{Field}BitOffset(int index) const {{
{indent}{indent}return {field}BitOffset + index*bitFieldArrayEntryBits;
{indent}}}
{indent}
{indent}/** returns the bit offset of field {field} at the given index, assuming it is present */
{indent}inline int has{Field}() const {{
{indent}{indent}return getNumFields() > {i};
{indent}}}
{indent}
{indent}/** returns the number of bits used by field {field}, assuming it is present */
{indent}inline int get{Field}NumBits() const {{
{indent}{indent}return {nextBitOffset} - {field}BitOffset;
{indent}}}
{indent}
{indent}/** returns the value of the field {field} at the given index, assuming it is present, and assuming it has <=31 bits */
{indent}inline uint32_t get{Field}(int index) const {{
{indent}{indent}const int bitOffset = {field}BitOffset + index*bitFieldArrayEntryBits;
{indent}{indent}const int nextBitOffset = {nextBitOffset};
{indent}{indent}return namedstruct::readBits(this, bitOffset, nextBitOffset-{field}BitOffset);
{indent}}}
{indent}
{indent}/** returns the value of the field {field} at the given index, assuming it has <= 31 bits, or the default the field is not present. */
{indent}inline uint32_t get{Field}OrDefault(int index, int defaultValue = 0) const {{
{indent}{indent}return has{Field}() ? get{Field}(index) : defaultValue;
{indent}}}""".format(i=i, field=field, indent=stringhelper.indent, nextBitOffset=nextBitOffset,
                     Field=stringhelper.capitalizeFirst(field))
        
        # finish
        result = result + "\n} " + self.getName() + ";"
        return result
    
    def merge(self, other):
        _typeEqualAssert(self, other, "fields")
        return self
    
    def isImmediate(self):
        return False
    
    def getWidth(self):
        raise Exception("cannot ask width of bitfield array type")
