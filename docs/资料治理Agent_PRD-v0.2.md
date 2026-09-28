# 资料治理 Agent PRD

版本：v0.2.1 研发规格稿  
日期：2026 年 9 月 28 日  
状态：待产品、技术与试点负责人评审。本文细化 v0.1，不代表上线日期、模型效果或对外 SLA 承诺。  
相关文档：[产品设计全貌 v0.2](./资料治理Agent产品设计全貌-v0.2.md)、[产品规划 v0.1](./资料治理Agent产品规划方案-v0.1.md)。

## 1. 目标、范围与术语

### 1.1 产品目标

在一个项目边界内，将持续变化的资料转为可追溯、按条件适用、可控发布的有效知识。系统应将可确定的资料整理自动化，把业务含义、规则范围、发布和高影响动作聚合为少量待决策事项。

首版支持上传 Markdown、TXT、DOCX、可提取正文 PDF；默认只读诊断，修订只产生派生版本，不覆盖或删除原件。支持一次项目内首次治理、第二批资料的增量处理、有效知识读取和一个外部 Agent/API 接入。

不在首版范围：扫描件/OCR、复杂表格及音视频解析；原件写回；跨项目规则自动复用；通用问答；全量连接器；公共知识库；多级企业审批；离线副本的实时撤回保证。

### 1.2 术语

| 术语 | 定义 |
|---|---|
| 项目 | 数据、人员、预算、规则和发布的最小隔离边界。 |
| 来源 | 用户接入的文件或未来连接器对象；来源有稳定身份，不等于某次文件内容。 |
| 来源版本 | 一次已读取的来源内容，以 SHA-256、大小和读取时间标识；是所有证据的锚点。 |
| 内容片段 | 来源版本中可定位的最小引用单元（页、段落或标题块）。 |
| 问题组 | 同一业务决定可以处理的一组发现；不是逐文件待办。 |
| 决策 | 人或已验证身份提交、且被确认的业务意见；可仅用于本次，也可形成规则。 |
| 规则版本 | 可执行或可评估的“条件—动作—例外—不确定处理”定义；一次编辑创建新版本。 |
| 修订集 | 基于确定输入、决策和规则生成的一组派生修改及验证结果。 |
| 知识版本 | 一条可被引用的结论及其条件、出处、确认状态。 |
| 发布快照 | 某一时刻被发布的一组知识版本和目标目的地；发布与下游验证分开。 |
| 有效知识 | 在给定项目、调用方权限、业务日期和上下文下，处于可用状态的知识版本。 |

### 1.3 成功与不可接受结果

试点验收以客户人工总时间、修订正确性、遗漏与误报、第二批资料中的规则复用和完整成本为准。系统不得把“任务完成”“修订完成”“本地发布”和“下游验证”混为同一结论；无法读取、超预算、证据不足或等待决定的范围必须明确标为未完成。

## 2. 组织、Agent 权限与审计

### 2.1 资源层级与预置 `ops` 项目

权限不再只以项目成员表达；所有资源位于以下层级，权限只能向下继承，不能向上回流：

```text
平台控制面（Platform）
  └── 组织 / 租户（Organization）
        ├── 系统托管项目：ops（每个组织创建时预置，唯一、不可删除）
        └── 业务项目：项目 A、项目 B …
              └── 来源、任务、规则、修订、知识、发布目的地
```

`ops` 是组织内预置的系统项目，固定 `project_key=ops`、`project_kind=ops`、`system_managed=true`。它保存组织运营所需的告警、任务编排配置、连接器健康度、成本/配额和平台 Agent 的运行记录；可存放被明确指定的运营知识，但**不自动继承任何业务项目的来源正文、知识、规则、发布权限或密钥**。业务项目向 `ops` 暴露的仅是最小状态与审计摘要，除非项目所有者另行授予可撤销访问授权。

平台控制面用于运营平台和前端平台的租户、产品配置、受支持 Agent 模板和全局安全策略。平台工作人员不因平台角色而获得客户组织或项目资料读取权；跨组织支持必须走明确、限时、可见、可撤销的支持授权。这样可在后续扩展运营平台时复用身份与策略，而不会把 `ops` 变成全局超级项目。

### 2.2 主体模型：人、Agent 与执行实例分离

| 概念 | 身份与生命周期 | 可被授予的权限 | 明确限制 |
|---|---|---|---|
| 人员主体（`user`） | 通过组织成员关系加入；可在多个组织有不同角色 | 组织/项目角色、临时委派 | 不能把本人角色直接共享给 Agent。 |
| 产品预置 Agent（`builtin_agent`） | 平台注册、版本化模板，如治理 Agent、ops Agent | 只通过组织安装和项目绑定获得能力 | 模板本身没有任何客户数据权限。 |
| 自建/外部 Agent（`service_agent`） | 由组织管理员注册，绑定负责人和客户端凭据 | 仅可获显式能力授权 | 不能确认业务事实、改变人类角色或创建永久提权。 |
| Agent 安装（`agent_installation`） | 某组织启用某 Agent 的配置实体 | 组织级配置和项目绑定 | 一个安装不得跨组织使用；停用即撤销令牌。 |
| 执行实例（`agent_run`） | 一次任务/工具调用的短生命周期身份 | 仅取“安装授权 ∩ 项目绑定 ∩ 本次委派 ∩ 动作风险策略” | 不能复用上一次任务上下文或令牌。 |
| 发布目的地/连接器 | 机器主体，独立凭据和健康状态 | 只接收已发布快照或被允许的事件 | 不能反向取得项目读取或发布权限。 |

每次 Agent 调用必须记录 `organization_id`、`installation_id`、`agent_run_id`、`initiating_principal_id`（如有人发起）、`delegation_id`（如存在）、`project_id`、`policy_version`、`request_id`。审计中必须同时展示“谁发起、哪个 Agent 执行、依据哪条授权”，不能把 Agent 行为归为泛化的系统用户。

### 2.3 角色与能力（RBAC + 约束授权）

角色只负责提供能力集合；实际允许结果还要经过资源范围、数据分类、运行时上下文、时间、预算和状态机校验。能力格式为 `resource:verb`，例如 `knowledge:read`、`tasks:create`、`rules:activate`，不得以模糊的 `admin` scope 代替。

| 层级 | 内置角色 | 典型能力 | 不能隐含获得 |
|---|---|---|---|
| 平台 | `platform_admin`、`platform_operator`、`platform_security_auditor` | 租户生命周期、模板发布、平台健康、全局审计元数据 | 客户正文/知识读取、客户项目发布、业务确认。 |
| 组织 | `org_owner`、`org_admin`、`org_billing_admin`、`org_auditor`、`org_member` | 成员、项目、Agent 安装、组织预算/保留、审计查看 | 任何项目的业务确认和发布（除非另获项目角色）。 |
| 项目 | `project_owner`、`project_contributor`、`business_approver`、`publisher`、`project_viewer` | 见下表 | 其他项目、`ops` 或组织配置权限。 |
| Agent | `governance_worker`、`ops_worker`、`external_reader`、`external_submitter` | 由安装策略映射为最小能力集 | 组织/项目角色管理、业务确认、永久授权、未授权原文读取。 |

