from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.object import OrderRequest

from ..template import RuleTemplate


class ActiveOrderRule(RuleTemplate):
    """活动委托数量上限"""

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine, setting: dict) -> None:
        super().__init__(main_engine, event_engine, setting)

        self.active_order_limit: int = setting.get("active_order_limit", 10)

    def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许委托"""
        active_order_count = len(self.main_engine.get_all_active_orders())
        if active_order_count >= self.active_order_limit:
            self.write_log(f"活动委托数量{active_order_count}达到上限{self.active_order_limit}")
            return False
        return True
