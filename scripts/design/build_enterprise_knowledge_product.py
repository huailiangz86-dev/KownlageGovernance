"""Author the business product proposal and its product journey illustrations."""
from pathlib import Path
from html import escape
import json
import re

from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from build_knowledge_engine_proposal import inline, table, set_font

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs/assets"
SOURCE = ROOT / "docs/企业知识库建设与运营产品方案-v3.0.md"
OUT = ROOT / "docs/deliverables/企业知识库建设与运营产品方案-v3.0.docx"


class Drawing:
    def __init__(self, width, height, title):
        self.width, self.height = width, height
        self.image = Image.new("RGB", (width, height), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
                    f'<title>{escape(title)}</title>', '<rect width="100%" height="100%" fill="white"/>']
        self.checked = []

    def text(self, x, y, value, size=23, color="#253650", bold=False, max_width=None):
        font = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc", size)
        bounds = self.draw.textbbox((x, y), value, font=font, anchor="lt")
        assert bounds[2] <= self.width and bounds[3] <= self.height, value
        if max_width:
            assert bounds[2] - x <= max_width, (value, bounds[2]-x, max_width)
        self.draw.text((x, y), value, fill=color, font=font, anchor="lt")
        self.svg.append(f'<text x="{x}" y="{y}" font-family="Microsoft YaHei, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}" dominant-baseline="text-before-edge">{escape(value)}</text>')
        self.checked.append({"text": value, "bounds": list(bounds)})

    def box(self, x, y, width, height, color):
        self.draw.rounded_rectangle((x, y, x+width, y+height), 8, fill=color)
        self.svg.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" fill="{color}"/>')

    def arrow(self, x1, y1, x2, y2, color="#8e9cb0"):
        self.draw.line((x1, y1, x2, y2), fill=color, width=3)
        if x1 == x2:
            tip = [(x2, y2), (x2-5, y2-8), (x2+5, y2-8)]
        else:
            tip = [(x2, y2), (x2-8, y2-5), (x2-8, y2+5)]
        self.draw.polygon(tip, fill=color)
        self.svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="3"/>')
        self.svg.append('<polygon points="' + " ".join(f"{x},{y}" for x,y in tip) + f'" fill="{color}"/>')

    def save(self, name):
        ASSETS.mkdir(exist_ok=True)
        self.svg.append("</svg>")
        self.image.save(ASSETS / f"{name}.png")
        (ASSETS / f"{name}.svg").write_text("\n".join(self.svg), encoding="utf-8")
        (ASSETS / f"{name}.layout.json").write_text(json.dumps({"text_checks": self.checked, "result": "within_assigned_bounds"}, ensure_ascii=False, indent=2), encoding="utf-8")