| 能力类 | 项目所有者 | 贡献者 | 业务确认人 | 发布人 | 治理 Agent | ops Agent |
|---|---:|---:|---:|---:|---:|---:|
| 来源：接入/读取/缩小范围 | 是 | 按授权 | 只读（需要时） | 只读（需要时） | 绑定项目且按数据分类 | 默认仅元数据 |
| 任务：创建/取消/读取 | 是 | 是（本人任务） | 是 | 是 | 可创建/继续已委派任务 | 仅监测/重试既有编排 |
| 问题：提交线索/查看 | 是 | 是 | 是 | 是 | 是 | 仅状态摘要 |
| 决策：确认业务事实/规则 | 是 | 否（除非另授） | 是 | 否（除非另授） | 否 | 否 |
| 规则：草案/试运行/激活 | 是 | 草案 | 确认/激活 | 否 | 草案和已授权试运行 | 不可改业务规则 |
| 修订：生成派生物/验证 | 是 | 按授权 | 否 | 否 | 仅已绑定范围且 L0/L1 | 可重试已授权工作单元 |
| 发布：快照/目的地/恢复 | 是 | 否 | 否 | 是 | 否 | 否 |
| 知识：读取已发布内容 | 是 | 按授权 | 按授权 | 按授权 | 按安装/项目/分类 | `ops` 自身及显式摘要 |

### 2.4 Agent 安装、项目绑定与委派

1. 组织管理员安装预置或外部 Agent 时，创建 `agent_installation`，指定负责人、允许的能力包、数据分类上限、预算上限、网络/工具策略和默认失效时间。安装默认 `disabled`，完成项目绑定后才可运行。
2. 项目所有者创建 `agent_project_binding`，选择该 Agent 在本项目可访问的资源类型、允许动作、来源/知识分类、可使用的发布状态、预算份额及是否允许后台持续维护。绑定不等于授予所有已安装 Agent。
3. 一次用户触发的执行可创建 `delegation`：它是人对 Agent 的短期、具目的、可撤销的临时授权，包含 `purpose`、项目、动作、资源选择器、上下文、最大成本、`expires_at` 和 `max_runs`。委派只能缩小、不能扩大安装和项目绑定的权限。
4. 运行时服务签发只对单次 `agent_run` 有效的短期令牌；令牌中包含 `org_id`、`installation_id`、`project_id`、`capabilities`、`resource_constraints`、`delegation_id`、`run_id`、`exp`。禁止宽泛的 `project_ids:*`、长期 bearer token 或 Agent 间转交令牌。
5. L2/L3 动作必须由已认证的人在服务端确认；Agent 可以准备确认摘要，但不能以委派、自然语言或回调参数替代确认。确认记录绑定待确认对象版本，版本变化后确认失效。
6. 撤销项目绑定、安装、委派、人员成员关系或来源权限时，授权校验即时失效；在跑任务进入 `paused_authorization_revoked`，保留检查点但不继续读取/写入。

### 2.5 `ops` 项目和运营平台的权限边界

- 每个组织只能有一个 `ops`；普通用户界面将其标为“系统运营”，不与业务项目混在默认项目选择器中。仅 `org_owner`、`org_admin`、被授予 `ops_operator` 的人员和绑定的 `ops_worker` 默认可访问。
- `ops_worker` 可读取组织级容量、作业状态、连接器健康和经脱敏的项目事件；它可按既有策略恢复失败的异步投递、创建告警和建议操作。它不能读取业务文件、证据摘录、未发布知识、业务意见或发布目的地密钥。
- 若运营需要协助某业务项目，项目所有者从项目内显式创建 `support_access_grant`，可选择 `metadata_only`、`published_knowledge` 或特定来源版本；必须填写原因和截止时间。默认最长 24 小时，提前撤销立即生效，所有读取在项目审计流可见。
- “运营平台”调用平台 API 只能管理组织、Agent 安装、策略、预算、健康和经授权的支持会话；“前端平台”在每次导航/按钮渲染前读取有效能力，不能仅靠前端隐藏按钮作为权限控制。

### 2.6 授权判定顺序与审计

对每个请求依次校验：认证主体有效 → 组织未禁用 → 安装/人员成员关系有效 → 项目属于组织 → 角色/能力存在 → Agent 项目绑定存在 → 委派（如需要）有效 → 资源选择器和数据分类匹配 → 预算与速率允许 → 资源状态机允许。任何一步失败均拒绝，记录不含正文的原因码。

业务确认不能扩大来源读取、预算、项目范围或发布权限。原文中的指令、链接和提示词只能作为资料内容。所有角色/能力/安装/绑定/委派变更、模拟授权、拒绝访问、Agent 运行、确认、修订、发布、支持访问及保留动作均写入追加式审计事件；审计至少保存对应项目保留期加 90 天。

### 2.7 运营平台与前端平台的权限体验要求

| 产品面 | 必要页面/能力 | 权限表现 |
|---|---|---|
| 运营平台 | 组织目录、组织 `ops` 概览、Agent 模板库、安装与项目绑定、支持访问、全局健康/配额、审计检索 | 以平台角色控制；默认显示聚合/脱敏数据。打开客户资料前必须进入可见的支持授权会话。 |
| 组织管理 | 成员与角色、业务项目、`ops` 配置、Agent 安装、预算、保留策略 | 只显示当前组织；安装和绑定分两步，不允许用安装页绕过项目所有者。 |
| 项目工作台 | 项目成员、有效能力、已绑定 Agent、活跃委派、来源分类、审计时间线 | 显示“直接/继承/临时委派”来源、可做动作、资源范围、到期时间及撤销入口。 |
| 前端基础框架 | 组织切换器、业务项目切换器、独立标识的 `ops` 入口、能力驱动导航、拒绝页 | 菜单、按钮和数据查询都以 `/effective-access` 的结果渲染；接口仍独立二次鉴权。 |

前端不得用“管理员”笼统展示所有操作：高风险按钮应给出所需角色/确认人、当前缺少的授权、影响范围和操作后果。Agent 相关页面应区分“模板”“组织安装”“项目绑定”“当前运行”“临时委派”五个对象，避免把一个 API key 误解为完整业务权限。

## 3. 核心业务规则

### 3.1 输入准入与解析

