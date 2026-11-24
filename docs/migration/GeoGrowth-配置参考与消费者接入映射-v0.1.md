# GeoGrowth 配置参考与 S5 接入映射 v0.1

日期：2026-10-11。按用户指定只读参考 GeoGrowth，未修改该仓库或其部署配置。

## 参考来源

仓库：[lidongjunsean-star/GeoGrowth](https://github.com/lidongjunsean-star/GeoGrowth)，读取固定版本 `d474f8833a11b12bb8f6b701753d898774e06299`。本机常用项目目录未找到同名 checkout，通过已连接 GitHub 仓库读取代码和 `.env.example`；没有读取部署中的真实 `.env`，不据此声称 GeoGrowth 云凭据已验证。

| 来源文件 | 核对结果 |
| --- | --- |
| [app/core/config.py](https://github.com/lidongjunsean-star/GeoGrowth/blob/d474f8833a11b12bb8f6b701753d898774e06299/app/core/config.py) | 百炼/DashScope 的键名、知识库选择、租户知识库白名单配置 |
| [.env.example](https://github.com/lidongjunsean-star/GeoGrowth/blob/d474f8833a11b12bb8f6b701753d898774e06299/.env.example) | 示例键名；不是运行环境的有效凭据证明 |
| [app/integrations/aliyun_kb_client.py](https://github.com/lidongjunsean-star/GeoGrowth/blob/d474f8833a11b12bb8f6b701753d898774e06299/app/integrations/aliyun_kb_client.py) | 当前直接调用阿里百炼检索，结果使用 kb_id、doc_id、chunk_id 等定位；部分片段 ID 缺失时派生摘要 ID |
| [app/services/evidence_retriever.py](https://github.com/lidongjunsean-star/GeoGrowth/blob/d474f8833a11b12bb8f6b701753d898774e06299/app/services/evidence_retriever.py) | 研究检索召回与证据聚合入口，保留供应商定位字段 |
| [app/services/price_evidence_retriever.py](https://github.com/lidongjunsean-star/GeoGrowth/blob/d474f8833a11b12bb8f6b701753d898774e06299/app/services/price_evidence_retriever.py) | 根据价格意图、型号/目录召回价格证据，并非已经确认的七项条件知识查询 |
| [app/db/models/content_planning.py](https://github.com/lidongjunsean-star/GeoGrowth/blob/d474f8833a11b12bb8f6b701753d898774e06299/app/db/models/content_planning.py) | 策划项目采用 Integer 主键，另有租户隔离字段，不等于治理业务项目 UUID |

此前在 KnowledgeHub 定位到的“供 GeoGrowth 等调用”的旧检索代理，只证明旧接口存在。本次读取 GeoGrowth 当前客户端后确认，其主要检索实现直接访问百炼，不能据旧接口注释认定当前流量已走 KnowledgeHub 或 S5。

## 配置兼容入口

本项目 `KnowledgeHubConfig.load(path, profile='geogrowth')` 新增显式 GeoGrowth 格式；默认 `knowledgehub` 的解析范围和默认选择保留。

| GeoGrowth .env 键名 | 本项目配置字段 | 用途 |
| --- | --- | --- |
| DASHSCOPE_API_KEY | api_key（BAILIAN_API_KEY 别名） | 资料模型分析凭据 |
| ALIBABA_CLOUD_ACCESS_KEY_ID | access_key_id（ALIYUN_ACCESS_KEY_ID 别名） | 提供商访问配置 |
| ALIBABA_CLOUD_ACCESS_KEY_SECRET | access_key_secret（ALIYUN_ACCESS_KEY_SECRET 别名） | 提供商访问配置 |
| WORKSPACE_ID | workspace_id（BAILIAN_WORKSPACE_ID 别名） | 云业务空间定位 |
| KNOWLEDGE_BASE_ID | knowledge_base_id | 云知识库定位元数据；公开状态仅显示是否配置 |

接受原有 BAILIAN_MODEL_NAME、BAILIAN_ENDPOINT、OSS_BUCKET_NAME、OSS_ENDPOINT 等提供商键名。GeoGrowth 示例没有直接 OSS 桶/地址配置；仅有阿里访问密钥不表示本项目 OSS 上传已配置。模型仍由 BAILIAN_MODEL_NAME 选择，未填沿用当前 qwen-plus 默认，不自动把 GeoGrowth 某角色的模型或缓存策略引入资料治理。

仅加载所选文件的允许键；文件中已声明的键允许同名进程环境覆盖。别名和规范键同时非空且不同，返回 provider_configuration_alias_conflict，不输出值、不猜测使用哪个账号；同值可以共存。数据库 URL、登录签名密钥、OPEN_API_KEY、Redis、其他模型/渠道凭据及租户白名单不导入提供商配置。

```powershell
# 只读预检：显式指向你选择的真实 GeoGrowth 本地配置文件，不在命令中写凭据。
.venv/Scripts/python.exe -m knowledge_governance.business_onboarding --database migration-output/local-workspace.db --knowledge-config <selected-GeoGrowth.env> --knowledge-profile geogrowth --output <new-report.json>

# 本地服务：GeoGrowth profile 要求显式 --knowledge-config。
.venv/Scripts/python.exe -m knowledge_governance.local_server --knowledge-config <selected-GeoGrowth.env> --knowledge-profile geogrowth
```

`--knowledge-profile geogrowth` 不会搜索或复制其他项目的真实配置文件，也不会变更当前运行服务。启动未提供所选配置会在创建工作区之前拒绝。公开状态显示来源和 model_ready/storage_ready/knowledge_base_configured，不显示 API Key、Access Key、workspace 或 knowledge base ID；就绪标志仍仅代表配置项存在。配置读取和只读预检不发送云请求。

[合成键名样例](../examples/geogrowth-provider.synthetic.env)只用于兼容性测试，任何 synthetic 值都不是有效凭据。预检证据 `migration-output/s5-geogrowth-config/synthetic-workspace-report.json` 使用该合成文件，不代表真实部署验收。

## 业务 ID 映射边界

消费者名称可明确为 GeoGrowth；它的 `research-agent`/证据检索及价格证据补取入口是可参考的业务调用点。接入需保留以下显式映射：

| GeoGrowth / 阿里字段 | 治理侧对象 | 接入处理 |
| --- | --- | --- |
| tenant_id | organization_id | 使用核对过的租户映射，不导入旧权限 |
| 策划 project_id（整数） | project_id（UUID） | 建立显式外部项目映射，不能强制转换或按同名项目猜测 |
| WORKSPACE_ID、KNOWLEDGE_BASE_ID | 提供商空间/索引 | 保留云定位，不当作治理项目或知识 ID |
| kb_id/doc_id/chunk_id | 来源/来源版本及片段证据定位 | 只有能核对版本和归属的映射才进入治理来源；派生文本摘要片段 ID 不是已发布知识证明 |
| 已验证、已明确发布的知识根 | knowledge_item_id（UUID） | 使用第三批查询和变更订阅范围；可从治理库发现实际 ID |
| Query / 产品型号 / 地区等研究上下文 | 显式日期和条件 | 按业务提供的完整条件投影，不从自由文本或价格意图补造客户、单位、税、币种、有效日期 |

GeoGrowth 的 KNOWLEDGE_BASE_IDS/KNOWLEDGE_BASE_TENANTS 是旧系统知识库选择与租户白名单配置，不替代新安装、绑定、人员委派、运行令牌或已发布状态。召回候选与旧 EvidencePack 不直接作为新治理授权结果。

当前默认治理 SQLite 工作区仍在 0009，尚无知识/发布表；副本升级到 0030 已验证，但没有自动生成或发布知识。本批配置兼容不能消除这个业务数据缺口。下一步沿用已有阿里配置或明确选定的 GeoGrowth 配置，升级实际工作区并完成来源核验/知识确认发布，再按实际 ID 接入 GeoGrowth 的治理查询适配器。

## 验证

新增 8 项专项通过：GeoGrowth 别名加载、默认 KnowledgeHub 不隐式读别名、密钥与云 ID 脱敏、同名环境覆盖、冲突拒绝、同值兼容、显式 OSS/模型配置、非法 profile 和启动缺少显式文件拒绝。没有新增数据库迁移，没有改动 GeoGrowth，也没有调用云端或切流。

最终完整 574 项回归通过（272.627 秒），日志 `migration-output/s5-geogrowth-config-regression.log`；编译、模型检查及差异格式检查通过。配置兼容不涉及新增迁移，本批没有 MySQL 在线检查或真实阿里云调用。

## 实际工作区进展（2026-10-11）

默认治理 SQLite 工作区已在保留备份后实际升级到 0030，旧记录完整保留；仍无知识/发布条目，现有验收来源不能直接生成当前支持的已确认价格知识。参见 [实际升级与业务资料就绪核查](../api/S5-实际工作区升级与业务资料就绪核查-v0.1.md)。本文前述 0009 为升级前状态。
