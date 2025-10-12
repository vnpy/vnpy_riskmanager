# cython: language_level=3
from typing import TYPE_CHECKING

from vnpy.trader.object import OrderRequest, CancelRequest, TickData, OrderData, TradeData

if TYPE_CHECKING:
    from .engine import RiskEngine


cdef class RuleTemplate:
    """风控规则模板（Cython 版本）"""

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        """构造函数"""
        self.risk_engine = risk_engine
        self.init_rule(setting)

    cpdef void write_log(self, str msg):
        """输出风控日志"""
        self.risk_engine.write_log(msg)

    cpdef str format_req(self, object req):
        """将委托请求转为字符串"""
        return f"{req.vt_symbol}|{req.type.value}|{req.direction.value}{req.offset.value}|{req.volume}@{req.price}|{req.reference}"

    cpdef void init_rule(self, dict setting):
        """初始化风控规则"""
        pass

    cpdef bint check_allowed(self, object req, str gateway_name):
        """检查是否允许委托"""
        return True

    cpdef bint check_cancel_allowed(self, object req):
        """检查是否允许撤单"""
        return True

    cpdef void on_tick(self, object tick):
        """行情推送"""
        pass

    cpdef void on_order(self, object order):
        """委托推送"""
        pass

    cpdef void on_trade(self, object trade):
        """成交推送"""
        pass

    cpdef void on_timer(self):
        """定时推送（每秒触发）"""
        pass

    cpdef list get_all_active_orders(self):
        """查询所有活动委托"""
        return self.risk_engine.get_all_active_orders()
