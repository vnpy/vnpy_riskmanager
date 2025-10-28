from typing import TYPE_CHECKING

from vnpy.trader.object import OrderRequest

from ..template import RuleTemplate

if TYPE_CHECKING:
    from ..engine import RiskEngine


class OrderSizeRule(RuleTemplate):
    """单笔委托数量上限"""

    name: str = "委托数量风控"

    parameters: dict[str, str] = {"order_size_limit": "单笔委托上限"}

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        super().__init__(risk_engine, setting)

        self.order_size_limit: int = 100

    def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许委托"""
        if req.volume > self.order_size_limit:
            self.write_log(f"单笔委托数量{req.volume}超过上限{self.order_size_limit}")
            return False
        return True
