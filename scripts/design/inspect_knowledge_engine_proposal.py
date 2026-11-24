"""Collect source integrity and render-layout evidence for the design artifact."""
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
from pypdf import PdfReader
from docx import Document

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / "docs/deliverables/knowledge-engine-v2-final-render"
SOURCE = ROOT / "docs/知识库引擎产品与技术完整方案-v2.0.md"


def main():
    paths = sorted(FOLDER.glob("page-*.png"), key=lambda p: int(p.stem.split("-")[-1]))
    for start in range(0, len(paths), 12):
        canvas = Image.new("RGB", (1125, 2120), "#d7dee8")
        draw = ImageDraw.Draw(canvas)
        for i, path in enumerate(paths[start:start+12]):
            with Image.open(path) as image:
                image.thumbnail((355, 485))
                x, y = (i % 3) * 375 + 10, (i // 3) * 530 + 30
                canvas.paste(image, (x, y))
                draw.text((x, y - 20), path.stem, fill="black")
        canvas.save(FOLDER / f"contact-{start//12+1}.jpg")
    source = SOURCE.read_text(encoding="utf-8")
    links = re.findall(r"\]\(([^)]+)\)", source)
    missing = [link for link in links if not link.startswith("https://") and not (SOURCE.parent / link).exists()]
    assert not missing, missing
    ET.parse(ROOT / "docs/assets/knowledge-engine-pipeline-v2.svg")
    pdf = next(FOLDER.glob("*.pdf"))
    reader = PdfReader(pdf)
    assert len(paths) == len(reader.pages)
    assert all(len(page.extract_text() or "") > 50 for page in reader.pages)
    doc = Document(ROOT / "docs/deliverables/知识库引擎产品与技术完整方案-v2.0.docx")
    titles = [p.text for p in doc.paragraphs if p.style.name == "Heading 1"]
    report = {
        "chapters": len(titles), "official_sources": len(re.findall(r"^- \[S", source, re.M)),
        "source_characters": len(source), "missing_local_links": missing,
        "pdf_pages": len(reader.pages), "rendered_pages": len(paths),
        "tables": len(doc.tables), "figures": len(doc.inline_shapes),
        "page_text_lengths": [len(p.extract_text() or "") for p in reader.pages],
        "visual_review": "pending",
    }
    (FOLDER / "artifact-check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "page_text_lengths"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
