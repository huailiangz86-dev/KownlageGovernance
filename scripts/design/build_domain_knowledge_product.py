"""Build the multi-domain knowledge structure product revision."""
from pathlib import Path
from build_enterprise_knowledge_product import Drawing, main as build_document
from build_reusable_knowledge_product import architecture

ROOT = Path(__file__).resolve().parents[2]


def structures():
    architecture()
    d=Drawing(1000,1150,"统一底座与多领域业务知识结构")
    d.text(42,24,"统一底座  多领域结构  多种应用视图",33,bold=True)
    d.text(42,76,"按业务含义建模，按责任与安全管理，按任务组合使用。",22)
    d.box(42,115,916,155,"#eaf1ff")
    d.text(60,129,"上层应用视图",28,bold=True)
    for i,(title,detail) in enumerate([
        ("员工助手","办事说明与适用条件"),
        ("流程 Agent","前置条件与办理步骤"),
        ("研究等 Agent","关联知识与证据包"),
    ]):
        x=60+i*298
        d.box(x,175,280,75,"#ffffff")
        d.text(x+11,184,title,25,bold=True,max_width=258)
        d.text(x+11,222,detail,19,max_width=258)
    d.box(42,305,916,105,"#eaf6f4")
    d.text(60,319,"统一知识服务出口",28,color="#237b70",bold=True)
    d.text(60,365,"选择领域与对象 → 核对含义和条件 → 按身份与用途返回知识",22,max_width=880)

    d.box(42,445,916,290,"#f0edfc")
    d.text(60,460,"业务领域可以维护不同结构",28,color="#6c53a0",bold=True)
    domains=[
        ("示意员工服务域",["人员、办理事项、制度", "适用、前置与负责关系", "本领域规则与维护责任"]),
        ("示意客户支持域",["客户、请求、解决方案", "关联、例外与处理关系", "本领域规则与维护责任"]),
        ("其他业务领域",["按自身对象与规则建模", "共享定义须共同确认", "采用模板后仍需验证"]),
    ]
    for i,(title,details) in enumerate(domains):
        x=60+i*298
        d.box(x,510,280,165,"#ffffff")
        d.text(x+11,524,title,24,bold=True,max_width=258)
        for j,line in enumerate(details):
            d.text(x+11,570+j*33,line,19,max_width=258)
    d.text(60,697,"跨域含义显式映射；相同事实不按应用重复维护。",22,max_width=880)

    d.box(42,770,916,145,"#edf5fb")
    d.text(60,785,"平台共用规范与企业共享定义",28,bold=True)
    d.text(60,833,"统一知识身份、来源证据、版本状态、授权与服务合同",22,max_width=880)
    d.text(60,871,"只共享经确认的业务定义，各领域保留含义与变更责任。",22,max_width=880)

    d.box(42,950,916,110,"#f1f4f7")
    d.text(60,966,"目录与标签分别服务管理和查找",27,bold=True)
    d.text(60,1011,"目录管归档与接入范围；标签做多面筛选；两者映射到知识。",21,max_width=880)

    for low,high in [(305,270),(445,410),(770,735)]:
        x,bottom,top=500,low-4,high+4
        d.draw.line((x,bottom,x,top),fill="#8798af",width=3)
        d.draw.polygon([(x,top),(x-5,top+8),(x+5,top+8)],fill="#8798af")
        d.svg.append(f'<path d="M{x},{bottom} L{x},{top} M{x-5},{top+8} L{x},{top} L{x+5},{top+8}" fill="none" stroke="#8798af" stroke-width="3"/>')
    d.text(42,1091,"领域模型、知识库空间和目录不是一一对应，复用不扩大内容权限。",21,max_width=916)
    d.text(42,1126,"示意结构须由业务问题、实际资料和领域责任人共同验证。",19,max_width=916)
    d.save("business-knowledge-structures-v32")


if __name__=="__main__":
    build_document(
        source=ROOT/"docs/可复用知识体系与统一知识引擎产品方案-v3.2.md",
        out=ROOT/"docs/deliverables/可复用知识体系与统一知识引擎产品方案-v3.2.docx",
        title="可复用知识体系与统一知识引擎产品方案", version="3.2",
        cover_intro="平台统一知识身份、证据、版本、权限和服务合同，各业务领域维护自己的概念、对象、关系与规则，上层Agent按任务组合知识。目录、标签、安全空间和业务结构分别设计。",
        cover_main="先以真实业务问题和代表性资料确认领域边界，再决定共用、扩展或独立的知识结构；用明确目录归档、受控标签查找和授权应用视图，持续维护同一事实与依据。",
        cover_nav=[
            ("整体架构","第2章  共用知识底座、统一出口与多Agent应用"),
            ("建库与资料","第5至12章  业务结构和安全空间、目录、接入与清洗"),
            ("领域建模","第13至14章  多领域结构、业务验证、目录标签和责任"),
            ("服务与运营","第15至31章  发布、使用、安全、开放、案例与验收"),
        ],extra_diagrams=structures,
    )
