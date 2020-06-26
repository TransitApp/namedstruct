//
//  zigzag.h
//  namedstruct
//
//  Created by Rodrigo Hausen on 2020-06-26.
//  Copyright © 2020 The Transit App. All rights reserved.
//

#ifndef __namedstruct__zigzag__
#define __namedstruct__zigzag__

#include <type_traits>
#include <limits>

namespace namedstruct {
    /* Documentation **********************************************************************/

    /** ZigZag-encodes an integer */
    template <typename Int>
    static inline typename std::make_unsigned<Int>::type zigZagEncode(Int num);


    /* Implementation *****************************************************************/

    template <typename Int>
    static inline typename std::make_unsigned<Int>::type zigZagEncode(Int num) {
        static_assert(std::numeric_limits<Int>::is_integer && std::numeric_limits<Int>::is_signed);
        using UInt = typename std::make_unsigned<Int>::type;
        return (static_cast<UInt>(num) << 1) ^ -(static_cast<UInt>(num) >> (sizeof(Int) * 8 - 1));
    }
}

#endif /* defined(__namedstruct__zigzag__) */
