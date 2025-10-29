# cython: language_level=3
from collections import defaultdict

from vnpy_riskmanager.template cimport RuleTemplate


cdef class DuplicateOrderRuleCy(RuleTemplate):
    """重复报单检查风控规则 (Cython 版本)"""

    cdef public int duplicate_order_limit
    cdef public object duplicate_order_count

    cpdef void on_init(self):
        """初始化"""
        # 默认参数
        self.duplicate_order_limit = 10

        # 重复报单统计
        self.duplicate_order_count = defaultdict(int)

    cpdef bint check_allowed(self, object req, str gateway_name):
        """检查是否允许委托"""
        cdef str req_str = self.format_req(req)
        self.duplicate_order_count[req_str] += 1
        self.put_event()

        cdef int duplicate_order_count = self.duplicate_order_count[req_str]
        if duplicate_order_count >= self.duplicate_order_limit:
            self.write_log(f"重复报单笔数{duplicate_order_count}达到上限{self.duplicate_order_limit}：{req}")
            return False

        return True

    cpdef str format_req(self, object req):
        """将委托请求转为字符串"""
        return f"{req.vt_symbol}|{req.type.value}|{req.direction.value}|{req.offset.value}|{req.volume}@{req.price}"


class DuplicateOrderRule(DuplicateOrderRuleCy):
    """重复报单检查规则的Python包装类"""

    name: str = "重复报单检查"

    parameters: dict[str, str] = {
        "duplicate_order_limit": "重复报单上限",
    }

    variables: dict[str, str] = {
        "duplicate_order_count": "重复报单笔数"
    }
