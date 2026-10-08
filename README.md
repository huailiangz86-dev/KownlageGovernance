# 资料治理 Agent

当前状态：PRD 与静态原型完成；S0 已形成迁移盘点和预检工具；S1 第一批组织、项目与权限后端代码已落地。真实客户数据和运营配置尚未迁移。

- [PRD v0.2.1](docs/资料治理Agent_PRD-v0.2.md)
- [技术架构 v0.1](docs/knowledge-governance-architecture-v0.1.md)
- [Sprint 计划](docs/sprints/实施路线与Sprint计划-v0.1.md)
- [S1 交付、运行说明与剩余范围](docs/sprints/S1-组织与项目骨架-v0.1.md)
- [KnowledgeHub 迁移盘点](docs/migration/旧系统迁移盘点-v0.1.md)
- [AIOps 迁移盘点](docs/migration/AIOps-迁移盘点-v0.1.md)
- [工作台原型 v0.6](prototypes/knowledge-agent-workbench-v0.6.html)

## 开发与验证

Python 3.12+，从仓库根目录运行（PowerShell）：

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
~~~

当前共 25 项测试。CI 配置位于 .github/workflows/backend.yml。

后端位于 src/knowledge_governance；当前提供领域服务和 Alembic schema，HTTP API、登录及前端联调尚未实现。数据库迁移须显式设置 DATABASE_URL，详见 S1 运行说明。SQLite 用于本地测试；MySQL 已验证 SQL 离线生成，尚未做真实实例联调。

S0 的只读元数据预检工具位于 scripts/migration，不连接生产库，也不导入数据。导出文件和报告应放在已忽略的 migration-output 目录，具体格式见迁移盘点文档。
