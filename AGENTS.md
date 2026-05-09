# Repository Guidelines

## Project Structure & Module Organization
- `src/lib.rs`: Rust PHP extension entrypoint and observer hook logic.
- `tests/`: Python unit tests for benchmark analysis utilities (`unittest`-based).
- `scripts/`: Benchmark orchestration and result summarization scripts.
- `bench/`: Micro-benchmark PHP workloads used by `scripts/run-benchmarks.sh`.
- `php.ini` and `test.php`: Local extension loading and manual sanity-check script.
- `target/` and `results/`: Build artifacts and generated benchmark outputs (do not hand-edit).

## Build, Test, and Development Commands
- `devenv shell`: Enter the Nix development shell with PHP/tooling dependencies.
- `cargo build`: Build debug extension artifact.
- `cargo build --release`: Build optimized extension used in benchmark runs.
- `php -c php.ini test.php`: Run a local manual extension check.
- `python3 -m unittest tests/test_benchmark_analysis.py`: Run Python test suite.
- `bash scripts/run-benchmarks.sh`: Run micro + Symfony benchmarks and write `results/<timestamp>/`.

## Coding Style & Naming Conventions
- Rust: follow idiomatic Rust (`snake_case` functions, `CamelCase` types, 4-space indentation), keep unsafe blocks minimal and justified.
- Python: follow PEP 8 with type hints where practical; keep scripts deterministic and CLI-friendly.
- PHP benchmark files: use descriptive, lowercase underscore names (for example `mixed_argument_shapes.php`).
- Prefer small, focused functions over large procedural blocks.

## Testing Guidelines
- Primary automated tests are Python `unittest` cases in `tests/test_benchmark_analysis.py`.
- Name new test methods `test_<behavior>` and keep each test focused on one behavior.
- For Rust observer changes, run both:
  - `cargo build --release`
  - `php -c php.ini test.php`
- When changing benchmark scripts, verify output files (`summary.json`, `summary.md`) are regenerated correctly.

## Commit & Pull Request Guidelines
- Use short, imperative commit messages, matching project history (examples: `Add benchmarking`, `Improve performance ...`, `refactor code`).
- Keep commits scoped to one logical change.
- PRs should include:
  - what changed and why,
  - commands run for validation,
  - benchmark before/after notes when performance-sensitive code is touched.
