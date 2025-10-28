from typing import TYPE_CHECKING

from vnpy.trader.object import OrderRequest, OrderData

from ..template import RuleTemplate

if TYPE_CHECKING:
    from ..engine import RiskEngine


class ActiveOrderRule(RuleTemplate):
    """活动委托数量上限"""

    name: str = "活动委托风控"

    parameters: dict[str, str] = {
        "active_order_limit": "活动委托上限"
    }

    variables: dict[str, str] = {
        "_active_order_count": "当前活动委托"
    }

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        super().__init__(risk_engine, setting)

        self.active_order_limit: int = 10

        self._active_orders: dict[str, OrderData] = {}
        self._active_order_count: int = 0

    def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许委托"""
        if self._active_order_count >= self.active_order_limit:
            self.write_log(f"活动委托数量{self._active_order_count}达到上限{self.active_order_limit}")
            return False
        return True

    def on_order(self, order: OrderData) -> None:
        """"""
        if order.is_active():
            self._active_orders[order.vt_orderid] = order
        elif order.vt_orderid in self._active_orders:
            self._active_orders.pop(order.vt_orderid)

        self._active_order_count = len(self._active_orders)
