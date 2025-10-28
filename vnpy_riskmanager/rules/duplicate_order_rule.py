import time
from typing import TYPE_CHECKING
from collections import defaultdict

from vnpy.trader.object import OrderRequest

from ..template import RuleTemplate

if TYPE_CHECKING:
    from ..engine import RiskEngine


class DuplicateOrderRule(RuleTemplate):
    """重复报单监控"""

    name: str = "重复报单风控"

    parameters: dict[str, str] = {
        "max_duplicate_orders": "重复报单上限",
        "duplicate_window": "统计时间窗口"
    }

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        """构造函数"""
        super().__init__(risk_engine, setting)

        self.max_duplicate_orders: int = 3
        self.duplicate_window: float = 1.0
        self._records: dict[str, list[float]] = defaultdict(list)

    def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许委托"""
        # 生成委托的唯一标识（合约+方向+开平+价格+数量）
        order_key: str = (
            f"{req.vt_symbol}|{req.direction.value}|{req.offset.value}|"
            f"{req.price}|{req.volume}"
        )

        current_time: float = time.time()
        timestamps: list[float] = self._records[order_key]

        # 移除超出时间窗口的旧记录
        timestamps[:] = [
            t for t in timestamps if current_time - t <= self.duplicate_window
        ]

        # 检查重复次数
        if len(timestamps) >= self.max_duplicate_orders:
            self.write_log(
                f"重复报单：{self.format_req(req)}，"
                f"在 {self.duplicate_window} 秒内已出现 {len(timestamps)} 次"
            )
            return False

        # 记录本次委托时间
        timestamps.append(current_time)
        return True
