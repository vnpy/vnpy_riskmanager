import time
from typing import TYPE_CHECKING
from collections import deque

from vnpy.trader.object import OrderRequest, CancelRequest

from ..template import RuleTemplate

if TYPE_CHECKING:
    from ..engine import RiskEngine


class RollingWindowRule(RuleTemplate):
    """滚动窗口委托/撤单笔数监控"""

    name: str = "滚动窗口风控"

    parameters: dict[str, str] = {
        "rolling_window_seconds": "滚动窗口时间长度",
        "rolling_order_limit": "滚动窗口内委托笔数上限",
        "rolling_cancel_limit": "滚动窗口内撤单笔数上限"
    }

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        """构造函数"""
        super().__init__(risk_engine, setting)

        self.rolling_window_seconds: float = 1.0
        self.rolling_order_limit: int = 20
        self.rolling_cancel_limit: int = 20

        self._order_timestamps: deque[float] = deque()
        self._cancel_timestamps: deque[float] = deque()

    def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许委托"""
        current_time: float = time.time()

        # 移除超出时间窗口的旧时间戳
        while self._order_timestamps and current_time - self._order_timestamps[0] > self.rolling_window_seconds:
            self._order_timestamps.popleft()

        # 检查当前时间窗口内的委托笔数
        if len(self._order_timestamps) >= self.rolling_order_limit:
            self.write_log(
                f"委托频率过快：在 {self.rolling_window_seconds} 秒内已有 "
                f"{len(self._order_timestamps)} 笔，超过限制 {self.rolling_order_limit}"
            )
            return False

        # 记录本次委托时间戳
        self._order_timestamps.append(current_time)
        return True

    def check_cancel_allowed(self, req: CancelRequest) -> bool:
        """检查是否允许撤单"""
        current_time: float = time.time()

        # 移除超出时间窗口的旧时间戳
        while self._cancel_timestamps and current_time - self._cancel_timestamps[0] > self.rolling_window_seconds:
            self._cancel_timestamps.popleft()

        # 检查当前时间窗口内的撤单笔数
        if len(self._cancel_timestamps) >= self.rolling_cancel_limit:
            self.write_log(
                f"撤单频率过快：在 {self.rolling_window_seconds} 秒内已有 "
                f"{len(self._cancel_timestamps)} 笔，超过限制 {self.rolling_cancel_limit}"
            )
            return False

        # 记录本次撤单时间戳
        self._cancel_timestamps.append(current_time)
        return True
