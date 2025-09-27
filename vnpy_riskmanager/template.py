from vnpy.event import Event
from vnpy.trader.event import EVENT_LOG
from vnpy.trader.engine import MainEngine, EventEngine
from vnpy.trader.object import OrderRequest, LogData, CancelRequest

from .base import APP_NAME


class RuleTemplate:
    """风控规则模板"""

    def __init__(
        self,
        main_engine: MainEngine,
        event_engine: EventEngine,
        setting: dict
    ) -> None:
        """构造函数"""
        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine

        self.init_rule(setting)
        self.register_event()

    def write_log(self, msg: str) -> None:
        """输出风控日志"""
        log: LogData = LogData(msg=msg, gateway_name=APP_NAME)
        event: Event = Event(EVENT_LOG, log)
        self.event_engine.put(event)

    def format_req(self, req: OrderRequest) -> str:
        """将委托请求转为字符串"""
        return f"{req.vt_symbol}|{req.type.value}|{req.direction.value}{req.offset.value}|{req.volume}@{req.price}|{req.reference}"

    def init_rule(self, setting: dict) -> None:
        """初始化风控规则"""
        pass

    def register_event(self) -> None:
        """注册事件数据监听"""
        pass

    def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许委托"""
        return True

    def check_cancel_allowed(self, req: CancelRequest) -> bool:
        """检查是否允许撤单"""
        return True
