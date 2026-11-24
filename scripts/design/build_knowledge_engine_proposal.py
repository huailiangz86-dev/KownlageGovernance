"""Build the v2 engine proposal and deterministic pipeline illustration."""

from pathlib import Path
from html import escape
import json
import re

from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs/assets"
SOURCE = ROOT / "docs/知识库引擎产品与技术完整方案-v2.0.md"
OUT = ROOT / "docs/deliverables/知识库引擎产品与技术完整方案-v2.0.docx"
FONT = "Microsoft YaHei"


def make_diagram():
    w, h = 1500, 1280
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
           '<title>知识库引擎构建与查询流水线</title>', '<rect width="100%" height="100%" fill="white"/>']
    text_bounds = []

    def text(x, y, value, size=25, bold=False, color="#23354c", max_width=None):
        f = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc", size)
        box = draw.textbbox((x, y), value, font=f, anchor="lt")
        assert box[2] <= w and box[3] <= h
        if max_width:
            assert box[2] - x <= max_width, value
        draw.text((x, y), value, fill=color, font=f, anchor="lt")
        svg.append(f'<text x="{x}" y="{y}" font-family="Microsoft YaHei, sans-serif" font-size="{size}" '
                   f'font-weight="{700 if bold else 400}" fill="{color}" dominant-baseline="text-before-edge">{escape(value)}</text>')
        text_bounds.append({"text": value, "bounds": box})

    def box(x, y, width, height, color):
        draw.rounded_rectangle((x, y, x + width, y + height), radius=10, fill=color)
        svg.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="10" fill="{color}"/>')

    def arrow(x, y1, y2):
        draw.line((x, y1, x, y2), fill="#8a9bb0", width=3)
        points = [(x, y2), (x - 6, y2 - 9), (x + 6, y2 - 9)]
        draw.polygon(points, fill="#8a9bb0")
        svg.append(f'<path d="M{x},{y1} L{x},{y2} M{x-6},{y2-9} L{x},{y2} L{x+6},{y2-9}" fill="none" stroke="#8a9bb0" stroke-width="3"/>')

    text(60, 30, "知识库引擎核心流水线", 40, True)
    text(60, 90, "目标设计  |  构建可追溯的索引，返回经过授权的证据", 25)
    text(80, 154, "构建与更新链路", 30, True, "#237b70")
    text(810, 154, "检索与问答链路", 30, True, "#3568c0")
    left = [
        ("来源与版本", "授权接入 · 摘要校验 · 不可变原件"),
        ("解析与标准内容块", "文档 / 表格 / 图像 / 音视频"),
        ("结构父子切片", "标题与条件 · token 上限 · 稳定证据"),
        ("Embedding 与关键词", "模型版本 · 维度 · 分词与精确字段"),
        ("索引投影与代次", "BM25 / dense / 视觉通道"),
        ("发布与更新同步", "事实事务 · Outbox · 水位与失效"),
    ]
    right = [
        ("问题与有效范围", "身份 · 知识库 · 目录 · 用途与条件"),
        ("混合候选召回", "关键词 + 向量 · 融合排名 · 去重"),
        ("权威版本与权限复核", "过滤未发布 / 撤回 / 来源受限"),
        ("重排与上下文", "Rerank · 父子展开 · token 预算"),
        ("证据服务与回答", "GEO 可取证据 · 问答可生成内容"),
        ("引用核对与使用反馈", "精确版本 · 回看依据 · 评估回归"),
    ]
    for x, rows, fill in [(60, left, "#eaf6f4"), (790, right, "#eaf1ff")]:
        for index, (title, desc) in enumerate(rows):
            y = 210 + index * 141
            box(x, y, 650, 110, fill)
            text(x + 20, y + 17, f"{index+1}  {title}", 29, True)
            text(x + 20, y + 66, desc, 24, max_width=610)
            if index < len(rows) - 1:
                arrow(x + 325, y + 115, y + 136)
    box(60, 1105, 1380, 99, "#253650")
    text(85, 1125, "共同合同：稳定证据 ID · 配置冻结 · 租户隔离 · 当前状态复核 · 可恢复作业", 25, True, "white", 1330)
    text(60, 1230, "切片与索引可重建；业务事实、原始依据和已发布引用保持可追溯。", 24)
    svg.append("</svg>")
    ASSETS.mkdir(exist_ok=True)
    img.save(ASSETS / "knowledge-engine-pipeline-v2.png")
    (ASSETS / "knowledge-engine-pipeline-v2.svg").write_text("\n".join(svg), encoding="utf-8")
    (ASSETS / "knowledge-engine-pipeline-v2.layout.json").write_text(
        json.dumps({"texts": text_bounds, "result": "within_canvas_and_columns"}, ensure_ascii=False, indent=2), encoding="utf-8")


