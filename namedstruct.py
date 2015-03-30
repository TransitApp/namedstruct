import numbers, re, array, collections, struct, math
import stringhelper, bithelper

# namedstruct library
# allows creation of binary files like you would build a json file, by just adding
# key:value pairs to some data blob. But the binary dump contains no
# metadata. Information about the file format is generated from the data blob
# as a c++ header file, which allows reading the data.
# Thus, to decode a file, the c++ header file needs to be available in order to 
# decode the data. Advantage is small size, exact control of how the stored data
# is represented, and fast access. There is no decoding, data is laid as plain
# old structs in memory - except for references, which are stored as byte offsets
# relative to where they are stored (i.e. there is one addition required to resolve
# a reference).
#
# The generated c++ headers include accessor functions that makes accessing data easy.
#
# This library supports many data types:
#   primitive data, structs, strings, arrays (fixed length/flexible, reference arrays),
#   bitfields, binary blobs, references (incl. typed null references), 
#   constant declarations
#
# Refer to the test cases at the bottom to see how the library can be used.
# Example:
#   # generate data
#   s = (namedstruct.Struct("MyStruct") # create struct with type name: MyStruct
#        .addInt32("bla",234)  # add an signed 32-bit integer with value 234, and name 'bla'
#        .add("greet","Hello World")) # add a string as a ref to char - the type is inferred from the argument                 
#   
#   # get c++ header definition
#   print namedstruct.generateHeader(s)
#
#   # get data dump
#   data = namedstruct.pack(s) # returns a binary string, that can be written via open(..,"wb").write(..)



# this offset has to follow the required alignment
# padding bytes may have to be added at the reference data offset
# value.pack(last struct offset, offset where referred data starts)
#   returns (packed data, referred offseted data)
# - if referred offset is None, just appends all referred data
# struc.pack, array.pack - complicated
# intvalue.pack - easy
# getImmediateDataSize() - the size of the data as stored immediately, i.e. excluiding referred data
#
#
# type.pack(address)
#  returns list of (string or value)
#  
# 
# FIXME:
#   - merge operation for constant pools, merge global constants
#   - when generating the huffman tests, char array gets printed twice.
#   - when adding a struct as immediate, which has in turn a reference, the reference is stored relative to the parent struct
#   - when using a null reference, the type doesn't appear to get included in the result
#
# TODO:
#   - exception on overriding constant?
#   - make a variableBitUIntArray
#   - deal with empty blobs ... their data shouldn't take up space, should they be zero? point to 1?
#   + deal with alignment of blobs
#   + add isNull for references
#   + add gzip blob 8byte header? {compressed,uncompressed}
#   + descriptors?
# OLD TODOs:
#   - rename the <Value>Value classes to <Value>
#   - negative reference?
#   - reference to blob, where the reference goes into the middle of it?
#   + bitfields
#     - bit fields could use an a single intvalue
#     - every field has a name
#   + merge constants
#   - enforce naming constraints
#   ++ flexible array
#     - we need a notion of a prefix and a suffix
#       - prefix: data that has to be there, coming before the real data
#       - suffix: padding bytes that have to be there, but that may be ovewritten by other structures
#   - union type - just a ref to multiple possible things 
#   - allow comments - always just pick the longest comment
#   - float type
#   - do better resolution of dependencies
#   - do smarter packing
#     - allow circular references, allow reusing objects
#     - optimize ordering so that reference values fit into the references
#   - todo figure out a way to validate arrays - is this already done?
#
#
# add<primitive>(name,value
#
#
# add(name,value) # int->int32, string->string, other value->ref(value)
#
#
# pack() -> simple, tree traversal creation of data
# packOptimized() -> will attempt to minimize the padding bytes used, or store data in padding?
#
#
#
#
# arrays:
#  - fixed size
#  - variable size uknown
#  - variable size known
#  - different dimensions
#  - different int-widths for shape
#
#
# int32_Size10Array    - fixed width array, we could also just use int32 x[10];
# int32*               - that's an unknown array, stored with byte offset
# int32_array          - single dimension known
# int32_2dArray        - 2d array, known dimension, 32 bit storage for shape
# int32_2u8dArray      - shape vars are u8
# int32_u16Rank4Array  - 4d array, known dimension, 16 bit storage for shape

# int32Array
# int32Matrix
# int32RefArray        - ref array allows elements with unknown size
# int32RefMatrix
# int32Rank3Array8
# int32Array8
#
#
# pack function
# - optional argument offset
#   - that's where child objects will be stored
#

# use 
# x_byteOffset
# or
# int32_array_u8offset = x_byteOffset

# reference array

# finalize should allow defining to what alignment the struct should be padded (no?)


# these should be singleton in the name - but things can be added as required
# actually they can't be singletons, because namedstruct isn't global
# --- unless we build factories... mmmh.
# we could get a factory and define a namespace for it.
#
#
# TODO
# - structs cannot be empty -> thus a byteOffset of 0 refers to nullptr
#
# - turn blobs into a Struct, so that there are methods like 
#    getBit
#    getBits
#    getBitReader
#
# - constructor methods



indent = " "*4

# ############# PUBLIC FUNCTIONS ############################################################
# returns the c++ header file text that defines the given struct(s), including all nested
# structs. If a namespace is set, the c++ code will be defined inside that namespace.
# If the 'define' is set, will use use that for the IF/IFNDEFs, otherwise till use the name of the
# first struct.
# headText can be used to add license/author etc.
# structs may be a single struct or a sequence of structs.
# constantPools may be a single constantPool or a sequence of constant Pools
def generateHeader(structs,constantPools=None,namespace=None,define=None,headText="",indent=indent):
    # massage arguments
    if isinstance(structs,Struct): structs = [structs]
    if constantPools == None: constantPools = []
    if isinstance(constantPools,ConstantPool): constantPools = [constantPools]
    if define == None: define = "__"+structs[0].getType().getName().upper()+"__"
    namespaceString = ""
    if namespace!=None:
        stringhelper.assertIsValidIdentifier(namespace)
        namespaceString = "namespace %s {\n" % namespace
    
    # get all types
    structTypes = []
    for s in structs:
        assert(isinstance(s,Struct))
        structTypes.append(s.type)
    types = getAllTypes(structTypes)
    
    # start header
    result = headText+"""
// Code generated by namedstruct.py

#ifndef {define}
#define {define}
#include <stdint.h>
#include "bits.h"

{namespaceString}""".format(define=define,namespaceString=namespaceString)
    currentIndent = "" if namespace==None else indent
              
    # put constants
    constants = ""
    if len(constantPools) > 0:
        for pool in constantPools:
            if pool.getNumConstants() > 0:
                constants = (constants
                             +"\n" + indent
                             +pool.getConstantDeclarations().replace("\n","\n"+indent))
    if len(constants) > 0:
        result = (result
                  + currentIndent + "\n" + currentIndent
                  +"// *** constants *****************************"
                  +constants
                  +"\n" + currentIndent + "\n")


    # put forward declaration of all types - todo put only necessary ones...
    forwardDeclarations = ""
    for type in types.values():
        forwardDeclaration = type.getForwardDeclaration()
        if forwardDeclaration == None: continue
        forwardDeclarations = forwardDeclarations + currentIndent + forwardDeclaration + "\n"
    if len(forwardDeclarations) >= 0:
        result = (result
                  + currentIndent + "\n" + currentIndent
                  +"// *** forward declarations ******************\n"
                  +forwardDeclarations)


    # put declaration of all types
    typeDeclarations = ""
    for name,type in types.items():
        declaration = type.getDeclaration(indent)
        if declaration == None: continue
        typeDeclarations = (typeDeclarations
                            +"\n"+currentIndent
                            +(declaration
                              +"\n").replace("\n","\n"+currentIndent)
                            +"\n"+currentIndent)
    if len(typeDeclarations) >= 0:
        result = (result + currentIndent + "\n" + currentIndent + "\n"
                  +currentIndent +"// *** type declarations *********************"
                  +typeDeclarations) 

    # finish header
    result = (result
              +"\n"
              +("" if not namespace else "}\n")
              +"#endif /* defined(%s) */\n" % define)
    return result


