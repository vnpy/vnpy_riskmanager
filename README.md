# VeighNa框架的事前风控模块

<p align="center">
  <img src ="https://vnpy.oss-cn-shanghai.aliyuncs.com/vnpy-logo.png"/>
</p>

<p align="center">
    <img src ="https://img.shields.io/badge/version-2.0.0-blueviolet.svg"/>
    <img src ="https://img.shields.io/badge/platform-windows|linux|macos-yellow.svg"/>
    <img src ="https://img.shields.io/badge/python-3.10|3.11|3.12|3.13-blue.svg" />
    <img src ="https://img.shields.io/github/license/vnpy/vnpy.svg?color=orange"/>
</p>

## 说明

提供包括交易流控、下单数量、活动委托、撤单总数等规则的统计和限制，有效实现事前风控功能。

## 功能特性

### 基础风控规则

- **OrderFlowRule** - 委托流速控制：限制单位时间内的委托笔数，防止瞬间大量下单
- **OrderSizeRule** - 单笔委托数量上限：限制单笔委托的最大手数
- **ActiveOrderRule** - 活动委托数量上限：限制同时存在的未成交委托数量
- **CancelLimitRule** - 撤单频率控制：限制单一合约在时间窗口内的撤单次数

### 高级风控规则

- **OrderValidityRule** - 委托指令合法性监控：
  - 检查合约是否存在
  - 检查委托价格是否为最小变动价位的整数倍
  - 检查委托数量是否超过单笔最大手数限制

- **DuplicateOrderRule** - 重复报单监控：检测并拦截短时间内完全相同的重复委托

- **DailyLimitRule** - 全天委托/撤单笔数监控：对整个交易日内的总委托和总撤单数量进行限制

- **RollingWindowRule** - 滚动窗口委托/撤单笔数监控：对短时间内的委托和撤单频率进行限制

### 性能优化

所有风控规则均使用 **Cython** 编译为 C 扩展，实现微秒级的风控检查延迟：
- OrderSizeRule: ~1000万 ops/s（整数比较）
- CancelLimitRule: ~5万 ops/s（时间窗口滑动）

## 安装

### 环境要求

- Python 3.10 或以上版本
- VeighNa 4.0.0 或以上版本
- C 编译器（用于编译 Cython 扩展）
  - Windows: MSVC (Visual Studio Build Tools)
  - Linux: gcc
  - macOS: clang

### 安装方法

**方式一：使用 pip 安装发布版本**

```bash
pip install vnpy_riskmanager
```

**方式二：从源代码安装**

```bash
# 下载源代码
git clone https://github.com/vnpy/vnpy_riskmanager.git
cd vnpy_riskmanager

# 安装（会自动编译 Cython 扩展）
pip install .
```

**方式三：开发模式安装**

```bash
# 开发模式安装（修改代码后无需重新安装）
pip install -e .
```

## 使用指南

### 启动风控模块

在 VeighNa Trader 中加载风控模块：

```python
from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

from vnpy_ctp import CtpGateway
from vnpy_riskmanager import RiskManagerApp

def main():
    qapp = create_qapp()
    
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    
    # 添加交易接口
    main_engine.add_gateway(CtpGateway)
    
    # 添加风控模块（会自动启动）
    main_engine.add_app(RiskManagerApp)
    
    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()
    
    qapp.exec()

if __name__ == "__main__":
    main()
```

### 配置风控参数

风控参数通过 `risk_engine_setting.json` 文件配置，该文件位于用户目录的 `.vntrader` 文件夹下。

**配置示例**：

```json
{
    "active_order_limit": 10,
    "order_size_limit": 100,
    "order_flow_limit": 10,
    "order_flow_clear": 1,
    "cancel_limit": 10,
    "cancel_window": 1,
    "check_contract_exists": true,
    "check_price_tick": true,
    "check_volume_limit": false,
    "max_order_volume": 1000,
    "max_duplicate_orders": 3,
    "duplicate_window": 1.0,
    "daily_order_limit": 1000,
    "daily_cancel_limit": 500,
    "rolling_window_seconds": 1.0,
    "rolling_order_limit": 20,
    "rolling_cancel_limit": 20
}
```

**参数说明**：

| 参数 | 说明 | 默认值 |
|-----|------|--------|
| `active_order_limit` | 活动委托数量上限 | 10 |
| `order_size_limit` | 单笔委托数量上限 | 100 |
| `order_flow_limit` | 流速控制：单位时间内委托笔数上限 | 10 |
| `order_flow_clear` | 流速控制：统计周期（秒） | 1 |
| `cancel_limit` | 单合约撤单次数上限 | 10 |
| `cancel_window` | 撤单统计窗口（秒） | 1 |
| `check_contract_exists` | 是否检查合约存在性 | true |
| `check_price_tick` | 是否检查价格合法性 | true |
| `check_volume_limit` | 是否检查委托数量上限 | false |
| `max_order_volume` | 单笔最大委托手数 | 1000 |
| `max_duplicate_orders` | 允许的重复委托次数 | 3 |
| `duplicate_window` | 重复检测时间窗口（秒） | 1.0 |
| `daily_order_limit` | 全天委托笔数上限 | 1000 |
| `daily_cancel_limit` | 全天撤单笔数上限 | 500 |
| `rolling_window_seconds` | 滚动窗口时间长度（秒） | 1.0 |
| `rolling_order_limit` | 滚动窗口内委托笔数上限 | 20 |
| `rolling_cancel_limit` | 滚动窗口内撤单笔数上限 | 20 |

