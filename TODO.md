# TODO List for cpp_contractgen

This document tracks outstanding work items, ideas, and future improvements for `cpp_contractgen`.

## Parser Improvements
- [ ] Enforce presence of `#include <cpp_contractgen>` in contract files (already started).
- [ ] Preserve verbatim code between `#include <cpp_contractgen>` and `define_contract`.
- [ ] Add support for namespaces (initially naive: emit surrounding code verbatim).
- [ ] Add better error messages for malformed contract definitions.

## Generator Improvements
- [ ] Rename generated classes consistently (`MyContractTraits`, `MyContractInterface`, etc.).
- [ ] Add `Owned` wrapper that constructs and owns the implementation object directly.
- [ ] Add metadata comments to generated headers:
  - [ ] Original contract definition in comments.
  - [ ] Hash/checksum of contract file for change detection.
- [ ] Add option to control alias names (`Direct`, `Virtual`, `Owned`).

## CLI Features
- [ ] Add config file support (`cpp_contractgen.json`) to define policies:
  - [ ] Always regenerate, warn on mismatch, error on mismatch, manual-only.
- [ ] Add CLI flag to emit the dummy `cpp_contractgen` header.
- [ ] Add option to auto-generate integration snippets (CMake, PlatformIO).
- [ ] Support recursive directory scanning with mirroring.

## Integration
- [ ] Improve CMake integration:
  - [ ] Configurable visibility (PUBLIC/PRIVATE/INTERFACE/NONE).
  - [ ] Option to enforce Python package availability at configure time.
- [ ] PlatformIO helper mode to ease adoption.

## Testing & QA
- [ ] Add more pytest coverage (parser edge cases, generator variations).
- [ ] Add integration tests that run actual C++ compiles with generated headers.
- [ ] Add CI workflow (GitHub Actions) for automated testing.

## Documentation
- [ ] Expand README with usage examples and integration tips.
- [ ] Document configuration file policies and workflow options.
- [ ] Provide examples for DSP-style use cases.
