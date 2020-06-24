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

namespace namedstruct {

template <typename T>
struct NonNegative;

template <typename T>
struct MaybeNegative;

template <typename T>
struct ShiftDomain {
    T value;

    inline constexpr explicit ShiftDomain(T value) : value(value) {}

    ShiftDomain() = delete;
};

template <typename T>
struct Clamped : public ShiftDomain<T> {
    using ShiftDomain<T>::value;

    inline constexpr explicit Clamped(T value) : ShiftDomain<T>(value) {}
    
    template <typename X>
    inline constexpr auto operator+(NonNegative<X> other) const {
        return NonNegative<X>(value + other.value);
    }
};

template <typename T>
struct BitWidth {
    static constexpr auto value = 8 * sizeof(T);

    inline constexpr explicit BitWidth() = default;

    template <typename X>
    inline constexpr static auto clamp(NonNegative<X> other) {
        return Clamped(other.value & (value - 1));
    }
    
    template <typename X>
    inline constexpr static auto clamp(Clamped<X> other) {
        return Clamped(other.value);
    }

    template <typename X>
    inline constexpr auto operator-(Clamped<X> other) const {
        return Clamped<X>(value - other.value);
    }

    template <typename X>
    inline constexpr auto operator-(NonNegative<X> other) const {
        return NonNegative<X>(value - other.value);
    }
};

template <typename Derived>
struct Shiftable {
    template <typename Exp>
    inline constexpr auto operator<<(NonNegative<Exp> exponent) const {
        return derived().shiftLeft(exponent);
    }

    template <typename Exp>
    inline constexpr auto operator>>(NonNegative<Exp> exponent) const {
        return derived().shiftRight(exponent);
    }
    
    template <typename Exp>
    inline constexpr auto operator<<(Clamped<Exp> exponent) const {
        return derived().shiftLeft(exponent);
    }

    template <typename Exp>
    inline constexpr auto operator>>(Clamped<Exp> exponent) const {
        return derived().shiftRight(exponent);
    }
    
    template <typename Exp>
    inline constexpr auto operator<<(MaybeNegative<Exp> exponent) const {
        return exponent.isPositive() ? derived() << exponent.toNonNegative() : derived() >> exponent.toNonNegativeOpposite();
    }

    template <typename Exp>
    inline constexpr auto operator>>(MaybeNegative<Exp> exponent) const {
        return exponent.isPositive() ? derived() >> exponent.toNonNegative() : derived() << exponent.toNonNegativeOpposite();
    }
    
    inline constexpr auto derived() const {
        return static_cast<const Derived&>(*this);
    }
};

/** Wrap any base or exponent that is possibly negative in MaybeNegative. */
template <typename T>
struct MaybeNegative : public ShiftDomain<T>, public Shiftable<MaybeNegative<T>> {
    using value_type = T;

    using ShiftDomain<T>::value;

    inline constexpr explicit MaybeNegative(T value) : ShiftDomain<T>(value) {}

    inline constexpr bool isPositive() const {
        return value > 0;
    }

    inline constexpr auto toNonNegative() const {
        return NonNegative<T>(value);
    }

    inline constexpr auto toNonNegativeOpposite() const {
        return NonNegative<T>(-value);
    }

protected:
    template <typename Exp>
    inline constexpr auto shiftLeft(Exp exponent) const {
        return value > 0 ? value << BitWidth<T>::clamp(exponent).value : -((-value) << BitWidth<T>::clamp(exponent)).value;
    }
    
    template <typename Exp>
    inline constexpr auto shiftRight(Exp exponent) const {
        return value > 0 ? value >> BitWidth<T>::clamp(exponent).value : ~((~value) >> BitWidth<T>::clamp(exponent)).value;
    }
    
    friend struct Shiftable<MaybeNegative<T>>;
};

/** Wrap any base or exponent that is guaranteed to be either positive or zero in NonNegative. */
template <typename T>
struct NonNegative : public ShiftDomain<T>, public Shiftable<NonNegative<T>> {
    using value_type = T;

    using ShiftDomain<T>::value;

    inline constexpr explicit NonNegative(T value) : ShiftDomain<T>(value) {}

    template <typename X>
    inline constexpr bool operator>(BitWidth<X> other) {
        return value > other.value;
    }

protected:
    template <typename Exp>
    inline constexpr auto shiftLeft(Exp exponent) const {
        return value << BitWidth<T>::clamp(exponent).value;
    }
    
    template <typename Exp>
    inline constexpr auto shiftRight(Exp exponent) const {
        return value >> BitWidth<T>::clamp(exponent).value;
    }
    
    friend struct Shiftable<NonNegative<T>>;
};

}

#endif /* defined(__namedstruct__shifts__) */
