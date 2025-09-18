# cpp_contractgen

**cpp_contractgen** is a Python code generator that turns simple declarative C++ “contracts” into traits, interfaces, and wrappers. This lets you write **compile-time enforced interfaces** without relying on virtual functions — or optionally generate runtime `virtual` interfaces when you need them.

---

## 🚀 Quick Example

### Input (`MyComb.hpp.contract`)
```cpp
define_contract MyComb {
    bool setDelaySamples(uint32_t d);
    float readTail(uint32_t i) const;
    void writeTail(uint32_t i, float s);
    void advance();
};
```

### Output (`MyComb.contract.hpp`)
Generated file contains:

1. **Traits class** — checks at compile time that a type implements the contract.
   ```cpp
   template<typename T>
   struct MyComb_Traits {
       static constexpr bool has_setDelaySamples =
           std::is_same<decltype(&T::setDelaySamples),
                        bool(T::*)(uint32_t)>::value;
       static_assert(has_setDelaySamples,
           "Type must implement bool setDelaySamples(uint32_t)");
       // ... repeats for other methods ...
   };

   #define IMPLEMENTS_CONTRACT_MyComb(X)        using traits = MyComb_Traits<X>;         (void)sizeof(traits) // force instantiation
   ```

2. **Interface (optional runtime polymorphism)**  
   ```cpp
   class MyComb_Interface {
   public:
       virtual ~MyComb_Interface() = default;
       virtual bool setDelaySamples(uint32_t d) = 0;
       virtual float readTail(uint32_t i) const = 0;
       virtual void writeTail(uint32_t i, float s) = 0;
       virtual void advance() = 0;
   };
   ```

3. **Wrapper** — bridges your implementation with either compile-time or runtime polymorphism.
   ```cpp
   template<typename Impl, bool use_virtual = false>
   class MyCombWrapper { /* calls impl_.method() */ };

   template<typename Impl>
   using MyComb = MyCombWrapper<Impl, false>; // compile-time only

   template<typename Impl>
   using MyCombVirtual = MyCombWrapper<Impl, true>; // virtual dispatch
   ```

---

## 📖 Syntax

A contract definition looks like a **struct of pure function signatures**:

```cpp
define_contract Name {
    return_type method_name(args...);
    return_type method_name(args...) const;
};
```

Rules:
- Must begin with `define_contract <Name> {`.
- End with `};`.
- Each line inside must look like a normal C++ function declaration (ending with `;`).
- Supported:
  - return type (`bool`, `void`, `float`, `T&`, etc.)
  - arguments with types and names
  - optional `const` at the end

---

## 🛠️ Using in your project

### With CMake

You can integrate contract generation in your build:

```cmake
include(cmake/ContractGen.cmake)

add_library(mylib mylib.cpp)

contractgen_generate_contracts(
    TARGET mylib
    SEARCH_DIR ${CMAKE_CURRENT_SOURCE_DIR}/contracts
    OUT_DIR ${CMAKE_BINARY_DIR}/generated/mylib
    INCLUDE_VISIBILITY PUBLIC   # or PRIVATE / INTERFACE / NONE
)
```

This:
- Scans `contracts/*.hpp.contract`
- Generates headers into `build/generated/mylib/`
- Adds them as a dependency of `mylib`
- Adds include paths so you can `#include "MyComb.contract.hpp"`

---

## ✅ Usage in C++

### Enforcing a contract
```cpp
class MyDerived {
    IMPLEMENTS_CONTRACT_MyComb(MyDerived);

public:
    bool setDelaySamples(uint32_t d) { ... }
    float readTail(uint32_t i) const { ... }
    void writeTail(uint32_t i, float s) { ... }
    void advance() { ... }
};
```

If you forget a method or get the signature wrong, the compiler fails with a descriptive `static_assert`.

---

### Compile-time wrapper
```cpp
MyDerived impl;
MyComb<MyDerived> comb(impl);

comb.advance();
```

### Runtime wrapper
```cpp
MyDerived impl;
MyCombVirtual<MyDerived> comb(impl);

MyComb_Interface* iface = &comb;
iface->advance(); // virtual dispatch
```

---

## ⚡ Why use cpp_contractgen?
- **Safer DSP / systems code**: contracts guarantee your class matches the required interface.  
- **Zero runtime cost**: when using compile-time wrappers (no vtables).  
- **Optional virtual dispatch**: for plugin-like use cases.  
- **Integration with CMake**: automatic header generation and inclusion.  
- **Familiar C++ syntax**: write interfaces almost like pure virtual classes.

---

## 📦 Installation

```bash
pip install cpp-contractgen
```

or for development:

```bash
git clone https://github.com/youruser/cpp_contractgen.git
cd cpp_contractgen
pip install -e .
```

---

## 🧪 Testing

- Python unit tests with `pytest`
- C++ traits tests with GoogleTest (CMake integration provided)
