# Contributing to Antigravity

Thank you for your interest in contributing to Antigravity! Antigravity models software delivery pipelines as physical systems subject to drag ("gravity") and applies automated, measurable counterforces ("thrust") to move delivery processes toward escape velocity.

## Getting Started

1. Fork the repo and create your feature branch:
   ```bash
   git checkout -b feature/my-new-thruster
   ```
2. Follow the coding standards in Section 12.2 of the README.
3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
4. Ensure all tests and static analysis checks pass locally:
   ```bash
   pytest --cov=antigravity --cov-report=term-missing
   mypy antigravity/
   ruff check antigravity/
   ruff format antigravity/
   ```
5. Open a Pull Request with:
   - Clear problem statement and objective.
   - Before/after metrics (if applicable, e.g. changes affecting `Fix@k` or drag rankings).
   - Test coverage matching or exceeding 90% on new code.
6. At least one maintainer approval and passing CI checks are required to merge.

## Coding Standards & Architecture Guidelines

- All public interfaces (`BaseSensor`, `BaseThruster`) are Protocol/ABC-typed. New plugins must implement the full interface.
- No thruster may perform a write action against an external system outside its declared `write_scope`. This is enforced by runtime guards.
- All new metrics must include: formula docstring, unit test with a hand-computed worked example (see `tests/metrics/test_fix_at_k.py`), and a rubric entry in the documentation.
- Prefer composition over inheritance for thruster variants; use `ThrusterRegistry` for dynamic binding.
