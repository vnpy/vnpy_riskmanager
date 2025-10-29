# cython: language_level=3

cdef class RuleTemplate:
    """风控规则模板 C 接口声明"""

    cdef readonly object risk_engine
    cdef public bint active
    cdef public str name
    cdef public dict parameters
    cdef public dict variables

    cpdef void write_log(self, str msg)
    cpdef void update_setting(self, dict rule_setting)
    cpdef bint check_allowed(self, object req, str gateway_name)
    cpdef void on_init(self)
    cpdef void on_tick(self, object tick)
    cpdef void on_order(self, object order)
    cpdef void on_trade(self, object trade)
    cpdef void on_timer(self)
    cpdef object get_contract(self, str vt_symbol)
    cpdef void put_event(self)
    cpdef dict get_data(self)
