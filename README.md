# **cpp_contractgen**
![GitHub Issues or Pull Requests](https://img.shields.io/github/issues/rtnate/cpp_contractgen)
![Dynamic TOML Badge](https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fraw.githubusercontent.com%2Frtnate%2Fcpp_contractgen%2Frefs%2Fheads%2Fdev%2Fpyproject.toml&query=%24.project.version&label=version)
![Dynamic TOML Badge](https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fraw.githubusercontent.com%2Frtnate%2Fcpp_contractgen%2Frefs%2Fheads%2Fdev%2Fpyproject.toml&query=%24.project.requires-python&label=python&color=FF4040)
![Static Badge](https://img.shields.io/badge/license-MIT-lightgrey)

## **Generate and Validate C++ Contract Wrappers**

**cpp_contractgen** is a Python code generator that turns simple declarative C++ “contracts” into traits, interfaces, and wrappers. 
This project aims to bring design-by-contract (DbC) principles easily into C++ projects using a simple, declarative syntax.
This allows for compile-time polymorphism with an enforced interface for use in circumstances where virtual overhead is 
costly (microcontrollers, highly-inlined dsp implementations, etc)

## **Installation (Beta v0.1.0)**

Since this is a pre-release version, you can install the package directly from the source repository using pip.

### **Using pip and Git**

Ensure you have Python v3.8 or better and git installed, then run:  
```Shell
pip install git+https://github.com/rtnate/cpp_contractgen@v0.1.0
```

### **Development Dependencies**

For development, testing, and contributions, install the project in editable mode including the test dependency group:  
```
pip install -e .[dev]
```

## **Quick Example**

### **Input (MyComb.hpp.contract)**
```c
define_contract MyComb {  
    bool setDelaySamples(uint32_t d);  
    float readTail(uint32_t i) const;  
    void writeTail(uint32_t i, float s);  
    void advance();  
};
```
### **Output (MyComb.contract.hpp)**

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

   #define IMPLEMENTS_CONTRACT_MyComb(X) \       
   using traits = MyComb_Traits<X>; \
   (void)sizeof(traits) // force instantiation
```

2. Interface (optional runtime polymorphism) 
```cpp  
   class MyCombInterface {  
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

## **Command Line Usage**

The cpp-contractgen tool supports three main modes of operation:

### **1. Single-File Mode (Requires both input and output paths)**

Processes a single contract file:  
```shell
cpp-contractgen --contract src/contracts/MyComb.hpp.contract --output include/generated/MyComb.contract.hpp
```

Generates file in cwd (becomes "./MyComb.contract.hpp"):
```shell
cpp-contractgen --contract src/contracts/MyComb.hpp.contract
```

Optionally send output to stdout:  
```shell
cpp-contractgen --contract src/contracts/MyComb.hpp.contract --output -
cpp-contractgen --contract src/contracts/MyComb.hpp.contract --output
cpp-contractgen --contract src/contracts/MyComb.hpp.contract -o
```
Optionally read from stdin:
```shell
cpp-contractgen --contract - --output include/generated/MyComb.contract.hpp
```

### **2. Batch Mode (For discovery and multiple files)**

Scans specified directories or uses paths from a configuration file.  

Scan multiple directories for *.hpp.contract files:
```shell
cpp-contractgen --search contracts/folder1 contracts/folder2
```

Use a config file for detailed policy and file paths:
```shell
cpp-contractgen   #searches cwd for cpp_contract.json by default
cpp-contractgen --config cpp_contract.json #specify explicity
```

Override the output directory (preserves subfolders of search directories):
```shell
cpp-contractgen --search contracts/folder1 --outdir generated
```

### **3. Emit-Header Mode (Utility)**

Generates a dummy header file that can be included by intellisense to help 
parsing contract files:
```Shell
# emits cpp_contractgen to cwd
cpp-contractgen --emit-header 
# specify the output directory
cpp-contractgen --emit-header include #generates include/cpp_contractgen
cpp-contractgen --emit-header --outdir .vscode #generates .vscode/cpp_contractgen
# or the output file explicitly
cpp-contractgen --emit-header include/myheader.h #generates include/myheader.h
cpp-contractgen --emit-header --output dummy_header.hpp #generates ./dummy_header.h
# or to stdout
cpp-contractgen --emit-header -o
```

### **CLI Flags**

| Flag | Description |
| :---- | :---- |
| -y, --yes | Auto-confirm all prompts (e.g., automatically overwrite existing files). |
| --no  | Auto-reject all prompts (e.g., automatically overwrite existing files). |
| --mode {debug, release} | Chooses configuration build mode (debug default) |
|  --debug, --release     | Chooses configuration build mode |
| -q, --quiet | Suppress unnecessary logging |
| -v, --verbose | Generate additional logging |
| --check  | Runs 'check' mode only and returns the number of contracts that have changed |
| --diff   | Runs 'check' mode only and returns a detailed diff of changed contracts |
| --overwrite | Overwrite changed contracts (default behaviour is to generated new only) |
| --contract | Specify input contract (single file mode, accepts file or '-' for stdin) |
| -o, --output | Specify output file (use nothing or '-' for stdout, not valid for batch generation) |
| --outdir | Specify output directory - uses input or default filenames for generated headers |
| --init | Generated a default cpp_contractgen.json to cwd |
| --version | Print the current version and exit. |

## **Syntax**

A contract definition looks like a **struct of pure function signatures**: 
```c
#include <cpp_contractgen>
define_contract Name {  
    return_type method_name(args...);  
    return_type method_name(args...) const;  
};
```

Rules:
* Contract parsing begins at `#include <cpp_contractgen>` and it is required
* Contracts themselves Must begin with define_contract <Name> {.  
* End with };.  
* Each line inside must look like a normal C++ function declaration (ending with ;).  
* Supported:  
  * return type (bool, void, float, T&, etc.)  
  * arguments with types and names  
  * optional const at the end
* Header content outside of `define_contract <Name>{ ... };` will be preserved

## **Using in your project**

## **Usage in C++**

### **Enforcing a contract**

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

If you forget a method or get the signature wrong, the compiler fails with a descriptive static_assert.

### **Compile-time wrapper**

```cpp
MyDerived impl;  
MyComb<MyDerived> comb(impl);

comb.advance();
```

### **Runtime wrapper**

```cpp
MyDerived impl;  
MyCombVirtual<MyDerived> comb(impl);

MyCombInterface* iface = &comb;  
iface->advance(); // virtual dispatch
```

## **Why use cpp_contractgen?**

* **Safer DSP / MCU code**: contracts guarantee your class matches the required interface.  
* **Zero runtime cost**: when using compile-time wrappers (no vtables).  
* **Optional virtual dispatch**: for plugin-like use cases.   
* **Familiar C++ syntax**: write interfaces almost like pure virtual classes.

## **Testing**

* Python unit tests with pytest  
* C++ traits tests with GoogleTest (CMake integration provided) - WIP

## **Contributing**

We welcome contributions! To get started:

1. **Fork** the repository on GitHub.  
2. **Clone** your forked repository.  
3. **Create a feature branch** (git checkout -b feature/my-new-feature).  
4. **Install dependencies** (pip install -e .[test]).  
5. **Write tests** for your changes.  
6. **Run tests** (python -m pytest).  
7. **Commit** your changes (git commit -m 'feat: added new contract feature').  
8. **Push** to your branch (git push origin feature/my-new-feature).  
9. **Open a Pull Request** against the main branch.