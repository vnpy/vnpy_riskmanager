from collections import defaultdict

from vnpy.trader.object import OrderRequest, OrderData, TradeData
from vnpy.trader.constant import Status

from ..template import RuleTemplate


class DailyLimitRule(RuleTemplate):
    """每日上限检查风控规则"""

    name: str = "每日上限检查"

    parameters: dict[str, str] = {
        "total_order_limit": "汇总委托上限",
        "total_cancel_limit": "汇总撤单上限",
        "total_trade_limit": "汇总成交上限",
        "contract_order_limit": "合约委托上限",
        "contract_cancel_limit": "合约撤单上限",
        "contract_trade_limit": "合约成交上限"
    }

    variables: dict[str, str] = {
        "total_order_count": "汇总委托笔数",
        "total_cancel_count": "汇总撤单笔数",
        "total_trade_count": "汇总成交笔数",
        "contract_order_count": "合约委托笔数",
        "contract_cancel_count": "合约撤单笔数",
        "contract_trade_count": "合约成交笔数"
    }

    def on_init(self) -> None:
        """初始化"""
        # 默认参数
        self.total_order_limit: int = 20_000
        self.total_cancel_limit: int = 10_000
        self.total_trade_limit: int = 10_000
        self.contract_order_limit: int = 2_000
        self.contract_cancel_limit: int = 1_000
        self.contract_trade_limit: int = 1_000

        # 委托号记录
        self.all_orderids: set[str] = set()
        self.cancel_orderids: set[str] = set()

        # 成交号记录
        self.all_tradeids: set[str] = set()

        # 数量统计
        self.total_order_count: int = 0
        self.total_cancel_count: int = 0
        self.total_trade_count: int = 0

        self.contract_order_count: dict[str, int] = defaultdict(int)
        self.contract_cancel_count: dict[str, int] = defaultdict(int)
        self.contract_trade_count: dict[str, int] = defaultdict(int)

    def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许委托"""
        contract_order_count: int = self.contract_order_count[req.vt_symbol]
        if contract_order_count >= self.contract_order_limit:
            self.write_log(f"合约委托笔数{contract_order_count}达到上限{self.contract_order_limit}：{req}")
            return False

        contract_cancel_count: int = self.contract_cancel_count[req.vt_symbol]
        if contract_cancel_count >= self.contract_cancel_limit:
            self.write_log(f"合约撤单笔数{contract_cancel_count}达到上限{self.contract_cancel_limit}：{req}")
            return False

        contract_trade_count: int = self.contract_trade_count[req.vt_symbol]
        if contract_trade_count >= self.contract_trade_limit:
            self.write_log(f"合约成交笔数{contract_trade_count}达到上限{self.contract_trade_limit}：{req}")
            return False

        if self.total_order_count >= self.total_order_limit:
            self.write_log(f"汇总委托笔数{self.total_order_count}达到上限{self.total_order_limit}：{req}")
            return False

        if self.total_cancel_count >= self.total_cancel_limit:
            self.write_log(f"汇总撤单笔数{self.total_cancel_count}达到上限{self.total_cancel_limit}：{req}")
            return False

        if self.total_trade_count >= self.total_trade_limit:
            self.write_log(f"汇总成交笔数{self.total_trade_count}达到上限{self.total_trade_limit}：{req}")
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
            order.status == Status.CANCELLED
            and order.vt_orderid not in self.cancel_orderids
        ):
            self.cancel_orderids.add(order.vt_orderid)
            self.total_cancel_count += 1

            self.contract_cancel_count[order.vt_symbol] += 1

            self.put_event()

    def on_trade(self, trade: TradeData) -> None:
        """成交推送"""
        if trade.vt_tradeid in self.all_tradeids:
            return

        self.all_tradeids.add(trade.vt_tradeid)
        self.total_trade_count += 1

        self.contract_trade_count[trade.vt_symbol] += 1

        self.put_event()
