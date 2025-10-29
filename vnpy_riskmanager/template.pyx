# cython: language_level=3
from typing import TYPE_CHECKING, Any

from vnpy.trader.object import (
    OrderRequest,
    CancelRequest,
    TickData,
    OrderData,
    TradeData,
    ContractData
)

if TYPE_CHECKING:
    from .engine import RiskEngine


cdef class RuleTemplate:
    """风控规则模板（Cython 版本）"""

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        """构造函数"""
        # 绑定风控引擎对象
        self.risk_engine = risk_engine

        # 初始化基本属性
        self.name = ""
        self.parameters = {}
        self.variables = {}
        
        # 添加启用状态参数
        self.active = True

        # 尝试从类属性获取元数据（用于Python风格的子类）
        if hasattr(self.__class__, 'name') and isinstance(self.__class__.name, str):
            self.name = self.__class__.name

        if hasattr(self.__class__, 'parameters') and isinstance(self.__class__.parameters, dict):
            self.parameters.update(self.__class__.parameters)

        if hasattr(self.__class__, 'variables') and isinstance(self.__class__.variables, dict):
            self.variables.update(self.__class__.variables)

        # 初始化规则（子类在这里设置元数据和初始值）
        self.on_init()

        # 构建完整的parameters字典（在on_init之后，添加"active"字段）
        parameters = {
            "active": "启用规则"
        }
        parameters.update(self.parameters)
        self.parameters = parameters

        # 更新规则参数
        self.update_setting(setting)

    cpdef void write_log(self, str msg):
        """输出风控日志"""
        self.risk_engine.write_log(msg)

    cpdef void update_setting(self, dict rule_setting):
        """更新风控规则参数"""
        cdef str name
        cdef object value
        
        for name in self.parameters.keys():
            if name in rule_setting:
                value = rule_setting[name]
                setattr(self, name, value)

    cpdef bint check_allowed(self, object req, str gateway_name):
        """检查是否允许委托"""
        return True

    cpdef void on_init(self):
        """初始化（子类重写）"""
        pass

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

    cpdef object get_contract(self, str vt_symbol):
        """查询合约信息"""
        return self.risk_engine.get_contract(vt_symbol)

    cpdef void put_event(self):
        """推送数据更新事件"""
        self.risk_engine.put_rule_event(self)

    cpdef dict get_data(self):
        """获取数据"""
        cdef dict parameters_data = {}
        cdef dict variables_data = {}
        cdef str name
        cdef object value
        
        # 收集所有parameters的值
        for name in self.parameters.keys():
            value = getattr(self, name, None)
            parameters_data[name] = value

        # 收集所有variables的值
        for name in self.variables.keys():
            value = getattr(self, name, None)
            variables_data[name] = value

        data = {
            "name": self.name,
            "class_name": self.__class__.__name__,
            "parameters": parameters_data,
            "variables": variables_data
        }
        return data