# packs a struct into a string, storing all contained values inside it
def pack(struct):
    data, offsetedData = struct.pack(None)
    assert(len(offsetedData) == 0)
    return data


# given a python object, will return a reasonable Value for it
# Value   -> returns the argument
# int     -> int32 value
# string  -> string value
# None    -> Null value
# an iterable -> an array value, using getValue on the elements
def getValue(value):
    if isinstance(value,Value):
        return value
    elif isinstance(value, numbers.Integral):
        return IntValue(value)
    elif isinstance(value, basestring):
        return StringValue(value)
    elif value == None:
        return NullValue()
    elif hasattr(value, "__iter__"):
        return getArrayValue(value)
    else:
        raise Exception("can't convert "+str(value)+" to a Value");

# given an array, will return a reasonable array value for it, i.e. makes a Value array by turning
# every element into a value using "getValue"
def getArrayValue(arrayValues,fixedSize=None):
    arrayValues = [getValue(v) for v in arrayValues]
    if isinstance(arrayValues, basestring):
        return stringValue(value,fixedSize)
    else:
        t = arrayValues[0].getType()
        for v in arrayValues[1:]:
            t = _mergeTypes(t,v.getType())
        if isinstance(t,ReferenceType):
            raise Exception("can't build arrays out of references")
        if t.isImmediate(): # elements are immediate - just build simple array
            return SimpleArray(t,arrayValues,fixedSize)
        else:
            return ReferenceArrayValue(arrayValues,fixedSize) # build reference array



# returns an ordered dict of unique name -> type of all the unique types that are contained in the list
# of types. The types with the same name are merged, which may result in exceptions if the types
# are inconsistent. Thus this validates all the types contained in the type list
def getAllTypes(typeList):
    types = collections.OrderedDict() # name -> type
    for root in typeList:
        for t in root.getAllContainedTypes():
            name = t.getUniqueName()
            if name in types:
                types[name] = types[name].merge(t)
            else:
                types[name] = t
    return types



# ############# CONSTANTS ##################################################################
# an object that has the add constant functions - they all get dispatched to "addConstant"
class AddConstantFunctions(object):
    def addConstant(self,name,value): # should return self
        raise Exception("not implemented")
    def addInt32Constant(self,name,value): return self.addConstant(name,IntValue(_dictGet(value,name),False,32))
    def addCharConstant (self,name,value): return self.addConstant(name,CharValue(_dictGet(value,name)))

# an object that can have constants associated with it
class ConstantPool(AddConstantFunctions):
    def __init__(self):
        self.constants = collections.OrderedDict() # name -> value
    def addConstant(self,name,value):
        value = getValue(_dictGet(value,name))
        value.getLiteral() # check whether there is a literal method
        self.constants[name] = value
        return self
    # returns the value associated with the constant
    def get(self,name):
        return self.constants[name]

    def getConstantDeclarations(self):
        result = ""
        typeWidth = max([len(v.getType().getName()) for v in self.constants.values()]+[0])
        for name,value in self.constants.items():
            typeName = value.getType().getName()
            space = " "*(typeWidth-len(typeName))
            literal = value.getLiteral()
            result = (result
                      +"static constexpr "+typeName
                      +" "+space
                      +name+value.getType().getDeclarationNameSuffix()
                      +" = "+literal+";\n")
        return result[:-1]
    def getNumConstants(self):
        return len(self.constants)


# ############# TYPES #######################################################################
class Type(object):
    # the type name that is used in C to represent this type
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
    def getDeclaration(self,indent=indent):
        return None
    def getForwardDeclaration(self):
        return None
    def getAccessorFunction(self,memberName,indent=indent):
        return None
    def getDeclarationNameSuffix(self): # for example [] for arrays, [24] for fixed arrays
        return ""
    def getNameSuffix(self): # a suffix for the name - e.g. "ByteOffset" for references
        return ""
    def getAlignment(self):
        raise Exception("unimplemented for "+repr(self))
    def getWidth(self):
        raise Exception("unimplemented for "+repr(self))
    def assertValueHasType(self,aValue):
        raise Exception("cannot verify whether "+repr(aValue)+" matches type "+repr(self))
    def __repr__(self):
        return self.getUniqueName();
    # returns whether the type may change (width) - this will ignore contained types
    def isMutable(self):
        return False
    # try if the data type is usually stored directly in a struct, rather than stored via a reference
    # this is not a strict requirement.
    def isImmediate(self):
        return False;
    # merge the other type with this -
    # will throw an error if the types are inconsistent (starting with their name)
    # the merge is to resolve unknown members
    def merge(self,other):
        raise Exception("unimplemented for "+repr(self))


class PrimitiveType(Type):
    def getAlignment(self): # by default the primtive type width=alignment
        return self.getWidth();
    def isImmediate(self):
        return True;
    def pack(self,aPythonValue): # returns a string representing the primitive
        f="<" # format prefix defining little endian, standard encoding
        formatChar = self.getFormatChar()
        return struct.pack(f+formatChar,aPythonValue)
    def assertValueHasType(self,aValue):
        self.pack(aValue)


class IntType(PrimitiveType):
    formats = {8:'b', 16:'h', 32:'i', 64:'q'} # map from bit width -> format chars
    def __init__(self,unsigned=False,bitWidth=32):
        assert bitWidth in IntType.formats
        self.name = ('u' if unsigned else '')+"int"+str(bitWidth)+"_t"
        self.unsigned = unsigned
        self.bitWidth = bitWidth
    def getName(self):
        return self.name
    def assertValueHasType(self,aValue):
        if not isinstance(aValue, numbers.Integral):
            raise Exception(str(aValue)+" is not integral")
        if not ((aValue >= 0 and aValue < 2**self.bitWidth)
                if self.unsigned else
                (aValue < 2**(self.bitWidth-1) and aValue >= -2**(self.bitWidth-1))):
            raise Exception(str(aValue)+" does not fit in "+self.name)
        self.pack(aValue)
    def getWidth(self):
        return self.bitWidth/8
    def merge(self,other):
        _typeEqualAssert(self,other,"name")
        return self
    def getFormatChar(self):
        f = IntType.formats[self.bitWidth]
        return f.upper() if self.unsigned else f.lower()
