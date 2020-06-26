//
//  shifts.h
//  namedstruct
//
//  Created by Rodrigo Hausen on 2020-06-23.
//  Copyright © 2020 The Transit App. All rights reserved.
//
//  Utility methods for ensuring that, on every platform, bitwise shifts are:
//  * [arithmetic](https://en.wikipedia.org/wiki/Arithmetic_shift); and/or
//  * total functions, i.e., `base << exponent` and `base >> exponent` are defined for any base and exponent in their ranges.
//
//  Usually, in C++, the expression `base << exponent` (or `base >> exponent`) results in undefined behaviour if at least one of these is true:
//  * `base` is negative;
//  * `exponent` is negative;
//  * `exponent` is greater than or equal to the number of bits in `base`.
//
//  By wrapping both the base and exponent in either `NonNegative` or `MaybeNegative`, the behaviour of any shift becomes well-defined,
//  mimicking the one expected on an x86 architecture.
//
//  The aim is to fix every shift in the code that relies on undefined behaviour with these methods, not only inside namedstruct but also in
//  any library for which namedstruct is a submodule.
//
//  The object code produced was checked on https://godbolt.org/ and is optimal when compiled with `clang -O2` targeting an x86-64 processor.
//  Every shift with a non-negative exponent is executed with exactly 1 instruction, whereas shitfs with an arbitrary exponent are done with
//  either 3 or 4 instructions.
//
//  See also: https://github.com/TransitApp/namedstruct/pull/21

#ifndef __namedstruct__shifts__
#define __namedstruct__shifts__

#include <type_traits>

namespace namedstruct {

template <typename T>
struct NonNegative;

template <typename T>
struct MaybeNegative;

template <typename T>
static constexpr auto BitWidth = 8 * sizeof(T);

template <typename T>
struct Shift {
    static constexpr auto Mask = BitWidth<T> - 1;

    template <typename X>
    std::enable_if_t<std::is_arithmetic<X>::value, X>
    static inline constexpr masked(X value) {
        return value & static_cast<X>(Mask);
    }

    template <typename Obj>
    std::enable_if_t<!std::is_arithmetic<Obj>::value, typename Obj::value_type>
    static inline constexpr masked(Obj obj) {
        return obj.value & static_cast<typename Obj::value_type>(Mask);
    }
};

template <typename T, typename Derived>
struct Shiftable {
    T value;

    inline constexpr explicit Shiftable(T value) : value(value) {}

    Shiftable() = delete;

    template <typename Exp>
    inline constexpr auto operator<<(MaybeNegative<Exp> exponent) const {
        return exponent.isPositive() ? self() << exponent.toNonNegative() : self() >> exponent.toNonNegativeOpposite();
    }

    template <typename Exp>
    inline constexpr auto operator>>(MaybeNegative<Exp> exponent) const {
        return exponent.isPositive() ? self() >> exponent.toNonNegative() : self() << exponent.toNonNegativeOpposite();
    }

private:
    constexpr auto self() const {
        return static_cast<const Derived&>(*this);
    }
};

/** Wrap any base or exponent that is possibly negative in MaybeNegative. */
template <typename T>
struct MaybeNegative : public Shiftable<T, MaybeNegative<T>> {
    using value_type = T;

    using Shiftable<T, MaybeNegative<T>>::value;

    using Shiftable<T, MaybeNegative<T>>::operator<<;

    using Shiftable<T, MaybeNegative<T>>::operator>>;

    inline constexpr explicit MaybeNegative(T value) : Shiftable<T, MaybeNegative<T>>(value) {}

    template <typename Exp>
    inline constexpr auto operator<<(NonNegative<Exp> exponent) const {
        return value > 0 ? value << Shift<T>::masked(exponent) : -((-value) << Shift<T>::masked(exponent));
    }

    template <typename Exp>
    inline constexpr auto operator>>(NonNegative<Exp> exponent) const {
        return value > 0 ? value >> Shift<T>::masked(exponent) : ~((~value) >> Shift<T>::masked(exponent));
    }

    inline constexpr bool isPositive() const {
        return value > 0;
    }

    inline constexpr auto toNonNegative() const {
        return NonNegative<T>(value);
    }

    inline constexpr auto toNonNegativeOpposite() const {
        return NonNegative<T>(-value);
    }
};

/** Wrap any base or exponent that is guaranteed to be either positive or zero in NonNegative. */
template <typename T>
struct NonNegative : public Shiftable<T, NonNegative<T>> {
    using value_type = T;

    using Shiftable<T, NonNegative<T>>::value;

    using Shiftable<T, NonNegative<T>>::operator<<;

    using Shiftable<T, NonNegative<T>>::operator>>;

    inline constexpr explicit NonNegative(T value) : Shiftable<T, NonNegative<T>>(value) {}

    template <typename Exp>
    inline constexpr auto operator<<(NonNegative<Exp> exponent) const {
        return value << Shift<T>::masked(exponent);
    }

    template <typename Exp>
    inline constexpr auto operator>>(NonNegative<Exp> exponent) const {
        return value >> Shift<T>::masked(exponent);
    }
};

}

#endif /* defined(__namedstruct__shifts__) */
