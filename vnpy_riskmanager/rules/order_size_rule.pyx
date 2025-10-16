# cython: language_level=3
from typing import TYPE_CHECKING

from ..template cimport RuleTemplate

if TYPE_CHECKING:
    from ..engine import RiskEngine


cdef class OrderSizeRule(RuleTemplate):
    """单笔委托数量上限（Cython 优化版本）"""

    # 属性声明（public 使其可从 Python 访问，确保 .py 和 .pyx 版本行为一致）
    cdef public int order_size_limit

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        super().__init__(risk_engine, setting)

    cpdef void init_rule(self, dict setting):
        """初始化风控规则"""
        self.order_size_limit = setting.get("order_size_limit", 100)

    cpdef bint check_allowed(self, object req, str gateway_name):
        """检查是否允许委托"""
        if req.volume > self.order_size_limit:
            self.write_log(f"单笔委托数量{req.volume}超过上限{self.order_size_limit}")
            return False
        return True
