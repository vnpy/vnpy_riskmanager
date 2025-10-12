"""OrderSizeRule 测试用例"""
from typing import Callable
from unittest.mock import Mock

import pytest

from vnpy.trader.object import OrderRequest
from vnpy.trader.constant import Direction, Offset, OrderType, Exchange

from vnpy_riskmanager.rules.order_size_rule import OrderSizeRule


class TestOrderSizeRule:
    """单笔委托数量上限规则测试"""

    def test_init_with_default_setting(self, mock_risk_engine: Mock) -> None:
        """测试使用默认配置初始化"""
        rule: OrderSizeRule = OrderSizeRule(mock_risk_engine, {})
        assert rule.order_size_limit == 100

    def test_init_with_custom_setting(self, mock_risk_engine: Mock) -> None:
        """测试使用自定义配置初始化"""
        setting: dict = {"order_size_limit": 50}
        rule: OrderSizeRule = OrderSizeRule(mock_risk_engine, setting)
        assert rule.order_size_limit == 50

    def test_check_allowed_below_limit(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试委托数量小于上限时允许下单"""
        rule: OrderSizeRule = OrderSizeRule(mock_risk_engine, setting_factory({}))

        result: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result is True
        mock_risk_engine.write_log.assert_not_called()

    def test_check_allowed_at_limit(
        self,
        mock_risk_engine: Mock,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试委托数量等于上限时允许下单"""
        setting: dict = setting_factory({"order_size_limit": 100})
        rule: OrderSizeRule = OrderSizeRule(mock_risk_engine, setting)

        req: OrderRequest = OrderRequest(
            symbol="IF2501",
            exchange=Exchange.CFFEX,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=100.0,
            price=4000.0,
            offset=Offset.OPEN,
            reference="test"
        )

        result: bool = rule.check_allowed(req, "CTP")

        assert result is True
        mock_risk_engine.write_log.assert_not_called()

    def test_check_allowed_above_limit(
        self,
        mock_risk_engine: Mock,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试委托数量超过上限时拒绝下单"""
        setting: dict = setting_factory({"order_size_limit": 100})
        rule: OrderSizeRule = OrderSizeRule(mock_risk_engine, setting)

        req: OrderRequest = OrderRequest(
            symbol="IF2501",
            exchange=Exchange.CFFEX,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=150.0,
            price=4000.0,
            offset=Offset.OPEN,
            reference="test"
        )

        result: bool = rule.check_allowed(req, "CTP")

        assert result is False
        mock_risk_engine.write_log.assert_called_once()
        log_msg: str = mock_risk_engine.write_log.call_args[0][0]
        assert "单笔委托数量" in log_msg
        assert "150" in log_msg
        assert "超过上限100" in log_msg

    def test_check_allowed_boundary_plus_one(
        self,
        mock_risk_engine: Mock,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试边界条件：上限+1"""
        setting: dict = setting_factory({"order_size_limit": 100})
        rule: OrderSizeRule = OrderSizeRule(mock_risk_engine, setting)

        req: OrderRequest = OrderRequest(
            symbol="IF2501",
            exchange=Exchange.CFFEX,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=101.0,
            price=4000.0,
            offset=Offset.OPEN,
            reference="test"
        )

        result: bool = rule.check_allowed(req, "CTP")

        assert result is False
        mock_risk_engine.write_log.assert_called_once()

    def test_check_allowed_boundary_minus_one(
        self,
        mock_risk_engine: Mock,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试边界条件：上限-1"""
        setting: dict = setting_factory({"order_size_limit": 100})
        rule: OrderSizeRule = OrderSizeRule(mock_risk_engine, setting)

        req: OrderRequest = OrderRequest(
            symbol="IF2501",
            exchange=Exchange.CFFEX,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=99.0,
            price=4000.0,
            offset=Offset.OPEN,
            reference="test"
        )

        result: bool = rule.check_allowed(req, "CTP")

        assert result is True
        mock_risk_engine.write_log.assert_not_called()

    def test_check_allowed_minimum_volume(
        self,
        mock_risk_engine: Mock,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试最小委托数量"""
        rule: OrderSizeRule = OrderSizeRule(mock_risk_engine, setting_factory({}))

        req: OrderRequest = OrderRequest(
            symbol="IF2501",
            exchange=Exchange.CFFEX,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=1.0,
            price=4000.0,
            offset=Offset.OPEN,
            reference="test"
        )

        result: bool = rule.check_allowed(req, "CTP")

        assert result is True
        mock_risk_engine.write_log.assert_not_called()

    def test_check_allowed_different_symbols(
        self,
        mock_risk_engine: Mock,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试不同合约受相同规则限制"""
        setting: dict = setting_factory({"order_size_limit": 50})
        rule: OrderSizeRule = OrderSizeRule(mock_risk_engine, setting)

        # 测试期货合约
        req1: OrderRequest = OrderRequest(
            symbol="IF2501",
            exchange=Exchange.CFFEX,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=60.0,
            price=4000.0,
            offset=Offset.OPEN,
            reference="test"
        )

        # 测试股票
        req2: OrderRequest = OrderRequest(
            symbol="600000",
            exchange=Exchange.SSE,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=60.0,
            price=10.0,
            offset=Offset.NONE,
            reference="test"
        )

        assert rule.check_allowed(req1, "CTP") is False
        assert rule.check_allowed(req2, "OES") is False

    def test_check_allowed_different_directions(
        self,
        mock_risk_engine: Mock,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试不同方向的委托"""
        setting: dict = setting_factory({"order_size_limit": 50})
        rule: OrderSizeRule = OrderSizeRule(mock_risk_engine, setting)

        # 买入
        req_long: OrderRequest = OrderRequest(
            symbol="IF2501",
            exchange=Exchange.CFFEX,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=60.0,
            price=4000.0,
            offset=Offset.OPEN,
            reference="test"
        )

        # 卖出
        req_short: OrderRequest = OrderRequest(
            symbol="IF2501",
            exchange=Exchange.CFFEX,
            direction=Direction.SHORT,
            type=OrderType.LIMIT,
            volume=60.0,
            price=4000.0,
            offset=Offset.OPEN,
            reference="test"
        )

        assert rule.check_allowed(req_long, "CTP") is False
        assert rule.check_allowed(req_short, "CTP") is False

    def test_check_allowed_with_limit_one(
        self,
        mock_risk_engine: Mock,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试上限为1的极端情况"""
        setting: dict = setting_factory({"order_size_limit": 1})
        rule: OrderSizeRule = OrderSizeRule(mock_risk_engine, setting)

        req_ok: OrderRequest = OrderRequest(
            symbol="IF2501",
            exchange=Exchange.CFFEX,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=1.0,
            price=4000.0,
            offset=Offset.OPEN,
            reference="test"
        )

        req_fail: OrderRequest = OrderRequest(
            symbol="IF2501",
            exchange=Exchange.CFFEX,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=2.0,
            price=4000.0,
            offset=Offset.OPEN,
            reference="test"
        )

        assert rule.check_allowed(req_ok, "CTP") is True
        assert rule.check_allowed(req_fail, "CTP") is False

    def test_check_allowed_large_limit(
        self,
        mock_risk_engine: Mock,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试大上限值"""
        setting: dict = setting_factory({"order_size_limit": 10000})
        rule: OrderSizeRule = OrderSizeRule(mock_risk_engine, setting)

        req: OrderRequest = OrderRequest(
            symbol="IF2501",
            exchange=Exchange.CFFEX,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=5000.0,
            price=4000.0,
            offset=Offset.OPEN,
            reference="test"
        )

        result: bool = rule.check_allowed(req, "CTP")

        assert result is True
        mock_risk_engine.write_log.assert_not_called()

    def test_log_message_format(
        self,
        mock_risk_engine: Mock,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试日志消息格式完整性"""
        setting: dict = setting_factory({"order_size_limit": 100})
        rule: OrderSizeRule = OrderSizeRule(mock_risk_engine, setting)

        req: OrderRequest = OrderRequest(
            symbol="IF2501",
            exchange=Exchange.CFFEX,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=200.0,
            price=4000.0,
            offset=Offset.OPEN,
            reference="test"
        )

        rule.check_allowed(req, "CTP")

        log_msg: str = mock_risk_engine.write_log.call_args[0][0]
        assert "单笔委托数量" in log_msg
        assert "200" in log_msg
        assert "上限" in log_msg
        assert "100" in log_msg

    def test_multiple_checks_independent(
        self,
        mock_risk_engine: Mock,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试多次检查相互独立"""
        setting: dict = setting_factory({"order_size_limit": 100})
        rule: OrderSizeRule = OrderSizeRule(mock_risk_engine, setting)

        req_small: OrderRequest = OrderRequest(
            symbol="IF2501",
            exchange=Exchange.CFFEX,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=50.0,
            price=4000.0,
            offset=Offset.OPEN,
            reference="test"
        )

        req_large: OrderRequest = OrderRequest(
            symbol="IF2501",
            exchange=Exchange.CFFEX,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=150.0,
            price=4000.0,
            offset=Offset.OPEN,
            reference="test"
        )

        # 第一次检查：允许
        assert rule.check_allowed(req_small, "CTP") is True

        # 第二次检查：拒绝
        assert rule.check_allowed(req_large, "CTP") is False

        # 第三次检查：允许（不受之前影响）
        assert rule.check_allowed(req_small, "CTP") is True

    def test_fractional_volumes(
        self,
        mock_risk_engine: Mock,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试小数数量"""
        setting: dict = setting_factory({"order_size_limit": 100})
        rule: OrderSizeRule = OrderSizeRule(mock_risk_engine, setting)

        req: OrderRequest = OrderRequest(
            symbol="IF2501",
            exchange=Exchange.CFFEX,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=99.5,
            price=4000.0,
            offset=Offset.OPEN,
            reference="test"
        )

        result: bool = rule.check_allowed(req, "CTP")

        assert result is True

    def test_integration_with_risk_engine(
        self,
        mock_risk_engine: Mock,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试与 RiskEngine 的集成"""
        rule: OrderSizeRule = OrderSizeRule(mock_risk_engine, setting_factory({}))

        assert rule.risk_engine == mock_risk_engine

        # 触发日志输出
        req: OrderRequest = OrderRequest(
            symbol="IF2501",
            exchange=Exchange.CFFEX,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=200.0,
            price=4000.0,
            offset=Offset.OPEN,
            reference="test"
        )

        rule.check_allowed(req, "CTP")
        mock_risk_engine.write_log.assert_called()

    def test_different_gateways(
        self,
        mock_risk_engine: Mock,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试不同网关名称不影响检查"""
        setting: dict = setting_factory({"order_size_limit": 100})
        rule: OrderSizeRule = OrderSizeRule(mock_risk_engine, setting)

        req: OrderRequest = OrderRequest(
            symbol="IF2501",
            exchange=Exchange.CFFEX,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=150.0,
            price=4000.0,
            offset=Offset.OPEN,
            reference="test"
        )

        # 不同网关应该返回相同结果
        assert rule.check_allowed(req, "CTP") is False
        assert rule.check_allowed(req, "OES") is False
        assert rule.check_allowed(req, "IB") is False

    def test_zero_volume(
        self,
        mock_risk_engine: Mock,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试零数量委托"""
        rule: OrderSizeRule = OrderSizeRule(mock_risk_engine, setting_factory({}))

        req: OrderRequest = OrderRequest(
            symbol="IF2501",
            exchange=Exchange.CFFEX,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=0.0,
            price=4000.0,
            offset=Offset.OPEN,
            reference="test"
        )

        result: bool = rule.check_allowed(req, "CTP")

        assert result is True
        mock_risk_engine.write_log.assert_not_called()
