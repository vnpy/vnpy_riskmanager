from typing import TYPE_CHECKING

from vnpy.trader.object import OrderRequest

from ..template import RuleTemplate

if TYPE_CHECKING:
    from ..engine import RiskEngine


class OrderFlowRule(RuleTemplate):
    """委托流速控制"""

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        super().__init__(risk_engine, setting)

    def init_rule(self, setting: dict) -> None:
        """初始化风控规则"""
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

    def on_timer(self) -> None:
        """定时检查，清理委托流速计数"""
        self.order_flow_timer += 1
        if self.order_flow_timer >= self.order_flow_clear:
            self.order_flow_count = 0
            self.order_flow_timer = 0
