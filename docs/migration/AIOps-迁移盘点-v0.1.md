# AIOps（GeoOps）迁移盘点 v0.1

日期：2026-10-08。源仓库：[lidongjunsean-star/AIOps](https://github.com/lidongjunsean-star/AIOps)，main 基线提交 1a175cbcfbbbcde226cf665c29b7334f7d7d7d0e。状态：代码与文档静态盘点；未访问生产数据库、Redis、密钥或客户资料。

目标依据：[PRD v0.2.1](../资料治理Agent_PRD-v0.2.md)、[技术架构](../knowledge-governance-architecture-v0.1.md)、[Sprint 计划](../sprints/实施路线与Sprint计划-v0.1.md)。

## 两种 ops 的边界

AIOps 是旧 GeoOps **平台控制面**：平台人员管理租户、预置角色、权限资源、模板与配置发布。新 PRD 的 **组织内 ops 项目** 是每个组织唯一的系统托管项目，保存该组织的运行健康、任务、成本与告警。AIOps 的平台员工、平台角色和全局配置不属于任何客户 ops 项目；旧 ops_admin 也不能变成客户项目的默认读取者。

## 功能迁移矩阵

| AIOps 源 | 已有能力 | 新平台处理 | Sprint |
|---|---|---|---|
| src/models/tenant.py、src/services/tenant_service.py、ops-ui/src/views/tenants | 租户生命周期、组织关联、初始化/重同步、运营界面 | 租户映射到 Organization；创建组织时同事务预置唯一 ops 项目。保留旧 tenant/code/KH organization_id 映射；初始化改为目标服务的领域流程，不直写旧 KH 业务表 | S0 映射，S1 实现 |
| src/models/platform_user.py、platform_role.py、src/api/auth.py、ops-ui 登录/用户页 | 平台员工与角色 | 平台主体、角色和管理页面可作起点；重新按目标 capability 与限时支持授权建模，平台角色不授客户正文权。旧密码哈希/令牌不直接导入 | S1 |
| src/models/permission_resource.py、preset_role.py、preset_role_permission.py、src/services/adapters/knowledgehub_adapter.py | 权限资源树、预置角色、按子系统过滤的权限载荷 | 复用权限目录和适配器分层经验；旧角色/权限码建立映射，不把 knowledgehub、geogrowth 或 ops_admin 权限自动合并。目标 effective-access 是唯一前端与 API 判定来源 | S1 |
| src/models/preset_config.py、business_module.py、geo_dimension.py、geo_rule_template.py、ops-ui 预置数据页 | 平台模板与模块配置 | 只迁入治理产品需要的模板元数据；GEO 行业、问题生成维度/规则留在 GeoGrowth 兼容边界，不能混作治理规则 | S1，GEO 内容后续 |
| src/models/config_publish.py、src/services/publish_service.py、ops-ui 发布页 | 配置快照、差异、发布事件、回滚操作 | 复用版本/差异展示思路；配置发布与业务知识发布分开建模。目标事务内写快照+Outbox，Worker 投递且有回执/重试；不照搬 DB commit 后直接写 Redis 的链路 | S1 配置、S4 知识发布 |
| src/models/init_log.py、ops-ui 初始化日志/仪表盘 | 初始化和运行可观测性 | 历史日志保留只读引用；新运行事件附组织/项目和操作主体；ops 项目只收该组织脱敏健康摘要 | S1–S2 |
| src/services/adapters/geogrowth_adapter.py、GeoGrowth 分发 | 外部系统配置适配 | 保留为旧消费者兼容参考；首版仅实现确定的一个真实 Agent/目的地，不提前搬入 GEO 全域 | S5 |

## 不可直接继承的旧行为

1. 旧 Tenant 模型保存长期 API Key；新 Agent 运行采用安装、项目绑定、委派交集和短期令牌。旧 Key 只作切流盘点，切流后轮换/停用。
2. 旧 tenant_service 通过共享数据库直接写 KnowledgeHub organizations、roles、role_permissions；新边界通过受控 API 或目标领域服务衔接，不共享业务表。尤其不能以旧 KnowledgeHub organization_id 直接替换目标 Organization ID。
3. 旧平台权限用 require_roles 校验平台角色，前端路由凭本地 token 显示；新运营前端须读取 effective-access，客户正文还需限时支持授权，所有 API 独立校验。
4. 旧 publish_service 在数据库提交后才写 Redis Stream；两步之间失败会遗失投递。目标配置与知识发布都使用事务 Outbox 和可幂等投递。配置版本不等于知识发布快照。
5. AIOps 系统模板、公共租户值 000000 和旧 ops_admin 仅是映射输入。客户资料不能回退到公共租户，也不能默认进入组织 ops 项目。

## 数据与代码迁移次序

1. S0 导出 AIOps tenants、platform_users/roles、permission_resources、preset_roles/bindings、preset_configs、config_versions/events 和 init_logs 的**元数据清单**；单列旧 tenant_id、code、KH organization_id、目标 Organization/Project ID。密钥、密码哈希、令牌和客户正文不进入清单。
2. 对照 KnowledgeHub 的 tenant_id、organization_id 与 AIOps tenants.organization_id，列出一对多、多对一、空值、公共值与已删除租户；只有人工批准的映射可进入试迁移。
3. S1 从租户创建、ops 项目唯一约束和有效能力开始；随后移植平台员工/模板/权限资源界面，逐页改接新 API。保留旧 UI 作对照，不把旧 API 响应直接映射到新权限。
4. S4/S5 再处理配置发布与外部消费者适配。先试运行新旧结果对照，再按组织/项目切流；运行时凭据重新签发。

## S0 出口补充

- AIOps 基线提交、源文件、目标对象和不迁入项有清单。
- AIOps 租户与 KnowledgeHub 组织/租户的交叉映射无未解释冲突；无映射客户资料留在隔离清单。
- 平台控制面与组织 ops 项目的数据流、角色、审计和撤权边界在 S1 接口契约中分别体现。
- 当前仅完成代码静态盘点。生产记录数、迁移成功率和系统行为仍待只读导出与试运行验证。

## AIOps 租户只读预检

脚本：[preflight_aiops.py](../../scripts/migration/preflight_aiops.py) 使用 AIOps 的 tenants 元数据导出与 KnowledgeHub 预检共用的审批映射文件。AIOps Tenant.code 对应旧 KnowledgeHub 的 tenant_id；AIOps Tenant.organization_id 是 KnowledgeHub 租户根组织，旧知识记录中的 organization_id 可能表示部门，二者不能按字段名直接相等连接。

输入导出只需 tenants 数组内的 id、code、organization_id、status、is_deleted。即使导出里含 api_key、联系方式，报告也不复制这些字段。运行：

    python -m scripts.migration.preflight_aiops --export aiops-tenants.json --mapping approved-mapping.json --output migration-output/aiops-preflight.json

工具将重复租户码、同一 KH 根组织被多个租户占用、非 active 租户和目标组织映射冲突挡在试导入前。ready 仅表示元数据可进入下一步验证，不代表旧权限或客户内容已经核对。
