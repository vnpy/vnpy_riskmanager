# cython: language_level=3
from typing import TYPE_CHECKING
from collections import deque, defaultdict
from libc.time cimport time, time_t

from ..template cimport RuleTemplate

if TYPE_CHECKING:
    from ..engine import RiskEngine


cdef class CancelLimitRule(RuleTemplate):
    """撤单频率控制（Cython 优化版本，使用 C 时间函数）"""

    cdef int cancel_limit
    cdef int cancel_window
    cdef object records  # 改为 object 类型以支持 defaultdict

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        """构造函数"""
        super().__init__(risk_engine, setting)

    cpdef void init_rule(self, dict setting):
        """初始化风控规则"""
        self.cancel_limit = setting.get("cancel_limit", 10)
        self.cancel_window = setting.get("cancel_window", 1)
        self.records = defaultdict(deque)

    cpdef bint check_cancel_allowed(self, object req):
        """检查是否允许撤单"""
        cdef object timestamps
        cdef double current_t
        cdef int count

        timestamps = self.records[req.vt_symbol]
        current_t = <double>time(NULL)  # 使用 C 标准库时间函数

        # 移除超出时间窗口的旧时间戳
        while timestamps and current_t - <double>timestamps[0] > self.cancel_window:
            timestamps.popleft()

        # 检查当前时间窗口内的撤单次数
        count = len(timestamps)
        if count >= self.cancel_limit:
            self.write_log(
                f"撤单过于频繁 {req.vt_symbol}，"
                f"超过每{self.cancel_window}秒{self.cancel_limit}次的限制"
            )
            return False

        # 记录本次撤单时间戳
        timestamps.append(current_t)
        return True