def set_font(run, size=None, bold=None, color=None):
    run.font.name = FONT
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), FONT)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def hyperlink(paragraph, label, url):
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True))
    run = OxmlElement("w:r")
    prop = OxmlElement("w:rPr")
    fonts = OxmlElement("w:rFonts")
    fonts.set(qn("w:ascii"), FONT)
    fonts.set(qn("w:eastAsia"), FONT)
    prop.append(fonts)
    col = OxmlElement("w:color")
    col.set(qn("w:val"), "245A93")
    prop.append(col)
    run.append(prop)
    content = OxmlElement("w:t")
    content.text = label
    run.append(content)
    link.append(run)
    paragraph._p.append(link)


def inline(paragraph, value):
    tokens = re.split(r"(\[[^\]]+\]\([^)]*\)|\*\*[^*]+\*\*|`[^`]+`)", value)
    for token in tokens:
        if not token:
            continue
        match = re.fullmatch(r"\[([^\]]+)\]\(([^)]*)\)", token)
        if match:
            hyperlink(paragraph, match[1], match[2])
        elif token.startswith("**"):
            set_font(paragraph.add_run(token[2:-2]), bold=True)
        elif token.startswith("`"):
            set_font(paragraph.add_run(token[1:-1]), size=10)
        else:
            set_font(paragraph.add_run(token))


def table(document, rows):
    count = len(rows[0])
    tbl = document.add_table(rows=1, cols=count)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    fractions = {3: [.22, .42, .36], 4: [.18, .29, .26, .27]}.get(count, [1/count]*count)
    for col, frac in zip(tbl.columns, fractions):
        col.width = Inches(6.9 * frac)
    props = tbl._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        node = OxmlElement("w:" + side)
        for key, val in [("val", "single"), ("sz", "5"), ("color", "D9D9D9")]:
            node.set(qn("w:" + key), val)
        borders.append(node)
    props.append(borders)
    for i, values in enumerate(rows):
        row = tbl.rows[0] if i == 0 else tbl.add_row()
        trpr = row._tr.get_or_add_trPr()
        if i == 0:
            repeat = OxmlElement("w:tblHeader")
            trpr.append(repeat)
        # Each row is short enough to keep intact; the whole table may span pages.
        trpr.append(OxmlElement("w:cantSplit"))
        for j, (cell, value) in enumerate(zip(row.cells, values)):
            cell.width = Inches(6.9 * fractions[j])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tcpr = cell._tc.get_or_add_tcPr()
            shade = OxmlElement("w:shd")
            shade.set(qn("w:fill"), "253650" if i == 0 else ("F1F5F9" if i % 2 == 0 else "FFFFFF"))
            tcpr.append(shade)
            margins = OxmlElement("w:tcMar")
            for side in ("top", "bottom", "left", "right"):
                pad = OxmlElement("w:" + side)
                pad.set(qn("w:w"), "95")
                pad.set(qn("w:type"), "dxa")
                margins.append(pad)
            tcpr.append(margins)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.14
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.keep_with_next = i == 0
            inline(p, value)
            for run in p.runs:
                set_font(run, size=10, bold=(i == 0), color="FFFFFF" if i == 0 else "000000")
    document.add_paragraph().paragraph_format.space_after = Pt(1)


