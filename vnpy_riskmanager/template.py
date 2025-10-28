from typing import TYPE_CHECKING, Any

from vnpy.trader.object import OrderRequest, TickData, OrderData, TradeData, ContractData

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
        # 绑定风控引擎对象
        self.risk_engine: RiskEngine = risk_engine

        # 添加启用状态参数
        self.active: bool = True

        parameters: dict[str, str] = {
            "active": "启用规则"
        }
        parameters.update(self.parameters)
        self.parameters = parameters

        # 初始化规则
        self.on_init()

        # 更新规则参数
        self.update_setting(setting)

    def write_log(self, msg: str) -> None:
        """输出风控日志"""
        self.risk_engine.write_log(msg)

    def update_setting(self, rule_setting: dict) -> None:
        """更新风控规则参数"""
        for name in self.parameters.keys():
            if name in rule_setting:
                value = rule_setting[name]
                setattr(self, name, value)

    def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许委托"""
        return True

    def on_init(self) -> None:
        """初始化"""
        pass

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
            value = getattr(self, name)
            variables[name] = value

        data: dict[str, Any] = {
            "name": self.name,
            "class_name": self.__class__.__name__,
            "parameters": parameters,
            "variables": variables
        }
        return data
