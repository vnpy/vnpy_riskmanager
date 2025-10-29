# cython: language_level=3
from vnpy_riskmanager.template cimport RuleTemplate


cdef class OrderValidityRuleCy(RuleTemplate):
    """委托指令检查风控规则 (Cython 版本)"""

    cpdef bint check_allowed(self, object req, str gateway_name):
        """检查是否允许委托"""
        cdef double pricetick
        cdef double remainder

        # 检查合约存在
        cdef object contract = self.get_contract(req.vt_symbol)
        if not contract:
            self.write_log(f"合约代码{req.vt_symbol}不存在：{req}")
            return False

        # 检查最小价格变动
        if contract.pricetick > 0:
            pricetick = contract.pricetick

            # 计算价格与最小变动价位的余数
            remainder = req.price % pricetick

            # 检查价格与最小变动价位的余数，确保价格为pricetick的整数倍（允许极小误差，适应浮点数精度问题）
            if abs(remainder) > 1e-6 and abs(remainder - pricetick) > 1e-6:
                self.write_log(f"价格{req.price}不是合约最小变动价位{pricetick}的整数倍：{req}")
                return False

        # 检查委托数量上限
        if contract.max_volume and req.volume > contract.max_volume:
            self.write_log(f"委托数量{req.volume}大于合约委托数量上限{contract.max_volume}：{req}")
            return False

        # 检查委托数量下限
        if req.volume < contract.min_volume:
            self.write_log(f"委托数量{req.volume}小于合约委托数量下限{contract.min_volume}：{req}")
            return False

        return True


class OrderValidityRule(OrderValidityRuleCy):
    """委托指令检查规则的Python包装类"""

    name: str = "委托指令检查"