| 规则 | 行为 |
|---|---|
| 格式准入 | 仅接受 `.md`、`.txt`、`.docx`、有可提取文本的 `.pdf`；其他格式创建来源记录但状态为 `unsupported`。 |
| 去重 | 同一项目内相同 SHA-256 的内容不重复解析；仍记录各来源与接入时间。不同项目不共享正文或向量。 |
| 版本识别 | 新内容的 SHA-256 与当前来源版本不同才创建新来源版本；文件名、修改时间仅作线索，不能决定替代关系。 |
| 解析失败 | 保留错误码、失败阶段和可重试标记；该版本及依赖它的范围标为“未检查”，不得计入覆盖。 |
| 内容定位 | 每个证据必须指向 `source_version_id + locator`；locator 至少含页码或段落序号及字符区间。 |
| 缓存 | 解析/候选/语义结果必须记录来源版本、解析器版本、规则版本和处理方法版本；任一依赖变化即失效。 |

### 3.2 诊断与问题归并

诊断输出的每个发现必须包含问题类型、置信度、至少一条证据、受影响对象、建议和不确定原因。首版问题类型为 `duplicate`、`near_duplicate`、`supersession_candidate`、`expired_content`、`future_content`、`review_overdue`、`content_mismatch`、`coverage_gap`、`applicability_gap`、`authority_gap`、`conflict`、`unsuitable_for_use`、`parse_failure`。完整判定边界、基线规则 ID、规则定义字段和测试要求见[资料清洗规则定义与基线规则库 v0.1](./资料清洗规则定义与基线规则库-v0.1.md)。

诊断规则必须输出 `matched`、`not_matched` 或 `indeterminate`。缺少业务日期、目标用途、必要条件、可读证据，或语义判断低于规则阈值时必须为 `indeterminate`；不得将其降级为“未发现问题”。`expired_content` 仅由业务有效期判定，文件上传/修改时间只能用于排序复核候选；`unsuitable_for_use` 必须包含目标用途和不适用原因，不能作为泛化的删除标签。发现的最小影响单位是可定位片段或知识断言，除非证据明确为整份来源范围。

问题组由“相同待确认业务命题 + 相容适用范围 + 同一项目”归并。归并不能跨项目，且任一发现出现互斥事实、不同生效条件或不同确认人时必须拆组。系统可按影响度排序，但排序不改变业务状态。影响度按受影响已发布知识数、阻塞任务数、规则适用范围和来源新鲜度计算；模型置信度不得单独决定自动执行。

### 3.3 渐进式规则发现与客户确认

客户不是首版规则的主要编写者。系统提供平台基线检测规则；AI 在任务与持续维护中从新资料、来源变化、重复的澄清请求、人工纠正、人工推翻、验证失败和未被现有规则解释的问题组中归纳**规则候选**。候选只描述“可能值得反复检查的模式”，没有修改、限制读取、替代或发布权限。

规则中心必须同时展示三层对象，且明确其状态和边界：

| 层 | 产生方 | 内容与权限 |
|---|---|---|
| 平台基线规则包 | 平台 | 重复、有效期、解析/证据/权限等通用检测；项目可启停允许的规则和配置局部阈值，但不能扩大数据权限。 |
| AI 规则候选 | AI/系统信号 | 相似的未覆盖发现、证据、建议的检测条件及潜在影响；只读、可忽略、不可自动生效。 |
| 项目规则 | 客户确认后的草案/规则版本 | 在明确项目、目标用途、条件、例外和动作等级内试运行并生效；不自动推广到其他项目。 |

候选可以由单个高风险、证据充分的发现立即提出，也可以由多个相似发现聚合提出。候选必须包含：触发信号、问题模式、至少一组定位证据、建议范围、建议检测/处理方式、可能误报原因、受影响对象估计和来源任务/规则版本。AI 不得把“模型发现过一次”表述为通用业务事实，也不得依据候选直接创造 L1 以上动作。

客户面对候选只需做业务选择：`one_time`（仅处理本次）、`promote_to_project_rule`（生成项目规则草案）、`exception`（记录特定对象/日期/用途例外）或 `dismiss`（忽略并填写原因）。首版编辑器由自然语言提案和结构化预览组成，不要求客户编写 DSL；高级结构化编辑仍须校验规则定义与权限范围。

规则的成熟路径为：`candidate → draft → trial → active → paused/superseded/revoked`。其中 `candidate` 不属于 `rule_versions`，推广后才创建不可覆盖的规则版本。试运行必须只输出命中、未命中、不确定、误报候选和影响预览；需同时覆盖正例、反例、边界例和例外例。第二批未见资料只用作复用验收，不能在不创建新版本的情况下反向调整阈值。

持续维护不能以“没有新候选”声称知识已全面覆盖。每个项目应报告已启用规则覆盖的资料/目标用途、未检查范围、重复澄清或人工推翻产生的候选数，以及候选转化、忽略和试运行误报率。

### 3.4 决策、规则与优先级

一条规则版本最少包含：身份与版本、自然语言描述、结构化条件、输入契约、检测逻辑及阈值、证据契约、动作、例外、作用范围、风险级别、不确定处理、确认人、试运行用例和有效期。检测规则负责生成发现，处理规则只消费已定位发现并决定受控动作；二者均须版本化。自由文本偏好只能作为 `reference_preference`，不得生成事实修改动作。

规则匹配顺序：先过滤项目与对象类型，再评估 `effective_from/effective_to`、条件和例外；只在结果为 `true` 时可适用。条件缺字段、语义判断低于规则阈值、证据冲突或多个同优先级规则给出不同动作时，结果为 `needs_decision`，禁止猜测。

冲突优先级从高到低：

1. 明确的本次已确认决策（只影响其任务）；
2. 更窄作用范围且已生效的项目规则；
3. 更高 `priority` 的已生效项目规则；
4. 默认安全策略（不修改、不发布、建立问题组）。

“更窄”按项目内对象集合、客户类型、资料类型和日期区间的真子集判断；无法计算包含关系时视为冲突。规则不能自动跨项目生效；跨项目复用必须创建目标项目的新草案与确认记录。

### 3.5 自动动作分级

| 风险 | 示例 | 允许条件 |
|---|---|---|
| L0 只读 | 解析、去重候选、差异比较、试运行 | 有读取权限和任务预算。 |
| L1 可恢复派生 | 已授权规则下生成标签、摘要、派生修订草案 | 规则已生效、输入版本未变化、验证通过；仍不可发布。 |
| L2 业务含义 | 冲突定论、事实替代、扩大规则范围 | 必须有对应业务确认人确认。 |
| L3 高影响 | 发布、恢复、目的地配置、原件写回、扩大来源权限 | 必须由发布人或所有者的显式确认；首版不提供原件写回。 |

用户沉默、任务超时、文件较新、模型高置信度均不构成 L2/L3 授权。

### 3.6 验证、发布与失效

修订集至少通过以下检查才可进入待发布：输入来源版本仍为任务读取版本；每个修改有证据与规则/决策链；引用定位可读取；规则条件和例外测试通过；没有未处理的阻塞级问题。验证失败只阻止关联范围，独立范围可继续。

