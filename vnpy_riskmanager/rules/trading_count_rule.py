from collections import defaultdict

from vnpy.trader.object import OrderRequest, OrderData
from vnpy.trader.constant import OrderStatus

from ..template import RuleTemplate


class TradingCountRule(RuleTemplate):
    """报撤笔数检查风控规则"""

    name: str = "报撤笔数检查"

    parameters: dict[str, str] = {
        "total_order_limit": "全天委托上限",
        "total_cancel_limit": "全天撤单上限"
    }

    variables: dict[str, str] = {
        "total_order_count": "全天委托笔数",
        "total_cancel_count": "全天撤单笔数",
        "contract_order_count": "合约委托笔数",
        "contract_cancel_count": "合约撤单笔数"
    }

    def on_init(self) -> None:
        """初始化"""
        # 默认参数
        self.total_order_limit: int = 1000
        self.total_cancel_limit: int = 800

        # 委托号记录
        self.all_orderids: set[str] = set()
        self.cancel_orderids: set[str] = set()

        # 数量统计
        self.total_order_count: int = 0
        self.total_cancel_count: int = 0

        self.contract_order_count: dict[str, int] = defaultdict(int)
        self.contract_cancel_count: dict[str, int] = defaultdict(int)

    def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许委托"""
        if self.total_order_count >= self.total_order_limit:
            self.write_log(f"全天委托笔数{self.total_order_count}达到上限{self.total_order_limit}")
            return False

        if self.total_cancel_count >= self.total_cancel_limit:
            self.write_log(f"全天撤单笔数{self.total_cancel_count}达到上限{self.total_cancel_limit}")
            return False

        return True

    def on_order(self, order: OrderData) -> None:
        """委托推送"""
        if order.vt_orderid not in self.all_orderids:
            self.all_orderids.add(order.vt_orderid)
            self.total_order_count += 1

            self.contract_order_count[order.vt_symbol] += 1

            self.put_event()
        elif (
            order.status == OrderStatus.CANCELLED
            and order.vt_orderid not in self.cancel_orderids
        ):
            self.cancel_orderids.add(order.vt_orderid)
            self.total_cancel_count += 1

            self.contract_cancel_count[order.vt_symbol] += 1

            self.put_event()