INT8   = IntType(False,8)
INT16  = IntType(False,16)
INT32  = IntType(False,32)
INT64  = IntType(False,64)
UINT8  = IntType(True, 8)
UINT16 = IntType(True, 16)
UINT32 = IntType(True, 32)
UINT64 = IntType(True, 64)




# chars are used to represent strings and blobs, and are unsigned 1 byte values
class CharType(IntType):
    def __init__(self):
        IntType.__init__(self,False,8)
        self.name = "char"
    def getFormatChar(self):
        return "s"
    def assertValueHasType(self,aValue):
        if not isinstance(aValue, basestring) or len(aValue) != 1:
            raise Exception(str(aValue)+" is not a char")
        self.pack(aValue)
CHAR = CharType()


# bit fields
class BitFieldType(Type):
    def __init__(self,name,totalBitWidth=32):
        self.dataType = IntType(True,totalBitWidth)
        self.name = name
        self.fields = {}  # field name -> member index
        self.fieldWidths = []
        self.fieldNames = []
        self.bitWidth = totalBitWidth
    # adds a field to the bit field
    def add(self,name,bitWidth=1):
        if bitWidth + sum(self.fieldWidths) > self.bitWidth:
            raise Exception("not enough bits to add field "+name+" to bit field "+self.name
                            +" (%d + %d > %d)" % (bitWidth,sum(self.fieldWidths),self.bitWidth))
        if name in self.fields:
            raise Exception("cannot use existing field name "+name+" as field name for bit field "+self.name)
        assert(bitWidth > 0)
        self.fieldWidths.append(bitWidth)
        self.fieldNames.append(name)
        self.fields[name] = len(self.fields)
    def getUniqueName(self):
        return (self.name + "("
                +(','.join(str(self.fieldWidths[i])
                           for i,name in enumerate(self.fieldNames)))
                +")%d" % self.bitWidth)
    def getAlignment(self):
        return self.dataType.getAlignment()
    def isImmediate(self):
        return True;
    def getWidth(self):
        return self.dataType.getWidth()
    def getForwardDeclaration(self):
        return "struct "+self.getName()+";"
    def getDeclaration(self,indent=indent):
        result = "typedef struct __attribute__((packed)) %s {\n" % self.getName()
        # add member
        result = result + indent + self.dataType.getName() + " bits;\n"
        # add accessor functions
        shift = 0
        if len(self.fieldNames) > 0:
            fieldNameWidth = max(len(name) for name in  self.fieldNames)
            maskChars = (max(self.fieldWidths)+3)/4
            for i,fieldWidth in enumerate(self.fieldWidths):
                fieldName = self.fieldNames[i]
                mask = ("0x%0"+str(maskChars)+"x") % ((1 << fieldWidth) - 1)
                s = "s" if fieldWidth > 1 else " "
                space = " "*(fieldNameWidth - len(fieldName))
                result = result + ("{indent}/** {bitWidth:2} bit{s} */ inline int get{fieldName}() {space}const {{"+
                                   " return (bits >> {shift:2}) & {mask}; "+
                                   "}}\n").format(
                                       indent=indent, fieldName=stringhelper.capitalizeFirst(fieldName),
                                       shift=shift, mask=mask, s=s, space=space, bitWidth=fieldWidth)
                shift = shift + fieldWidth
        return result + "} " + self.getName() + ";"
    def merge(self,other):
        _typeEqualAssert(self,other,"name","fieldNames","fieldWidths")
        return self


# a type that represents null/none values
class NullType(Type):
    def __init__(self):
        pass
    def getName(self):
        return "void"
    def isImmediate(self):
        return False;
    def merge(self,other):
        _typeEqualAssert(self,other)
        return self
        


# represents references - they are stored as integer byte offsets to another object, so contain that target type
# the target type may be None, if it is unknown.
# A reference type to None may be merged with any othe reference type, if the refere bit width is the same.
# if the reference bit width is 8, will use unsigned references, otherwise the references are signed.
class ReferenceType(Type):
    formats = {8:True,16:False,32:False} # bit width -> isUnsigned?
    def __init__(self,targetType,referenceBitWidth=32):
        self.referenceBitWidth = referenceBitWidth
        self.targetType = targetType;
        self.referenceType = IntType(ReferenceType.formats[referenceBitWidth],referenceBitWidth);
        self.name = self.referenceType.name
    def __repr__(self):
        return self.getUniqueName();
#    def __repr__(self):
#        return "ref"+str(self.referenceType.bitWidth) #+"->"+repr(self.targetType);
    def getContainedTypes(self):
        return [] if self.targetType==None else [self.targetType]
    def getAlignment(self):
        return self.referenceType.getAlignment()
    def getWidth(self):
        return self.referenceType.getWidth()
    def isImmediate(self):
        return True;
    def getNameSuffix(self):
        return "ByteOffset"
    def merge(self,other):
        _typeEqualAssert(self,other)
        self.referenceType.merge(other.referenceType)
        return ReferenceType(_mergeTypes(self.targetType,other.targetType),
                             self.referenceBitWidth)
    def getUniqueName(self):
        return ("ref"+str(self.referenceBitWidth)
                +"->"
                +(self.targetType.getUniqueName() if self.targetType != None else "0"))
    def getAccessorFunction(self,memberName,indent=indent):
          memberTypeName = self.targetType.getName() if self.targetType != None else "void"
          functionName = "get"+stringhelper.capitalizeFirst(memberName);
          functionCode = (
              "/** Returns {memberTypeName}-pointer to member {memberName}.\n"+
              " *  If {memberName} is null/void then the result is undefined. */\n"+
              "inline {memberTypeName}* {functionName}() const {{\n"+
              "{indent}return ({memberTypeName}*)(uintptr_t(this)+this->{memberName}{suffix});\n"+
              "}}").format(indent=indent,functionName=functionName,suffix=self.getNameSuffix(),
                             memberName=memberName,memberTypeName=memberTypeName)
          return functionCode


class ArrayType(Type):
    def __init__(self,elementType):
        if elementType.isMutable():
            raise Exception("cannot use type "+elementType+" for elements in array - it's not finalized")
        if elementType.getWidth()==None: # may raise exception if width is undefined
            raise Exception("cannot use type "+elementType+" for elements in array - width undefined")
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
    def __init__(self,elementType,fixedSize=None,byteAlignment=None):
        ArrayType.__init__(self,elementType)
        self.fixedSize = fixedSize
        self.suffix = ""
        self.name = elementType.getName()
        if fixedSize != None:
            self.suffix = "["+str(fixedSize)+"]"
        else:
            self.suffix = "[]"
        self.alignment = byteAlignment if byteAlignment != None else elementType.getAlignment()
        if byteAlignment != None:
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
        return self.fixedSize;
    def getAlignment(self):
        return self.alignment
    def getWidth(self):
        if self.fixedSize != None:
            return self.fixedSize * self.elementType.getWidth()
        else:
            raise Exception("non-fixed array has no width")
    def merge(self,other):
        _typeEqualAssert(self,other,"fixedSize","alignment")
        t1 = self.elementType
        t2 = other.elementType
        if t1.getUniqueName() != t2.getUniqueName():
            return SimpleArrayType(t1.merge(t2), # we only have to merge if the unique type names mismatch
                                   self.fixedSize)
        return self


