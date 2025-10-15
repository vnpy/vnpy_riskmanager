import time
from typing import TYPE_CHECKING
from collections import deque

from vnpy.trader.object import OrderRequest, CancelRequest

from ..template import RuleTemplate

if TYPE_CHECKING:
    from ..engine import RiskEngine


class RollingWindowRule(RuleTemplate):
    """滚动窗口委托/撤单笔数监控"""

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        """构造函数"""
        super().__init__(risk_engine, setting)

    def init_rule(self, setting: dict) -> None:
        """初始化风控规则"""
        self.rolling_window_seconds: float = setting.get("rolling_window_seconds", 1.0)
        self.rolling_order_limit: int = setting.get("rolling_order_limit", 20)
        self.rolling_cancel_limit: int = setting.get("rolling_cancel_limit", 20)

        self.order_timestamps: deque[float] = deque()
        self.cancel_timestamps: deque[float] = deque()

    def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许委托"""
        current_time: float = time.time()

        # 移除超出时间窗口的旧时间戳
        while self.order_timestamps and current_time - self.order_timestamps[0] > self.rolling_window_seconds:
            self.order_timestamps.popleft()

        # 检查当前时间窗口内的委托笔数
        if len(self.order_timestamps) >= self.rolling_order_limit:
            self.write_log(
                f"委托频率过快：在 {self.rolling_window_seconds} 秒内已有 "
                f"{len(self.order_timestamps)} 笔，超过限制 {self.rolling_order_limit}"
            )
            return False

        # 记录本次委托时间戳
        self.order_timestamps.append(current_time)
        return True

    def check_cancel_allowed(self, req: CancelRequest) -> bool:
        """检查是否允许撤单"""
        current_time: float = time.time()

        # 移除超出时间窗口的旧时间戳
        while self.cancel_timestamps and current_time - self.cancel_timestamps[0] > self.rolling_window_seconds:
            self.cancel_timestamps.popleft()

        # 检查当前时间窗口内的撤单笔数
        if len(self.cancel_timestamps) >= self.rolling_cancel_limit:
            self.write_log(
                f"撤单频率过快：在 {self.rolling_window_seconds} 秒内已有 "
                f"{len(self.cancel_timestamps)} 笔，超过限制 {self.rolling_cancel_limit}"
            )
            return False

        # 记录本次撤单时间戳
        self.cancel_timestamps.append(current_time)
        return True

