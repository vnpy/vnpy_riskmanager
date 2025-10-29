"""
vnpy_riskmanager模块一致性测试
"""

import unittest
from typing import Any
from collections import defaultdict

from vnpy.trader.constant import Direction, Offset, OrderType, Status

# 导入Python规则
from vnpy_riskmanager.rules.active_order_rule import ActiveOrderRule as PyActiveOrderRule
from vnpy_riskmanager.rules.daily_limit_rule import DailyLimitRule as PyDailyLimitRule
from vnpy_riskmanager.rules.duplicate_order_rule import DuplicateOrderRule as PyDuplicateOrderRule
from vnpy_riskmanager.rules.order_size_rule import OrderSizeRule as PyOrderSizeRule
from vnpy_riskmanager.rules.order_validity_rule import OrderValidityRule as PyOrderValidityRule

# 导入Cython规则
try:
    from vnpy_riskmanager.rules.active_order_rule_cy import ActiveOrderRule as CyActiveOrderRule
    from vnpy_riskmanager.rules.daily_limit_rule_cy import DailyLimitRule as CyDailyLimitRule
    from vnpy_riskmanager.rules.duplicate_order_rule_cy import DuplicateOrderRule as CyDuplicateOrderRule
    from vnpy_riskmanager.rules.order_size_rule_cy import OrderSizeRule as CyOrderSizeRule
    from vnpy_riskmanager.rules.order_validity_rule_cy import OrderValidityRule as CyOrderValidityRule
except ImportError:
    print("未找到Cython规则，请先编译")
    exit()


class MockContract:
    """模拟合约数据"""

    def __init__(self) -> None:
        self.pricetick: float = 0.1
        self.max_volume: float = 100.0
        self.min_volume: float = 1.0
        self.size: float = 1.0


class MockRiskEngine:
    """模拟风控引擎"""

    def __init__(self) -> None:
        self.contract = MockContract()

    def get_contract(self, vt_symbol: str) -> Any | None:
        if "FAIL" in vt_symbol:
            return None
        return self.contract

    def write_log(self, msg: str) -> None:
        pass

    def put_rule_event(self, rule: Any) -> None:
        pass


class MockOrderRequest:
    """模拟委托请求"""

    def __init__(
        self,
        vt_symbol: str,
        volume: float,
        price: float,
        direction: Direction = Direction.LONG,
        offset: Offset = Offset.OPEN,
        type: OrderType = OrderType.LIMIT,
    ):
        self.vt_symbol = vt_symbol
        self.volume = volume
        self.price = price
        self.direction = direction
        self.offset = offset
        self.type = type

    def __str__(self) -> str:
        return f"MockOrderRequest({self.vt_symbol}, {self.volume}@{self.price})"


class MockOrderData:
    """模拟委托数据"""

    def __init__(
        self,
        vt_orderid: str,
        vt_symbol: str,
        status: Status,
    ):
        self.vt_orderid = vt_orderid
        self.vt_symbol = vt_symbol
        self.status = status

    def is_active(self) -> bool:
        return self.status in [Status.SUBMITTING, Status.NOTTRADED, Status.PARTTRADED]


class MockTradeData:
    """模拟成交数据"""

    def __init__(self, vt_tradeid: str, vt_symbol: str):
        self.vt_tradeid = vt_tradeid
        self.vt_symbol = vt_symbol


class BaseRuleConsistencyTest(unittest.TestCase):
    """规则一致性测试的基类"""
    py_rule_class: type | None = None
    cy_rule_class: type | None = None

    def setUp(self) -> None:
        """为每个测试设置新的Python和Cython规则实例"""
        if self.py_rule_class is None or self.cy_rule_class is None:
            self.skipTest("规则一致性测试的基类")

        self.mock_engine = MockRiskEngine()
        self.py_rule = self.py_rule_class(self.mock_engine, {})
        self.cy_rule = self.cy_rule_class(self.mock_engine, {})

    def assert_state_equal(self, msg: str) -> None:
        """用于比较两个规则内部状态的辅助方法"""
        py_data = self.py_rule.get_data()
        cy_data = self.cy_rule.get_data()

        # defaultdict无法直接比较
        py_vars = py_data["variables"]
        cy_vars = cy_data["variables"]
        for k, v in py_vars.items():
            if isinstance(v, defaultdict):
                py_vars[k] = dict(v)
        for k, v in cy_vars.items():
            if isinstance(v, defaultdict):
                cy_vars[k] = dict(v)

        self.assertDictEqual(py_data, cy_data, msg)


