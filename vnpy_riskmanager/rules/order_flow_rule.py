from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.object import OrderRequest

from ..template import RuleTemplate


class OrderFlowRule(RuleTemplate):
    """委托流速控制"""

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine, setting: dict) -> None:
        super().__init__(main_engine, event_engine, setting)

        self.order_flow_count: int = 0
        self.order_flow_limit: int = setting.get("order_flow_limit", 10)
        self.order_flow_clear: int = setting.get("order_flow_clear", 1)
        self.order_flow_timer: int = 0

    def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许委托"""
        self.order_flow_count += 1
        if self.order_flow_count > self.order_flow_limit:
            self.write_log(f"委托流速过快，超过每{self.order_flow_clear}秒{self.order_flow_limit}笔的限制")
            return False
        return True
