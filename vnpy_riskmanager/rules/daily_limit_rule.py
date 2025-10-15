from datetime import datetime
from typing import TYPE_CHECKING

from vnpy.trader.object import OrderRequest, CancelRequest

from ..template import RuleTemplate

if TYPE_CHECKING:
    from ..engine import RiskEngine


class DailyLimitRule(RuleTemplate):
    """全天委托/撤单笔数监控"""

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        """构造函数"""
        super().__init__(risk_engine, setting)

    def init_rule(self, setting: dict) -> None:
        """初始化风控规则"""
        self.daily_order_limit: int = setting.get("daily_order_limit", 1000)
        self.daily_cancel_limit: int = setting.get("daily_cancel_limit", 500)

        self.order_count: int = 0
        self.cancel_count: int = 0
        self.current_date: str = ""

    def _check_and_reset_date(self) -> None:
        """检查日期并重置计数器"""
        today: str = datetime.now().strftime("%Y-%m-%d")
        if today != self.current_date:
            self.current_date = today
            self.order_count = 0
            self.cancel_count = 0

    def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许委托"""
        self._check_and_reset_date()

        if self.order_count >= self.daily_order_limit:
            self.write_log(
                f"当日委托笔数 {self.order_count} 已达到上限 {self.daily_order_limit}"
            )
            return False

        self.order_count += 1
        return True

    def check_cancel_allowed(self, req: CancelRequest) -> bool:
        """检查是否允许撤单"""
        self._check_and_reset_date()

        if self.cancel_count >= self.daily_cancel_limit:
            self.write_log(
                f"当日撤单笔数 {self.cancel_count} 已达到上限 {self.daily_cancel_limit}"
            )
            return False

        self.cancel_count += 1
        return True

