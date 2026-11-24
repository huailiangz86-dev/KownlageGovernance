"""Inspect the shared knowledge architecture revision."""
from pathlib import Path
from inspect_enterprise_knowledge_product import main

ROOT = Path(__file__).resolve().parents[2]

if __name__ == "__main__":
    main(
        source=ROOT / "docs/可复用知识体系与统一知识引擎产品方案-v3.1.md",
        folder=ROOT / "docs/deliverables/reusable-knowledge-v31-final-render",
        docx=ROOT / "docs/deliverables/可复用知识体系与统一知识引擎产品方案-v3.1.docx",
        svg_names=("reusable-knowledge-engine-architecture-v31", "enterprise-knowledge-journey-v3", "enterprise-knowledge-safety-v3"),
    )
