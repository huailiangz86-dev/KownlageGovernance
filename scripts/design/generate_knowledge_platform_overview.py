"""Generate the product target architecture as editable SVG and preview PNG."""

from html import escape
from pathlib import Path
import json

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "assets"
WIDTH, HEIGHT = 1900, 1390
REGULAR = "C:/Windows/Fonts/msyh.ttc"
BOLD = "C:/Windows/Fonts/msyhbd.ttc"
LAYERS = [
    ("L6", "上层应用", "#eaf1ff", "#3568c0", [
        "知识门户 · 阅读与搜索", "知识问答 · 研究与写作", "GEO · 企业 Agent · 业务系统"]),
    ("L5", "产品与知识服务", "#eaf6f4", "#237b70", [
        "知识库与目录 · 内容协作", "治理规则 · 审核与发布", "搜索 · 问答 · 开放 API"]),
    ("L4", "知识库核心引擎", "#f0edfc", "#7560af", [
        "知识表示 · 证据与切片", "索引构建 · 混合召回", "版本复核 · 重排与上下文"]),
    ("L3", "多模态解析与理解", "#fff3e7", "#aa6826", [
        "文档结构 · OCR · 表格", "语音转写 · 说话人", "视频镜头 · 帧图 · 时间轴"]),
    ("L2", "资料接入与同步", "#edf5fb", "#337b9e", [
        "上传 · 连接器 · 范围授权", "来源身份 · 文件版本 · 摘要", "增量同步 · 变更与失效"]),
    ("", "资料来源", "#f2f4f7", "#5f6b7b", [
        "文件 · 文件夹 · 云存储", "文档 · 图片 · 音频 · 视频", "内容系统 · 业务数据 · 人工编写"]),
]


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "#ffffff")
    draw = ImageDraw.Draw(canvas)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
           f'height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" '
           'aria-labelledby="title description">',
           '<title id="title">多模态知识库产品完整结构图</title>',
           '<desc id="description">目标设计。从资料接入、多模态解析、知识引擎和产品服务，'
           '到知识门户、问答与GEO应用。底层资源支撑各层，权限与质量贯穿全过程。</desc>',
           '<rect width="100%" height="100%" fill="white"/>']
    checks = []

    def text(x, y, value, size=24, fill="#243247", bold=False, max_width=None):
        font = ImageFont.truetype(BOLD if bold else REGULAR, size)
        bounds = draw.textbbox((x, y), value, font=font, anchor="lt")
        if max_width is not None:
            assert bounds[2] - x <= max_width, (value, bounds[2] - x, max_width)
        assert 0 <= bounds[0] and bounds[2] <= WIDTH and bounds[3] <= HEIGHT, value
        draw.text((x, y), value, font=font, fill=fill, anchor="lt")
        svg.append(f'<text x="{x}" y="{y}" font-family="Microsoft YaHei, sans-serif" '
                   f'font-size="{size}" font-weight="{700 if bold else 400}" '
                   f'fill="{fill}" dominant-baseline="text-before-edge">{escape(value)}</text>')
        checks.append({"text": value, "bounds": list(bounds)})

    def rectangle(x, y, w, h, fill, stroke=None, radius=12):
        draw.rounded_rectangle((x, y, x + w, y + h), radius, fill, stroke, 1)
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
                   f'fill="{fill}" stroke="{stroke or "none"}"/>')

    def line(points, fill="#9ba8ba", width=3):
        draw.line(points, fill=fill, width=width)
        serialized = " ".join(f"{x},{y}" for x, y in points)
        svg.append(f'<polyline points="{serialized}" fill="none" stroke="{fill}" '
                   f'stroke-width="{width}"/>')

    def up_arrow(x, lower_y, upper_y):
        line([(x, lower_y), (x, upper_y)])
        triangle = [(x, upper_y), (x - 6, upper_y + 9), (x + 6, upper_y + 9)]
        draw.polygon(triangle, fill="#9ba8ba")
        svg.append('<polygon points="' + " ".join(f"{a},{b}" for a, b in triangle)
                   + '" fill="#9ba8ba"/>')

    text(80, 42, "多模态知识库 · 完整产品结构", 44, bold=True)
    text(80, 106, "目标设计  |  资料进入 → 知识形成 → 授权使用 → 持续更新", 25, "#58677a")
    main_x, main_w, first_y, gap, row_h = 80, 1410, 172, 150, 120
    for i, (number, title, fill, accent, columns) in enumerate(LAYERS):
        y = first_y + i * gap
        rectangle(main_x, y, main_w, row_h, fill)
        rectangle(main_x, y + 16, 5, row_h - 32, accent, radius=2)
        label = f"{number}  {title}" if number else title
        text(main_x + 25, y + 17, label, 29, accent, bold=True)
        for j, content in enumerate(columns):
            text(main_x + 25 + j * 460, y + 73, content, 23, max_width=445)
        if i:
            up_arrow(main_x + main_w // 2, y - 5, y - gap + row_h + 5)

    side_x, side_y, side_w, side_h = 1530, 172, 290, 870
    rectangle(side_x, side_y, side_w, side_h, "#f5f7fa", "#dbe2ea")
    text(side_x + 24, side_y + 22, "贯穿全部层次", 29, bold=True, max_width=side_w - 48)
    side_groups = [
        ("身份与权限", ["团队 / 知识库 / 目录", "人员职责 / 调用方 / 用途"]),
        ("版本与有效性", ["来源 / 知识 / 发布版本", "变更 / 替代 / 撤回"]),
        ("执行与追溯", ["任务恢复 / 幂等 / 审计", "证据 / 配置 / 处理回执"]),
        ("质量与运行", ["评估集 / 反馈 / 回归", "覆盖 / 延迟 / 失败 / 告警"]),
    ]
    for index, (title, details) in enumerate(side_groups):
        y = side_y + 112 + index * 173
        text(side_x + 24, y, title, 25, bold=True)
        for j, value in enumerate(details):
            text(side_x + 24, y + 45 + j * 35, value, 19, "#58677a", max_width=side_w - 48)
    text(side_x + 24, side_y + 808, "治理承担质量控制", 23, "#237b70", bold=True)

    base_y = 1102
    rectangle(80, base_y, 1740, 164, "#253650")
    text(105, base_y + 18, "L1  基础资源与执行底座", 29, "#ffffff", bold=True)
    foundations = [
        ("MySQL · 私有对象存储", "事实 / 关系 / 原件 / 产物"),
        ("搜索与向量后端", "关键词 / 语义 / 多模态"),
        ("任务队列 · Worker", "调度 / 检查点 / 恢复"),
        ("模型与处理引擎适配", "阿里云 / 火山 / RAGFlow"),
    ]
    for index, (title, details) in enumerate(foundations):
        x = 105 + index * 430
        text(x, base_y + 75, title, 25, "#ffffff", bold=True, max_width=415)
        text(x, base_y + 118, details, 21, "#d2dcec", max_width=415)

    text(80, 1293, "实线箭头：内容走向应用的主要路径；基础资源支撑各层，横向控制贯穿全过程。", 23, "#58677a")
    text(80, 1333, "逻辑分层不等于微服务拆分；本图为产品目标结构，具体实现与验收状态见配套说明。", 23, "#58677a")
    svg.append("</svg>")
    name = "knowledge-platform-overview-v1"
    (OUTPUT / f"{name}.svg").write_text("\n".join(svg), encoding="utf-8")
    canvas.save(OUTPUT / f"{name}.png")
    report = {"width": WIDTH, "height": HEIGHT, "text_checks": checks,
              "result": "all_text_within_canvas_and_assigned_column_widths"}
    (OUTPUT / f"{name}.layout.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"outputs": [str(OUTPUT / f"{name}.{ext}") for ext in ("svg", "png")],
                      "validated_texts": len(checks)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
