# cython: language_level=3
import time
from typing import TYPE_CHECKING
from collections import defaultdict

from ..template cimport RuleTemplate

if TYPE_CHECKING:
    from ..engine import RiskEngine


cdef class DuplicateOrderRule(RuleTemplate):
    """重复报单监控（Cython 优化版本）"""

    # 属性声明（public 使其可从 Python 访问，确保 .py 和 .pyx 版本行为一致）
    cdef public int max_duplicate_orders
    cdef public double duplicate_window
    cdef public object records  # defaultdict[str, list[float]]

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        """构造函数"""
        super().__init__(risk_engine, setting)

    cpdef void init_rule(self, dict setting):
        """初始化风控规则"""
        self.max_duplicate_orders = setting.get("max_duplicate_orders", 3)
        self.duplicate_window = setting.get("duplicate_window", 1.0)
        self.records = defaultdict(list)

    cpdef bint check_allowed(self, object req, str gateway_name):
        """检查是否允许委托"""
        cdef str order_key
        cdef double current_time
        cdef object timestamps
        cdef int count

        # 生成委托的唯一标识（合约+方向+开平+价格+数量）
        order_key = (
            f"{req.vt_symbol}|{req.direction.value}|{req.offset.value}|"
            f"{req.price}|{req.volume}"
        )

        current_time = time.time()  # 使用 Python 的 time.time() 而非 C time()，以便在测试中可被 mock
        timestamps = self.records[order_key]

        # 移除超出时间窗口的旧记录
        timestamps[:] = [
            t for t in timestamps if current_time - t <= self.duplicate_window
        ]

        # 检查重复次数
        count = len(timestamps)
        if count >= self.max_duplicate_orders:
            self.write_log(
                f"重复报单：{self.format_req(req)}，"
                f"在 {self.duplicate_window} 秒内已出现 {count} 次"
            )
            return False

        # 记录本次委托时间
        timestamps.append(current_time)
        return True