def main():
    make_diagram()
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = Inches(.72)
    section.left_margin = section.right_margin = Inches(.8)
    section.header_distance = section.footer_distance = Inches(.3)
    for name in ("Normal", "Title", "Subtitle", "Heading 1", "Heading 2", "Heading 3", "Caption"):
        style = doc.styles[name]
        style.font.name = FONT
        style.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), FONT)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.italic = False
    # The bundled Word template may carry a rule under Title in inherited styles.
    for border in list(doc.styles.element.xpath(".//w:pBdr")):
        border.getparent().remove(border)
    normal = doc.styles["Normal"]
    normal.font.size = Pt(11)
    normal.paragraph_format.line_spacing = 1.23
    normal.paragraph_format.space_after = Pt(7)
    normal.paragraph_format.widow_control = True
    for name, size in [("Heading 1", 17), ("Heading 2", 13), ("Heading 3", 12)]:
        style = doc.styles[name]
        style.font.size = Pt(size)
        style.font.bold = True
        style.paragraph_format.space_before = Pt(15)
        style.paragraph_format.space_after = Pt(8)
        style.paragraph_format.keep_with_next = True
    doc.styles["Title"].font.size = Pt(27)
    doc.styles["Title"].font.bold = True
    doc.styles["Subtitle"].font.size = Pt(12)
    doc.styles["Caption"].font.size = Pt(9)
    header = section.header.paragraphs[0]
    set_font(header.add_run("多模态知识库引擎产品与技术完整方案"), size=9, color="000000")
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_font(footer.add_run("目标设计  2026年11月23日    "), size=9)
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)

    source = SOURCE.read_text(encoding="utf-8")
    lines = source.splitlines()
    doc.add_paragraph("多模态知识库引擎\n产品与技术完整方案", "Title")
    doc.add_paragraph("版本 2.0    2026年11月23日", "Subtitle")
    doc.add_paragraph("方案覆盖市场引擎选型、切片与向量化、混合检索、重排问答、多模态处理、数据模型、GEO接入及生产验证。现有治理与发布能力继续复用，新增引擎目标单独验收。")
    doc.add_heading("推荐决策", 2)
    doc.add_paragraph("平台持有知识身份、证据、切片、索引配置、权限与正式状态，复用成熟解析器、模型和检索后端。首个验证候选采用 Elasticsearch 混合检索，优先复用阿里云资产，并以统一样本对照火山与 RAGFlow。")
    doc.add_heading("阅读导航", 2)
    for label, detail in [
        ("产品与选型", "第1至4章  产品范围、市场分类、比较及架构"),
        ("引擎核心", "第5至15章  内容模型、解析、切片、向量、索引、检索与问答"),
        ("工程落地", "第16至20章  数据模型、接口、更新、GEO与部署运行"),
        ("实施验证", "第21至26章  指标、差距、批次、风险和22项官方资料"),
    ]:
        p = doc.add_paragraph()
        set_font(p.add_run(label + "  "), bold=True)
        p.add_run(detail)
    doc.add_paragraph("说明  首套参数、资源算例与SLO均为验证输入，尚未进行供应商实测、真实视频试验或生产切流。")
    doc.add_page_break()

    idx = 1
    code = False
    while idx < len(lines):
        value = lines[idx].strip()
        if not value:
            idx += 1
            continue
        if value.startswith("```"):
            code = not code
            idx += 1
            continue
        if code:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.04
            p.paragraph_format.left_indent = Inches(.12)
            p.paragraph_format.keep_with_next = idx + 1 < len(lines) and not lines[idx+1].startswith("```")
            p.paragraph_format.keep_together = True
            set_font(p.add_run(lines[idx]), size=9)
            idx += 1
            continue
        if value.startswith("|"):
            rows = []
            while idx < len(lines) and lines[idx].strip().startswith("|"):
                row = [s.strip() for s in lines[idx].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", s) for s in row):
                    rows.append(row)
                idx += 1
            table(doc, rows)
            continue
        image = re.fullmatch(r"!\[([^]]*)\]\(([^)]*)\)", value)
        if image:
            p = doc.add_paragraph()
            p.paragraph_format.keep_with_next = True
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(str(SOURCE.parent / image[2]), width=Inches(6.9))
            idx += 1
            continue
        heading = re.match(r"^(#{2,4})\s+(.+)", value)
        if heading:
            title = re.sub(r"(?<=\d)\.(?=\d)", " ", heading[2])
            p = doc.add_heading(title, level=len(heading[1]) - 1)
        elif value.startswith("图") and re.match(r"图\d", value):
            inline(doc.add_paragraph(style="Caption"), value)
        elif value.startswith("- "):
            inline(doc.add_paragraph(style="List Bullet"), value[2:])
        else:
            p = doc.add_paragraph()
            inline(p, value)
            next_nonblank = next((line for line in lines[idx+1:] if line.strip()), "")
            if next_nonblank.startswith("```"):
                p.paragraph_format.keep_with_next = True
        idx += 1

    doc.core_properties.title = "多模态知识库引擎产品与技术完整方案"
    doc.core_properties.subject = "市场选型与知识库引擎完整设计"
    doc.core_properties.author = ""
    doc.core_properties.keywords = "RAG, chunking, embedding, hybrid search, multimodal, GEO"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(json.dumps({"docx": str(OUT), "paragraphs": len(doc.paragraphs), "tables": len(doc.tables),
                      "source_characters": len(source)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
