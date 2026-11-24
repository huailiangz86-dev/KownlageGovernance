"""Check the model-generated product diagrams and proposal render."""
from pathlib import Path
import hashlib
import json
from PIL import Image
from inspect_enterprise_knowledge_product import main

ROOT = Path(__file__).resolve().parents[2]


if __name__ == "__main__":
    folder = ROOT / "docs/deliverables/knowledge-product-v33-final-render"
    main(
        source=ROOT / "docs/可复用知识体系与统一知识引擎产品方案-v3.3.md",
        folder=folder,
        docx=ROOT / "docs/deliverables/可复用知识体系与统一知识引擎产品方案-v3.3.docx",
        svg_names=(),
    )
    manifest = json.loads((ROOT / "docs/assets/knowledge-product-v33-image-prompts.json").read_text(encoding="utf-8"))
    assert manifest["mode"] == "built-in image_gen"
    assert manifest["mcp_used_for_graphics"] is False
    assert len(manifest["assets"]) == 3
    assets = []
    for asset in manifest["assets"]:
        p = ROOT / "docs/assets" / asset["file"]
        assert asset["prompt"]
        with Image.open(p) as image:
            image.verify()
        with Image.open(p) as image:
            assert image.width >= 1400 and image.height >= 900
            assets.append({"file": asset["file"], "size": list(image.size),
                           "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    path = folder / "artifact-check.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["chapters"] == 31 and report["tables"] == 12 and report["figures"] == 3
    report["image_generation"] = {"mode": manifest["mode"], "assets": assets}
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