class TestActiveOrderRuleConsistency(BaseRuleConsistencyTest):
    py_rule_class = PyActiveOrderRule
    cy_rule_class = CyActiveOrderRule

    def test_on_order(self) -> None:
        """测试on_order的一致性"""
        self.assert_state_equal("初始状态应相同")

        # 活动委托
        order1 = MockOrderData("order1", "IF2401", Status.NOTTRADED)
        self.py_rule.on_order(order1)
        self.cy_rule.on_order(order1)
        self.assert_state_equal("收到活动委托后状态应相同")

        # 非活动委托
        order2 = MockOrderData("order1", "IF2401", Status.ALLTRADED)
        self.py_rule.on_order(order2)
        self.cy_rule.on_order(order2)
        self.assert_state_equal("委托变为非活动后状态应相同")

    def test_check_allowed(self) -> None:
        """测试check_allowed的一致性"""
        req = MockOrderRequest("IF2401", 1, 4000)
        self.assertEqual(
            self.py_rule.check_allowed(req, "CTP"),
            self.cy_rule.check_allowed(req, "CTP")
        )

        self.py_rule.active_order_limit = 0
        self.cy_rule.active_order_limit = 0
        self.assertEqual(
            self.py_rule.check_allowed(req, "CTP"),
            self.cy_rule.check_allowed(req, "CTP")
        )


class TestDailyLimitRuleConsistency(BaseRuleConsistencyTest):
    py_rule_class = PyDailyLimitRule
    cy_rule_class = CyDailyLimitRule

    def test_consistency(self) -> None:
        """测试完整的生命周期一致性"""
        self.assert_state_equal("初始状态应相同")

        # 新委托
        order1 = MockOrderData("order1", "IF2401", Status.NOTTRADED)
        self.py_rule.on_order(order1)
        self.cy_rule.on_order(order1)
        self.assert_state_equal("新委托后状态应相同")

        # 撤销委托
        order2 = MockOrderData("order1", "IF2401", Status.CANCELLED)
        self.py_rule.on_order(order2)
        self.cy_rule.on_order(order2)
        self.assert_state_equal("撤销委托后状态应相同")

        # 成交
        trade1 = MockTradeData("trade1", "IF2401")
        self.py_rule.on_trade(trade1)
        self.cy_rule.on_trade(trade1)
        self.assert_state_equal("成交后状态应相同")


class TestDuplicateOrderRuleConsistency(BaseRuleConsistencyTest):
    py_rule_class = PyDuplicateOrderRule
    cy_rule_class = CyDuplicateOrderRule

    def test_check_allowed(self) -> None:
        """测试check_allowed的一致性"""
        req1 = MockOrderRequest("IF2401", 1, 4000)
        req2 = MockOrderRequest("IF2401", 1, 4000)

        res1_py = self.py_rule.check_allowed(req1, "CTP")
        res1_cy = self.cy_rule.check_allowed(req1, "CTP")
        self.assertEqual(res1_py, res1_cy)
        self.assert_state_equal("第一个请求后状态应相同")

        res2_py = self.py_rule.check_allowed(req2, "CTP")
        res2_cy = self.cy_rule.check_allowed(req2, "CTP")
        self.assertEqual(res2_py, res2_cy)
        self.assert_state_equal("第二个（重复）请求后状态应相同")


class TestOrderSizeRuleConsistency(BaseRuleConsistencyTest):
    py_rule_class = PyOrderSizeRule
    cy_rule_class = CyOrderSizeRule

    def test_check_allowed(self) -> None:
        """测试check_allowed的一致性"""
        # 合法
        req1 = MockOrderRequest("IF2401", 1, 4000)
        self.assertEqual(
            self.py_rule.check_allowed(req1, "CTP"),
            self.cy_rule.check_allowed(req1, "CTP")
        )

        # 数量限制
        req2 = MockOrderRequest("IF2401", 1000, 4000)
        self.assertEqual(
            self.py_rule.check_allowed(req2, "CTP"),
            self.cy_rule.check_allowed(req2, "CTP")
        )

        # 价值限制
        req3 = MockOrderRequest("IF2401", 10, 500000)
        self.assertEqual(
            self.py_rule.check_allowed(req3, "CTP"),
            self.cy_rule.check_allowed(req3, "CTP")
        )


class TestOrderValidityRuleConsistency(BaseRuleConsistencyTest):
    py_rule_class = PyOrderValidityRule
    cy_rule_class = CyOrderValidityRule

    def test_check_allowed(self) -> None:
        """测试check_allowed的一致性"""
        # 合法
        req1 = MockOrderRequest("IF2401", 10, 4000.1)
        self.assertEqual(
            self.py_rule.check_allowed(req1, "CTP"),
            self.cy_rule.check_allowed(req1, "CTP")
        )

        # 非法合约
        req2 = MockOrderRequest("FAIL2401", 10, 4000.1)
        self.assertEqual(
            self.py_rule.check_allowed(req2, "CTP"),
            self.cy_rule.check_allowed(req2, "CTP")
        )

        # 非法价格
        req3 = MockOrderRequest("IF2401", 10, 4000.15)
        self.assertEqual(
            self.py_rule.check_allowed(req3, "CTP"),
            self.cy_rule.check_allowed(req3, "CTP")
        )

        # 非法最小数量
        req4 = MockOrderRequest("IF2401", 0.5, 4000.1)
        self.assertEqual(
            self.py_rule.check_allowed(req4, "CTP"),
            self.cy_rule.check_allowed(req4, "CTP")
        )

        # 非法最大数量
        req5 = MockOrderRequest("IF2401", 200, 4000.1)
        self.assertEqual(
            self.py_rule.check_allowed(req5, "CTP"),
            self.cy_rule.check_allowed(req5, "CTP")
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
