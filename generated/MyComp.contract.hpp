// Auto-generated from MyComp.hpp.contract
#pragma once
#include <type_traits>

// === Traits ================================================================

template<typename T>
struct MyComb_Traits {
    static constexpr bool has_setDelaySamples =
        std::is_same<decltype(&T::setDelaySamples),
                     bool(T::*)(['uint32_t'])>::value;
    static_assert(has_setDelaySamples, 
        "Type must implement bool setDelaySamples(['uint32_t'])");
    static constexpr bool has_readTail =
        std::is_same<decltype(&T::readTail),
                     float(T::*)(['uint32_t']) const>::value;
    static_assert(has_readTail, 
        "Type must implement float readTail(['uint32_t']) const");
    static constexpr bool has_writeTail =
        std::is_same<decltype(&T::writeTail),
                     void(T::*)(['uint32_t', 'float'])>::value;
    static_assert(has_writeTail, 
        "Type must implement void writeTail(['uint32_t', 'float'])");
    static constexpr bool has_advance =
        std::is_same<decltype(&T::advance),
                     void(T::*)([])>::value;
    static_assert(has_advance, 
        "Type must implement void advance([])");
};

#define IMPLEMENTS_CONTRACT_MyComb(X) \
    using traits = MyComb_Traits<X>; \
    static_assert(true, ""); // force instantiation

// === Interface =============================================================

class MyComb_Interface {
public:
    virtual ~MyComb_Interface() = default;
    virtual bool setDelaySamples(uint32_t d) = 0;
    virtual float readTail(uint32_t i) const = 0;
    virtual void writeTail(uint32_t i, float s) = 0;
    virtual void advance() = 0;
};

// === Wrapper ===============================================================

template<typename Impl, bool use_virtual = false>
class MyCombWrapper {
    IMPLEMENTS_CONTRACT_MyComb(Impl);

public:
    MyCombWrapper(Impl& impl) : impl_(impl) {}

    bool setDelaySamples(uint32_t d) {
        return impl_.setDelaySamples(d);
    }
    float readTail(uint32_t i) const {
        return impl_.readTail(i);
    }
    void writeTail(uint32_t i, float s) {
        return impl_.writeTail(i, s);
    }
    void advance() {
        return impl_.advance();
    }

protected:
    Impl& impl_;
};

// Specialization for virtual
template<typename Impl>
class MyCombWrapper<Impl, true> : public MyComb_Interface {
    IMPLEMENTS_CONTRACT_MyComb(Impl);

public:
    MyCombWrapper(Impl& impl) : impl_(impl) {}

    bool setDelaySamples(uint32_t d) override {
        return impl_.setDelaySamples(d);
    }
    float readTail(uint32_t i) const override {
        return impl_.readTail(i);
    }
    void writeTail(uint32_t i, float s) override {
        return impl_.writeTail(i, s);
    }
    void advance() override {
        return impl_.advance();
    }

protected:
    Impl& impl_;
};

// === Aliases ===============================================================

template<typename Impl>
using MyComb = MyCombWrapper<Impl, false>;

template<typename Impl>
using MyCombVirtual = MyCombWrapper<Impl, true>;