发布前服务端重新检查发布人权限、修订验证、知识版本状态、未来生效时间、来源限制和目的地配置。发布快照不可修改；恢复是引用历史知识版本创建新的发布快照。来源权限撤回时，立即停止正文读取，按保留策略将派生内容标记 `restricted`、归档或删除，并向相关发布目的地发送撤回事件（若目的地支持）。

## 4. 状态机与状态迁移

### 4.1 任务

`draft → queued → inventorying → diagnosing → waiting_decision → proposing → revising → validating → ready_to_publish → completed`

任何运行态可进入 `paused`、`cancelled` 或 `failed`；`paused` 在权限、预算和输入仍有效时可回到前一运行态；`failed` 仅能从检查点 `retry`；`cancelled` 只停止未开始工作，不回滚已生成派生物。`completed` 表示任务处理结束，不表示发布完成。等待决策只阻塞关联工作单元。

### 4.2 问题、决策与规则

| 对象 | 状态与合法迁移 |
|---|---|
| 问题组 | `open → analyzing → waiting_decision → resolved`；可转 `ignored`，必须填写原因和操作者。新的冲突可使 `resolved → reopened`。 |
| 决策 | `draft → submitted → confirmed → revoked`；撤销不删除其历史影响，而是触发影响分析。 |
| 规则候选 | `candidate → promoted/dismissed`；`dismissed` 必须记录原因；候选无自动动作能力。相同模式的新证据可使 `dismissed → candidate`，并保留关联。 |
| 规则版本 | `draft → trial → active → superseded/revoked`；`active ↔ paused`；撤销、暂停后不得新增自动执行。一次改动创建新版本，旧版本不覆盖。 |
| 修订集 | `draft → revising → validation_failed/ready_to_publish → published/restored`；发布后不可编辑。 |
| 知识版本 | `pending_confirmation → unpublished → current/future → superseded/revoked/restricted`；`current` 与 `future` 由业务生效时间和发布快照共同决定。 |
| 发布快照 | `draft → locally_active → delivered → verified`；投递失败为 `delivery_failed`，可重试至 `delivered`。 |

所有状态迁移均要求乐观锁版本号匹配；对终态的重复请求按幂等规则返回已有结果，而非重复执行。

## 5. 功能规格：输入、处理与输出

| 功能 | 输入 | 系统处理/规则 | 输出与完成条件 |
|---|---|---|---|
| 创建项目 | 名称、用途、时区、默认预算、所有者 | 创建隔离边界和默认保留策略 | 项目 ID；初始状态 `active`。 |
| 上传来源 | 文件、显示名、可选标签/范围 | 校验格式、大小、权限；计算哈希，创建来源及版本，异步解析 | 来源/版本 ID、解析任务；解析失败明确未检查。 |
| 发起治理任务 | 来源版本集合、目标、范围、预算、允许动作 | 锁定输入清单和授权快照；预算预留；只读开始 | 任务 ID、`queued`；重复 `idempotency_key` 返回原任务。 |
| 诊断 | 任务、可读片段、已有有效规则 | 先确定性检查，后候选召回和语义分析；按规则 3.2 归并 | 覆盖范围、问题组、跳过/失败清单、消耗；无问题不等于全库正确。 |
| 发现规则候选 | 问题组、重复澄清/纠正、来源变化、验证结果、已启用规则覆盖 | 聚合同模式与证据，标明未覆盖范围和误报风险；不执行处理动作 | `candidate`、证据、建议检测/处理定义和影响预览；可忽略或提升为项目草案。 |
| 提升规则候选 | 候选、客户选择的范围/例外/本次或项目意图 | `one_time` 只形成决策；项目规则生成结构化草案，校验动作等级和权限 | 已确认决策或 `rule_version(draft)`；仍须试运行才能激活。 |
| 提交意见 | 问题组、意见文本、适用范围、本次/规则意图 | 记录原文和结构化解释；外部 Agent 意见为线索 | 决策草案或规则草案，必要时返回澄清问题。 |
| 试运行规则 | 规则草案、显式测试样本/影响范围 | 不改变知识；校验冲突、条件和例外 | 命中/未命中/不确定列表、影响预览、验证结果。 |
| 生成修订 | 已确认决策/已生效规则、输入版本 | 仅对未变化输入生成派生物；每项建立溯源链 | 修订集、逐项 diff、待验证项；绝不覆盖原件。 |
| 验证修订 | 修订集、测试用例 | 运行 3.6 的硬检查与规则测试 | `ready_to_publish` 或失败列表及恢复/重试入口。 |
| 发布 | 通过验证的修订/知识、目的地、发布说明 | 再授权、创建不可变快照、异步投递 | 快照 ID、本地生效结果、投递状态；不将“已接收”写为“已验证”。 |
| 读取有效知识 | 项目、意图、上下文、业务日期 | 认证后按条件、时间、状态、权限筛选；上下文不足不挑选最新项 | 知识项、证据、适用条件、快照版本，或 `clarification_required`。 |

## 6. API 契约（v1）

### 6.1 通用约定

- 基址：`/api/v1`；JSON 使用 UTF-8，时间为 RFC 3339 UTC，ID 使用 UUIDv7。
- 认证：人员使用 Bearer session；Agent/连接器只使用由 `agent_run` 或投递任务签发的短期 Bearer token。令牌最少含 `org_id, principal_id, installation_id, run_id, project_id, capabilities, resource_constraints, delegation_id, policy_version, exp`；服务端每次仍核验安装、绑定、委派、成员关系和令牌未撤销。不得签发“组织内所有项目”或长期万能 token。
- 所有写入接口要求 `Idempotency-Key`（UUID），键在同一调用方/路径下保存 24 小时；同键不同请求体返回 `409 idempotency_conflict`。
- `GET` 列表使用 `cursor`、`limit`（默认 20，最大 100）；所有可编辑资源返回 `version`，更新请求以 `If-Match: <version>` 乐观锁定。
- 成功响应格式为 `{ "data": ..., "request_id": "..." }`；失败为 `{ "error": { "code": "...", "message": "...", "details": [...] }, "request_id": "..." }`。不得在错误中返回无权限原文。

### 6.2 资源与端点

