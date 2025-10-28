from vnpy.trader.object import OrderRequest, OrderData

from ..template import RuleTemplate


class ActiveOrderRule(RuleTemplate):
    """活动委托数量检查风控规则"""

    name: str = "活动委托检查"

    parameters: dict[str, str] = {
        "active_order_limit": "活动委托上限"
    }

    variables: dict[str, str] = {
        "active_order_count": "活动委托数量"
    }

    def on_init(self) -> None:
        """初始化"""
        # 默认参数
        self.active_order_limit: int = 50

        # 活动委托
        self.active_orders: dict[str, OrderData] = {}

        # 数量统计
        self.active_order_count: int = 0

    def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许委托"""
        if self.active_order_count >= self.active_order_limit:
            self.write_log(f"活动委托数量{self.active_order_count}达到上限{self.active_order_limit}")
            return False

        return True

    def on_order(self, order: OrderData) -> None:
        """委托推送"""
        if order.is_active():
            self.active_orders[order.vt_orderid] = order
        elif order.vt_orderid in self.active_orders:
            self.active_orders.pop(order.vt_orderid)

        self.active_order_count = len(self.active_orders)

        self.put_event()
