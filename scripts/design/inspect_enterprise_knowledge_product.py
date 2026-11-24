"""Validate business proposal sources and prepare page-by-page visual review."""
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
from pypdf import PdfReader
from docx import Document

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / "docs/deliverables/enterprise-knowledge-v3-release-render"
SOURCE = ROOT / "docs/企业知识库建设与运营产品方案-v3.0.md"


def main(*, source=None, folder=None, docx=None, svg_names=None):
    source = source or SOURCE
    folder = folder or FOLDER
    docx = docx or ROOT / "docs/deliverables/企业知识库建设与运营产品方案-v3.0.docx"
    if svg_names is None:
        svg_names = ("enterprise-knowledge-journey-v3", "enterprise-knowledge-safety-v3")
    paths = sorted(folder.glob("page-*.png"), key=lambda p: int(p.stem.split("-")[-1]))
    for start in range(0, len(paths), 12):
        canvas = Image.new("RGB", (1125, 2120), "#d7dee8")
        draw = ImageDraw.Draw(canvas)
        for i, path in enumerate(paths[start:start+12]):
            with Image.open(path) as image:
                image.thumbnail((355,485))
                x,y = (i%3)*375+10, (i//3)*530+30
                canvas.paste(image,(x,y))
                draw.text((x,y-20),path.stem,fill="black")
        canvas.save(folder / f"contact-{start//12+1}.jpg")
    source_path = source
    source = source_path.read_text(encoding="utf-8")
    links = re.findall(r"\]\(([^)]+)\)",source)
    missing = [x for x in links if not x.startswith("https://") and not (source_path.parent/x).exists()]
    assert not missing, missing
    for name in svg_names:
        ET.parse(ROOT / f"docs/assets/{name}.svg")
    pdf = next(folder.glob("*.pdf"))
    reader = PdfReader(pdf)
    assert len(paths)==len(reader.pages)
    lengths = [len(p.extract_text() or "") for p in reader.pages]
    assert all(n>40 for n in lengths),lengths
    doc=Document(docx)
    report={"chapters":len([p for p in doc.paragraphs if p.style.name=="Heading 1"]),
            "source_characters":len(source),"tables":len(doc.tables),"figures":len(doc.inline_shapes),
            "pages":len(reader.pages),"rendered_pages":len(paths),"missing_local_links":missing,
            "page_text_lengths":lengths,"visual_review":"pending"}
    (folder / "artifact-check.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="page_text_lengths"},ensure_ascii=False))


if __name__=="__main__":
    main()
