from datetime import datetime
from typing import TYPE_CHECKING

from vnpy.trader.object import OrderRequest, CancelRequest

from ..template import RuleTemplate

if TYPE_CHECKING:
    from ..engine import RiskEngine


class DailyLimitRule(RuleTemplate):
    """全天委托/撤单笔数监控"""

    name: str = "全天必输风控"

    parameters: dict[str, str] = {
        "daily_order_limit": "每日委托上限",
        "daily_cancel_limit": "每日撤单上限"
    }
    variables: dict[str, str] = {
        "_order_count": "今日委托次数",
        "_cancel_count": "今日撤单次数"
    }

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        """构造函数"""
        super().__init__(risk_engine, setting)

        self.daily_order_limit: int = 1000
        self.daily_cancel_limit: int = 500

        self._order_count: int = 0
        self._cancel_count: int = 0
        self._current_date: str = ""

    def _check_and_reset_date(self) -> None:
        """检查日期并重置计数器"""
        today: str = datetime.now().strftime("%Y-%m-%d")
        if today != self._current_date:
            self._current_date = today
            self._order_count = 0
            self._cancel_count = 0

    def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许委托"""
        self._check_and_reset_date()

        if self._order_count >= self.daily_order_limit:
            self.write_log(
                f"当日委托笔数 {self._order_count} 已达到上限 {self.daily_order_limit}"
            )
            return False

        self._order_count += 1
        return True

    def check_cancel_allowed(self, req: CancelRequest) -> bool:
        """检查是否允许撤单"""
        self._check_and_reset_date()

        if self._cancel_count >= self.daily_cancel_limit:
            self.write_log(
                f"当日撤单笔数 {self._cancel_count} 已达到上限 {self.daily_cancel_limit}"
            )
            return False

        self._cancel_count += 1
        return True