def diagrams():
    d = Drawing(1000, 1160, "企业知识库建设与使用流程")
    d.text(45, 27, "企业知识库建设与使用流程", 35, bold=True)
    d.text(45, 82, "产品目标  从企业资料到可靠使用，再回到持续维护", 22)
    steps = [
        ("建库与分工", "知识负责人和管理员确认用途、受众、责任与默认安全范围", "结果  有人负责且范围明确的知识空间"),
        ("目录主题与标签", "维护人建立初始资料目录、用户主题和业务标签字典", "结果  资料有归属，知识有阅读路径和查找方式"),
        ("资料接入与准备", "贡献者选范围接入，核对来源权限、重复、失败和覆盖", "结果  原件与版本清单，限制和待补内容明确保留"),
        ("清洗与问题决定", "整理人核对原文，处理差异、修订、并存与暂缓", "结果  有证据的候选知识和可追踪的问题处置"),
        ("审核发布", "审核人与发布人确认固定内容、条件、受众及外发用途", "结果  当前可用的正式知识，未通过范围继续待办"),
        ("员工搜索与问答", "员工按本人权限浏览、筛选、提问、回看依据和反馈", "结果  可解释的答案和知识缺口，原件另查权限"),
        ("应用开放与运营", "应用负责人试读后接入，维护人处理更新、复核和撤回", "结果  有期限的知识供给，变更可追踪并可停止"),
    ]
    for i, (title, actor, result) in enumerate(steps):
        y = 128 + i * 126
        d.box(45, y, 910, 110, "#eaf6f4" if i < 5 else "#eaf1ff")
        d.text(64, y+12, f"{i+1}  {title}", 27, bold=True)
        d.text(64, y+50, actor, 21, max_width=870)
        d.text(64, y+80, result, 21, color="#526278", max_width=870)
        if i < 6:
            d.arrow(500, y+113, 500, y+123)
    d.box(45, 1034, 910, 70, "#253650")
    d.text(64, 1053, "每一步都检查权限、内容状态与使用目的；反馈和变化回到维护。", 23, color="white", bold=True, max_width=870)
    d.text(45, 1122, "说明  为产品目标流程，案例和新增机制需分别实现与验收。", 20)
    d.save("enterprise-knowledge-journey-v3")

    d = Drawing(1000, 1010, "知识使用前的安全判断")
    d.text(42, 28, "一次知识使用怎样被允许", 35, bold=True)
    d.text(42, 83, "适用于员工、搜索问答、共享链接和应用调用", 23)
    checks = [
        ("身份有效", "人员仍在职且有成员资格，应用凭证未到期"),
        ("允许这个动作", "读知识、看原件、下载和外发分别授权"),
        ("允许这个范围", "知识库、目录、来源限制与指定受众均满足"),
        ("内容当前可用", "正式版本、适用条件、有效期与来源状态均通过"),
        ("用途和传播符合要求", "内部阅读许可不自动成为对外调用或导出许可"),
    ]
    for i, (title, body) in enumerate(checks):
        y = 140 + i * 126
        d.box(42, y, 720, 103, "#edf5fb")
        d.text(60, y+14, title, 27, bold=True)
        d.text(60, y+59, body, 21, max_width=680)
        if i < 4:
            d.arrow(400, y+107, 400, y+121)
        d.arrow(765, y+51, 797, y+51, "#b86b6b")
    d.box(800, 140, 155, 607, "#fbefef")
    for i, value in enumerate(["任一不满足", "拒绝该动作", "不返回", "受限标题", "或正文", "留必要记录"]):
        d.text(812, 236+i*57, value, 22, color="#9b4242", bold=(i < 2), max_width=132)
    d.arrow(400, 751, 400, 783)
    d.box(42, 786, 913, 104, "#eaf6f4")
    d.text(62, 803, "全部满足才提供本次允许的内容", 28, color="#237b70", bold=True)
    d.text(62, 848, "返回知识版本、条件和引用，记录必要使用信息。", 23)
    d.text(42, 932, "业务标签帮助查找；安全属性参与规则，但都不能单独授予权限。", 22, max_width=913)
    d.text(42, 970, "目标规则  权限变化后重新判断，不靠旧会话、缓存或链接继续放行。", 21, max_width=913)
    d.save("enterprise-knowledge-safety-v3")


