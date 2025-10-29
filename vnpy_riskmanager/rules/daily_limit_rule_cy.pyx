# cython: language_level=3
from collections import defaultdict

from vnpy.trader.constant import Status

from vnpy_riskmanager.template cimport RuleTemplate


cdef class DailyLimitRuleCy(RuleTemplate):
    """每日上限检查风控规则 (Cython 版本)"""

    cdef public int total_order_limit
    cdef public int total_cancel_limit
    cdef public int total_trade_limit
    cdef public int contract_order_limit
    cdef public int contract_cancel_limit
    cdef public int contract_trade_limit

    cdef set all_orderids
    cdef set cancel_orderids
    cdef set all_tradeids

    cdef public int total_order_count
    cdef public int total_cancel_count
    cdef public int total_trade_count

    cdef public object contract_order_count
    cdef public object contract_cancel_count
    cdef public object contract_trade_count

    cpdef void on_init(self):
        """初始化"""
        # 默认参数
        self.total_order_limit = 20_000
        self.total_cancel_limit = 10_000
        self.total_trade_limit = 10_000
        self.contract_order_limit = 2_000
        self.contract_cancel_limit = 1_000
        self.contract_trade_limit = 1_000

        # 委托号记录
        self.all_orderids = set()
        self.cancel_orderids = set()

        # 成交号记录
        self.all_tradeids = set()

        # 数量统计
        self.total_order_count = 0
        self.total_cancel_count = 0
        self.total_trade_count = 0

        self.contract_order_count = defaultdict(int)
        self.contract_cancel_count = defaultdict(int)
        self.contract_trade_count = defaultdict(int)

    cpdef bint check_allowed(self, object req, str gateway_name):
        """检查是否允许委托"""
        cdef str vt_symbol = req.vt_symbol

        cdef int contract_order_count = self.contract_order_count[vt_symbol]
        if contract_order_count >= self.contract_order_limit:
            self.write_log(f"合约委托笔数{contract_order_count}达到上限{self.contract_order_limit}：{req}")
            return False

        cdef int contract_cancel_count = self.contract_cancel_count[vt_symbol]
        if contract_cancel_count >= self.contract_cancel_limit:
            self.write_log(f"合约撤单笔数{contract_cancel_count}达到上限{self.contract_cancel_limit}：{req}")
            return False

        cdef int contract_trade_count = self.contract_trade_count[vt_symbol]
        if contract_trade_count >= self.contract_trade_limit:
            self.write_log(f"合约成交笔数{contract_trade_count}达到上限{self.contract_trade_limit}：{req}")
            return False

        if self.total_order_count >= self.total_order_limit:
            self.write_log(f"汇总委托笔数{self.total_order_count}达到上限{self.total_order_limit}：{req}")
            return False

        if self.total_cancel_count >= self.total_cancel_limit:
            self.write_log(f"汇总撤单笔数{self.total_cancel_count}达到上限{self.total_cancel_limit}：{req}")
            return False

        if self.total_trade_count >= self.total_trade_limit:
            self.write_log(f"汇总成交笔数{self.total_trade_count}达到上限{self.total_trade_limit}：{req}")
            return False

        return True

    cpdef void on_order(self, object order):
        """委托推送"""
        cdef str vt_orderid = order.vt_orderid
        cdef str vt_symbol = order.vt_symbol

        if vt_orderid not in self.all_orderids:
            self.all_orderids.add(vt_orderid)
            self.total_order_count += 1
            self.contract_order_count[vt_symbol] += 1
            self.put_event()
        elif (
            order.status == Status.CANCELLED
            and vt_orderid not in self.cancel_orderids
        ):
            self.cancel_orderids.add(vt_orderid)
            self.total_cancel_count += 1
            self.contract_cancel_count[vt_symbol] += 1
            self.put_event()

    cpdef void on_trade(self, object trade):
        """成交推送"""
        cdef str vt_tradeid = trade.vt_tradeid

        if vt_tradeid in self.all_tradeids:
            return

        self.all_tradeids.add(vt_tradeid)
        self.total_trade_count += 1
        self.contract_trade_count[trade.vt_symbol] += 1
        self.put_event()


class DailyLimitRule(DailyLimitRuleCy):
    """每日上限检查规则的Python包装类"""

    name: str = "每日上限检查"

    parameters: dict[str, str] = {
        "total_order_limit": "汇总委托上限",
        "total_cancel_limit": "汇总撤单上限",
        "total_trade_limit": "汇总成交上限",
        "contract_order_limit": "合约委托上限",
        "contract_cancel_limit": "合约撤单上限",
        "contract_trade_limit": "合约成交上限"
    }

    variables: dict[str, str] = {
        "total_order_count": "汇总委托笔数",
        "total_cancel_count": "汇总撤单笔数",
        "total_trade_count": "汇总成交笔数",
        "contract_order_count": "合约委托笔数",
        "contract_cancel_count": "合约撤单笔数",
        "contract_trade_count": "合约成交笔数"
    }