# array of references - modelled as a struct
class ReferenceArrayType(ArrayType):
    infix = {8: "8", 16: "16", 32: ""} # infix used to denote the array
    def __init__(self,elementType,fixedSize=None,referenceBitWidth=32):
        ArrayType.__init__(self,ReferenceType(elementType,referenceBitWidth))
        self.referenceBitWidth = referenceBitWidth
        self.fixedSize = fixedSize
        arraySuffix = "Ref" + ReferenceArrayType.infix[referenceBitWidth] + "Array"
        if fixedSize != None:
            fixedSize + 1; # check int
            arraySuffix = "Size" + str(fixedSize) + arraySuffix
        self.name = elementType.getName()+arraySuffix
        self.uniqueName = elementType.getUniqueName()+arraySuffix
    def getCointainedTypes(self):
        return [self.elementType.targetType]
    def getUniqueName(self):
        return self.uniqueName
    def isImmediate(self):
        return self.fixedSize
    def getWidth(self):
        if self.fixedSize != None:
            return self.fixedSize * self.elementType.getWidth()
        else:
            raise Exception("non-fixed array has no width")
    def merge(self,other):
        _typeEqualAssert(self,other,"fixedSize","referenceBitWidth")
        t1 = self.elementType.targetType
        t2 = other.elementType.targetType
        if t1.getUniqueName() != t2.getUniqueName():
            return ReferenceArrayType(_mergeTypes(t1,t2), # we only have to merge if the unique type names mismatch
                                   self.fixedSize)
        return self
    def getAlignment(self):
        return min(self.elementType.getAlignment(),4)
    def getForwardDeclaration(self):
        return "struct "+self.getName()+";"
    def getDeclaration(self,indent=indent):
        result = "typedef struct __attribute__((packed)) %s {\n" % self.getName()
        # add member
        result = (result + indent + self.elementType.referenceType.getName() +" elementByteOffsets"
                  + "[" + (str(self.fixedSize) if self.fixedSize != None else "") + "]"
                  + ";\n" + indent + "\n")

        # add accessor function
        elementTypeName = self.elementType.targetType.getName()
        result = result + (
            "{indent}/** Returns {elementTypeName}-pointer to the element at the given index.\n"+
            "{indent} *  If the element at the given index is null/void, then the result is undefined. */\n"+
            "{indent}inline {elementTypeName}* get(const int index) const {{\n"+
            "{indent}{indent}return ({elementTypeName}*)(uintptr_t(this)+this->elementByteOffsets[index]);\n"+
            "{indent}}}").format(indent=indent,elementTypeName=elementTypeName)

        
        # finish
        result = result + "\n} " + self.getName() + ";"
        return result


# this is the only type that is mutable
class StructType(Type,AddConstantFunctions):
    def __init__(self,name):
        self.constantPool = ConstantPool()
        self.mutable = True
        self.name = name
        self.alignment = 1
        self.members   = {}  # member name -> member index
        self.names     = []  # list of member names
        self.offsets   = []  # list of member offsets
        self.types     = []  # list of member types
        self.numPadBytes = 0 # the total number of padding bytes in struct
    
    def addConstant(self,name,value): # should return self
        self.constantPool.addConstant(name,value)
        return self
        
    def getConstantPool(self):
        return self.constantPool

    # will add padding bytes until the current struct is aligned to the given byte alignment
    # returns how many padding bytes were added
    def addPadding(self,byteAlignment):
        # perform alignment
        padding = 0
        currentWidth = self.getCurrentWidth()
        if currentWidth > 0:
            while (-currentWidth) % byteAlignment != 0:
                self.addMember("paddingByte"+str(self.numPadBytes),PaddingValue().type)
                self.numPadBytes = self.numPadBytes + 1
                currentWidth = currentWidth + 1
                padding = padding + 1
        return padding
    
    # returns how many padding bytes were added before adding the member
    def addMember(self,name,type):
        if not self.mutable:
            raise Exception("cannot add member to finalized struct "+self.name)
        # check validity
        if name in self.members: raise Exception("name %s already in struct %s" % (name,self.name))
        assert(isinstance(type,Type))
        stringhelper.assertIsValidIdentifier(name)
        padding = self.addPadding(type.getAlignment())
        # actually add member
        self.members[name] = len(self.offsets)
        self.names.append(name)
        self.offsets.append(self.getCurrentWidth())
        self.types.append(type)
        self.alignment = max(self.alignment,type.getAlignment())
        return padding
    
    # returns the byte offset,type,name for the member at the given index
    def getMember(self,index):
        return self.offsets[index],self.types[index],self.names[index]
    
    def getWidth(self):
        if self.mutable:
            raise Exception("cannot ask the width of non-finished struct type "+repr(self))
        return self.getCurrentWidth()
    
    def getCurrentWidth(self):
        if len(self.offsets) == 0: return 0
        return self.offsets[-1] + self.types[-1].getWidth()
    
    # this will finalize the definition of this struct. The Struct may never grow in size
    # from this point on, otherwise it will become incompatible. Reserved elements may be added
    # to reserve space for future additions. After finalizing, the the struct may have a fixed
    # width, depending on whether the last member is fixed. returns the number of padding bytes
    def finalize(self,byteAlignment=4):
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

    def merge(self,other):
        _typeEqualAssert(self,other,"name","mutable","names")
        # TODO - merge constant pools
        # go through and check if the unique names are the same - in that case we can just return self
        equal = True
        for i,name in enumerate(self.names):
            t1 = self.types[i]
            t2 = other.types[i]
            if t1.getUniqueName() != t2.getUniqueName():
                equal = False
                break
        if equal: 
            return self
        result = StructType(self.name)
        for i,name in enumerate(self.names):
            t1 = self.types[i]
            t2 = other.types[i]
            if t1.getUniqueName != t2.getUniqueName():
                result.addMember(name,t1.merge(t2)) # we only have to merge if the unique type names mismatch
            else:
                result.addMember(name,t1)
        result.mutable = self.mutable
        return result

    def getForwardDeclaration(self):
        return "struct "+self.getName()+";"
    
    def getDeclaration(self,indent=indent):
        result = "typedef struct __attribute__((packed)) %s {\n" % self.getName()
        
        # add constants
        if self.constantPool.getNumConstants() > 0:
            result = (result 
                      +indent
                      +self.constantPool.getConstantDeclarations().replace("\n","\n"+indent) + "\n")
            
        # add members
        typeWidth = max([0]+[len(memberType.getName()) for memberType in self.types])
        for i,memberName in enumerate(self.names):
            memberType = self.types[i]
            memberName = memberName + memberType.getNameSuffix();
            space = " "*(typeWidth+1-len(memberType.getName()))
            comment = "" # comment comes from struct or from type
            result = (result
                      +indent
                      +memberType.getName()+space
                      +memberName+memberType.getDeclarationNameSuffix()+";"
                      +comment
                      +"\n")
        
        # add accessor functions
        functions = ""
        for i,memberName in enumerate(self.names):
            memberType = self.types[i]
            function = memberType.getAccessorFunction(memberName,indent=indent)
            if function != None:
                function = ("\n" + function + "\n").replace("\n","\n"+indent)
                functions = functions + function
        if len(functions) > 0:
            result = result + functions[:-len(indent)]

        # finish
        result = result + "} " + self.getName() + ";"
        return result