def main(*, source=None, out=None, title="企业知识库建设与运营产品方案", version="3.0",
         cover_intro=None, cover_main=None, cover_nav=None, extra_diagrams=None,
         generate_diagrams=True, document_date="2026年11月23日"):
    source = source or SOURCE
    out = out or OUT
    if generate_diagrams:
        diagrams()
    if extra_diagrams:
        extra_diagrams()
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    sec.top_margin = sec.bottom_margin = Inches(.72)
    sec.left_margin = sec.right_margin = Inches(.8)
    sec.header_distance = sec.footer_distance = Inches(.3)
    for name in ("Normal", "Title", "Subtitle", "Heading 1", "Heading 2", "Caption", "List Bullet"):
        style = doc.styles[name]
        style.font.name = "Microsoft YaHei"
        style.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        style.font.color.rgb = RGBColor(0,0,0)
        style.font.italic = False
    for border in list(doc.styles.element.xpath(".//w:pBdr")):
        border.getparent().remove(border)
    doc.styles["Normal"].font.size = Pt(11)
    normal = doc.styles["Normal"].paragraph_format
    normal.line_spacing = 1.22
    normal.space_after = Pt(7)
    normal.widow_control = True
    for name, size in [("Heading 1", 17), ("Heading 2", 13)]:
        style = doc.styles[name]
        style.font.size = Pt(size)
        style.font.bold = True
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.space_before = Pt(15)
        style.paragraph_format.space_after = Pt(8)
    doc.styles["Title"].font.size = Pt(27)
    doc.styles["Title"].font.bold = True
    doc.styles["Subtitle"].font.size = Pt(12)
    doc.styles["Caption"].font.size = Pt(9)
    set_font(sec.header.paragraphs[0].add_run(title), size=9)
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_font(footer.add_run(f"产品目标设计  {document_date}    "), size=9)
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)
    doc.add_paragraph(title, "Title")
    doc.add_paragraph(f"版本 {version}    {document_date}", "Subtitle")
    doc.add_paragraph(cover_intro or "面向企业知识负责人、业务管理者、产品和实施人员。说明企业资料如何进入知识库，怎样清洗和组织，员工及应用怎样使用，以及权限、安全和日常维护如何贯穿全过程。")
    doc.add_heading("产品主线", 2)
    doc.add_paragraph(cover_main or "确定知识库与责任，接入并保管原件，核对内容问题，形成主题与知识，审核发布，按身份使用，按用途开放，再持续处理更新和反馈。每一步都有人员、动作、结果和限制。")
    doc.add_heading("阅读导航", 2)
    for label, detail in (cover_nav or [
        ("如何搭建", "第1至8章  产品层次、分工、建库、目录主题和接入"),
        ("如何整理", "第9至15章  清洗决定、知识形成、知识体系、标签与发布"),
        ("如何使用与保护", "第16至26章  搜索问答、媒体、权限、安全、开放与运营"),
        ("如何落地验收", "第27至31章  页面、完整案例、业务验收与实施范围"),
    ]):
        p = doc.add_paragraph()
        set_font(p.add_run(label + "  "), bold=True)
        p.add_run(detail)
    doc.add_paragraph("阅读说明  20份资料的案例是产品演示，新增产品机制属于目标设计；现有工程能力和待实现范围在正文分别说明。")
    doc.add_page_break()
    lines = source.read_text(encoding="utf-8").splitlines()
    idx = 1
    while idx < len(lines):
        value = lines[idx].strip()
        if not value:
            idx += 1
            continue
        if value.startswith("|"):
            rows = []
            while idx < len(lines) and lines[idx].strip().startswith("|"):
                row = [c.strip() for c in lines[idx].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c) for c in row):
                    rows.append(row)
                idx += 1
            table(doc, rows)
            continue
        match = re.fullmatch(r"!\[([^]]*)\]\(([^)]*)\)", value)
        if match:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.keep_with_next = True
            p.add_run().add_picture(str(source.parent / match[2]), width=Inches(6.3) if "architecture-v31" in match[2] else Inches(6.55))
        elif value.startswith("### "):
            doc.add_heading(re.sub(r"(?<=\d)\.(?=\d)", " ", value[4:]), 2)
        elif value.startswith("## "):
            doc.add_heading(value[3:], 1)
        elif re.match(r"图\d", value):
            inline(doc.add_paragraph(style="Caption"), value)
        elif value.startswith("- "):
            inline(doc.add_paragraph(style="List Bullet"), value[2:])
        else:
            inline(doc.add_paragraph(), value)
        idx += 1
    reference_start = next(i for i,p in enumerate(doc.paragraphs)
                           if p.style.name == "Heading 1" and p.text.startswith("31 "))
    for p in doc.paragraphs[reference_start:-1]:
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.keep_together = True
    doc.core_properties.title = title
    doc.core_properties.subject = "可复用知识体系 统一知识服务 多Agent与业务应用"
    doc.core_properties.author = ""
    out.parent.mkdir(exist_ok=True)
    doc.save(out)
    print(json.dumps({"source_characters": len(source.read_text(encoding="utf-8")),
                      "chapters": len([p for p in doc.paragraphs if p.style.name == "Heading 1"]),
                      "tables": len(doc.tables), "figures": len(doc.inline_shapes), "docx": str(out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
