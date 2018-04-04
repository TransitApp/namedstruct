//
//  bits.h
//
//  Created by Anton Dubrau on 2013-09-26.
//  Copyright (c) 2013 Transit. All rights reserved.
//
//  utility functions for reading bits
//  some functions look kinda long, but there should only be the following operations
//    shift, addition, subtraction, read word, comparison, or, and.
//  TODO - differentiate between aligned and misaligned?
//       - i.a. do misalignedReadBits, misalignedStartReadBits etc.

//       - build a reader that reads n bit from source, and the rest from another
//         - maybe we should just make that a simple object?

#ifndef bgtfsLib_bits_h
#define bgtfsLib_bits_h

#include <stdint.h>
#include <cmath>

namespace namedstruct {
    /* Documentation **********************************************************************/
    /**
     reads numBits bits bitOffset bits away from data and returns it as an uint32.
     numBits has to be <= 31. Will always access the 32-bit memory value that this points to. */
    static inline uint32_t readBits(const void* pData,int bitOffset,int numBits);
    
    /** Sets up the sequential reading of bit values.
     The currentWord and currentBitsLeftInWord will be assigned by this, and the data
     pointer will be pointed at the current word that is being read. To use the
     "readNext" functions, the pData, currentWord and currentBitsLeft in word have to be
     supplied. This will ensure that words are only loaded as needed. */
    static inline void startReadBits(const void* &pData,int bitOffset,
                                     uint32_t &currentWord, int &currentBitsLeftInWord);
    
    /** peforms a sequential reading of bit values. numBits has to be <= 31.
     pData, currentWord and currentBitsLeftInWord Have to be initialized by startReadBits */
    static inline uint32_t readNextBits(const void* &pData,uint32_t &currentWord,
                                        int &currentBitsLeftInWord,int numBits);
    
    /** performs a sequential read of a single bit value
     pData, currentWord and currentBitsLeftInWord Have to be initialized by startReadBits */
    static inline int readNextBit(const void* &pData,uint32_t &currentWord,int &currentBitsLeftInWord);
    
    /** while performing a sequential read operation, skips ahead by numBits, where numBits >= 0 */
    static inline void skipNextBits(const void* &pData,uint32_t &currentWord,
                                    int &currentBitsLeftInWord,int numBits);
    
    /** given the data pointer given to startReadBits, the current data pointer, and the
     current bits left in word, returns the bit offset from the original data pointer
     to the current location. This allows finding out how many bits have been read. */
    static inline int getBitOffset(const void* pDataOriginal, const void* pDataNow, int currentBitsLeftInWord);
    
    
    /** Sets up the backwards sequential reading of bit values.
     The currentWord and currentBitsLeftInWord will be assigned by this, and the data
     pointer will be pointed at the current word that is being read. To use the
     "readPrevious" functions, the pData, currentWord and currentBitsLeft in word have to be
     supplied. This will ensure that words are only loaded as needed. */
    static inline void startReversedReadBits(const void* &pData,int bitOffset,
                                             uint32_t &currentWord, int &currentBitsLeftInWord);
    
    /** performs a reverse sequential read of a single bit value.
     pData, currentWord and currentBitsLeftInWord Have to be initialized by startReversedReadBits.
     The returned bit is the the one that comes before the current location. */
    static inline int readPreviousBit(const void* &pData,uint32_t &currentWord,int &currentBitsLeftInWord);
    
    /** performs a reverse sequential read of bit values. numBits has to be <= 31.
     pData, currentWord and currentBitsLeftInWord Have to be initialized by startReversedReadBits.
     This will first step backwards by numBits bits, and then return numBits bits starting at
     that location. */
    static inline uint32_t readPreviousBits(const void* &pData,uint32_t &currentWord,
                                            int &currentBitsLeftInWord,int numBits);
    
    /**
     returns the number of bits required to store the given number: 0 -> 0, 255 -> 8, 256 -> 9 */
    static int inline requiredBits(int number) {
        return (number == 0)? 0 : (static_cast<int>(log2(number)) + 1);
    }
    
    class BitReader {
    public:
        inline BitReader(const void* newData, int bitOffset = 0){
            this->pData = newData;
            startReadBits(this->pData, bitOffset, currentWord, bitsLeft);
        }
        inline uint32_t readNextBit() {
            return namedstruct::readNextBit(pData, currentWord, bitsLeft);
        }
        inline uint32_t readNextBits(int numBits) {
            return namedstruct::readNextBits(pData, currentWord, bitsLeft, numBits);
        }
        inline void skipBits(int numBits) {
            namedstruct::skipNextBits(pData, currentWord, bitsLeft, numBits);
        }
        inline int getBitOffset(const void* originalData) {
            return namedstruct::getBitOffset(originalData, pData, bitsLeft);
        }
    private:
        const void* pData;
        int bitsLeft;
        uint32_t currentWord;
    };
    
    
    
    /* Implementations *****************************************************************/
    static inline uint32_t readBits(const void* pData, int bitOffset, int numBits) {
        uint32_t* pFirst = (((uint32_t*)pData)+(bitOffset>>5));
        int bitAddress = bitOffset & 0x1F;
        uint32_t first  = (*pFirst) >> bitAddress; //bit address should always be < 32
        uint32_t second = ((bitAddress + numBits > 32)?
                           (*(++pFirst) << (32-bitAddress))
                           :0);
        return (first | second) & (((uint32_t)1 << numBits) - 1);
    }
    
