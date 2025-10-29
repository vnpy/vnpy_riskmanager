# cython: language_level=3
from vnpy.trader.object import OrderRequest, OrderData

# 使用cimport导入Cython扩展类型
from vnpy_riskmanager.template cimport RuleTemplate


cdef class ActiveOrderRuleCy(RuleTemplate):
    """活动委托数量检查风控规则（Cython 版本）"""

    # 实例属性声明
    cdef public int active_order_limit
    cdef public int active_order_count
    cdef dict active_orders

    cpdef void on_init(self):
        """初始化"""
        # 默认参数
        self.active_order_limit = 50

        # 活动委托
        self.active_orders = {}

        # 数量统计
        self.active_order_count = 0

    cpdef bint check_allowed(self, object req, str gateway_name):
        """检查是否允许委托"""
        if self.active_order_count >= self.active_order_limit:
            msg = f"活动委托数量{self.active_order_count}达到上限{self.active_order_limit}：{self.format_req(req)}"
            self.write_log(msg)
            return False

        return True

    cpdef void on_order(self, object order):
        """委托推送"""
        cdef str vt_orderid = order.vt_orderid
        
        if order.is_active():
            self.active_orders[vt_orderid] = order
        elif vt_orderid in self.active_orders:
            self.active_orders.pop(vt_orderid)

        self.active_order_count = len(self.active_orders)

        self.put_event()


# Python wrapper类，用于提供类属性（engine.py需要）
class ActiveOrderRule(ActiveOrderRuleCy):
    """活动委托检查规则的Python包装类"""
    
    name: str = "活动委托检查"
    
    parameters: dict[str, str] = {
        "active_order_limit": "活动委托上限"
    }
    
    variables: dict[str, str] = {
        "active_order_count": "活动委托数量"
    }
