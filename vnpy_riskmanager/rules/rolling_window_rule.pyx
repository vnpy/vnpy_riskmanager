# cython: language_level=3
from typing import TYPE_CHECKING
from collections import deque
from libc.time cimport time

from ..template cimport RuleTemplate

if TYPE_CHECKING:
    from ..engine import RiskEngine


cdef class RollingWindowRule(RuleTemplate):
    """滚动窗口委托/撤单笔数监控（Cython 优化版本）"""

    cdef double rolling_window_seconds
    cdef int rolling_order_limit
    cdef int rolling_cancel_limit
    cdef object order_timestamps  # deque[float]
    cdef object cancel_timestamps  # deque[float]

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        """构造函数"""
        super().__init__(risk_engine, setting)

    cpdef void init_rule(self, dict setting):
        """初始化风控规则"""
        self.rolling_window_seconds = setting.get("rolling_window_seconds", 1.0)
        self.rolling_order_limit = setting.get("rolling_order_limit", 20)
        self.rolling_cancel_limit = setting.get("rolling_cancel_limit", 20)
        self.order_timestamps = deque()
        self.cancel_timestamps = deque()

    cpdef bint check_allowed(self, object req, str gateway_name):
        """检查是否允许委托"""
        cdef double current_time
        cdef int count

        current_time = <double>time(NULL)

        # 移除超出时间窗口的旧时间戳
        while self.order_timestamps and current_time - <double>self.order_timestamps[0] > self.rolling_window_seconds:
            self.order_timestamps.popleft()

        # 检查当前时间窗口内的委托笔数
        count = len(self.order_timestamps)
        if count >= self.rolling_order_limit:
            self.write_log(
                f"委托频率过快：在 {self.rolling_window_seconds} 秒内已有 "
                f"{count} 笔，超过限制 {self.rolling_order_limit}"
            )
            return False

        # 记录本次委托时间戳
        self.order_timestamps.append(current_time)
        return True

    cpdef bint check_cancel_allowed(self, object req):
        """检查是否允许撤单"""
        cdef double current_time
        cdef int count

        current_time = <double>time(NULL)

        # 移除超出时间窗口的旧时间戳
        while self.cancel_timestamps and current_time - <double>self.cancel_timestamps[0] > self.rolling_window_seconds:
            self.cancel_timestamps.popleft()

        # 检查当前时间窗口内的撤单笔数
        count = len(self.cancel_timestamps)
        if count >= self.rolling_cancel_limit:
            self.write_log(
                f"撤单频率过快：在 {self.rolling_window_seconds} 秒内已有 "
                f"{count} 笔，超过限制 {self.rolling_cancel_limit}"
            )
            return False

        # 记录本次撤单时间戳
        self.cancel_timestamps.append(current_time)
        return True