# a special struct type, an array of bitfield values
class BitFieldArrayType(Type):
    def __init__(self,name,fields):
        self.name = name
        if len(fields) == 0:
            raise Exception("BitFieldArrayType needs at least one field")
        for field in fields:
            stringhelper.assertIsValidIdentifier(field)
            assert(field != 'bitFieldArrayEntryBits')
        self.fields = fields
    def getFields(self):
        return self.fields
    def getUniqueName(self):
        return "BitFieldArray:"+self.name
    def getAlignment(self):
        return 4
    def getForwardDeclaration(self):
        return "struct "+self.getName()+";"    
    def getDeclaration(self,indent=indent):
        result = "typedef struct __attribute__((packed)) %s {\n" % self.getName()
        
        # add members
        result += indent + "uint16_t bitFieldArrayEntryBits;\n"
        for i,field in enumerate(self.fields):
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
{indent}}}""".format(indent=indent)
        # by name accessors:
        for i,field in enumerate(self.fields):
            if i == len(self.fields)-1:
                nextBitOffset = "endOffset" 
            else:
                nextBitOffset = self.fields[i+1]+"BitOffset"
            result += """{indent}
{indent}
{indent}/** returns the bit offset of field {field} at the given index */
{indent}inline int get{Field}BitOffset(int index) const {{
{indent}{indent}return {field}BitOffset + index*bitFieldArrayEntryBits;
{indent}}}
{indent}
{indent}
{indent}/** returns the number of bits used by field {field} */
{indent}inline int get{Field}NumBits() const {{
{indent}{indent}return {nextBitOffset} - {field}BitOffset;
{indent}}}
{indent}
{indent}/** returns the value of the field {field} at the given index, assuming it has <=31 bits */
{indent}inline uint32_t get{Field}(int index) const {{
{indent}{indent}const int bitOffset = {field}BitOffset + index*bitFieldArrayEntryBits;
{indent}{indent}const int nextBitOffset = {nextBitOffset};
{indent}{indent}return namedstruct::readBits(this, bitOffset, nextBitOffset-{field}BitOffset);
{indent}}}""".format(field=field,indent=indent,nextBitOffset=nextBitOffset,Field=stringhelper.capitalizeFirst(field))
        
        # finish
        result = result + "\n} " + self.getName() + ";"
        return result

    def merge(self,other):
        _typeEqualAssert(self,other,"fields")
        return self
    def isImmediate(self):
        return False
    def getWidth(self):
        raise Exception("cannot ask width of bitfield array type")
    def merge(self,other):
        _typeEqualAssert(self,other,"name","fields")
        return self

    

# ############# VALUES ######################################################################
class Value(object):
    def __init__(self,type):
        self.type = type;
    def getAlignement():
        raise Exception()
    def getType(self):
        return self.type;
    # returns a tuple of strings, the immediate data, and the offseted data, which is assumed to start at dataOffset
    # the caller has to ensure proper alignment of the immediate data, but the function will ensure alignment of the offseted data
    def pack(self,dataOffset=None):
        raise Exception()
    def getPythonValue(self): # will return a python value, basically what was used to create this
        raise Exception()
    def pretty(self):
        raise Exception("unimplemented for "+repr(self))
    def getLiteral(self):
        raise Exception("cannot get literal for "+repr(self))
    def getImmediateDataSize(self):
        return self.type.getWidth()


# primitve value
class PrimitiveValue(Value):
    def __init__(self,type,pythonValue):
        Value.__init__(self,type)
        self.pythonValue = pythonValue
        type.assertValueHasType(pythonValue)
    def hasFixedWidth(self):
        return True
    def getPythonValue(self):
        return self.pythonValue;
    def pretty(self):
        return repr(self.pythonValue)
    def pack(self,dataOffset=None):
        return self.type.pack(self.pythonValue),""


# integer value
class IntValue(PrimitiveValue):
    def __init__(self,intValue,unsigned=False,bitWidth=32):
        type = IntType(unsigned,bitWidth)
        type.assertValueHasType(intValue)
        PrimitiveValue.__init__(self,type,intValue)
    def getLiteral(self):
        return str(self.getPythonValue())

# a single char
class CharValue(PrimitiveValue):
    def __init__(self,char):
        assert(isinstance(char,basestring))
        assert(len(char)==1)
        type = CharType()
        PrimitiveValue.__init__(self,type,char)
    def getLiteral(self):
        return stringhelper.literalFromString(self.getPythonValue(),quote="'")

# an integer that acts as a bit field
class BitField(Value):
    def __init__(self,name,bitWidth=32):
        self.type = BitFieldType(name,bitWidth)
        self.values = []
    def add(self,name,value,bitWidth=1):
        assert(value >= 0 and value < 2**bitWidth)
        self.type.add(name,bitWidth)
        self.values.append(value)
        return self
    def hasFixedWidth(self):
        return True
    def getPythonValue(self):
        return self
    def get(self,fieldName): # returns the value of the field name
        return self.values[self.getType().fields[fieldName]]
    def pretty(self):
        result = "bitField{bitWidth}{{".format(bitWidth=self.type.bitWidth)
        nameLen = max(len(name) for name in self.type.fieldNames) if len(self.values) > 0 else 0
        for i,memberValue in enumerate(self.values):
            bitWidth = self.type.fieldWidths[i]
            name = self.type.fieldNames[i]
            result = result + (("\n{name:"+str(nameLen)+"}:{bitWidth:2} = {value}")
                               .format(name=name,bitWidth=bitWidth,value=memberValue))
        result = result.replace("\n","\n"+indent)
        result = result +"\n}"
        return result
    def pack(self,dataOffset=None):
        value = 0
        shift = 0
        for i,v in enumerate(self.values):
            value = value | (v << shift)
            shift = shift + self.type.fieldWidths[i]
        return IntValue(value,True,self.type.bitWidth).pack(dataOffset)


# padding byte
class PaddingValue(IntValue):
    def __init__(self):
        IntValue.__init__(self,0,True,8)

# null value
class NullValue(Value):
    def __init__(self):
        Value.__init__(self,NullType())
    def pretty(self):
        return "<NULL>";
    def getPythonValue(self):
        return None

# reference value
class ReferenceValue(Value):
    # a target of None is allowed - in that case (and only that case) target type may be set
    def __init__(self,targetValue,referenceBitWidth=32,targetType=None):
        if targetValue != None and targetType != None:
            raise Exception("cannot set target type for non-null reference")
        if targetValue == None:
            targetValue = NullValue()
        targetValue = getValue(targetValue)
        Value.__init__(self,ReferenceType(targetValue.type, referenceBitWidth=referenceBitWidth))
        self.targetValue = targetValue
    def pretty(self):
        return ("->"+
                (self.targetValue.pretty().replace("\n",indent+"\n")
                 if self.targetValue != None else
                 "None"))
    def getPythonValue(self):
        return self.targetValue.getPythonValue()
    def pack(self,dataOffset=None):
        if dataOffset == None:
            raise Exception("cannot pack reference without a data offset (is the reference not contained in a struct?)")
        if self.targetValue.getPythonValue() == None:
            return self.type.referenceType.pack(0),""
        else:
            # add padding bytes until data offset is aligned with target type
            padding = ((-dataOffset) % self.type.targetType.getAlignment())
            packedReference = self.type.referenceType.pack(dataOffset + padding)
            packedData = "\x00"*padding + pack(self.targetValue)
            return packedReference,packedData



# all the array-like values
class ArrayValue(Value):
    def __init__(self,type,values):
        Value.__init__(self,type)
        # check correctness on values - either incoming values are python values or Value objects
        self.elementsAreValueObjects = (len(values) > 0 and isinstance(values[0],Value))
        for v in values:
            if self.elementsAreValueObjects:
                assert(isinstance(v,Value))
                type.getElementType().merge(v.getType())
            else:
                type.getElementType().assertValueHasType(v)
        self.values = values

    def getPythonValue(self):
        return self.values

    # will pack the elements
    def pack(self,dataOffset=None,elementOffsetsRelativeToElement=True):
        if dataOffset == None:
            dataOffset = self.getImmediateDataSize()
        immediateData = []
        offsetedData = []
        immediateLen = 0
        for value in self.values:
            if self.elementsAreValueObjects:
                immediate,referred = value.pack(dataOffset - 
                                                (immediateLen 
                                                 if elementOffsetsRelativeToElement else
                                                 0)) # offset is relative to element
                dataOffset = dataOffset + len(referred)
                immediateData.append(immediate)
                offsetedData.append(referred)
                immediateLen += len(immediateData[-1])
            else:
                immediateData.append(self.type.getElementType().pack(value))
                immediateLen += len(immediateData[-1])
        immediateString = "".join(immediateData)
        offsetedString= "".join(offsetedData)
        return immediateString,offsetedString

    def pretty(self):
        maxChars = 500
        minResults = 2
        results = [v.pretty() if self.elementsAreValueObjects else str(v) for v in self.values]
        chars = 0
        i = 0
        while((chars <= maxChars or i < minResults) and i < len(results)):
            chars += len(results[i])
            i += 1
        return "[" + ", ".join(results[:i]) + (",..." if i < len(results) else "")+ "]"


# c array - either variable length, or fixed length
class SimpleArray(ArrayValue):
    def __init__(self,elementType,values,fixedSize=None,byteAlignment=None):
        if isinstance(elementType,ReferenceType):
            raise Exception("simple arrays cannot store references")
        if not fixedSize == None:
            assert(len(values) <= fixedSize)
        self.fixedSize = fixedSize
        ArrayValue.__init__(self,SimpleArrayType(elementType,fixedSize,byteAlignment),values)

    def getImmediateDataSize(self):
        return (self.type.getElementType().getWidth() 
                * (len(self.values) if self.fixedSize==None else self.fixedSize))
    def pack(self,dataOffset=None):
        immediateData,offsetData = ArrayValue.pack(self,dataOffset) # call super pack
        if self.fixedSize != None:
            # fill the data with zero bytes 
            immediateData = (immediateData
                             + "\x00"*(self.getImmediateDataSize()-len(immediateData)))
        if dataOffset == None:
            return immediateData + offsetData, ""
        else:
            return immediateData,offsetData

        

# c array of chars - arbitrary strings get converted to utf-8
class StringValue(SimpleArray):
    def __init__(self,string="",fixedSize=None,omitTerminal=False):
        chars = stringhelper.stringToChars(string)
        if omitTerminal:
            chars = chars[:-1]
        SimpleArray.__init__(self,CharType(),chars,fixedSize)
        self.string = string
    def pretty(self):
        return stringhelper.cutStringIfTooLong(repr(self.string))
    def getPythonValue(self):
        return self.string
    def getLiteral(self):
        return stringhelper.literalFromString(self.string)


# c array of chars - but inputs as arrays of 0/1 (bit) values, packed into 8 bits per char
blobStrings = []
class BlobValue(SimpleArray):
    # the alignment is 4 bytes by default, which can be overriden
    def __init__(self,blob,fixedSize=None,byteAlignment=4):
        global blobStrings
        blobStrings.append(blob)
        if isinstance(blob, basestring):
            bitArrays = [bithelper.toBits(ord(c),numBits=8) for c in blob]
            blob = []
            for bitArray in bitArrays:
                blob.extend(bitArray)
        blob = array.array('B',blob) # turn blob into an actual binary array - if it's not a string
        SimpleArray.__init__(self,CharType(),bithelper.packBitsToChars(blob),fixedSize,byteAlignment)
        self.blob=blob
    def pretty(self):
        return stringhelper.cutStringIfTooLong("["+''.join(str(b) for b in self.blob[0:200])+"]",length=len(self.blob))
    def getPythonValue(self):
        return self.blob

# reference array
class ReferenceArrayValue(ArrayValue):
    # construct reference array from a sequence of values - those may be values, or will be turned into values
    def __init__(self,values,fixedSize=None,referenceBitWidth=32):
        if len(values) == 0:
            raise Exception("reference array values cannot be empty")
        if not fixedSize == None:
            assert(len(values) <= fixedSize)
        self.fixedSize = fixedSize
        # turn all values into references
        targetValues = []
        elementType = getValue(values[0]).getType()
        for v in values:
            v = getValue(v)
            if not isinstance(v,Value):
                raise Exception("reference array needs to be constructed from Value elements")
            if isinstance(v,ReferenceValue):
                raise Exception("cannot store references in reference array")
            elementType = _mergeTypes(v.getType(),elementType)
            targetValues.append(v)
        referenceValues = [ReferenceValue(v,referenceBitWidth) for v in targetValues]
        ArrayValue.__init__(self,ReferenceArrayType(elementType,fixedSize,referenceBitWidth),referenceValues)

    def getImmediateDataSize(self):
        return (self.type.getElementType().getWidth() 
                * (len(self.values) if self.fixedSize==None else self.fixedSize))

    def pack(self,dataOffset=None):
        if dataOffset == None:
            dataOffset = self.getImmediateDataSize()
            combine = True
        else:
            combine = False
        immediateData,offsetData = ArrayValue.pack(self,dataOffset,elementOffsetsRelativeToElement=False)
        if self.fixedSize != None:
            # fill the data with zero bytes 
            immediateData = (immediateData
                             + "\x00"*(self.getImmediateDataSize()-len(immediateData)))
        if combine:
            return immediateData + offsetData, ""
        else:
            return immediateData, offsetData


# reserved is just a set of bytes reserved for futrue use
class ReservedValue(SimpleArray):
    pass



# struct value
# structs don't have fixed width unless they are closed/finished
class Struct(Value,AddConstantFunctions):
    def __init__(self,name,alignment=32):
        structType = StructType(name)
        Value.__init__(self,structType)
        self.values    = [] # list of member values

    def __repr__(self):
        type = self.type
        numMembers = len(type.members)
        return ("<Struct:"+str(type.name)
                +" with "+str(numMembers)
                +" member%s>" % ("" if numMembers == 1 else "s"))

    def getName(self):
        return self.type.name

    def addConstant(self,name,value):
        self.getType().addConstant(name,value)
        return self
        
    def getPythonValue(self):
        return self # struct is a container, so it's not a python value

    def get(self,key): # returns the python value associated with the given key
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
    def add(self,name,value):
        value = getValue(_dictGet(value,name))
        if value.getType().isImmediate():
            self.addImmediate(name,value)
        else:
            self.addReference(name,value)
        return self
        
    # will add a reference to the given value to this struct
    # if the type is defined, and value=None allows adding a typed reference even if the value is Null
    def addReference(self,name,value,referenceBitWidth=32,targetType=None):
        if targetType != None:
            if value != None: 
                raise Exception("can only override reference type for Null Value")
            return self.addImmediate(name,ReferenceValue(None,referenceBitWidth,targetType=targetType))
        return self.addImmediate(name,ReferenceValue(value,referenceBitWidth))
    
    #short hand for addReference(name,None,referenceBitWidth,targetType)
    def addNullReference(self,name,targetType,referenceBitWidth=32):
        return self.addImmediate(name,ReferenceValue(None,referenceBitWidth,targetType=targetType))

    # shorthand for addReference(name,value,referenceBitWidth=8,targetType=targetType)
    def addRef8(self,name,value,targetType=None):
        referenceBitWidth = 8
        return self.addReference(name,value,referenceBitWidth=referenceBitWidth,targetType=targetType)

    # shorthand for addReference(name,value,referenceBitWidth=16,targetType=targetType)
    def addRef16(self,name,value,targetType=None):
        referenceBitWidth = 16
        return self.addReference(name,value,referenceBitWidth=referenceBitWidth,targetType=targetType)

    # shorthand for addReference(name,value,referenceBitWidth=32,targetType=targetType)
    def addRef32(self,name,value,targetType=None):
        referenceBitWidth = 32
        return self.addReference(name,value,referenceBitWidth=referenceBitWidth,targetType=targetType)


    # will add the value
    def addImmediate(self,name,value):
        value = getValue(_dictGet(value,name))
        padBytes = self.getType().addMember(name,value.getType())
        self.values.extend([PaddingValue()]*padBytes)
        self.values.append(value)
        return self
    
    # add an int32 to the struct. if 'anInt' is a dictionary d, will add d[name]
    # if the name exists, will throw an error
    # returns self
    def addInt8  (self,name,anInt): return self.add(name,IntValue(_dictGet(anInt,name),False,8))
    def addInt16 (self,name,anInt): return self.add(name,IntValue(_dictGet(anInt,name),False,16))
    def addInt32 (self,name,anInt): return self.add(name,IntValue(_dictGet(anInt,name),False,32))
    def addInt64 (self,name,anInt): return self.add(name,IntValue(_dictGet(anInt,name),False,64))
    def addUInt8 (self,name,anInt): return self.add(name,IntValue(_dictGet(anInt,name),True,8))
    def addUInt16(self,name,anInt): return self.add(name,IntValue(_dictGet(anInt,name),True,16))
    def addUInt32(self,name,anInt): return self.add(name,IntValue(_dictGet(anInt,name),True,32))
    def addUInt64(self,name,anInt): return self.add(name,IntValue(_dictGet(anInt,name),True,64))
    def addChar  (self,name,aChar): return self.add(name,CharValue(_dictGet(aChar,name)))
    
    # will reference add a binary blob, either an array of 0/1 values, or a string, to the struct.
    # if 'aBlob' is a dictionary d, will add d[name] will store the the byte offset in the C struct,
    # using the name <name>+ByteOffset. If the name exists, will throw an error.
    # Blobs will be word aligned by default, but that can be overriden.
    # Blobs are stored little endian, i.e. [0,1,0,0,1,0,0,1]=0x92=146.
    # returns self
    def addBlob(self,name,blob,byteAlignment=4,referenceBitWidth=32):
        self.addReference(name,
                          BlobValue(_dictGet(blob,name),byteAlignment=4),
                          referenceBitWidth=referenceBitWidth);
        return self;
    
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
    def addString(self,name,string,fixedWidth=None,omitTerminal=False,referenceBitWidth=32):
        string = _dictGet(string,name);
        if string == None:
            if fixedWidth != None:
                raise Exception("cannot add fixed with string as a null-reference")
            self.addImmediate(name,ReferenceValue(None,targetType=SimpleArrayType(CharType())))
        else:
            self.addReference(name,StringValue(string,fixedWidth,omitTerminal),referenceBitWidth)
        return self;

    # will add an array of values to the struct.
    # if value is a dictionary, will add value[name]
    # if the value is an array of Value objects, will add an array with the val
    # otherwise it will attempt to turn the value into a value using "getValue"
    def addArray(self,name,arrayValues,fixedSize=None):
        arrayValues = _dictGet(arrayValues,name)
        value = getArrayValue(arrayValues,fixedSize)
        if value.getType().isImmediate():
            self.addImmediate(name,value)
        else:
            self.addReference(name,value)
        return self

    # will add a reference array to the struct.
    # if value is a dictionary, will add value[name]
    # if the value is an array of Value objects, will add an array with the val
    # otherwise it will attempt to turn the value into a value using "getValue"
    def addReferenceArray(self,name,arrayValues,fixedSize=None,referenceBitWidth=32):
        arrayValues = _dictGet(arrayValues,name)
        arrayValues = [getValue(v) for v in arrayValues]
        array = ReferenceArrayValue(arrayValues,fixedSize,referenceBitWidth)
        if array.getType().isImmediate():
            self.addImmediate(name,array)
        else:
            self.addReference(name,array)
        return self

    # this will finalize type of this struct. The Struct may never grow in size from this point on.
    # returns self.
    def finalize(self,byteAlignment=4):
        padBytes = self.getType().finalize(byteAlignment)
        self.values.extend([PaddingValue()]*padBytes)
        return self

    def pretty(self):
        result = "struct "+self.type.getName()+" {"
        length = max([0]+[len(repr(self.type.getMember(i)[1])) for i in range(len(self.values))])
        for i,memberValue in enumerate(self.values):
            offset,type,name = self.type.getMember(i)
            typeName = repr(type)
            result = result + (("\n{pos:02}: {type} "+(" "*(length-len(typeName)))+"{name}=")
                               .format(pos=offset,type=typeName,name=name,value=memberValue.pretty())
                               +memberValue.pretty())
        result = result.replace("\n","\n"+indent)
        result = result +"\n}"
        return result
    
    def pack(self,dataOffset=None):
        currentMember = ""
        try:
            if dataOffset == None:
                dataOffset = self.getImmediateDataSize()
                combine = True
            else:
                combine = False
            immediateData = ""
            offsetedData = ""
            for i,value in enumerate(self.values):
                currentMember = self.getType().names[i]
                immediate,referred = value.pack(dataOffset)
                dataOffset = dataOffset + len(referred)
                immediateData = immediateData + immediate
                offsetedData = offsetedData + referred
            padding = self.getImmediateDataSize() - len(immediateData)
            immediateData = immediateData + "\x00"*padding
            if combine:
                return immediateData + offsetedData, ""
            else:
                return immediateData, offsetedData
        except Exception as e:
            print "error when packing struct %s, member %s" % (self.getName(),repr(currentMember))
            raise e


    # prints the sizes of every member
    # indent allows indenting the printing result by 'indent' spaces
    def printSizes(self,indent=0):
        # collect names/sizes
        names = []
        sizes = []
        dataOffset = self.getImmediateDataSize()
        for i,value in enumerate(self.values):
            immediate,referred = value.pack(dataOffset)
            names.append(self.type.getMember(i)[2])
            sizes.append(len(immediate)+len(referred))
            dataOffset = dataOffset + len(referred)
        total = "total:"
        maxNameLen = max([len(total)]+[len(name) for name in names]) + 1
        numLen = len(str(sum(sizes)))
        numFormat = "%"+str(numLen)+"d"
        # print name, sizes, total
        print " "*indent + "struct %s:" % self.type.getName()
        print " "*indent + "-"*(maxNameLen+numLen)
        for i,name in enumerate(names):
            print " "*indent + name+(" "*(maxNameLen - len(name)))+(numFormat % sizes[i])
        print " "*indent + "-"*(maxNameLen+numLen)
        print " "*indent + total+(" "*(maxNameLen-len(total)))+(numFormat % sum(sizes))


# an array of bitfield values, with variable number of bits
class BitFieldArray(Value):
    def __init__(self,name,*fields):
        self.type = BitFieldArrayType(name,fields)
        self.entries = [] # each entry is an array of (isBlob,value)
    def __repr__(self):
        return "<BitFieldArray:%s with %d fields>" % (self.type.getName(),len(self.type.getFields()))
    # adds a new entry to the bit field array
    # the fieldValues may be a dictionary of field-value, or a sequence of values in the same order as the fields
    # the values themselves may be (positive) integers, or BlobValue objects
    def add(self,fieldValues):
        fields = self.type.getFields()
        assert(len(fields) == len(fieldValues))
        if isinstance(fieldValues,dict):
            fieldValues = [fieldValues[field] for field in fields]
        entry = []
        for value in fieldValues:
            if isinstance(value,BlobValue):
                entry.append((True,value))
            else:
                if not isinstance(value, numbers.Integral):
                    raise Exception("attempting to add "+repr(value)+", but bitFieldArray only supports int or blobValue.")
                if not (value >= 0 and value < 2**31):
                    raise Exception("bitFieldArray only supports values between 0 (incl) and 2^31 (excl), received "+repr(value))
                entry.append((False,value))
        self.entries.append(entry)
        return self
    # calls add on all elements of a sequence, returns self
    def addAll(self,entries):
        for entry in entries:
            self.add(entry)
        return self
    def hasFixedWidth(self):
        return False
    def getPythonValue(self):
        return self
    def get(self,fieldName,index): # returns the value of the field name at the given index
        return self.entries[index][self.type.getFields().index(fieldName)][1]
    # for every field, returns the bit length of it
    def getFieldLengths(self):
        fields = self.type.getFields()
        if len(self.entries) == 0:
            return [0]*len(fields)
        return [
            max(len(entry[fieldIndex][1].getPythonValue())
                if entry[fieldIndex][0] else
                bithelper.requiredBits(entry[fieldIndex][1])
                for entry in self.entries)
            for fieldIndex in range(len(fields))]
    def pretty(self):
        fields = self.type.getFields()
        fieldLengths = self.getFieldLengths()
        result = "bitFieldArray[{length}x{numBits}]{{".format(length=len(self.entries),numBits=sum(fieldLengths))
        rows = [indent+s+":" for s in stringhelper.getColumn(fields)]
        rows = [rows[i]+s+" = [" for i,s in enumerate(stringhelper.getColumn(fieldLengths))]
        maxColumnWidth = 80
        maxEntryWidth = 12
        numEntries = len(self.entries)
        for i,entry in enumerate(self.entries):
            # build column values
            values = []
            for isBlob,value in entry:
                if isBlob:
                    blob = ''.join(str(v) for v in value.getPythonValue())
                    if len(blob) > maxEntryWidth:
                        blob = blob[0:maxEntryWidth-2]+".."
                    values.append(blob)
                else:
                    values.append(value)
            strings = stringhelper.getColumn(values)
            # stop if rows grow too big
            if len(rows[0])+1+len(strings[0]) > maxColumnWidth:
                if i < numEntries:
                    rows = [row+".." for row in rows]
                break;
            # add row
            delim = ("" if (i == numEntries-1) else ",")
            rows = [rows[j]+s+delim for j,s in enumerate(strings)]
        rows = [row+"]" for row in rows]
        result += "\n" + "\n".join(rows)
        result = result +"\n}"
        return result
    def getImmediateDataSize(self):
        fieldLengths = self.getFieldLengths()
        return (len(fieldLengths) + 2)*2 + (sum(fieldLengths)*len(self.entries)+7)/8
    def pack(self,dataOffset=None):
        fieldLengths = self.getFieldLengths()
        offset = (len(fieldLengths) + 2)*16
        headerValues = [sum(fieldLengths)]+[offset + sum(fieldLengths[:i]) for i in range(len(fieldLengths)+1)]
        header = pack(SimpleArray(UINT16,headerValues))
        # create data blob
        blob = array.array('B',[])
        for entry in self.entries:
            for i,(isBlob,value) in enumerate(entry):
                if isBlob:
                    b = value.getPythonValue()
                    blob.extend(b)
                    blob.extend((fieldLengths[i]-len(b))*array.array('B',[0]))
                else:
                    blob.extend(array.array('B',bithelper.toBits(value,fieldLengths[i])))
        data = pack(BlobValue(blob))
        assert(len(blob)==sum(fieldLengths)*len(self.entries))
        return header+data,""



# ######### UTILS #####################################################################################
# if value is a dictionary, returns value[name], otherwise returns value
def _dictGet(value,name):
    return value[name] if isinstance(value,dict) else value

# given two types, merges them, but if one of them is NullType, returns the other type
def _mergeTypes(typeA,typeB):
    if isinstance(typeA,NullType): 
        return typeB
    if isinstance(typeB,NullType):
        return typeA
    return typeA.merge(typeB)


# given two types, will ensure that 
# the python type of typeA and typeB are the same,
# and that all given keys are the same
def _typeEqualAssert(typeA,typeB,*keys):
    if not type(typeA) == type(typeB):
        raise Exception("can't merge types "+repr(typeA)+" and "+repr(typeB))
    for key in keys:
        valueA = typeA.__getattribute__(key) 
        valueB = typeB.__getattribute__(key)
        if valueA != valueB:
            raise Exception("can't merge types "+repr(typeA)+" and "+repr(typeB)+", attribute "+key+" doesn't match, "
                            +repr(valueA)+" vs "+repr(valueB))







