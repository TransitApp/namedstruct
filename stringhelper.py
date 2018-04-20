from builtins import str
import re

indent = " " * 4


# ********** packing *********************************************************
# takes a string and returns it as a null terminated string of bytes char
def stringToChars(string):
    bytesString = bytes(string, 'utf-8') + b"\0"
    arrayOfIndividualBytes = []
    for charValue in bytesString:
        arrayOfIndividualBytes.append(bytes([charValue]))

    return arrayOfIndividualBytes


# ********** creating types/headers *****************************************
# given a string, returns a copy with the first letter capitalized, and the others unchanged
def capitalizeFirst(string):
    return string[0].upper() + string[1:]


def escapeChar(char):
    r = repr(char)
    if r[0] == 'u':
        r = r[1:]  # remove leading string char
    assert (r[0] == '"' and r[-1] == '"') or (r[0] == "'" and r[-1] == "'")
    r = r[1:-1]
    if r == "'":
        return "\\'"
    if r == '"':
        return '\\"'
    return bytes(r, 'utf-8')


def literalFromString(string, quote='"'):
    quote = bytes(quote, 'utf-8')
    return quote + b"".join(escapeChar(c) for c in string) + quote


# checks whether a given name is a valid identifier in c++. Throws an exception if it isn't.
def assertIsValidIdentifier(name):
    if not _identifierMatchObject.match(name):
        raise Exception(repr(name) + " not a valid identifier")
    if name.endswith("ByteOffset"):
        raise Exception(
                repr(name) + " - an identifier may not end with ByteOffset, that suffix is reserved for internal use.")
    if isCppKeyword(name):
        raise Exception(repr(name) + " cannot be an identifier, it is a C/C++ keyword")


def isCppKeyword(name):
    return name in _cPlusPlusKeywords


_identifierMatchObject = re.compile('^[_a-zA-z][0-9_a-zA-Z]*')
_cPlusPlusKeywords = frozenset(["alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand", "bitor",
                                "bool", "break", "case", "catch", "char", "char16_t", "char32_t", "class", "compl",
                                "const", "constexpr",
                                "const_cast", "continue", "decltype", "default", "delete", "do", "double",
                                "dynamic_cast", "else", "enum",
                                "explicit", "export", "extern", "false", "float", "for", "friend", "goto", "if",
                                "inline", "int", "long",
                                "mutable", "namespace", "new", "noexcept", "not", "not_eq", "nullptr", "operator", "or",
                                "or_eq", "private",
                                "protected", "public", "register", "reinterpret_cast", "return", "short", "signed",
                                "sizeof", "static",
                                "static_assert", "static_cast", "struct", "switch", "template", "this", "thread_local",
                                "throw", "true",
                                "try", "typedef", "typeid", "typename", "union", "unsigned", "using", "virtual", "void",
                                "volatile",
                                "wchar_t", "while", "xor", "xor_eq"])

# ********** pretty printing *************************************************
# given a string such as "[abccdefghijklmnopqrstuvwxyz]", will ensure the maximum length of the string 
# is at most maxLength, for example if the max length is 15, it will return "26:[abcdefg...]"
maxRepresentationLength = 60


def cutStringIfTooLong(string, maxLength=maxRepresentationLength, length=None):
    if length is None:
        length = len(string)
    if len(string) <= maxLength:
        return string
    head = str(length) + ":"
    tail = "..." + string[-1]
    return head + string[0:maxLength - len(head) - len(tail)] + tail


# given a set of values, returns a format string that will give all values the same length.
# max length will force a max length. default will be used if len(values) = 0
def getColumnFormat(values, maxLength=None, default=1, rightAlign=True):
    length = default
    if len(values) > 0:
        length = max(len(str(v)) for v in values)
    align = "+" if rightAlign else "-"
    if maxLength is not None and length >= maxLength:
        length = maxLength
    return "%{align}{length}.{length}s".format(align=align, length=length)


# uses get column format to build a column of values, returns a string for every inputted value
def getColumn(values, maxLength=None, rightAlign=True):
    if len(values) == 0:
        return []
    columnFormat = getColumnFormat(values, maxLength=maxLength, rightAlign=rightAlign)
    return [columnFormat % str(v) for v in values]
