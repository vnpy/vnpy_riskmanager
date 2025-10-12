from typing import TYPE_CHECKING

from vnpy.trader.object import OrderRequest

from ..template import RuleTemplate

if TYPE_CHECKING:
    from ..engine import RiskEngine


class ActiveOrderRule(RuleTemplate):
    """活动委托数量上限"""

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        super().__init__(risk_engine, setting)

    def init_rule(self, setting: dict) -> None:
        """初始化风控规则"""
        self.active_order_limit: int = setting.get("active_order_limit", 10)

    def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许委托"""
        active_order_count: int = len(self.get_all_active_orders())
        if active_order_count >= self.active_order_limit:
            self.write_log(f"活动委托数量{active_order_count}达到上限{self.active_order_limit}")
            return False
        return True
