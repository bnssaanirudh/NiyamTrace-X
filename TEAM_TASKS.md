# Team Tasks & Handoff

Welcome! This document outlines the remaining work items to complete the NiyamTrace testing suite. 

## 🎯 Current Priority: Testing & Test Cases

The core integration tests up to Week 6 (`test_week6_fuzz.py`) are present, but there are several gaps in our testing pyramid that need to be addressed before the next milestone.

### 1. Regression Testing
- **Status**: Not started. The `niyamtrace/tests/regression/` directory is currently empty (only contains `__init__.py`).
- **Action Items**:
  - [ ] Identify key workflows that have broken in the past or are critical to the application.
  - [ ] Create regression test scripts for these workflows.
  - [ ] Ensure backward compatibility of the NLP pipeline is verified continuously.

### 2. Replay Testing
- **Status**: Not started. The `niyamtrace/tests/replay/` directory is currently empty (only contains `__init__.py`).
- **Action Items**:
  - [ ] Setup replay mechanisms to re-run historical traces (from `traces/` folder).
  - [ ] Build assertions that verify the system behaves identically (or within expected variance) when re-processing gold standard traces.

### 3. Unit Test Coverage
- **Status**: In progress. Many unit tests exist in `niyamtrace/tests/unit/`, but coverage needs to be verified.
- **Action Items**:
  - [ ] Run a coverage report (`pytest --cov=niyamtrace niyamtrace/tests/unit/`).
  - [ ] Identify any core modules (like parsers, simulators, or the new multilingual components) lacking >= 80% coverage.
  - [ ] Write unit tests to cover those edge cases, especially for the newly added Telugu and Hinglish language components.

### 4. Continuous Integration
- **Status**: Check GitHub Actions setup.
- **Action Items**:
  - [ ] Verify that `.github/workflows/ci.yml` properly executes all the new regression and replay test suites.
  - [ ] Ensure that trace artifacts needed for replay tests are accessible in the CI environment.

---
*Feel free to check off these items or convert them into GitHub Issues as you begin working on them!*