### 在界面中使用

1. 启动 VeighNa Trader 后，在菜单栏选择 **功能 -> 风控管理**
2. 在弹出的风控管理窗口中：
   - 勾选"启用风控"复选框来启用/禁用风控功能
   - 调整各项风控参数
   - 点击"保存"按钮保存配置

## 开发新规则

### 方式一：仅 Python 实现（快速原型）

适合快速开发和测试新的风控逻辑。

**步骤**：

1. 在 `vnpy_riskmanager/rules/` 目录下创建新的 `.py` 文件，例如 `my_custom_rule.py`

2. 继承 `RuleTemplate` 并实现风控逻辑：

```python
from typing import TYPE_CHECKING

from vnpy.trader.object import OrderRequest, CancelRequest

from ..template import RuleTemplate

if TYPE_CHECKING:
    from ..engine import RiskEngine


class MyCustomRule(RuleTemplate):
    """自定义风控规则"""

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        """构造函数"""
        super().__init__(risk_engine, setting)

    def init_rule(self, setting: dict) -> None:
        """初始化风控规则"""
        self.my_limit: int = setting.get("my_limit", 100)

    def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许委托"""
        if req.volume > self.my_limit:
            self.write_log(f"委托数量 {req.volume} 超过限制 {self.my_limit}")
            return False
        return True
```

3. **无需手动注册** - `RiskEngine` 会自动发现并加载 `rules/` 目录下所有继承自 `RuleTemplate` 的规则类

4. 在 `risk_engine_setting.json` 中添加规则所需的配置参数：

```json
{
    "my_limit": 100
}
```

5. 重启应用即可生效

### 方式二：Cython 优化（性能关键路径）

适合对性能要求高的风控规则，可获得 10-100 倍的性能提升。

**步骤**：

1. 首先创建 `.py` 文件实现基础逻辑（参考方式一）

2. 创建对应的 `.pyx` 文件，使用 Cython 语法优化：

```python
# cython: language_level=3
from typing import TYPE_CHECKING

from ..template cimport RuleTemplate

if TYPE_CHECKING:
    from ..engine import RiskEngine


cdef class MyCustomRule(RuleTemplate):
    """自定义风控规则（Cython 优化版本）"""

    # 属性声明（public 使其可从 Python 访问，确保 .py 和 .pyx 版本行为一致）
    cdef public int my_limit

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        """构造函数"""
        super().__init__(risk_engine, setting)

    cpdef void init_rule(self, dict setting):
        """初始化风控规则"""
        self.my_limit = setting.get("my_limit", 100)

    cpdef bint check_allowed(self, object req, str gateway_name):
        """检查是否允许委托"""
        if req.volume > self.my_limit:
            self.write_log(f"委托数量 {req.volume} 超过限制 {self.my_limit}")
            return False
        return True
```

3. 在 `setup.py` 中添加 Extension 配置：

```python
from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    # ... 现有的扩展 ...
    Extension(
        "vnpy_riskmanager.rules.my_custom_rule",
        ["vnpy_riskmanager/rules/my_custom_rule.pyx"],
    ),
]

setup(
    ext_modules=cythonize(extensions, compiler_directives={"language_level": "3"}),
)
```

4. 重新编译安装：

```bash
pip install -e .
```

5. **Python 会自动优先加载编译后的 `.pyd` 文件**，无需修改 `engine.py`

### Cython 开发注意事项

为确保 `.py` 和 `.pyx` 版本行为一致，并支持完整的测试覆盖：

1. **属性声明使用 `cdef public`**
   ```python
   # 使 Cython 属性可从 Python 访问，便于测试
   cdef public int my_limit
   ```

2. **时间相关功能使用 Python 的 `time.time()`**
   ```python
   import time  # 不要用 from libc.time cimport time
   current_time = time.time()  # 使用 Python 的 time.time() 而非 C time()，以便在测试中可被 mock
   ```

3. **合约查询直接调用 `risk_engine`**
   ```python
   contract = self.risk_engine.get_contract(req.vt_symbol)
   ```

4. **保持接口一致**
   - `.py` 和 `.pyx` 文件的类名、方法签名必须完全一致
   - 确保测试用例能同时验证两个版本

### 性能基准测试

运行性能基准测试：

```bash
python benchmark_cython.py
```

输出示例：
```
OrderSizeRule: 10000000 checks in 1.23s (8130081 ops/s)
CancelLimitRule: 100000 checks in 2.15s (46511 ops/s)
```

## 测试

运行完整测试套件：

```bash
# 安装测试依赖
pip install pytest

# 运行所有测试
pytest tests/ -v

# 运行特定规则的测试
pytest tests/rules/test_order_validity_rule.py -v
```

## 代码质量检查

```bash
# Ruff 代码检查
ruff check .

# Mypy 类型检查
mypy vnpy_riskmanager
```
