# First Contribution Guide: SAGE Audit

Welcome to SAGE Audit! We welcome contributions to our 3-pillar diagnostic auditing engine (Technical SEO, Entity AEO, Generative GEO).

---

## ⚡ 5-Step Contributor Journey

1. **Clone & Setup**:
   ```bash
   git clone https://github.com/tmolavi/sage-audit.git
   cd sage-audit
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev,mcp]"
   ```

2. **Run Tests & Demo**:
   ```bash
   PYTHONPATH=src pytest tests/ -v
   PYTHONPATH=src python examples/public_demo/run_demo.py
   ```

3. **Open Issue / Discussion**: Check [GitHub Discussions](https://github.com/tmolavi/sage-audit/discussions).
4. **Implement Changes**: Ensure all checks are tagged with the Epistemic Evidence Taxonomy (E0–E5).
5. **Submit Pull Request**: Open a PR adhering to our review checklist.