| 方法与路径 | 所需 scope | 请求核心字段 | 成功响应/语义 |
|---|---|---|---|
| `POST /organizations` | 平台/自助注册策略 | `name,timezone,retention_policy` | `201 organization`，事务内预置唯一 `ops` 项目和默认安全策略。 |
| `GET /organizations/{id}/effective-access` | 本人或 `access:inspect` | `project_id`（可选） | 返回调用方在组织/项目的有效能力、来源、约束和失效时间；供运营及前端平台统一使用。 |
| `POST /organizations/{id}/agent-installations` | `agents:install` | `agent_template_id,owner_id,capability_packages,data_classification_ceiling,budget_policy` | `201 installation(disabled)`；安装本身不含项目访问。 |
| `POST /agent-installations/{id}/project-bindings` | `agents:bind` + `project:manage` | `project_id,capabilities,resource_constraints,budget_share,background_maintenance` | `201 binding`；拒绝跨组织、`ops` 默认越权及超过安装能力包的请求。 |
| `POST /agent-installations/{id}/delegations` | 发起人具对应项目权限 | `project_id,purpose,capabilities,resource_constraints,max_cost,expires_at,max_runs` | `201 delegation`；能力只能为绑定的子集，需运行时授权的动作才可创建。 |
| `POST /delegations/{id}/revoke` | 委派人、项目所有者或组织管理员 | `reason` | `200 delegation(revoked)`；关联运行暂停。 |
| `POST /projects/{id}/support-access-grants` | `project:manage` | `grantee_installation_id,access_level,source_version_ids,reason,expires_at` | `201 grant`；仅项目所有者可给运营支持，默认不含正文。 |
| `POST /projects` | `projects:write` | `name,purpose,timezone,default_budget` | `201 project`。 |
| `GET /projects/{id}` | `projects:read` | — | 项目及调用方可见配置。 |
| `POST /projects/{id}/sources` | `sources:write` | multipart `file`，可选 `display_name,retention_class` | `202 source,source_version,parse_job_id`。 |
| `GET /projects/{id}/sources` | `sources:read` | `status,cursor,limit` | 来源及当前版本摘要，不默认返回正文。 |
| `POST /projects/{id}/tasks` | `tasks:write` | `source_version_ids,objective,scope,budget,allowed_actions` | `202 task`；服务端拒绝越权版本。 |
| `GET /tasks/{id}` | `tasks:read` | — | 任务、覆盖、检查点、预算与状态。 |
| `POST /tasks/{id}/cancel` | `tasks:write` | `reason` | `200 task`；仅停止未执行工作。 |
| `GET /tasks/{id}/issues` | `issues:read` | `status,cursor,limit` | 问题组及脱敏影响摘要。 |
| `POST /issues/{id}/opinions` | `opinions:write` | `text,scope,apply_mode` | `202 decision_draft`；外部调用创建 `unverified_lead`。 |
| `POST /decisions/{id}/confirm` | `decisions:confirm` | `confirmation_note` | `200 decision`；须业务确认人。 |
| `GET /projects/{id}/rule-candidates` | `rules:read` | `status,source,cursor,limit` | 候选模式、证据、建议范围、影响摘要与覆盖来源。 |
| `POST /rule-candidates/{id}/promote` | `rules:write` | `choice,scope,exceptions,actions,tests` | `200 decision(one_time)` 或 `201 rule_version(draft)`；不得直接激活。 |
| `POST /rule-candidates/{id}/dismiss` | `rules:write` | `reason` | `200 candidate(dismissed)`；相同模式的新证据保留可追溯关联。 |
| `POST /rules` | `rules:write` | `project_id,name,rule_definition,scope,tests` | `201 rule_version(draft)`。 |
| `POST /rules/{id}/trial` | `rules:trial` | `sample_ids` 或 `impact_scope` | `202 trial_job`，不改知识。 |
| `POST /rules/{id}/activate` | `rules:confirm` | `confirmation_note` | `200 rule_version(active)`；须已通过试运行。 |
| `POST /tasks/{id}/revision-sets` | `revisions:write` | `decision_ids,rule_version_ids` | `202 revision_set`。 |
| `POST /revision-sets/{id}/validate` | `revisions:validate` | `test_case_ids` | `202 validation_job`。 |
| `POST /publication-snapshots` | `publications:write` | `project_id,knowledge_version_ids,destination_ids,note` | `202 snapshot`；只有 `ready_to_publish` 内容可选。 |
| `GET /publication-snapshots/{id}` | `publications:read` | — | 本地、交付、验证状态与失败原因。 |
| `POST /knowledge/query` | `knowledge:read` | `project_id,intent,context,business_date` | `200 knowledge_response` 或 `clarification_required`。 |
| `GET /changes` | `changes:read` | `project_id,after_cursor` | 已发布、撤销、受限事件的有序增量。 |

### 6.3 关键请求与响应示例

创建任务：

```json
POST /api/v1/projects/018.../tasks
Idempotency-Key: 1b4d...
{
  "source_version_ids": ["018...a", "018...b"],
  "objective": "维护本项目当前报价和交付口径",
  "scope": {"document_types": ["proposal", "minutes"], "business_date": "2026-10-01"},
  "budget": {"unit": "credit", "limit": 100, "warn_at": 80},
  "allowed_actions": ["read_diagnose", "create_derived_revision"]
}
```

```json
{
  "data": {
    "id": "019...", "status": "queued", "input_snapshot_hash": "sha256:...",
    "coverage": {"requested": 2, "accepted": 2, "unreadable": 0},
    "allowed_actions": ["read_diagnose", "create_derived_revision"]
  },
  "request_id": "req_..."
}
```

有效知识查询；上下文不足时不返回猜测答案：

```json
POST /api/v1/knowledge/query
{
  "project_id": "018...", "intent": "查询报价",
  "context": {"customer_type": "channel"}, "business_date": "2026-10-01"
}
```

```json
{
  "data": {
    "status": "clarification_required",
    "questions": [{"field": "channel_tier", "reason": "现行规则将渠道客户作为例外"}],
    "candidate_evidence": [{"source_version_id": "018...", "locator": {"page": 3, "paragraph": 2}}]
  },
  "request_id": "req_..."
}
```

查询成功的每个 `knowledge_item` 必须返回 `knowledge_version_id`、`statement`、`conditions`、`effective_from/to`、`status`、`publication_snapshot_id`、`citations[]` 和 `limitations[]`；仅在调用方有正文权限时返回引文文本。

### 6.4 错误、异步与通知

| HTTP | 错误码 | 客户端动作 |
|---:|---|---|
| 400 | `invalid_request` / `invalid_state_transition` | 修正字段或在正确状态重试。 |
| 401/403 | `unauthenticated` / `forbidden` | 刷新认证或请求权限；不猜测资源存在性。 |
| 404 | `not_found` | 资源不存在或对调用方不可见。 |
| 409 | `version_conflict` / `input_version_changed` / `idempotency_conflict` | 读取最新状态，不能覆盖重试。 |
| 422 | `clarification_required` / `validation_failed` / `rule_conflict` | 提供所需上下文、确认或修订规则。 |
| 429 | `budget_exhausted` / `rate_limited` | 等待 `retry_after` 或增加经授权预算。 |
| 503 | `processing_unavailable` | 以相同幂等键重试；任务检查点保留。 |

