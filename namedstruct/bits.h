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
    using Word = uint32_t;

    /* Documentation **********************************************************************/

    /** ZigZag-encodes an integer */
    template <typename Int>
    static inline typename std::make_unsigned<Int>::type zigZagEncode(Int num);

    /** extracts the numBits least-significant bits from a word. */
    static inline Word getLSB(Word word, int numBits);

    /**
     reads numBits bits bitOffset bits away from data and returns it as an uint32.
     numBits has to be <= 31. Will always access the 32-bit memory value that this points to. */
    static inline Word readBits(const void* pData, int bitOffset, int numBits);
    
    /** Sets up the sequential reading of bit values.
     The currentWord and currentBitsLeftInWord will be assigned by this, and the data
     pointer will be pointed at the current word that is being read. To use the
     "readNext" functions, the pData, currentWord and currentBitsLeft in word have to be
     supplied. This will ensure that words are only loaded as needed. */
    static inline void startReadBits(const void* &pData, int bitOffset,
                                     Word &currentWord, int &currentBitsLeftInWord);
    
    /** peforms a sequential reading of bit values. numBits has to be <= 31.
     pData, currentWord and currentBitsLeftInWord Have to be initialized by startReadBits */
    static inline Word readNextBits(const void* &pData, Word &currentWord,
                                        int &currentBitsLeftInWord, int numBits);
    
    /** performs a sequential read of a single bit value
     pData, currentWord and currentBitsLeftInWord Have to be initialized by startReadBits */
    static inline int readNextBit(const void* &pData, Word &currentWord, int &currentBitsLeftInWord);
    
    /** while performing a sequential read operation, skips ahead by numBits, where numBits >= 0 */
    static inline void skipNextBits(const void* &pData, Word &currentWord,
                                    int &currentBitsLeftInWord, int numBits);
    
    /** given the data pointer given to startReadBits, the current data pointer, and the
     current bits left in word, returns the bit offset from the original data pointer
     to the current location. This allows finding out how many bits have been read. */
    static inline int getBitOffset(const void* pDataOriginal, const void* pDataNow, int currentBitsLeftInWord);
    
    
    /** Sets up the backwards sequential reading of bit values.
     The currentWord and currentBitsLeftInWord will be assigned by this, and the data
     pointer will be pointed at the current word that is being read. To use the
     "readPrevious" functions, the pData, currentWord and currentBitsLeft in word have to be
     supplied. This will ensure that words are only loaded as needed. */
    static inline void startReversedReadBits(const void* &pData, int bitOffset,
                                             Word &currentWord, int &currentBitsLeftInWord);
    
    /** performs a reverse sequential read of a single bit value.
     pData, currentWord and currentBitsLeftInWord Have to be initialized by startReversedReadBits.
     The returned bit is the the one that comes before the current location. */
    static inline int readPreviousBit(const void* &pData, Word &currentWord, int &currentBitsLeftInWord);
    
    /** performs a reverse sequential read of bit values. numBits has to be <= 31.
     pData, currentWord and currentBitsLeftInWord Have to be initialized by startReversedReadBits.
     This will first step backwards by numBits bits, and then return numBits bits starting at
     that location. */
    static inline Word readPreviousBits(const void* &pData, Word &currentWord,
                                            int &currentBitsLeftInWord, int numBits);
    
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

        inline Word readNextBit() {
            return namedstruct::readNextBit(pData, currentWord, bitsLeft);
        }

        /** The call operator is an alias for readNextBit. */
        inline auto operator()() {
            return readNextBit();
        }

        inline Word readNextBits(int numBits) {
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

        inline Word getCurrentWord() const {
            return currentWord;
        }

    private:
        const void* pData;
        int bitsLeft;
        Word currentWord;
    };

    /* Implementations *****************************************************************/

    constexpr auto WordWidth = BitWidth<Word>;

    template <typename Int>
    static inline typename std::make_unsigned<Int>::type zigZagEncode(Int num) {
        static_assert(std::numeric_limits<Int>::is_integer && std::numeric_limits<Int>::is_signed);
        using UInt = typename std::make_unsigned<Int>::type;
        return (static_cast<UInt>(num) << 1) ^ -(static_cast<UInt>(num) >> (BitWidth<Int> - 1));
    }

    static inline Word getLSB(Word word, int numBits) {
        // TODO: use BEXTR on Intel and UBFX on ARM
        return numBits >= WordWidth ? word : word & ((static_cast<Word>(1) << numBits) - 1);
    }

    static inline const void* advance(const void* pData, int numWords) {
        return reinterpret_cast<const void*>(reinterpret_cast<const Word*>(pData) + numWords);
    }

    /** returns the Word at the memory location starting at the given pointer, stored in little endian order. */
    static inline Word getWord(const void* littleEndianData) {
        static_assert(sizeof(Word) == 4 || sizeof(Word) == 8);

        // manually-unrolled loop so even clang with -O1 can optimize this to a single instruction
        Word result = 0;
        result |= reinterpret_cast<const uint8_t*>(littleEndianData)[0];
        result |= reinterpret_cast<const uint8_t*>(littleEndianData)[1] << 8;
        result |= reinterpret_cast<const uint8_t*>(littleEndianData)[2] << 16;
        result |= reinterpret_cast<const uint8_t*>(littleEndianData)[3] << 24;

        if constexpr (sizeof(Word) == 8) { // future-proofing the code
            result |= reinterpret_cast<const uint8_t*>(littleEndianData)[4] << 32;
            result |= reinterpret_cast<const uint8_t*>(littleEndianData)[5] << 40;
            result |= reinterpret_cast<const uint8_t*>(littleEndianData)[6] << 48;
            result |= reinterpret_cast<const uint8_t*>(littleEndianData)[7] << 56;
        }

        return result;
    }

    /** calculates the absolute minimum number of bits needed to store an integer Num.
     *  E.g.: numbits<32>() is 6 since 32 = 0b100000. */
    template <std::size_t Num>
    static constexpr std::size_t numbits() {
        constexpr auto SmallerNum = Num >> 1;
        return Num == 0 ? 0 : numbits<SmallerNum>() + 1;
    }

    /** calculates x / WordWidth using a right shift */
    static inline auto fastDivisionByWordWidth(int x) {
        return x >> numbits<WordWidth - 1>();
    }

    /** Masks the shift exponent to n bits to mimic IA-32 behaviour. For instance, n = 5 when shifting a 32-bit word.
     *  (SAL/SAR/SHL/SHR – Shift, Chapter 4. Instruction Set Reference, IA-32 Intel Architecture Software Developer’s
     *   Manual)
     */
    static inline auto masked(int x) {
        return Shift<Word>::masked(x);
    }

    static inline Word readBits(const void* pData, int bitOffset, int numBits) {
        const void* pFirst = advance(pData, fastDivisionByWordWidth(bitOffset));
        int bitAddress = masked(bitOffset);
        Word first  = getWord(pFirst) >> bitAddress; //bit address should always be < 32
        Word second = ((bitAddress + numBits > WordWidth)?
                           (getWord(advance(pFirst, 1)) << (WordWidth - bitAddress))
                           :0);
        return getLSB(first | second, numBits);
    }

    static inline void startReadBits(const void* &pData, int bitOffset,
                                     Word &currentWord, int &currentBitsLeftInWord) {
        pData = advance(pData, fastDivisionByWordWidth(bitOffset)); //get pointer to the correct location
        int bitAddress = masked(bitOffset);
        currentWord = getWord(pData) >> bitAddress;
        currentBitsLeftInWord = WordWidth - bitAddress;
    }

    static inline int getBitOffset(const void* pDataOriginal, const void* pDataNow, int currentBitsLeftInWord) {
        return int((intptr_t(pDataNow)-intptr_t(pDataOriginal))<<3) + (32-currentBitsLeftInWord);
    }
    
    
    static inline Word readNextBits(const void* &pData, Word &currentWord,
                                        int &currentBitsLeftInWord, int numBits) {
        if (numBits > currentBitsLeftInWord) {
            // data is in current word, and next
            pData = advance(pData, 1); //advance pointer
            Word nextWord = getWord(pData);
            numBits = numBits - currentBitsLeftInWord; //number of bits needed from the new word
            Word result = (currentWord | (getLSB(nextWord, numBits) << currentBitsLeftInWord));
            currentWord = nextWord >> numBits;
            currentBitsLeftInWord = WordWidth - numBits;
            return result;
        }
        else {
            // data is contained in current word alone
            Word result = getLSB(currentWord, numBits); // this is why 32bits don't work
            currentBitsLeftInWord -= numBits;
            currentWord >>= numBits;
            return result;
        }
        return 0;
    }
    
    static inline int readNextBit(const void* &pData, Word &currentWord, int &currentBitsLeftInWord) {
        if (__builtin_expect(currentBitsLeftInWord == 0, 0)) {
            pData = advance(pData, 1); //advance pointer
            currentWord = getWord(pData);
            currentBitsLeftInWord = WordWidth;
        }
        currentBitsLeftInWord -= 1;
        int32_t result = currentWord & 1;
        currentWord >>= 1;
        return result;
    }
    
    static inline void skipNextBits(const void* &pData, Word &currentWord,
                                    int &currentBitsLeftInWord, int numBits){
        if (numBits < currentBitsLeftInWord) {
            currentBitsLeftInWord -= numBits;
            currentWord >>= numBits;
        } else {
            numBits -= currentBitsLeftInWord;
            startReadBits(pData, numBits + WordWidth, currentWord, currentBitsLeftInWord);
        }
        /*
         //TODO - dummy implementation, do something better and test it
         for (int i = 0; i < numBits; i++){
         readNextBit(pData, currentWord, currentBitsLeftInWord);
         }*/
    }

    static inline void startReversedReadBits(const void* &pData, int bitOffset,
                                             Word &currentWord,
                                             int &currentBitsLeftInWord) {
        int bitAddress = masked(bitOffset-1) + 1; // get lower bits, but 32->32, 0->32
        pData = advance(pData, // get pointer to the correct location
                        +fastDivisionByWordWidth(bitOffset)
                        -fastDivisionByWordWidth(bitAddress)); // if bit Address is 32, we read the previous word
        currentWord = getWord(pData) << masked(WordWidth - bitAddress);
        currentBitsLeftInWord = bitAddress;
    }
    
    static inline Word readPreviousBits(const void* &pData, Word &currentWord,
                                            int &currentBitsLeftInWord, int numBits) {
        if (numBits > currentBitsLeftInWord) {
            // data is in current word, and previous
            pData = advance(pData, -1); //step pointer backwards
            Word previousWord = getWord(pData);
            numBits = numBits - currentBitsLeftInWord; //number of bits needed from the new word
            Word word = NonNegative(currentWord) >> NonNegative(WordWidth - currentBitsLeftInWord);
            Word result = (word << numBits) | (previousWord >> (WordWidth - numBits));
            currentWord = previousWord << numBits;
            currentBitsLeftInWord = WordWidth - numBits;
            return result;
        }
        else {
            // data is contained in current word alone
            Word result = (numBits == 0? //we have to guard against 0, cuz >> 32 is undefined
                               0
                               :currentWord >> (WordWidth - numBits));
            currentBitsLeftInWord -= numBits;
            currentWord <<= numBits;
            return result;
        }
        return 0;
    }
    
    static inline int readPreviousBit(const void* &pData, Word &currentWord, int &currentBitsLeftInWord) {
        if (__builtin_expect(currentBitsLeftInWord == 0, 0)) {
            pData = advance(pData, -1); //step pointer backwards
            currentWord = getWord(pData);
            currentBitsLeftInWord = WordWidth;
        }
        currentBitsLeftInWord -= 1;
        int32_t result = currentWord >> (WordWidth - 1);
        currentWord <<= 1;
        return result;
    }
    
}

#endif
