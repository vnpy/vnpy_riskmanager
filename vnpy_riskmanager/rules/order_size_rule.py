from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.object import OrderRequest

from ..template import RuleTemplate


class OrderSizeRule(RuleTemplate):
    """单笔委托数量上限"""

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine, setting: dict) -> None:
        super().__init__(main_engine, event_engine, setting)

        self.order_size_limit: int = setting.get("order_size_limit", 100)

    def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许委托"""
        if req.volume > self.order_size_limit:
            self.write_log(f"单笔委托数量{req.volume}超过上限{self.order_size_limit}")
            return False
        return True