长任务返回 `202` 与资源 ID。客户端通过 `GET /tasks/{id}`、`GET /changes` 或 Webhook 获得进展。Webhook 事件为 `task.waiting_decision`、`task.completed`、`publication.delivered`、`publication.delivery_failed`、`knowledge.published`、`knowledge.revoked`、`source.permission_revoked`、`agent.delegation_revoked`、`agent.binding_changed`；负载仅含事件 ID、组织/项目 ID、资源 ID、版本、时间和签名，正文需重新鉴权读取。至少一次投递，消费者以 `event_id` 去重。

## 7. 数据库逻辑定义

建议首版采用 PostgreSQL；对象存储保存原文件和派生文件，数据库只保存 URI、哈希和元数据。正文/向量索引必须有项目隔离键；数据库 RLS 与应用层 scope 双重校验。

### 7.1 约定

- 主键为 `uuid`，主业务表都有 `created_at,updated_at,created_by,version`；时间用 `timestamptz`。
- 所有项目数据都有不可为空的 `project_id`，外键采用 `ON DELETE RESTRICT`；业务删除用 `deleted_at`，禁止级联物理删除证据链。
- 枚举值由数据库 `CHECK` 或枚举类型约束；金额/预算使用 `numeric(18,4)`，哈希为小写十六进制 SHA-256。
- `jsonb` 只用于可演进的条件、结构化模型输出、错误详情和审计补充字段；高频筛选字段必须拆列和建索引。

### 7.2 核心表

| 表 | 关键字段（除通用字段） | 约束与索引 |
|---|---|---|
| `organizations` | `id,name,slug,timezone,status,retention_policy_id,created_from` | `slug` 全局唯一；`status in (active,suspended,archived)`；创建事务内建立 `ops`。 |
| `principals` | `id,type,user_id,agent_template_id,external_subject,status` | `type in (user,builtin_agent,service_agent,connector)`；外部主体唯一；主体本身不带项目权限。 |
| `organization_memberships` | `organization_id,principal_id,role,status` | 仅人员主体；`unique(organization_id,principal_id)`；组织角色/启用状态索引。 |
| `projects` | `id,organization_id,project_key,project_kind,name,purpose,timezone,status,default_budget,retention_policy_id,owner_id,system_managed` | `unique(organization_id,project_key)`；`project_kind in (ops,business)`；每组织恰有一个活跃 `ops`，`ops` 不可物理删除。 |
| `role_bindings` | `id,organization_id,project_id,principal_id,role,scope_selector,expires_at,status,granted_by` | 人员绑定可在组织/项目层；`unique` 覆盖同主体/角色/范围；`scope_selector` 只能缩小角色范围。 |
| `agent_templates` | `id,key,version,kind,declared_capabilities,tool_policy,status` | 平台控制面管理；`unique(key,version)`；模板发布不自动变更现有安装。 |
| `agent_installations` | `id,organization_id,template_id,principal_id,owner_id,status,capability_packages,data_classification_ceiling,budget_policy,config_encrypted` | `principal_id` 类型必须为 Agent；`unique(organization_id,principal_id)`；默认 `disabled`。 |
| `agent_project_bindings` | `id,installation_id,project_id,capabilities,resource_constraints,budget_share,background_maintenance,status,expires_at,granted_by` | `unique(installation_id,project_id)`；能力必须为安装能力包子集；项目与安装必须同组织。 |
| `delegations` | `id,organization_id,project_id,installation_id,delegated_by,purpose,capabilities,resource_constraints,max_cost,max_runs,runs_used,expires_at,status,revoked_at` | 委派能力/范围必须为项目绑定子集；`expires_at`、`max_runs` 必填；`status in (active,exhausted,expired,revoked)`。 |
| `support_access_grants` | `id,project_id,grantee_installation_id,access_level,source_version_ids,reason,expires_at,status,granted_by,revoked_at` | `access_level in (metadata_only,published_knowledge,selected_source_versions)`；最长 24 小时；无授权不得含正文。 |
| `agent_runs` | `id,organization_id,project_id,installation_id,delegation_id,initiated_by,task_id,purpose,authorization_snapshot,status,started_at,finished_at` | 每次工具调用绑定运行；授权快照不可改；撤销后运行不得继续。 |
| `api_credentials` | `id,principal_id,installation_id,token_hash,credential_type,expires_at,revoked_at,last_used_at` | 仅存 token hash；只用于换取短期运行令牌，不能直接带项目 scopes。 |
| `sources` | `id,project_id,display_name,origin_type,origin_ref,read_scope,status,retention_class,current_version_id` | `unique(project_id,origin_type,origin_ref)`；`(project_id,status)` 索引。 |
| `source_versions` | `id,source_id,content_sha256,byte_size,mime_type,read_status,parser_version,storage_uri,read_at,parse_error` | `unique(source_id,content_sha256)`；哈希与状态索引；`storage_uri` 受访问控制。 |
| `content_segments` | `id,project_id,source_version_id,ordinal,locator,text_hash,extracted_text,parse_status` | `unique(source_version_id,ordinal)`；`(project_id,source_version_id)` 索引；全文/向量索引必须过滤 project。 |
| `tasks` | `id,project_id,objective,scope,input_snapshot_hash,input_manifest,budget_limit,budget_used,allowed_actions,status,checkpoint,requested_by` | `(project_id,status,created_at desc)`；输入清单不可在运行后改写。 |
| `task_work_units` | `id,task_id,kind,status,depends_on,checkpoint,error_code,started_at,finished_at` | `unique(task_id,kind,...)`；`(task_id,status)` 索引。 |
| `issues` | `id,project_id,task_id,type,severity,status,claim,uncertainty,impact_summary,detector_id,detector_version,confidence,recommendation,target_use` | `target_use` 对 `unsuitable_for_use` 必填；记录检测器/版本/置信度；`(project_id,status,severity)`、`task_id` 索引。 |
| `issue_evidence` | `id,issue_id,source_version_id,segment_id,locator,excerpt_hash,stance` | `stance in (supports,contradicts,context)`；证据 FK 不允许级联删除。 |
| `issue_impacts` | `issue_id,object_type,object_id,impact_kind` | `unique(issue_id,object_type,object_id,impact_kind)`。 |
| `rule_candidates` | `id,project_id,status,pattern,trigger_signals,suggested_detector,suggested_policy,suggested_scope,uncertainty,impact_summary,created_by,source_rule_version_id,promoted_rule_id,dismiss_reason` | `status in (candidate,promoted,dismissed)`；候选无 `actions` 执行权；`(project_id,status,created_at desc)` 索引。 |
| `rule_candidate_evidence` | `id,rule_candidate_id,issue_id,source_version_id,segment_id,locator,signal_type` | 至少一条可读取定位证据；`signal_type in (issue_cluster,source_change,clarification,user_correction,override,validation_failure,coverage_gap)`。 |
| `decisions` | `id,project_id,issue_id,text,structured_interpretation,scope,apply_mode,status,submitted_by,confirmed_by,confirmed_at,revoked_at` | `apply_mode in (one_time,project_rule,reference)`；确认人非空才可 `confirmed`。 |
| `rules` | `id,project_id,name,object_type,status,current_version_id` | `unique(project_id,name)`；`(project_id,status)` 索引。 |
| `rule_versions` | `id,rule_id,number,kind,natural_language,scope,input_contract,conditions,detection_logic,evidence_contract,actions,exceptions,priority,risk_level,uncertainty_policy,effective_from,effective_to,status,confirmed_by,confirmed_at,supersedes_id` | `kind in (detector,policy)`；`unique(rule_id,number)`；`active` 需确认人、测试和动作；语义检测逻辑必须记录方法/模型/阈值版本；条件/时间索引。 |
| `rule_tests` | `id,rule_version_id,case_kind,input_context,expected_outcome,actual_outcome,status,evidence_refs` | `case_kind in (positive,negative,boundary,exception,unseen_acceptance)`；激活前至少各有一条通过正例、反例和边界例；有例外时须有例外例。 |
| `revision_sets` | `id,project_id,task_id,status,input_snapshot_hash,rule_version_ids,decision_ids,validation_summary,created_by` | `(project_id,status)`；输入哈希必须等于任务快照。 |
| `revision_items` | `id,revision_set_id,source_version_id,kind,before_content,after_content,diff_uri,evidence_chain,status` | `kind in (create,update,supersede,restrict)`；每项必须有 evidence chain。 |
| `validation_runs` | `id,revision_set_id,kind,status,results,started_at,finished_at,method_version` | `(revision_set_id,status)`；不可用“同一模型自评”作为唯一通过项。 |
| `knowledge_items` | `id,project_id,key,object_type,status,current_version_id` | `unique(project_id,key)`；`(project_id,status)` 索引。 |
| `knowledge_versions` | `id,knowledge_item_id,number,statement,conditions,effective_from,effective_to,status,confirmation_ref,source_refs,revision_item_id,restricted_at` | `unique(knowledge_item_id,number)`；`current/future` 必有来源和发布关联；条件+时间索引。 |
| `publication_snapshots` | `id,project_id,status,note,created_by,locally_active_at` | `(project_id,status,locally_active_at desc)`。 |
| `publication_entries` | `snapshot_id,knowledge_version_id,operation` | `unique(snapshot_id,knowledge_version_id)`；发布快照条目不可更新。 |
| `destinations` | `id,project_id,type,name,config_encrypted,status` | 凭据加密存储；配置只允许发布人读取。 |
| `delivery_attempts` | `id,snapshot_id,destination_id,status,attempt_no,external_ref,error_code,delivered_at,verified_at` | `unique(snapshot_id,destination_id,attempt_no)`；`(status,next_retry_at)` 索引。 |
| `audit_events` | `id,organization_id,project_id,actor_id,initiating_principal_id,installation_id,agent_run_id,delegation_id,action,resource_type,resource_id,request_id,before_hash,after_hash,metadata,occurred_at` | 追加写；必须记录人/Agent 链；`(organization_id,occurred_at desc)`、`(project_id,occurred_at desc)`、资源索引。 |
| `outbox_events` | `id,organization_id,project_id,type,aggregate_type,aggregate_id,payload,occurred_at,published_at,delivery_count` | `unique(id)`；未发布事件索引，事务内与状态变更同写。 |

