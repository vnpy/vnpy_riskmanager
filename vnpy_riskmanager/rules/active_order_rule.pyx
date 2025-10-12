# cython: language_level=3
from typing import TYPE_CHECKING

from ..template cimport RuleTemplate

if TYPE_CHECKING:
    from ..engine import RiskEngine


cdef class ActiveOrderRule(RuleTemplate):
    """活动委托数量上限（Cython 优化版本）"""

    cdef int active_order_limit

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        super().__init__(risk_engine, setting)

    cpdef void init_rule(self, dict setting):
        """初始化风控规则"""
        self.active_order_limit = setting.get("active_order_limit", 10)

    cpdef bint check_allowed(self, object req, str gateway_name):
        """检查是否允许委托"""
        cdef int active_order_count = len(self.get_all_active_orders())
        if active_order_count >= self.active_order_limit:
            self.write_log(f"活动委托数量{active_order_count}达到上限{self.active_order_limit}")
            return False
        return True
