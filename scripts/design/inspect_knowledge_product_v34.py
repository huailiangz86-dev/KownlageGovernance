"""Inspect the formal lifecycle revision and its diagram assets."""
from pathlib import Path
from datetime import date, timedelta
import hashlib
import json
from PIL import Image
from inspect_enterprise_knowledge_product import main

ROOT = Path(__file__).resolve().parents[2]


if __name__ == "__main__":
    folder = ROOT / "docs/deliverables/knowledge-product-v34-final-render"
    source = ROOT / "docs/可复用知识体系与统一知识引擎产品方案-v3.4.md"
    main(source=source, folder=folder,
         docx=ROOT / "docs/deliverables/可复用知识体系与统一知识引擎产品方案-v3.4.docx",
         svg_names=())
    older = json.loads((ROOT / "docs/assets/knowledge-product-v33-image-prompts.json").read_text(encoding="utf-8"))
    newer = json.loads((ROOT / "docs/assets/knowledge-product-v34-image-prompt.json").read_text(encoding="utf-8"))
    assets = []
    for asset in [*older["assets"], newer]:
        p = ROOT / "docs/assets" / asset["file"]
        assert asset["prompt"]
        with Image.open(p) as image:
            image.verify()
        with Image.open(p) as image:
            assert image.width >= 1400 and image.height >= 900
            assets.append({"file": asset["file"], "size": list(image.size),
                           "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    text = source.read_text(encoding="utf-8")
    assert text.count("### 25.") == 16
    assert date(2027, 3, 1) + timedelta(days=90) == date(2027, 5, 30)
    for citation in ("P06", "P07", "P08"):
        assert f"[{citation} " in text and f"[{citation}]" in text
    path = folder / "artifact-check.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["chapters"] == 31 and report["tables"] == 14 and report["figures"] == 4
    report["image_generation"] = {"mode": "built-in image_gen", "assets": assets}
    report["lifecycle_sections"] = 16
    report["example_90_day_interval"] = "passed"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
