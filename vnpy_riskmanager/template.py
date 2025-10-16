from typing import TYPE_CHECKING

from vnpy.trader.object import OrderRequest, CancelRequest, TickData, OrderData, TradeData, ContractData

if TYPE_CHECKING:
    from .engine import RiskEngine


class RuleTemplate:
    """风控规则模板"""

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        """构造函数"""
        self.risk_engine: RiskEngine = risk_engine
        self.init_rule(setting)

    def write_log(self, msg: str) -> None:
        """输出风控日志"""
        self.risk_engine.write_log(msg)

    def format_req(self, req: OrderRequest) -> str:
        """将委托请求转为字符串"""
        return f"{req.vt_symbol}|{req.type.value}|{req.direction.value}{req.offset.value}|{req.volume}@{req.price}|{req.reference}"

    def init_rule(self, setting: dict) -> None:
        """初始化风控规则"""
        pass

    def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许委托"""
        return True

    def check_cancel_allowed(self, req: CancelRequest) -> bool:
        """检查是否允许撤单"""
        return True

    def on_tick(self, tick: TickData) -> None:
        """行情推送"""
        pass

    def on_order(self, order: OrderData) -> None:
        """委托推送"""
        pass

    def on_trade(self, trade: TradeData) -> None:
        """成交推送"""
        pass

    def on_timer(self) -> None:
        """定时推送（每秒触发）"""
        pass

    def get_all_active_orders(self) -> list[OrderData]:
        """查询所有活动委托"""
        return self.risk_engine.get_all_active_orders()

    def get_contract(self, vt_symbol: str) -> ContractData | None:
        """查询合约信息"""
        return self.risk_engine.get_contract(vt_symbol)
