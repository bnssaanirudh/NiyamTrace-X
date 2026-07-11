# NiyamTrace-X

Welcome to the NiyamTrace-X project repository! 

**NiyamTrace-X** is an extended workspace containing the core `niyamtrace` platform alongside its execution traces. NiyamTrace is a local-first, NLP-first assurance platform for tool-using LLM agents operating in multilingual (English, Hinglish, Telugu, Romanized Telugu) enterprise environments.

## Repository Structure

- `niyamtrace/`: The core application codebase. This includes all the backend services, NLP models, test suites, and documentation.
- `traces/`: Contains the execution traces and system run logs in `.jsonl` and `.parquet` formats, used for auditing and performance metrics.

## Getting Started

To get started with the NiyamTrace core application:

```bash
cd niyamtrace
pip install -e ".[dev]"
```

*For a detailed breakdown of the architecture, decisions, and development guidelines, please refer to the `README.md` inside the `niyamtrace/` directory and the `niyamtrace/docs/` folder.*

## Team Collaboration

We are actively developing this platform. If you are a team member taking over current tasks, please see `TEAM_TASKS.md` in this root directory for your assignments.
