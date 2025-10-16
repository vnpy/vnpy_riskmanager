# cython: language_level=3
from typing import TYPE_CHECKING
from datetime import datetime

from ..template cimport RuleTemplate

if TYPE_CHECKING:
    from ..engine import RiskEngine


cdef class DailyLimitRule(RuleTemplate):
    """全天委托/撤单笔数监控（Cython 优化版本）"""

    # 属性声明（public 使其可从 Python 访问，确保 .py 和 .pyx 版本行为一致）
    cdef public int daily_order_limit
    cdef public int daily_cancel_limit
    cdef public int order_count
    cdef public int cancel_count
    cdef public str current_date

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        """构造函数"""
        super().__init__(risk_engine, setting)

    cpdef void init_rule(self, dict setting):
        """初始化风控规则"""
        self.daily_order_limit = setting.get("daily_order_limit", 1000)
        self.daily_cancel_limit = setting.get("daily_cancel_limit", 500)
        self.order_count = 0
        self.cancel_count = 0
        self.current_date = ""

    cdef void _check_and_reset_date(self):
        """检查日期并重置计数器"""
        cdef str today
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self.current_date:
            self.current_date = today
            self.order_count = 0
            self.cancel_count = 0

    cpdef bint check_allowed(self, object req, str gateway_name):
        """检查是否允许委托"""
        self._check_and_reset_date()

        if self.order_count >= self.daily_order_limit:
            self.write_log(
                f"当日委托笔数 {self.order_count} 已达到上限 {self.daily_order_limit}"
            )
            return False

        self.order_count += 1
        return True

    cpdef bint check_cancel_allowed(self, object req):
        """检查是否允许撤单"""
        self._check_and_reset_date()

        if self.cancel_count >= self.daily_cancel_limit:
            self.write_log(
                f"当日撤单笔数 {self.cancel_count} 已达到上限 {self.daily_cancel_limit}"
            )
            return False

        self.cancel_count += 1
        return True

