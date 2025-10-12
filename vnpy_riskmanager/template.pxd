# cython: language_level=3

cdef class RuleTemplate:
    """风控规则模板 C 接口声明"""

    cdef readonly object risk_engine

    cpdef void write_log(self, str msg)
    cpdef str format_req(self, object req)
    cpdef void init_rule(self, dict setting)
    cpdef bint check_allowed(self, object req, str gateway_name)
    cpdef bint check_cancel_allowed(self, object req)
    cpdef void on_tick(self, object tick)
    cpdef void on_order(self, object order)
    cpdef void on_trade(self, object trade)
    cpdef void on_timer(self)
    cpdef list get_all_active_orders(self)
