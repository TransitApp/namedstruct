//
//  shifts.h
//  namedstruct
//
//  Created by Rodrigo Hausen on 2020-06-23.
//  Copyright © 2020 The Transit App. All rights reserved.
//
//  Utility methods for ensuring bitwise shifts are arithmetic and/or total functions on every platform.

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
struct MaybeNegative : public ShiftDomain<T> {
    using ShiftDomain<T>::value;

    inline constexpr explicit MaybeNegative(T value) : ShiftDomain<T>(value) {}

    template <typename Exp>
    inline constexpr auto operator<<(NonNegative<Exp> exponent) {
        return value > 0 ? value << exponent.clamped<T>() : -((-value) << exponent.clamped<T>());
    }

    template <typename Exp>
    inline constexpr auto operator>>(NonNegative<Exp> exponent) {
        return value > 0 ? value >> exponent.clamped<T>() : -((-value) >> exponent.clamped<T>());
    }

    template <typename Exp>
    inline constexpr auto operator<<(MaybeNegative<Exp> exponent) {
        return exponent.isPositive() ? *this << exponent.toNonNegative() : *this >> exponent.toNonNegativeOpposite();
    }

    template <typename Exp>
    inline constexpr auto operator>>(MaybeNegative<Exp> exponent) {
        return exponent.isPositive() ? *this >> exponent.toNonNegative() : *this << exponent.toNonNegativeOpposite();
    }

    inline constexpr auto isPositive() const {
        return value > 0;
    }

    inline constexpr auto toNonNegative() const {
        return NonNegative<T>(value);
    }

    inline constexpr auto toNonNegativeOpposite() const {
        return NonNegative<T>(-value);
    }
};

template <typename T>
struct NonNegative : public ShiftDomain<T> {
    using ShiftDomain<T>::value;

    inline constexpr explicit NonNegative(T value) : ShiftDomain<T>(value) {}

    template <typename Exp>
    inline constexpr auto operator<<(NonNegative<Exp> exponent) {
        return value << exponent.clamped<T>();
    }

    template <typename Exp>
    inline constexpr auto operator>>(NonNegative<Exp> exponent) {
        return value >> exponent.clamped<T>();
    }

    template <typename Exp>
    inline constexpr auto operator<<(MaybeNegative<Exp> exponent) {
        return exponent.isPositive() ? *this << exponent.toNonNegative() : *this >> exponent.toNonNegativeOpposite();
    }

    template <typename Exp>
    inline constexpr auto operator>>(MaybeNegative<Exp> exponent) {
        return exponent.isPositive() ? *this >> exponent.toNonNegative() : *this << exponent.toNonNegativeOpposite();
    }

    template <typename X>
    inline constexpr auto clamped() {
        constexpr auto ShiftLimit = 8 * sizeof(X) - 1;
        return value & ShiftLimit;
    }
};

}

#endif /* defined(__namedstruct__shifts__) */