    static inline void startReadBits(const void* &pData,int bitOffset,
                                     uint32_t &currentWord, int &currentBitsLeftInWord) {
        pData = (void*)(((uint32_t*)pData)+(bitOffset>>5)); //get pointer to the correct location
        int bitAddress = bitOffset & 0x1F;
        currentWord = (*(uint32_t*)pData) >> bitAddress;
        currentBitsLeftInWord = 32 - bitAddress;
    }
    
    static inline int getBitOffset(const void* pDataOriginal, const void* pDataNow, int currentBitsLeftInWord) {
        return int((intptr_t(pDataNow)-intptr_t(pDataOriginal))<<3) + (32-currentBitsLeftInWord);
    }
    
    
    static inline uint32_t readNextBits(const void* &pData, uint32_t &currentWord,
                                        int &currentBitsLeftInWord, int numBits) {
        if (numBits > currentBitsLeftInWord) {
            // data is in current word, and next
            pData = (void*)((uint32_t*)pData+1); //advance pointer
            uint32_t nextWord = *(uint32_t*)pData;
            numBits = numBits - currentBitsLeftInWord; //number of bits needed from the new word
            uint32_t bitMask = (((uint32_t)1 << numBits) - 1);
            uint32_t result = (currentWord |
                               ((nextWord & bitMask) << currentBitsLeftInWord));
            currentWord = nextWord >> numBits;
            currentBitsLeftInWord = 32 - numBits;
            return result;
        }
        else {
            // data is contained in current word alone
            uint32_t bitMask = (((uint32_t)1 << numBits) - 1);
            uint32_t result = currentWord & bitMask; // this is why 32bits don't work
            currentBitsLeftInWord -= numBits;
            currentWord >>= numBits;
            return result;
        }
        return 0;
    }
    
    static inline int readNextBit(const void* &pData,uint32_t &currentWord,int &currentBitsLeftInWord) {
        if (__builtin_expect(currentBitsLeftInWord == 0, 0)) {
            pData = (void*)((uint32_t*)pData+1); //advance pointer
            currentWord = *(uint32_t*)pData;
            currentBitsLeftInWord = 32;
        }
        currentBitsLeftInWord -= 1;
        int32_t result = currentWord & 1;
        currentWord >>= 1;
        return result;
    }
    
    static inline void skipNextBits(const void* &pData,uint32_t &currentWord,
                                    int &currentBitsLeftInWord,int numBits){
        if (numBits < currentBitsLeftInWord) {
            currentBitsLeftInWord -= numBits;
            currentWord >>= numBits;
        } else {
            numBits -= currentBitsLeftInWord;
            startReadBits(pData, numBits+32, currentWord, currentBitsLeftInWord);
        }
        /*
         //TODO - dummy implementation, do something better and test it
         for (int i = 0; i < numBits; i++){
         readNextBit(pData,currentWord,currentBitsLeftInWord);
         }*/
    }
    
    static inline void startReversedReadBits(const void* &pData,int bitOffset,
                                             uint32_t &currentWord,
                                             int &currentBitsLeftInWord) {
        int bitAddress = ((bitOffset-1) & 0x1F)+1; // get lower bits, but 32->32, 0->32
        pData = (void*)(((uint32_t*)pData) // get pointer to the correct location
                        +(bitOffset>>5)
                        -(bitAddress>>5)); // if bit Address is 32, we read the previous word
        currentWord = (*(uint32_t*)pData) << ((32 - bitAddress) & 0x1F);
        currentBitsLeftInWord = bitAddress;
    }
    
    static inline uint32_t readPreviousBits(const void* &pData,uint32_t &currentWord,
                                            int &currentBitsLeftInWord, int numBits) {
        if (numBits > currentBitsLeftInWord) {
            // data is in current word, and previous
            pData = (void*)((uint32_t*)pData-1); //step pointer backwards
            uint32_t previousWord = *(uint32_t*)pData;
            numBits = numBits - currentBitsLeftInWord; //number of bits needed from the new word
            uint32_t result = (((currentWord >> (32 - currentBitsLeftInWord)) << numBits)
                               | (previousWord >> (32 - numBits)));
            currentWord = previousWord << numBits;
            currentBitsLeftInWord = 32 - numBits;
            return result;
        }
        else {
            // data is contained in current word alone
            uint32_t result = (numBits == 0? //we have to guard against 0, cuz >> 32 is undefined
                               0
                               :currentWord >> (32 - numBits));
            currentBitsLeftInWord -= numBits;
            currentWord <<= numBits;
            return result;
        }
        return 0;
    }
    
    static inline int readPreviousBit(const void* &pData,uint32_t &currentWord,int &currentBitsLeftInWord) {
        if (__builtin_expect(currentBitsLeftInWord == 0, 0)) {
            pData = (void*)((uint32_t*)pData-1); //step pointer backwards
            currentWord = *(uint32_t*)pData;
            currentBitsLeftInWord = 32;
        }
        currentBitsLeftInWord -= 1;
        int32_t result = currentWord >> 31;
        currentWord <<= 1;
        return result;
    }
    
}

#endif