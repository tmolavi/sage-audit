# Contributing to SAGE Audit

We welcome pull requests and issues!

## Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/tmolavi/sage-audit.git
   cd sage-audit
   ```
2. Set up virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   pip install pytest pytest-cov
   ```
3. Run tests:
   ```bash
   PYTHONPATH=src pytest tests/ -v
   ```

## Guidelines

- All audits must be deterministic and never crash on malformed HTML.
- Zero fake metrics: Citation Survival Proxy (CSP) is explicitly labeled as a diagnostic factor.
- Follow Conventional Commits format (`feat: ...`, `fix: ...`, `docs: ...`).
