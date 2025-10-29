# cython: language_level=3
from vnpy_riskmanager.template cimport RuleTemplate


cdef class OrderSizeRuleCy(RuleTemplate):
    """委托规模检查风控规则 (Cython 版本)"""

    cdef public int order_volume_limit
    cdef public float order_value_limit

    cpdef void on_init(self):
        """初始化"""
        self.order_volume_limit = 500
        self.order_value_limit = 1_000_000

    cpdef bint check_allowed(self, object req, str gateway_name):
        """检查是否允许委托"""
        cdef object contract
        cdef float order_value

        if req.volume > self.order_volume_limit:
            self.write_log(f"委托数量{req.volume}超过上限{self.order_volume_limit}：{req}")
            return False

        contract = self.get_contract(req.vt_symbol)
        if contract and req.price:      # 只考虑限价单
            order_value = req.volume * req.price * contract.size
            if order_value > self.order_value_limit:
                self.write_log(f"委托价值{order_value}超过上限{self.order_value_limit}：{req}")
                return False

        return True


class OrderSizeRule(OrderSizeRuleCy):
    """委托规模检查规则的Python包装类"""

    name: str = "委托规模检查"

    parameters: dict[str, str] = {
        "order_volume_limit": "委托数量上限",
        "order_value_limit": "委托价值上限",
    }
