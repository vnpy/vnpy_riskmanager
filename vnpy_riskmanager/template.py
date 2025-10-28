from typing import TYPE_CHECKING, Any

from vnpy.trader.object import OrderRequest, CancelRequest, TickData, OrderData, TradeData, ContractData

if TYPE_CHECKING:
    from .engine import RiskEngine


class RuleTemplate:
    """风控规则模板"""

    # 风控规则名称
    name: str = ""

    # 参数字段和名称
    parameters: dict[str, str] = {}

    # 变量字段和名称
    variables: dict[str, str] = {}

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        """构造函数"""
        self.risk_engine: RiskEngine = risk_engine

        self.update_setting(setting)

    def write_log(self, msg: str) -> None:
        """输出风控日志"""
        self.risk_engine.write_log(msg)

    def format_req(self, req: OrderRequest) -> str:
        """将委托请求转为字符串"""
        return f"{req.vt_symbol}|{req.type.value}|{req.direction.value}{req.offset.value}|{req.volume}@{req.price}|{req.reference}"

    def update_setting(self, setting: dict) -> None:
        """更新风控规则参数"""
        for name in self.parameters.keys():
            if name in setting:
                value = setting[name]
                setattr(self, name, value)

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

    def put_event(self) -> None:
        """推送数据更新事件"""
        self.risk_engine.put_rule_event(self)

    def get_data(self) -> dict[str, Any]:
        """获取数据"""
        parameters: dict[str, Any] = {}
        for name in self.parameters.keys():
            value: Any = getattr(self, name)
            parameters[name] = value

        variables: dict[str, Any] = {}
        for name in self.variables.keys():
            value: Any = getattr(self, name)
            variables[name] = value

        data: dict[str, Any] = {
            "name": self.name,
            "parameters": parameters,
            "variables": variables
        }
        return data
