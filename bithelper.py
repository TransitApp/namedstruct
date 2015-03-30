import struct, math

# returns the number of bits required to store the number
# 0 -> 0, 255 -> 8, 256 -> 9
def requiredBits(number):
  if (number == 0): return 0
  return int(math.log(number,2)) + 1

# returns a postive number as an array of bits
# numBits forces 0-bits to be added so that the len of the result is numBits
# if the number of required bits is longer than numBits, throws an exception
def toBits(number,numBits=None):
  theNumber = number
  if (number < 0): raise Exception("received negative number "+str(number))
  if (int(number) != number): raise Exception("received non int-number "+str(number))
  bits = []
  while (number>0):
    bits.append(number & 1)
    number = number >> 1;
  if numBits == None: return bits
  if (len(bits) > numBits): raise Exception("number %d doesn't fit in %d bits" % (theNumber,numBits));
  return bits+[0]*(numBits-len(bits)) #add 0 bits


# takes an array of bits, and returns them as a string (i.e. char array)
# this operation should be indemptotent, i.e. a string will be returned as is
def packBitsToChars(bits):
    if isinstance(bits, basestring):
        for c in bits:
            if (ord(c) < 0 or ord(c) > 255): raise Exception("blob strings myst be made of 8-bit chars, but found "+repr(c))
        return bits
    c = 0
    numBits = 0
    result = []
    for b in bits:
        if not (b==0 or b==1):
            raise Exception("blobs can only be made from sequences of 0,1 values")
        if (numBits == 8):
            result.append(c)
            c = 0
            numBits = 0
        c = c + (b << numBits)
        numBits += 1
    if (numBits > 0):
        result.append(c)
    return struct.pack("<"+str(len(result))+"B",*result)
