"""Extend the accepted product proposal with a shared knowledge architecture."""
from pathlib import Path
from build_enterprise_knowledge_product import Drawing, main as build_document

ROOT = Path(__file__).resolve().parents[2]


def architecture():
    d = Drawing(1000, 1315, "可复用知识体系与统一知识引擎整体架构")
    d.text(42, 24, "可复用知识体系与统一知识引擎", 35, bold=True)
    d.text(42, 78, "共用知识资产，通过统一服务支持多种Agent与业务应用", 22)

    d.box(42, 123, 916, 160, "#eaf1ff")
    d.text(60, 137, "上层应用  多种Agent与业务系统", 27, bold=True)
    applications = ["员工服务 Agent", "客户支持 Agent", "研究分析 Agent",
                    "流程协作 Agent", "GEO等内容应用", "企业业务系统"]
    for i, label in enumerate(applications):
        x, y = 60 + (i%3)*298, 181 + (i//3)*47
        d.box(x, y, 280, 37, "#ffffff")
        d.text(x+11, y+6, label, 21, max_width=258)

    d.box(42, 318, 916, 140, "#eaf6f4")
    d.text(60, 332, "统一知识服务出口", 29, bold=True, color="#237b70")
    capabilities = ["按对象发现与读取", "按关系与条件展开", "取证据与任务上下文",
                    "可选有依据问答", "版本复验与变更同步", "按应用身份与用途服务"]
    for i,label in enumerate(capabilities):
        d.text(60+(i%3)*298, 382+(i//3)*34, label, 21, max_width=280)

    d.box(42, 493, 916, 290, "#f0edfc")
    d.text(60, 508, "可复用知识体系", 32, color="#6c53a0", bold=True)
    d.text(60, 554, "维护一次，按各应用的授权和任务提供不同知识视图", 22)
    shared = [
        ("领域与概念", "主题定义、统一术语与别名"),
        ("知识对象", "稳定身份、类型和标准属性"),
        ("关系与依赖", "前置、组成、例外与替代"),
        ("条件与规则", "适用对象、时间、情形"),
        ("证据与版本", "原文依据、批准与有效性"),
        ("责任与使用边界", "维护、审核、受众与用途"),
    ]
    for i,(title,body) in enumerate(shared):
        x,y = 60+(i%3)*298, 593+(i//3)*85
        d.box(x,y,280,73,"#ffffff")
        d.text(x+10,y+9,title,25,bold=True,max_width=260)
        d.text(x+10,y+45,body,18,max_width=260)

    d.box(42,818,916,125,"#fff3e7")
    d.text(60,832,"资料接入与知识加工",28,bold=True,color="#9d6328")
    d.text(60,878,"连接资料 → 解析理解 → 清洗核对 → 建立对象关系 → 审核发布",21,max_width=880)
    d.text(60,910,"新内容进入同一体系，原件、候选、正式知识分开管理。",21,max_width=880)

    d.box(42,978,916,95,"#f1f4f7")
    d.text(60,991,"企业资料与数据来源",27,bold=True)
    d.text(60,1035,"文档 · 表格 · 图片 · 音频 · 视频 · 内容系统 · 业务数据",22,max_width=880)

    d.box(42,1108,916,93,"#edf5fb")
    d.text(60,1121,"引擎与运行底座  支撑各层",25,bold=True)
    d.text(60,1164,"解析 · 分段 · 向量 · 检索 · 模型 · 存储 · 作业调度",22,max_width=880)

    for low, high in [(318,283),(493,458),(818,783),(978,943)]:
        x, bottom, top = 500, low-4, high+4
        d.draw.line((x,bottom,x,top),fill="#8798af",width=3)
        points=[(x,top),(x-5,top+8),(x+5,top+8)]
        d.draw.polygon(points,fill="#8798af")
        d.svg.append(f'<path d="M{x},{bottom} L{x},{top} M{x-5},{top+8} L{x},{top} L{x+5},{top+8}" fill="none" stroke="#8798af" stroke-width="3"/>')
    d.box(42,1230,916,52,"#253650")
    d.text(60,1245,"贯穿各层  权限安全 · 质量发布 · 版本责任 · 审计运营",22,color="white",bold=True,max_width=880)
    d.text(42,1291,"目标架构  共用知识不等于全部共享，每个应用仍按身份与用途使用。",19,max_width=916)
    d.save("reusable-knowledge-engine-architecture-v31")


if __name__ == "__main__":
    build_document(
        source=ROOT / "docs/可复用知识体系与统一知识引擎产品方案-v3.1.md",
        out=ROOT / "docs/deliverables/可复用知识体系与统一知识引擎产品方案-v3.1.docx",
        title="可复用知识体系与统一知识引擎产品方案", version="3.1",
        cover_intro="以共用知识体系为核心，把企业资料加工为具有概念、对象、关系、条件、证据和版本的知识，通过统一服务出口供多种Agent与业务应用使用。GEO仅是其中一种应用。",
        cover_main="资料进入平台后经过清洗核对、对象与关系确认、审核发布，形成可维护的知识资产。员工助手、流程Agent、研究Agent等按各自任务和授权，复用同一知识及版本。",
        cover_nav=[
            ("整体架构", "第2章  共用知识体系、统一出口和多Agent应用层"),
            ("建设与加工", "第3至12章  分工、建库、接入、清洗和知识形成"),
            ("知识体系", "第13至15章  概念对象、关系条件、复用、标签和发布"),
            ("服务与运营", "第16至31章  使用、安全、统一服务、多应用案例与验收"),
        ], extra_diagrams=architecture,
    )
