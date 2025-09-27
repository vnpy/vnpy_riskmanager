# vnpy_riskmanager 模块改造开发计划

## 目标
根据新的监管要求，对 `vnpy_riskmanager` 模块进行重构，设计标准化的风控规则模板，支持动态加载和扩展新规则，并覆盖委托和撤单两种请求场景，全面提升风险管理的健壮性和灵活性。

---

## Phase 1: 核心功能增强 - 模板与引擎升级

本阶段主要目标是扩展核心的 `RiskTemplate` 和 `RiskEngine`，使其支持撤单风控，为后续功能迭代打下坚实基础。

- [x] **任务 1.1: 升级风控规则模板 `RuleTemplate`**
    - **文件**: `vnpy_riskmanager/template.py`
    - **目标**: 增加对撤单请求 `CancelRequest` 的风控检查能力。
    - **步骤**:
        - 从 `vnpy.trader.object` 中导入 `CancelRequest`。
        - 在 `RuleTemplate` 类中，新增 `check_cancel_allowed(self, req: CancelRequest) -> bool:` 方法。
        - 该方法的默认实现应直接返回 `True`，确保对未实现该检查的旧规则兼容。

- [x] **任务 1.2: 升级风控引擎 `RiskEngine`**
    - **文件**: `vnpy_riskmanager/engine.py`
    - **目标**: 拦截 `MainEngine` 的撤单操作，并执行相应的风控检查。
    - **步骤**:
        - 在 `patch_function` 方法中，仿照 `send_order` 的方式，对 `main_engine.cancel_order` 进行修补（Patch）。
        - 创建新的 `cancel_order` 方法，在该方法内部调用风控检查逻辑。
        - 创建 `check_cancel_allowed(self, req: CancelRequest) -> bool:` 方法，遍历所有已加载的规则实例，并调用其 `check_cancel_allowed` 方法。
        - 如果任何规则返回 `False`，则拦截撤单请求，并记录日志。

---

## Phase 2: 动态化与扩展性改造

本阶段的核心是解决当前风控规则写死在代码中的问题，实现风控规则的动态加载，让系统可以自动发现并加载新的规则，从而做到真正的可插拔。

- [x] **任务 2.1: 实现风控规则动态发现机制**
    - **文件**: `vnpy_riskmanager/engine.py`
    - **目标**: 替换 `load_rules` 方法中硬编码的规则列表，改为自动扫描。
    - **步骤**:
        - 建议在 `vnpy_riskmanager` 中创建一个新的子包 `rules` 用于存放所有风控规则的实现（例如 `vnpy_riskmanager/rules/__init__.py`, `vnpy_riskmanager/rules/order_limit_rule.py`）。
        - 编写一个辅助函数，该函数可以遍历 `vnpy_riskmanager.rules` 包下的所有模块。
        - 在每个模块中，查找所有继承自 `RuleTemplate` 的子类。
        - `load_rules` 方法调用此函数获取所有风控规则类的列表。

- [ ] **任务 2.2: 重构 `RiskEngine` 的规则加载逻辑**
    - **文件**: `vnpy_riskmanager/engine.py`
    - **目标**: 使用新的动态发现机制来加载和实例化所有风控规则。
    - **步骤**:
        - 修改 `load_rules` 方法，移除静态的规则类列表。
        - 调用上一步实现的动态发现函数，获取所有规则类。
        - 遍历规则类列表，创建每个规则的实例对象，并添加到 `self.rules` 列表中。

---

## Phase 3: 新规则实现与配置

在完成核心引擎的改造后，本阶段将着手实现一个新的、基于撤单风控场景的具体规则，以验证新架构的有效性。

- [ ] **任务 3.1: 开发新的撤单频率风控规则**
    - **文件**: `vnpy_riskmanager/rules/cancel_limit_rule.py` (新文件)
    - **目标**: 实现一个用于限制单一合约撤单频率的 `CancelLimitRule`。
    - **步骤**:
        - 创建 `CancelLimitRule` 类，继承自 `RuleTemplate`。
        - 在 `init_rule` 方法中，从配置文件加载频率限制参数（如 `max_cancels_per_second`）。
        - 实现 `check_cancel_allowed` 方法，记录每个合约的撤单时间戳，并检查在指定时间窗口内的撤单次数是否超限。
        - 通过监听 `EVENT_ORDER` 事件来清理已经处理完毕（进入非激活状态）的委托相关记录，避免内存无限增长。

- [ ] **任务 3.2: 更新风控配置文件**
    - **文件**: `risk_engine_setting.json`
    - **目标**: 为新开发的撤单频率规则添加配置项。
    - **步骤**:
        - 在JSON文件中添加新的配置，例如 `"max_cancels_per_second": 10`。

---

## Phase 4: 文档与收尾

最后阶段，我们需要完善项目的文档，确保其他开发者能够轻松理解新的架构，并能独立开发和集成自己的风控规则。

- [ ] **任务 4.1: 更新项目文档**
    - **文件**: `README.md`
    - **目标**: 清晰地说明新版风控模块的架构和扩展方法。
    - **步骤**:
        - 详细描述如何开发一个新的风控规则（创建类、继承模板、实现检查方法）。
        - 说明只需将新规则文件放入 `vnpy_riskmanager/rules` 文件夹下，引擎即可自动加载。
        - 更新配置文件说明，包含所有可用的风控参数。

- [ ] **任务 4.2: 代码审查与最终测试**
    - **目标**: 确保代码质量，并进行完整的集成测试。
    - **步骤**:
        - 对所有修改和新增的代码进行一次全面的 Code Review。
        - 检查代码风格是否遵循 PEP-8 和项目内部规范。
        - 编写或运行测试用例，覆盖委托、撤单、风控触发、风控不触发等多种场景。
