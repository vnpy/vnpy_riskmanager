"""RollingWindowRule 测试用例"""
from unittest.mock import Mock, patch

from vnpy.trader.object import OrderRequest, CancelRequest

from vnpy_riskmanager.rules.rolling_window_rule import RollingWindowRule


class TestRollingWindowRule:
    """滚动窗口委托/撤单笔数监控规则测试"""

    def test_init_with_default_setting(self, mock_risk_engine: Mock) -> None:
        """测试使用默认配置初始化"""
        rule: RollingWindowRule = RollingWindowRule(mock_risk_engine, {})
        assert rule.rolling_window_seconds == 1.0
        assert rule.rolling_order_limit == 20
        assert rule.rolling_cancel_limit == 20
        assert len(rule.order_timestamps) == 0
        assert len(rule.cancel_timestamps) == 0

    def test_init_with_custom_setting(self, mock_risk_engine: Mock) -> None:
        """测试使用自定义配置初始化"""
        setting: dict = {
            "rolling_window_seconds": 2.0,
            "rolling_order_limit": 30,
            "rolling_cancel_limit": 25
        }
        rule: RollingWindowRule = RollingWindowRule(mock_risk_engine, setting)
        assert rule.rolling_window_seconds == 2.0
        assert rule.rolling_order_limit == 30
        assert rule.rolling_cancel_limit == 25

    def test_order_below_limit(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试委托频率未超限时允许"""
        setting: dict = {"rolling_order_limit": 10}
        rule: RollingWindowRule = RollingWindowRule(mock_risk_engine, setting)

        with patch("vnpy_riskmanager.rules.rolling_window_rule.time.time", return_value=1000.0):
            for _ in range(5):
                result: bool = rule.check_allowed(sample_order_request, "CTP")
                assert result is True

        assert len(rule.order_timestamps) == 5
        mock_risk_engine.write_log.assert_not_called()

    def test_order_at_limit(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试委托频率达到限制时拦截"""
        setting: dict = {"rolling_order_limit": 5, "rolling_window_seconds": 1.0}
        rule: RollingWindowRule = RollingWindowRule(mock_risk_engine, setting)

        # 在同一时间发送 6 笔委托
        with patch("vnpy_riskmanager.rules.rolling_window_rule.time.time", return_value=1000.0):
            for _ in range(5):
                rule.check_allowed(sample_order_request, "CTP")

            result: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result is False
        mock_risk_engine.write_log.assert_called_once()
        assert "委托频率过快" in str(mock_risk_engine.write_log.call_args)

    def test_cancel_below_limit(
        self,
        mock_risk_engine: Mock,
        sample_cancel_request: CancelRequest
    ) -> None:
        """测试撤单频率未超限时允许"""
        setting: dict = {"rolling_cancel_limit": 10}
        rule: RollingWindowRule = RollingWindowRule(mock_risk_engine, setting)

        with patch("vnpy_riskmanager.rules.rolling_window_rule.time.time", return_value=1000.0):
            for _ in range(5):
                result: bool = rule.check_cancel_allowed(sample_cancel_request)
                assert result is True

        assert len(rule.cancel_timestamps) == 5
        mock_risk_engine.write_log.assert_not_called()

    def test_cancel_at_limit(
        self,
        mock_risk_engine: Mock,
        sample_cancel_request: CancelRequest
    ) -> None:
        """测试撤单频率达到限制时拦截"""
        setting: dict = {"rolling_cancel_limit": 5, "rolling_window_seconds": 1.0}
        rule: RollingWindowRule = RollingWindowRule(mock_risk_engine, setting)

        # 在同一时间发送 6 笔撤单
        with patch("vnpy_riskmanager.rules.rolling_window_rule.time.time", return_value=1000.0):
            for _ in range(5):
                rule.check_cancel_allowed(sample_cancel_request)

            result: bool = rule.check_cancel_allowed(sample_cancel_request)

        assert result is False
        mock_risk_engine.write_log.assert_called_once()
        assert "撤单频率过快" in str(mock_risk_engine.write_log.call_args)

    def test_window_cleanup_orders(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试委托时间窗口清理功能"""
        setting: dict = {"rolling_order_limit": 5, "rolling_window_seconds": 1.0}
        rule: RollingWindowRule = RollingWindowRule(mock_risk_engine, setting)

        # 在 t=1000 时发送 5 笔
        with patch("vnpy_riskmanager.rules.rolling_window_rule.time.time", return_value=1000.0):
            for _ in range(5):
                rule.check_allowed(sample_order_request, "CTP")

        # 在 t=1001.5 时再发送（超过 1 秒窗口，旧数据应被清理）
        with patch("vnpy_riskmanager.rules.rolling_window_rule.time.time", return_value=1001.5):
            result: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result is True
        assert len(rule.order_timestamps) == 1
        mock_risk_engine.write_log.assert_not_called()

    def test_window_cleanup_cancels(
        self,
        mock_risk_engine: Mock,
        sample_cancel_request: CancelRequest
    ) -> None:
        """测试撤单时间窗口清理功能"""
        setting: dict = {"rolling_cancel_limit": 5, "rolling_window_seconds": 1.0}
        rule: RollingWindowRule = RollingWindowRule(mock_risk_engine, setting)

        # 在 t=1000 时发送 5 笔
        with patch("vnpy_riskmanager.rules.rolling_window_rule.time.time", return_value=1000.0):
            for _ in range(5):
                rule.check_cancel_allowed(sample_cancel_request)

        # 在 t=1001.5 时再发送（超过 1 秒窗口，旧数据应被清理）
        with patch("vnpy_riskmanager.rules.rolling_window_rule.time.time", return_value=1001.5):
            result: bool = rule.check_cancel_allowed(sample_cancel_request)

        assert result is True
        assert len(rule.cancel_timestamps) == 1
        mock_risk_engine.write_log.assert_not_called()

    def test_order_and_cancel_separate(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        sample_cancel_request: CancelRequest
    ) -> None:
        """测试委托和撤单计数器独立"""
        setting: dict = {"rolling_order_limit": 10, "rolling_cancel_limit": 10}
        rule: RollingWindowRule = RollingWindowRule(mock_risk_engine, setting)

        with patch("vnpy_riskmanager.rules.rolling_window_rule.time.time", return_value=1000.0):
            # 发送 5 笔委托
            for _ in range(5):
                rule.check_allowed(sample_order_request, "CTP")

            # 发送 3 笔撤单
            for _ in range(3):
                rule.check_cancel_allowed(sample_cancel_request)

        assert len(rule.order_timestamps) == 5
        assert len(rule.cancel_timestamps) == 3

    def test_sliding_window_behavior(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试滑动窗口行为"""
        setting: dict = {"rolling_order_limit": 3, "rolling_window_seconds": 1.0}
        rule: RollingWindowRule = RollingWindowRule(mock_risk_engine, setting)

        # t=1000: 发送 3 笔
        with patch("vnpy_riskmanager.rules.rolling_window_rule.time.time", return_value=1000.0):
            for _ in range(3):
                rule.check_allowed(sample_order_request, "CTP")

        # t=1000.5: 再发一笔（窗口内已有3笔，应拦截）
        with patch("vnpy_riskmanager.rules.rolling_window_rule.time.time", return_value=1000.5):
            result1: bool = rule.check_allowed(sample_order_request, "CTP")

        # t=1001.1: 再发一笔（前3笔已超出窗口，应允许）
        with patch("vnpy_riskmanager.rules.rolling_window_rule.time.time", return_value=1001.1):
            result2: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result1 is False
        assert result2 is True

    def test_log_message_format(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试日志消息格式"""
        setting: dict = {"rolling_order_limit": 1, "rolling_window_seconds": 1.0}
        rule: RollingWindowRule = RollingWindowRule(mock_risk_engine, setting)

        with patch("vnpy_riskmanager.rules.rolling_window_rule.time.time", return_value=1000.0):
            rule.check_allowed(sample_order_request, "CTP")
            rule.check_allowed(sample_order_request, "CTP")

        log_message: str = str(mock_risk_engine.write_log.call_args[0][0])
        assert "委托频率过快" in log_message
        assert "秒内" in log_message

