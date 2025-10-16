"""DailyLimitRule 测试用例"""
from unittest.mock import Mock, patch
from datetime import datetime

from vnpy.trader.object import OrderRequest, CancelRequest

from vnpy_riskmanager.rules.daily_limit_rule import DailyLimitRule


class TestDailyLimitRule:
    """全天委托/撤单笔数监控规则测试"""

    def test_init_with_default_setting(self, mock_risk_engine: Mock) -> None:
        """测试使用默认配置初始化"""
        rule: DailyLimitRule = DailyLimitRule(mock_risk_engine, {})
        assert rule.daily_order_limit == 1000
        assert rule.daily_cancel_limit == 500
        assert rule.order_count == 0
        assert rule.cancel_count == 0

    def test_init_with_custom_setting(self, mock_risk_engine: Mock) -> None:
        """测试使用自定义配置初始化"""
        setting: dict = {"daily_order_limit": 500, "daily_cancel_limit": 200}
        rule: DailyLimitRule = DailyLimitRule(mock_risk_engine, setting)
        assert rule.daily_order_limit == 500
        assert rule.daily_cancel_limit == 200

    def test_order_below_limit(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试委托笔数未超限时允许"""
        setting: dict = {"daily_order_limit": 10}
        rule: DailyLimitRule = DailyLimitRule(mock_risk_engine, setting)

        for _ in range(5):
            result: bool = rule.check_allowed(sample_order_request, "CTP")
            assert result is True

        assert rule.order_count == 5
        mock_risk_engine.write_log.assert_not_called()

    def test_order_at_limit(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试委托笔数达到限制时拦截"""
        setting: dict = {"daily_order_limit": 3}
        rule: DailyLimitRule = DailyLimitRule(mock_risk_engine, setting)

        # 发送 3 笔委托
        rule.check_allowed(sample_order_request, "CTP")
        rule.check_allowed(sample_order_request, "CTP")
        rule.check_allowed(sample_order_request, "CTP")

        # 第 4 笔被拦截
        result: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result is False
        assert rule.order_count == 3
        mock_risk_engine.write_log.assert_called_once()
        assert "委托笔数" in str(mock_risk_engine.write_log.call_args)

    def test_cancel_below_limit(
        self,
        mock_risk_engine: Mock,
        sample_cancel_request: CancelRequest
    ) -> None:
        """测试撤单笔数未超限时允许"""
        setting: dict = {"daily_cancel_limit": 10}
        rule: DailyLimitRule = DailyLimitRule(mock_risk_engine, setting)

        for _ in range(5):
            result: bool = rule.check_cancel_allowed(sample_cancel_request)
            assert result is True

        assert rule.cancel_count == 5
        mock_risk_engine.write_log.assert_not_called()

    def test_cancel_at_limit(
        self,
        mock_risk_engine: Mock,
        sample_cancel_request: CancelRequest
    ) -> None:
        """测试撤单笔数达到限制时拦截"""
        setting: dict = {"daily_cancel_limit": 3}
        rule: DailyLimitRule = DailyLimitRule(mock_risk_engine, setting)

        # 发送 3 笔撤单
        rule.check_cancel_allowed(sample_cancel_request)
        rule.check_cancel_allowed(sample_cancel_request)
        rule.check_cancel_allowed(sample_cancel_request)

        # 第 4 笔被拦截
        result: bool = rule.check_cancel_allowed(sample_cancel_request)

        assert result is False
        assert rule.cancel_count == 3
        mock_risk_engine.write_log.assert_called_once()
        assert "撤单笔数" in str(mock_risk_engine.write_log.call_args)

    def test_date_change_reset(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试日期变更后计数器重置"""
        setting: dict = {"daily_order_limit": 5}
        rule: DailyLimitRule = DailyLimitRule(mock_risk_engine, setting)

        # 第一天发送 5 笔
        with patch("vnpy_riskmanager.rules.daily_limit_rule.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 10, 0, 0)
            mock_datetime.strftime = datetime.strftime
            for _ in range(5):
                rule.check_allowed(sample_order_request, "CTP")

            assert rule.order_count == 5

        # 第二天重置
        with patch("vnpy_riskmanager.rules.daily_limit_rule.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 2, 10, 0, 0)
            mock_datetime.strftime = datetime.strftime
            result: bool = rule.check_allowed(sample_order_request, "CTP")

            assert result is True
            assert rule.order_count == 1

    def test_order_and_cancel_separate(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        sample_cancel_request: CancelRequest
    ) -> None:
        """测试委托和撤单计数器独立"""
        setting: dict = {"daily_order_limit": 10, "daily_cancel_limit": 10}
        rule: DailyLimitRule = DailyLimitRule(mock_risk_engine, setting)

        # 发送 5 笔委托
        for _ in range(5):
            rule.check_allowed(sample_order_request, "CTP")

        # 发送 3 笔撤单
        for _ in range(3):
            rule.check_cancel_allowed(sample_cancel_request)

        assert rule.order_count == 5
        assert rule.cancel_count == 3

    def test_same_date_multiple_times(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试同一天多次调用不重置计数器"""
        setting: dict = {"daily_order_limit": 100}
        rule: DailyLimitRule = DailyLimitRule(mock_risk_engine, setting)

        with patch("vnpy_riskmanager.rules.daily_limit_rule.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 10, 0, 0)
            mock_datetime.strftime = datetime.strftime
            rule.check_allowed(sample_order_request, "CTP")
            rule.check_allowed(sample_order_request, "CTP")
            rule.check_allowed(sample_order_request, "CTP")

            assert rule.order_count == 3

