# cython: language_level=3
from typing import TYPE_CHECKING

from ..template cimport RuleTemplate

if TYPE_CHECKING:
    from ..engine import RiskEngine


cdef class OrderValidityRule(RuleTemplate):
    """委托指令合法性监控（Cython 优化版本）"""

    # 属性声明（public 使其可从 Python 访问，确保 .py 和 .pyx 版本行为一致）
    cdef public bint check_contract_exists
    cdef public bint check_price_tick
    cdef public bint check_volume_limit
    cdef public int max_order_volume

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        super().__init__(risk_engine, setting)

    cpdef void init_rule(self, dict setting):
        """初始化风控规则"""
        self.check_contract_exists = setting.get("check_contract_exists", True)
        self.check_price_tick = setting.get("check_price_tick", True)
        self.check_volume_limit = setting.get("check_volume_limit", False)
        self.max_order_volume = setting.get("max_order_volume", 1000)

    cpdef bint check_allowed(self, object req, str gateway_name):
        """检查是否允许委托"""
        cdef object contract
        cdef double price_tick
        cdef double remainder

        # 检查合约是否存在
        if self.check_contract_exists:
            # 直接调用 risk_engine.get_contract() 查询合约信息（不通过 template 包装）
            contract = self.risk_engine.get_contract(req.vt_symbol)
            if not contract:
                self.write_log(f"委托失败：合约 {req.vt_symbol} 不存在")
                return False

            # 检查价格是否为 pricetick 的整数倍
            if self.check_price_tick:
                if contract.pricetick > 0:
                    price_tick = contract.pricetick
                    remainder = req.price % price_tick
                    if abs(remainder) > 1e-6 and abs(remainder - price_tick) > 1e-6:
                        self.write_log(
                            f"委托失败：价格 {req.price} 不是最小变动价位 {price_tick} 的整数倍"
                        )
                        return False

        # 检查委托数量上限
        if self.check_volume_limit:
            if req.volume > self.max_order_volume:
                self.write_log(
                    f"委托失败：数量 {req.volume} 超过单笔最大限制 {self.max_order_volume}"
                )
                return False

        return True

