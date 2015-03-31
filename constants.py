import collections
import values

# an object that has the add constant functions - they all get dispatched to "addConstant"
class AddConstantFunctions(object):
    def addConstant(self,name,value): # should return self
        raise Exception("not implemented")
    def addInt32Constant(self, name, value): return self.addConstant(name, values.Int(values._dictGet(value, name),False,32))
    def addCharConstant (self, name, value): return self.addConstant(name, values.Char(values._dictGet(value, name)))

# an object that can have constants associated with it
class ConstantPool(AddConstantFunctions):
    def __init__(self):
        self.constants = collections.OrderedDict() # name -> value
    def addConstant(self,name,value):
        value = values.getValue(values._dictGet(value,name))
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