### 7.3 关键关系与一致性

```text
Project ──< Source ──< SourceVersion ──< ContentSegment
   │                         │                 │
   ├──< Task ──< Issue ──< IssueEvidence ──────┘
   │       │        └──< Decision ──< RuleVersion ──< RuleTest
   │       └──< RevisionSet ──< RevisionItem ──< ValidationRun
   └──< KnowledgeItem ──< KnowledgeVersion ──< PublicationEntry >── PublicationSnapshot
                                                            └──< DeliveryAttempt >── Destination
```

`Organization ──< Project` 位于上图所有项目资源之前；`Organization ──< AgentInstallation ──< AgentProjectBinding ──< Delegation ──< AgentRun` 是独立的授权链。`ops` 仅是 `Project` 的系统托管类型，不是跨项目父节点。

数据库/服务层必须执行：

1. `source_versions.content_sha256` 是不可变的；新文件内容永远插入新版本。
2. `issue_evidence`、`revision_items.evidence_chain` 和 `knowledge_versions.source_refs` 引用的来源版本必须属于相同项目。
3. 规则激活、修订集进入 `ready_to_publish`、发布快照本地生效均用单一事务；事务同时写 `audit_events` 与 `outbox_events`。
4. 单项目内同一 `knowledge_item` 在任一时点至多一个条件完全相同且状态为 `current` 的版本；条件重叠但结论不同必须创建问题组，不能依赖“最后写入者获胜”。
5. 权限撤回以事务先禁用来源/令牌和正文访问，再异步清理索引及下游撤回；清理完成前相关知识为 `restricted`。
6. 创建组织与预置 `ops` 项目必须是同一事务；应用和数据库约束均保证每组织只有一个 `project_kind=ops`。该项目不能转为业务项目或删除。
7. `agent_project_bindings`、`delegations`、`support_access_grants` 的组织/项目/安装必须一致；数据库触发器或服务事务校验其 capability、数据分类和资源选择器始终为上级授权的子集。
8. `agent_runs.authorization_snapshot` 写入后不可更新；每次执行前重新校验撤销表和上级状态，不能只相信快照或 JWT 的过期时间。
9. 任何 L2/L3 迁移必须存在同项目的、状态有效的人员确认记录；`actor_id` 为 Agent 的审计事件不能单独满足该约束。

## 8. 非功能、保留与安全要求

| 类别 | P0 要求 |
|---|---|
| 隔离 | 每次查询均按组织、项目、主体、安装/委派和 scope 过滤；禁止跨组织/项目候选召回、向量检索和缓存命中。`ops` 不因系统托管而绕过项目边界。 |
| 可追溯 | 任何已发布知识可在界面/API 追到知识版本、修订项、规则/决策、证据片段和来源版本。 |
| 一致性 | 写接口幂等；版本更新乐观锁；异步投递至少一次且可去重；读取不得显示未本地发布内容为当前有效。 |
| 可恢复 | 任务有检查点；派生物可按修订/快照恢复；首版禁止原件覆盖与自动物理删除。 |
| 性能 | 上传接口在完成持久化后 5 秒内返回；任务状态读取 P95 小于 500ms；首版不对诊断完成时间承诺 SLA，而需持续报告进度和范围。 |
| 预算 | 每个工作单元在模型/解析调用前校验剩余预算；达到 `warn_at` 告警，达到上限停止新工作单元，不把余项标完成。 |
| 保留 | 原文、派生正文、索引、审计各按项目策略管理；来源失权/删除按策略限权、归档或删除，并留最小审计凭据。 |
| 安全 | 传输 TLS；对象存储与敏感配置静态加密；长期凭据仅保存哈希；Agent 只获得单运行短期令牌；日志不记录正文、令牌和完整意见；模型供应商调用仅发送任务所需最小片段。 |

