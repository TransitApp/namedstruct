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

#include "shifts.h"
#include <cmath>
#include <limits>
#include <stdint.h>
#include <type_traits>

namespace namedstruct {
    /* Documentation **********************************************************************/

    /** ZigZag-encodes an integer */
    template <typename Int>
    static inline typename std::make_unsigned<Int>::type zigZagEncode(Int num);

    /** extracts the numBits least-significant bits from a word. */
    static inline uint32_t getLSB(uint32_t word, int numBits);

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
        inline explicit BitReader() {}

        inline BitReader(const void* newData, int bitOffset = 0) {
            reset(newData, bitOffset);
        }

        inline void reset(const void* newData, int bitOffset = 0) {
            this->pData = newData;
            startReadBits(this->pData, bitOffset, currentWord, bitsLeft);
        }

        inline uint32_t readNextBit() {
            return namedstruct::readNextBit(pData, currentWord, bitsLeft);
        }

        /** The call operator is an alias for readNextBit. */
        inline auto operator()() {
            return readNextBit();
        }

        inline uint32_t readNextBits(int numBits) {
            return namedstruct::readNextBits(pData, currentWord, bitsLeft, numBits);
        }

        template <typename T> inline T readNextBits(int numBits) {
            return static_cast<T>(namedstruct::readNextBits(pData, currentWord, bitsLeft, numBits));
        }

        inline void skipBits(int numBits) {
            namedstruct::skipNextBits(pData, currentWord, bitsLeft, numBits);
        }

        inline int getBitOffset(const void* originalData) {
            return namedstruct::getBitOffset(originalData, pData, bitsLeft);
        }

        inline const void* getCurrentDataPointer() const {
            return pData;
        }

        inline int getBitsLeft() const {
            return bitsLeft;
        }

        inline uint32_t getCurrentWord() const {
            return currentWord;
        }

    private:
        const void* pData;
        int bitsLeft;
        uint32_t currentWord;
    };

    /* Implementations *****************************************************************/

    template <typename Int>
    static inline typename std::make_unsigned<Int>::type zigZagEncode(Int num) {
        static_assert(std::numeric_limits<Int>::is_integer && std::numeric_limits<Int>::is_signed);
        using UInt = typename std::make_unsigned<Int>::type;
        return (static_cast<UInt>(num) << 1) ^ -(static_cast<UInt>(num) >> (sizeof(Int) * 8 - 1));
    }

    static inline uint32_t getLSB(uint32_t word, int numBits) {
        // TODO: use BEXTR on Intel and UBFX on ARM
        return numBits >= 32 ? word : word & ((static_cast<uint32_t>(1) << numBits) - 1);
    }

    static inline const void* advance(const void* pData, int num32BitWords) {
        return reinterpret_cast<const void*>(reinterpret_cast<const uint32_t*>(pData) + num32BitWords);
    }

    static inline uint32_t getUInt32(const void* littleEndianData) {
        uint32_t result = reinterpret_cast<const uint8_t*>(littleEndianData)[0];
        result |= reinterpret_cast<const uint8_t*>(littleEndianData)[1] << 8;
        result |= reinterpret_cast<const uint8_t*>(littleEndianData)[2] << 16;
        result |= reinterpret_cast<const uint8_t*>(littleEndianData)[3] << 24;
        return result;
    }

    static inline uint32_t readBits(const void* pData, int bitOffset, int numBits) {
        constexpr BitWidth<uint32_t> bitwidth;

        const void* pFirst = advance(pData, bitOffset >> 5);
        auto bitAddress = bitwidth.clamp(NonNegative(bitOffset));
        uint32_t first  = NonNegative(getUInt32(pFirst)) >> bitAddress; //bit address should always be < 32
        uint32_t second = ((bitAddress + NonNegative(numBits) > bitwidth)?
                           (NonNegative(getUInt32(advance(pFirst, 1))) << (bitwidth - bitAddress))
                           :0);
        return getLSB(first | second, numBits);
    }

    static inline void startReadBits(const void* &pData,int bitOffset,
                                     uint32_t &currentWord, int &currentBitsLeftInWord) {
        constexpr BitWidth<uint32_t> bitwidth;

        pData = advance(pData, bitOffset>>5); //get pointer to the correct location
        auto bitAddress = bitwidth.clamp(NonNegative(bitOffset));
        currentWord = NonNegative(getUInt32(pData)) >> bitAddress;
        currentBitsLeftInWord = (bitwidth - bitAddress).value;
    }

    static inline int getBitOffset(const void* pDataOriginal, const void* pDataNow, int currentBitsLeftInWord) {
        return int((intptr_t(pDataNow)-intptr_t(pDataOriginal))<<3) + (32-currentBitsLeftInWord);
    }
    
    
    static inline uint32_t readNextBits(const void* &pData, uint32_t &currentWord,
                                        int &currentBitsLeftInWord, int numBits) {
        if (numBits > currentBitsLeftInWord) {
            // data is in current word, and next
            pData = advance(pData, 1); //advance pointer
            uint32_t nextWord = getUInt32(pData);
            numBits = numBits - currentBitsLeftInWord; //number of bits needed from the new word
            uint32_t result = (currentWord | (getLSB(nextWord, numBits) << currentBitsLeftInWord));
            currentWord = nextWord >> numBits;
            currentBitsLeftInWord = 32 - numBits;
            return result;
        }
        else {
            // data is contained in current word alone
            uint32_t result = getLSB(currentWord, numBits); // this is why 32bits don't work
            currentBitsLeftInWord -= numBits;
            currentWord >>= numBits;
            return result;
        }
        return 0;
    }
    
    static inline int readNextBit(const void* &pData,uint32_t &currentWord,int &currentBitsLeftInWord) {
        if (__builtin_expect(currentBitsLeftInWord == 0, 0)) {
            pData = advance(pData, 1); //advance pointer
            currentWord = getUInt32(pData);
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
        constexpr BitWidth<uint32_t> bitwidth;

        auto bitAddress = bitwidth.clamp(NonNegative(bitOffset-1)) + NonNegative(1); // get lower bits, but 32->32, 0->32
        pData = advance(pData, // get pointer to the correct location
                        +(bitOffset>>5)
                        -(bitAddress >> NonNegative(5))); // if bit Address is 32, we read the previous word
        currentWord = NonNegative(getUInt32(pData)) << (bitwidth - bitAddress);
        currentBitsLeftInWord = bitAddress.value;
    }
    
    static inline uint32_t readPreviousBits(const void* &pData,uint32_t &currentWord,
                                            int &currentBitsLeftInWord, int numBits) {
        if (numBits > currentBitsLeftInWord) {
            // data is in current word, and previous
            pData = advance(pData, -1); //step pointer backwards
            uint32_t previousWord = getUInt32(pData);
            numBits = numBits - currentBitsLeftInWord; //number of bits needed from the new word
            uint32_t word = NonNegative(currentWord) >> NonNegative(32 - currentBitsLeftInWord);
            uint32_t result = (word << numBits) | (previousWord >> (32 - numBits));
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
            pData = advance(pData, -1); //step pointer backwards
            currentWord = getUInt32(pData);
            currentBitsLeftInWord = 32;
        }
        currentBitsLeftInWord -= 1;
        int32_t result = currentWord >> 31;
        currentWord <<= 1;
        return result;
    }
    
}

#endif
