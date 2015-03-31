import collections
import stringhelper, bithelper, values, types, constants

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
#   - The generate header should allow top level types other than struct -> check for types that require headers
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



# ############# PUBLIC FUNCTIONS ############################################################
# returns the c++ header file text that defines the given struct(s), including all nested
# structs. If a namespace is set, the c++ code will be defined inside that namespace.
# If the 'define' is set, will use use that for the IF/IFNDEFs, otherwise till use the name of the
# first struct.
# headText can be used to add license/author etc.
# structs may be a single struct or a sequence of structs.
# constantPools may be a single constantPool or a sequence of constant Pools
def generateHeader(structs,constantPools=None,namespace=None,define=None,headText="",indent=stringhelper.indent):
    # massage arguments
    if isinstance(structs, values.Value): structs = [structs]
    if constantPools == None: constantPools = []
    if isinstance(constantPools, constants.ConstantPool): constantPools = [constantPools]
    if define == None: define = "__"+structs[0].getType().getName().upper()+"__"
    namespaceString = ""
    if namespace!=None:
        stringhelper.assertIsValidIdentifier(namespace)
        namespaceString = "namespace %s {\n" % namespace
    
    # get all types
    structTypes = []
    for s in structs:
        assert(isinstance(s, values.Struct))
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
    constant = ""
    if len(constantPools) > 0:
        for pool in constantPools:
            if pool.getNumConstants() > 0:
                constant = (constant
                            +"\n" + indent
                            +pool.getConstantDeclarations().replace("\n","\n"+indent))
    if len(constant) > 0:
        result = (result
                  + currentIndent + "\n" + currentIndent
                  +"// *** constants *****************************"
                  +constant
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