## 9. 埋点、验收与测试数据

### 9.1 必要事件与指标

记录 `task_created`、`source_parsed`、`coverage_reported`、`issue_created/resolved`、`rule_candidate_created/promoted/dismissed`、`decision_confirmed`、`rule_trialled/activated/paused`、`revision_validated`、`publication_*`、`knowledge_query`、`clarification_required`、`permission_revoked`、`agent_installed/bound/delegated/revoked/run_*`、`support_access_*`、`budget_warning/exhausted`。每个事件带组织、项目、资源、调用入口、人员/Agent 身份链、处理方法版本、耗时、成本和结果，不带原文。

试点报表必须可计算：人工准备/澄清/审核/返工时间；检测误报/漏报；修订正确/错误/引入问题数；规则在未见第二批资料的命中、例外与错误推广；从来源变更到下游验证的时差；模型、解析、存储、集成和人工支持的完整成本。

### 9.2 P0 验收用例

| 编号 | 前置数据与操作 | 期望结果 |
|---|---|---|
| AC-01 | 上传同一内容两次，随后上传内容不同的同名文件 | 同内容不重复解析；不同内容建立新来源版本，文件名不决定替代。 |
| AC-02 | 含一份无法提取正文的 PDF 发起任务 | 任务显示该版本未检查和原因，不计入已覆盖。 |
| AC-03 | 两份报价冲突，用户确认“新客户新版、老客户合同价、渠道待确认” | 形成限定项目和客户类型的规则/决策；渠道查询返回澄清而非任一价格。 |
| AC-04 | 同一优先级规则对相同上下文给出不同动作 | 创建规则冲突问题，停止关联修订。 |
| AC-05 | 规则试运行后未获确认即请求生成/发布 | 可输出试运行，不可自动执行 L2/L3 或发布。 |
| AC-06 | 修订前更新输入来源 | 返回 `input_version_changed`，旧输入的修订不得覆盖新内容。 |
| AC-07 | 验证失败后发布同一修订集 | 返回 `validation_failed`，不创建本地生效快照。 |
| AC-08 | 已发布后下游投递失败 | 本地状态仍为 `locally_active`，目的地为 `delivery_failed`，可幂等重试。 |
| AC-09 | 撤回来源读取权限 | 即刻不能读取原文，关联知识受限并产生撤回/审计事件。 |
| AC-10 | 外部 Agent 用同一幂等键两次创建任务 | 返回同一任务；其意见仅为线索，无法确认规则或发布。 |
| AC-11 | 相同调用方无项目 scope 查询知识 | 返回 404/403，不泄漏条目名称、正文或存在性。 |
| AC-12 | 第二批资料满足已生效规则 | 自动生成派生提案（如已授权），但仍需单独验证和发布。 |
| AC-13 | 创建组织 | 系统在同一事务中创建唯一、不可删除的 `ops` 项目；它不出现在普通业务项目默认列表。 |
| AC-14 | 未经项目绑定的已安装治理 Agent 请求业务项目正文 | 拒绝访问；安装或组织角色本身不能形成项目读取权。 |
| AC-15 | 已绑定 Agent 以过期或已撤销委派继续运行 | 当前工作单元进入 `paused_authorization_revoked`；不再读取或写入，保留检查点。 |
| AC-16 | `ops_worker` 查询普通项目 | 默认仅见脱敏健康/作业摘要；读取正文、未发布知识或密钥均被拒绝。 |
| AC-17 | 项目所有者创建限时支持访问后提前撤销 | 指定运营主体即时失去读取权；审计显示授权原因、实际读取和撤销时间。 |
| AC-18 | 前端请求有效能力并尝试绕过隐藏按钮直接调用发布 API | 能力接口不返回发布权，API 也拒绝；前端隐藏不作为唯一防线。 |
| AC-19 | 一份批准报价的 `effective_to` 早于查询业务日期，另一份尚未生效 | 当前查询不返回两者；历史查询可见前者，未来查询可见后者。文件修改时间不影响判定。 |
| AC-20 | 文件名为“当前价格表”，正文为未批准会议纪要；另一份资料仅适用于产品 B | 分别形成 `content_mismatch` 与 `applicability_gap`，列出定位与缺失上下文；不把任一资料作为产品 A 的正式价格依据。 |
| AC-21 | 高度相似的两份合同，其中一份有客户例外 | 形成 `near_duplicate` 候选并展示例外；不自动合并、替代或删除。 |
| AC-22 | 含受限个人信息的材料被销售 Agent 请求用于对外回答 | 形成带 `target_use` 的 `unsuitable_for_use` 或拒绝读取；审计/受权用途不受该结论泛化影响。 |
| AC-23 | AI 反复发现“产品说明”实际为未批准会议讨论稿 | 创建只读规则候选，展示定位证据、潜在误报和建议用途限制；不得自动限制、修订或发布。 |
| AC-24 | 业务确认人把候选提升为“未批准讨论稿不可作为销售依据” | 只创建限定项目与销售用途的规则草案；试运行覆盖正例、反例、边界例后才能激活，审计用途不被误伤。 |
| AC-25 | 同一候选被忽略后，新资料再次出现且有不同证据 | 保留忽略原因并重新打开候选；不静默改变已忽略状态或自动激活规则。 |

测试集至少包括：完全/近似重复、同名不同内容、部分/全量替代、条件冲突、时间冲突、例外客户、已过有效期、未来生效、仅复核过期、标题/正文不匹配、目标用途不适用、权威性不足、无权限来源、解析失败、规则冲突、规则撤销、输入并发变化和下游失败。每类至少含正例、反例、边界例和适用时的例外例；第二批集不得参与规则设计，作为复用验收集。

## 10. 研发拆分与待确认决策

建议按依赖分为：

1. **组织与授权层**：组织、预置 `ops` 项目、主体、角色绑定、Agent 模板/安装/项目绑定、委派、运行令牌、有效能力接口与审计；
2. **基础治理层**：来源与版本、解析、对象存储、预算、任务状态机；
3. **诊断与决策层**：片段证据、候选与问题组、对话意见、决策、规则与试运行；
4. **修订与发布层**：派生修订、验证、知识版本、快照、目的地与 outbox；
5. **开放服务层**：v1 API、变更游标/Webhook、首个 Agent 适配；
6. **试点质量层**：金标准资料、回归测试、人工与成本埋点、第二批验证。

进入实现前仍需由负责人确认：单文件与单任务预算单位及上限、默认保留期和失权后的删除时限、首个发布目的地/Agent、业务确认人配置方式、`ops` 是否允许存放组织运营知识及其数据分类、支持访问默认时长、平台人员的 break-glass 流程，以及试点资料的脱敏与模型供应商边界。这些决定会影响配置值和集成方案，不应由模型或前端默认推断。
