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

vnpy_riskmanager是[VeighNa](https://www.vnpy.com)框架的事前风控模块。它提供了一套风控规则引擎，可以在交易过程中对委托下单进行实时检查。所有核心风控规则均使用 **Cython** 编译为C语言扩展，实现了微秒级的风控检查延迟，确保了在高速交易场景下的性能表现。

## 功能特性

本模块内置了多种常用的风控规则，覆盖了从委托合法性到交易频率的多个方面：

- **ActiveOrderRule** - 活动委托数量上限：限制任何时候账户中处于未成交状态的委托总数。
- **DailyLimitRule** - 全天委托/撤单笔数监控：对整个交易日内的总委托和总撤单数量进行限制。
- **DuplicateOrderRule** - 重复报单监控：检测并拦截在极短时间窗口内，针对同一合约的、方向和价格等完全相同的重复委托。
- **OrderSizeRule** - 单笔委托数量上限：限制单笔委托的最大手数，防止因“乌龙指”下出超大订单。
- **OrderValidityRule** - 委托指令合法性监控：在下单前对委托指令进行合法性检查，包括：
  - 检查委托的合约是否存在。
  - 检查委托价格是否为合约最小价格变动的整数倍。
  - 检查委托数量是否超过了交易所规定的单笔最大手数限制。

## 安装

### 环境要求

- Python 3.10 或以上版本
- VeighNa 4.0.0 或以上版本
- C++编译器（用于从源码安装时编译Cython扩展）
  - Windows: [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
  - Linux: `sudo apt-get install build-essential`
  - macOS: `xcode-select --install`

### 安装方法

**方式一：使用 pip 安装（推荐）**

```bash
pip install vnpy_riskmanager
```

**方式二：从源代码安装**

如果你需要进行二次开发，可以从源代码安装。

```bash
# 下载源代码
git clone https://github.com/vnpy/vnpy_riskmanager.git
cd vnpy_riskmanager

# 开发模式安装（修改代码后无需重新安装）
pip install -e .
```
执行 `pip install` 时会自动编译Cython代码。

## 开发与编译

如果你修改了 `.pyx` 文件，或者希望手动编译，可以执行以下步骤：

1.  **安装开发依赖**:
    ```bash
    pip install cython
    ```

2.  **执行编译**:
    在项目根目录下，运行 `setup.py` 的 `build_ext` 命令。
    ```bash
    python setup.py build_ext --inplace
    ```
    `--inplace` 参数会使编译生成的扩展文件（Windows下为`.pyd`，Linux/macOS下为`.so`）直接放在源代码目录中，方便直接运行和调试。

## 使用指南

### 启动风控模块

在VeighNa Trader的启动入口脚本中，添加`RiskManagerApp`即可。

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
    
    main_engine.add_gateway(CtpGateway)
    
    # 添加风控模块（会自动启动）
    main_engine.add_app(RiskManagerApp)
    
    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()
    
    qapp.exec()

if __name__ == "__main__":
    main()
```

## 开发新规则

你可以根据自己的风控需求，轻松地添加新的规则。

### 1. 添加纯Python规则

适合快速开发和逻辑验证。

1.  **创建文件**: 在 `.vntrader`文件夹平级的`rules/` 目录下创建一个新的Python文件，例如 `my_new_rule.py`。
2.  **编写代码**: 文件内容需要包含一个继承自 `RuleTemplate` 的类。类名必须以 `Rule` 结尾。

    ```python
    from vnpy.trader.object import OrderRequest, OrderData
    from ..template import RuleTemplate

    class MyNewRule(RuleTemplate):
        """在这里写规则的中文描述"""

        # 规则的英文名，必须是唯一的
        name: str = "MyNewRule"

        # 定义可配置的参数，用于在UI上显示和修改
        parameters: dict[str, str] = {
            "my_param": "我的参数"
        }

        # 定义需要监控的变量，用于在UI上显示
        variables: dict[str, str] = {
            "my_variable": "我的变量"
        }

        def on_init(self) -> None:
            """初始化方法"""
            self.my_param: int = 100         # 设置参数的默认值
            self.my_variable: int = 0        # 初始化变量

        def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
            """
            核心风控逻辑。
            如果订单允许通过，返回 True。
            如果订单被拦截，调用 self.write_log() 记录原因，并返回 False。
            """
            if req.volume > self.my_param:
                msg = f"委托数量{req.volume}超过参数限制{self.my_param}"
                self.write_log(msg)
                return False
            
            return True

        def on_order(self, order: OrderData) -> None:
            """处理委托回报，用于更新规则的内部状态"""
            self.my_variable += 1
            self.put_event()          # 更新UI显示
    ```
3.  **重启程序**: `RiskEngine` 会在启动时自动发现并加载新规则。

### 2. 添加Cython规则（性能优化）

对于需要处理高频事件（如`on_tick`）或包含复杂计算的规则，推荐使用Cython进行性能优化。

1.  **创建`.pyx`文件**: 在 `.vntrader`文件夹平级的`rules/` 目录下创建Cython文件，例如 `my_new_rule_cy.pyx`。
2.  **编写Cython代码**: 关键在于，需要定义一个 `cdef class` 来实现核心逻辑，并在文件末尾提供一个同名的Python `class` 作为包装器，用于被`RiskEngine`识别。

    ```cython
    # cython: language_level=3
    from vnpy.trader.object import OrderRequest
    from vnpy_riskmanager.template cimport RuleTemplate

    cdef class MyNewRuleCy(RuleTemplate):
        """Cython规则实现"""
        cdef public int my_param
        cdef public int my_variable

        cpdef void on_init(self):
            self.my_param = 100
            self.my_variable = 0

        cpdef bint check_allowed(self, object req, str gateway_name):
            if req.volume > self.my_param:
                msg = f"委托数量{req.volume}超过参数限制{self.my_param}"
                self.write_log(msg)
                return False
            return True

    # Python包装器，用于被RiskEngine发现和加载
    class MyNewRule(MyNewRuleCy):
        name: str = "MyNewRule"
        
        parameters: dict[str, str] = {
            "my_param": "我的参数"
        }
        
        variables: dict[str, str] = {
            "my_variable": "我的变量"
        }
    ```
3.  **创建编译脚本**: 用户自定义的Cython规则不应修改项目本身的`setup.py`。反之，应该为你的规则创建一个独立的编译脚本`rule_setup.py`，并与`.pyx`文件放在同一个`rules/`目录下。

    **`rule_setup.py` 内容示例:**
    ```python
    from setuptools import setup, Extension
    from Cython.Build import cythonize

    # 注意：这里的 name 需要和 .pyx 文件名保持一致
    rule_name = "my_new_rule_cy"

    extensions = [
        Extension(
            name=rule_name,
            sources=[f"{rule_name}.pyx"],
        )
    ]

    setup(
        ext_modules=cythonize(
            extensions,
            compiler_directives={"language_level": "3"}
        )
    )
    ```

4.  **编译**: 在 `rules/` 目录下打开终端，运行 `rule_setup.py` 来编译你的规则。
    ```bash
    # 确保你正处于 rules/ 目录下
    python rule_setup.py build_ext --inplace
    ```
    编译成功后，会在当前目录下生成同名的 `.pyd` (Windows) 或 `.so` (Linux/macOS) 文件。

5.  **重启程序**: `RiskEngine`会自动优先加载编译好的Cython版本规则。


## 运行脚本

`script/` 目录下提供了一些用于测试和演示的实用脚本。

- **`run_trader.py`**: 启动一个加载了本风控模块的VeighNa Trader实例，用于图形界面的功能测试和日常使用。
- **`benchmark_performance.py`**: 用于对比纯Python规则和Cython规则的性能差异。它会模拟大量的 `check_allowed` 调用，并打印出每秒操作数（ops/s）。
- **`test_cython_rules.py`**: 用于对Cython规则进行简单的单元测试，确保其逻辑正确性。
