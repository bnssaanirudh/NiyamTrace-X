# Antigravity Setup & Execution Guide for NiyamTrace-X

Welcome to the NiyamTrace-X project! As an Antigravity agent, if you are tasked with working on this repository, you should follow this guide to set up the local environment and avoid common pitfalls.

## 1. Project Context
**NiyamTrace-X** is an extended workspace containing the core `niyamtrace` platform. The core codebase is inside the `niyamtrace/` directory. All Python commands (install, tests, scripts) must be run from inside the `niyamtrace/` directory.

## 2. Environment Setup

### Install Dependencies
Run the following commands to install the project in editable mode with development dependencies:
```bash
cd c:\Users\aniru\Downloads\NYAMTRACE\niyamtrace
pip install -e ".[dev]"
```

### Environment Variables (.env)
The project relies on environment variables (like API keys) which are **not** checked into version control for security reasons. 
You will see a `.env.example` file in the `niyamtrace/` directory.

1. **Check if `.env` exists:** Use `view_file` or `list_dir` to see if `.env` exists in `niyamtrace/`.
2. **If `.env` is missing:** The human user has likely not provided the API keys. You should:
   - Copy `.env.example` to `.env`
   - Ask the human user to provide the actual values for `GEMINI_API_KEY` and `GROQ_API_KEY`. DO NOT try to run tests without these keys, as API calls will fail.

## 3. Running the Tests

To ensure the environment is correctly set up, you should run the test suite. 

> [!WARNING]
> **Always use `python -m pytest`** instead of just `pytest`. 
> The `pytest` executable is often installed in a `Scripts` directory that is not in the system's `PATH` on Windows. Using `python -m pytest` ensures it uses the module installed in the current Python environment.

**Run all tests:**
```bash
cd c:\Users\aniru\Downloads\NYAMTRACE\niyamtrace
python -m pytest tests/ -v
```

**Seed the test database (if needed by tests):**
```bash
cd c:\Users\aniru\Downloads\NYAMTRACE\niyamtrace
python data/synthetic/erp.py
```

## 4. Starting the Server

If you need to test the gateway locally:
```bash
cd c:\Users\aniru\Downloads\NYAMTRACE\niyamtrace
python -m uvicorn apps.gateway.main:app --reload
```
You can then make requests to `http://localhost:8000/invoke`.

## 5. Summary Checklist
- [ ] Are you in the `niyamtrace/` directory?
- [ ] Is `.env` present and populated with real keys?
- [ ] Did you use `python -m pytest` to run the tests?

If you followed these steps, the project should run perfectly on the host machine.
