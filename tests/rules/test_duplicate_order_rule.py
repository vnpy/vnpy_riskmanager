"""DuplicateOrderRule 测试用例"""
from typing import Callable
from unittest.mock import Mock, patch

from vnpy.trader.object import OrderRequest
from vnpy.trader.constant import Direction, Offset, OrderType, Exchange

from vnpy_riskmanager.rules.duplicate_order_rule import DuplicateOrderRule


class TestDuplicateOrderRule:
    """重复报单监控规则测试"""

    def test_init_with_default_setting(self, mock_risk_engine: Mock) -> None:
        """测试使用默认配置初始化"""
        rule: DuplicateOrderRule = DuplicateOrderRule(mock_risk_engine, {})
        assert rule.max_duplicate_orders == 3
        assert rule.duplicate_window == 1.0
        assert len(rule.records) == 0

    def test_init_with_custom_setting(self, mock_risk_engine: Mock) -> None:
        """测试使用自定义配置初始化"""
        setting: dict = {"max_duplicate_orders": 5, "duplicate_window": 2.0}
        rule: DuplicateOrderRule = DuplicateOrderRule(mock_risk_engine, setting)
        assert rule.max_duplicate_orders == 5
        assert rule.duplicate_window == 2.0

    def test_first_order_allowed(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试首次相同委托允许通过"""
        rule: DuplicateOrderRule = DuplicateOrderRule(mock_risk_engine, {})

        result: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result is True
        mock_risk_engine.write_log.assert_not_called()

    def test_duplicate_below_limit(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试重复次数未超限时允许"""
        setting: dict = {"max_duplicate_orders": 3, "duplicate_window": 1.0}
        rule: DuplicateOrderRule = DuplicateOrderRule(mock_risk_engine, setting)

        # 连续发送 2 次相同委托
        with patch("vnpy_riskmanager.rules.duplicate_order_rule.time.time", return_value=1000.0):
            result1: bool = rule.check_allowed(sample_order_request, "CTP")
            result2: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result1 is True
        assert result2 is True
        mock_risk_engine.write_log.assert_not_called()

    def test_duplicate_at_limit(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试重复次数达到限制时拦截"""
        setting: dict = {"max_duplicate_orders": 3, "duplicate_window": 1.0}
        rule: DuplicateOrderRule = DuplicateOrderRule(mock_risk_engine, setting)

        # 连续发送 4 次相同委托
        with patch("vnpy_riskmanager.rules.duplicate_order_rule.time.time", return_value=1000.0):
            rule.check_allowed(sample_order_request, "CTP")
            rule.check_allowed(sample_order_request, "CTP")
            rule.check_allowed(sample_order_request, "CTP")
            result4: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result4 is False
        mock_risk_engine.write_log.assert_called_once()
        assert "重复报单" in str(mock_risk_engine.write_log.call_args)

    def test_window_cleanup(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试时间窗口清理功能"""
        setting: dict = {"max_duplicate_orders": 2, "duplicate_window": 1.0}
        rule: DuplicateOrderRule = DuplicateOrderRule(mock_risk_engine, setting)

        # 第一次发送
        with patch("vnpy_riskmanager.rules.duplicate_order_rule.time.time", return_value=1000.0):
            rule.check_allowed(sample_order_request, "CTP")

        # 1.5 秒后再次发送（已超出时间窗口）
        with patch("vnpy_riskmanager.rules.duplicate_order_rule.time.time", return_value=1001.5):
            result: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result is True
        mock_risk_engine.write_log.assert_not_called()

    def test_different_orders_isolated(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试不同委托互不影响"""
        setting: dict = {"max_duplicate_orders": 2, "duplicate_window": 1.0}
        rule: DuplicateOrderRule = DuplicateOrderRule(mock_risk_engine, setting)

        req1: OrderRequest = sample_order_request
        req2: OrderRequest = OrderRequest(
            symbol="IC2501",
            exchange=Exchange.CFFEX,
            direction=Direction.SHORT,
            type=OrderType.LIMIT,
            volume=10.0,
            price=4000.0,
            offset=Offset.CLOSE
        )

        with patch("vnpy_riskmanager.rules.duplicate_order_rule.time.time", return_value=1000.0):
            result1: bool = rule.check_allowed(req1, "CTP")
            result1_again: bool = rule.check_allowed(req1, "CTP")
            result2: bool = rule.check_allowed(req2, "CTP")

        assert result1 is True
        assert result1_again is True
        assert result2 is True

    def test_same_symbol_different_price(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试相同合约不同价格视为不同委托"""
        setting: dict = {"max_duplicate_orders": 2, "duplicate_window": 1.0}
        rule: DuplicateOrderRule = DuplicateOrderRule(mock_risk_engine, setting)

        with patch("vnpy_riskmanager.rules.duplicate_order_rule.time.time", return_value=1000.0):
            sample_order_request.price = 4000.0
            rule.check_allowed(sample_order_request, "CTP")
            rule.check_allowed(sample_order_request, "CTP")

            sample_order_request.price = 4001.0
            result: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result is True
        mock_risk_engine.write_log.assert_not_called()

    def test_log_message_format(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试日志消息格式"""
        setting: dict = {"max_duplicate_orders": 1, "duplicate_window": 1.0}
        rule: DuplicateOrderRule = DuplicateOrderRule(mock_risk_engine, setting)

        with patch("vnpy_riskmanager.rules.duplicate_order_rule.time.time", return_value=1000.0):
            rule.check_allowed(sample_order_request, "CTP")
            rule.check_allowed(sample_order_request, "CTP")

        log_message: str = str(mock_risk_engine.write_log.call_args[0][0])
        assert "重复报单" in log_message
        assert "秒内" in log_message

