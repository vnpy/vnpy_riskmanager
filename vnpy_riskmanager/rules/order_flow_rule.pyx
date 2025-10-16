# cython: language_level=3
from typing import TYPE_CHECKING

from ..template cimport RuleTemplate

if TYPE_CHECKING:
    from ..engine import RiskEngine


cdef class OrderFlowRule(RuleTemplate):
    """委托流速控制（Cython 优化版本）"""

    # 属性声明（public 使其可从 Python 访问，确保 .py 和 .pyx 版本行为一致）
    cdef public int order_flow_count
    cdef public int order_flow_limit
    cdef public int order_flow_clear
    cdef public int order_flow_timer

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        super().__init__(risk_engine, setting)

    cpdef void init_rule(self, dict setting):
        """初始化风控规则"""
        self.order_flow_count = 0
        self.order_flow_limit = setting.get("order_flow_limit", 10)
        self.order_flow_clear = setting.get("order_flow_clear", 1)
        self.order_flow_timer = 0

    cpdef bint check_allowed(self, object req, str gateway_name):
        """检查是否允许委托"""
        self.order_flow_count += 1
        if self.order_flow_count > self.order_flow_limit:
            self.write_log(f"委托流速过快，超过每{self.order_flow_clear}秒{self.order_flow_limit}笔的限制")
            return False
        return True

    cpdef void on_timer(self):
        """定时检查，清理委托流速计数"""
        self.order_flow_timer += 1
        if self.order_flow_timer >= self.order_flow_clear:
            self.order_flow_count = 0
            self.order_flow_timer = 0
