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

## 🎨 Current Priority: UI/UX & Frontend Development

The NiyamTrace dashboard (`niyamtrace/apps/dashboard/`) needs a significant design overhaul to make it enterprise-ready, dynamic, and visually appealing.

### 5. UI Overhaul & Styling
- **Status**: Needs design system integration.
- **Action Items**:
  - [ ] **Modernize the Dashboard**: Implement a rich, premium aesthetic (vibrant colors, dark mode, glassmorphism) using Vanilla CSS in `apps/dashboard/static/`.
  - [ ] **Interactive Elements**: Add hover effects and subtle micro-animations to buttons, tables, and trace detail views.
  - [ ] **Responsive Design**: Ensure the dashboard is fully responsive across desktop, tablet, and mobile breakpoints.
  - [ ] **Typography**: Integrate modern Google Fonts (e.g., Inter, Roboto, or Outfit) to replace browser defaults.

### 6. Frontend Functionality
- **Status**: Basic structure exists, needs enhanced interactivity.
- **Action Items**:
  - [ ] **Trace Visualization**: Build a dynamic trace viewer for the `.jsonl` and `.parquet` files that allows easy filtering, sorting, and drill-down into specific agent actions.
  - [ ] **Real-time Updates**: (Optional) Look into WebSocket or polling integrations for live trace streaming to the dashboard.
  - [ ] **Error/Empty States**: Design and implement visually appealing empty states and error boundary UI.

---

## 📚 Additional Tasks

### 7. Documentation & Onboarding
- **Action Items**:
  - [ ] Update `niyamtrace/docs/architecture.md` with any newly added components (e.g., UI architecture).
  - [ ] Add inline code documentation (docstrings) for any newly written tests and frontend scripts.

---
*Feel free to check off these items or convert them into GitHub Issues as you begin working on them!*
