from __future__ import absolute_import
from builtins import object
import collections
import re


# an object that has the add constant functions - they all get dispatched to "addConstant"
class AddConstantFunctions(object):
    def addConstant(self, name, value):  # should return self
        raise Exception("not implemented")
    
    def addInt32Constant(self, name, value):
        from . import values  # to avoid circular dependencies
        return self.addConstant(name, values.Int(values.dictGet(value, name)))
    
    def addCharConstant(self, name, value):
        from . import values  # to avoid circular dependencies
        return self.addConstant(name, values.Char(values.dictGet(value, name)))


# an object that can have constants associated with it
class ConstantPool(AddConstantFunctions):
    def __init__(self):
        self.constants = collections.OrderedDict()  # name -> value
    
    def addConstant(self, name, value):
        from . import values  # to avoid circular dependencies
        
        value = values.getValue(values.dictGet(value, name))
        # value.getLiteral()  # check whether there is a literal method
        self.constants[name] = value
        return self
    
    # returns the value associated with the constant
    def get(self, name):
        return self.constants[name]
    
    def getConstantDeclarations(self):
        result = b""
        typeWidth = max([len(v.getType().getName()) for v in list(self.constants.values())] + [0])
        for name, value in list(self.constants.items()):
            name = bytes(name, encoding='utf-8')
            declarationNameSuffix = bytes(value.getType().getDeclarationNameSuffix(), encoding='utf-8')
            typeName = bytes(value.getType().getName(), encoding='utf-8')
            space = bytes(" " * (typeWidth - len(typeName)), encoding='utf-8')
            literal = value.getLiteral()
            result = (result
                      + b"static constexpr " + typeName
                      + b" " + space
                      + name + declarationNameSuffix
                      + b" = " + literal + b";\n")
        return result[:-1]
    
    def getNumConstants(self):
        return len(self.constants)


class EnumConstant(object):
    # noinspection PyUnusedLocal
    def __init__(self, name, keyToValue):
        pass


# converts a camelCase name to CONSTANT_CASE
# if the string is already constant case, generally leaves it untouched
def toConstantName(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).upper()
