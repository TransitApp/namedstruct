//
//  getlsb.h
//  namedstruct
//
//  Created by Rodrigo Hausen on 2020-06-26.
//  Copyright © 2020 The Transit App. All rights reserved.
//

#ifndef __namedstruct__getlsb__
#define __namedstruct__getlsb__

namespace namedstruct {
    /* Documentation **********************************************************************/

    /** extracts the numBits least-significant bits from an unsigned word. */
    template <typename Word>
    static inline Word getLSB(Word word, int numBits);


    /* Implementation *****************************************************************/

    template <typename Word>
    inline static Word getLSB_generic(Word word, int numBits) {
        return numBits >= sizeof(Word) * 8 ? word : word & ((static_cast<Word>(1) << numBits) - 1);
    }

#if __x86_64
#define NAMEDSTRUCT_USE_GET_LSB_NATIVE 1

    template <typename Word>
    inline static Word getLSB_native(Word word, int numBits) {
        if constexpr (sizeof(Word) != 4 && sizeof(Word) != 8) {
            return getLSB_generic(word, numBits);
        }
        else {
            constexpr auto adjustWidth = [](int n) {
                return sizeof(Word) == 4 ? n : reinterpret_cast<Word&>(n);
            }

            Word result;
            numBits <<= 8;
            asm ("bextr %[numBits], %[word], %[result])"
                 : [result] "=r" (result)
                 : [word] "r" (word), [numBits] "r" (adjustWidth(numBits))
                 : "cc");
            return result;
        }
    }
#endif

    template <typename Word>
    inline static Word getLSB(Word word, int numBits) {
#if NAMEDSTRUCT_USE_GET_LSB_NATIVE
        return getLSB_native(word, numBits);
#else
        return getLSB_generic(word, numBits);
#endif
    }
}

#endif /* defined(__namedstruct__getlsb__) */
