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

    /** extracts the numBits least-significant bits from a word. */
    template <typename Word>
    static inline Word getLSB(Word word, int numBits);


    /* Implementation *****************************************************************/

    template <typename Word>
    inline static Word getLSB_generic(Word word, int numBits) {
        return numBits >= sizeof(Word) * 8 ? word : word & ((static_cast<Word>(1) << numBits) - 1);
    }

#if __BMI__ && __x86_64
#include <x86intrin.h>
#define NAMEDSTRUCT_USE_GET_LSB_NATIVE 1

    template <typename Word>
    inline static Word getLSB_native(Word word, int numBits) {
        if constexpr (sizeof(Word) == 4) {
            return _bextr_u32(word, 0, numBits);
        }
        else if constexpr (sizeof(Word) == 8) {
            return _bextr_u64(word, 0, numBits);
        }
        else {
            return getLSB_generic(word, numBits);
        }
    }
#endif

#if __ARM_NEON
#include <arm_neon.h>
#define NAMEDSTRUCT_USE_GET_LSB_NATIVE 1

    template <typename Word>
    inline static Word getLSB_native(Word word, int numBits) {
        if constexpr (sizeof(Word) == 4) {
            return _arm_ubfx(word, 0, numBits);
        }
        else {
            return getLSB_generic(word, numBits);
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
