"""Inspect the business domain structure proposal."""
from pathlib import Path
from inspect_enterprise_knowledge_product import main

ROOT=Path(__file__).resolve().parents[2]

if __name__=="__main__":
    main(
        source=ROOT/"docs/可复用知识体系与统一知识引擎产品方案-v3.2.md",
        folder=ROOT/"docs/deliverables/domain-knowledge-v32-render",
        docx=ROOT/"docs/deliverables/可复用知识体系与统一知识引擎产品方案-v3.2.docx",
        svg_names=("business-knowledge-structures-v32","reusable-knowledge-engine-architecture-v31",
                   "enterprise-knowledge-journey-v3","enterprise-knowledge-safety-v3"),
    )
