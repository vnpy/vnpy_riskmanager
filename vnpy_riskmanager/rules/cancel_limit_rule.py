import time
from collections import deque, defaultdict

from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.object import CancelRequest

from ..template import RuleTemplate


class CancelLimitRule(RuleTemplate):
    """撤单频率控制"""

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine, setting: dict) -> None:
        """构造函数"""
        super().__init__(main_engine, event_engine, setting)

        self.cancel_limit: int = 10
        self.cancel_window: int = 1
        self.records: dict[str, deque] = defaultdict(deque)

    def init_rule(self, setting: dict) -> None:
        """初始化风控规则"""
        self.cancel_limit = setting.get("cancel_limit", 10)
        self.cancel_window = setting.get("cancel_window", 1)

    def check_cancel_allowed(self, req: CancelRequest) -> bool:
        """检查是否允许撤单"""
        timestamps: deque = self.records[req.vt_symbol]
        current_t: float = time.time()

        # 移除超出时间窗口的旧时间戳
        while timestamps and current_t - timestamps[0] > self.cancel_window:
            timestamps.popleft()

        # 检查当前时间窗口内的撤单次数
        if len(timestamps) >= self.cancel_limit:
            self.write_log(
                f"撤单过于频繁 {req.vt_symbol}，"
                f"超过每{self.cancel_window}秒{self.cancel_limit}次的限制"
            )
            return False

        # 记录本次撤单时间戳
        timestamps.append(current_t)
        return True
