"""ActiveOrderRule 测试用例"""
from collections.abc import Callable
from unittest.mock import Mock


from vnpy.trader.object import OrderRequest, OrderData

from vnpy_riskmanager.rules.active_order_rule import ActiveOrderRule


class TestActiveOrderRule:
    """活动委托数量上限规则测试"""

    def test_init_with_default_setting(self, mock_risk_engine: Mock) -> None:
        """测试使用默认配置初始化"""
        rule: ActiveOrderRule = ActiveOrderRule(mock_risk_engine, {})
        assert rule.active_order_limit == 10

    def test_init_with_custom_setting(self, mock_risk_engine: Mock) -> None:
        """测试使用自定义配置初始化"""
        setting: dict = {"active_order_limit": 20}
        rule: ActiveOrderRule = ActiveOrderRule(mock_risk_engine, setting)
        assert rule.active_order_limit == 20

    def test_check_allowed_with_zero_active_orders(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试无活动委托时允许下单"""
        rule: ActiveOrderRule = ActiveOrderRule(mock_risk_engine, setting_factory({}))
        mock_risk_engine.get_all_active_orders.return_value = []

        result: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result is True
        mock_risk_engine.write_log.assert_not_called()

    def test_check_allowed_below_limit(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict],
        active_orders_factory: Callable[[int], list[OrderData]]
    ) -> None:
        """测试活动委托数量小于上限时允许下单"""
        rule: ActiveOrderRule = ActiveOrderRule(mock_risk_engine, setting_factory({}))
        mock_risk_engine.get_all_active_orders.return_value = active_orders_factory(5)

        result: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result is True
        mock_risk_engine.write_log.assert_not_called()

    def test_check_allowed_at_limit(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict],
        active_orders_factory: Callable[[int], list[OrderData]]
    ) -> None:
        """测试活动委托数量等于上限时拒绝下单"""
        setting: dict = setting_factory({"active_order_limit": 10})
        rule: ActiveOrderRule = ActiveOrderRule(mock_risk_engine, setting)
        mock_risk_engine.get_all_active_orders.return_value = active_orders_factory(10)

        result: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result is False
        mock_risk_engine.write_log.assert_called_once()
        log_msg: str = mock_risk_engine.write_log.call_args[0][0]
        assert "活动委托数量10达到上限10" in log_msg

    def test_check_allowed_above_limit(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict],
        active_orders_factory: Callable[[int], list[OrderData]]
    ) -> None:
        """测试活动委托数量超过上限时拒绝下单"""
        setting: dict = setting_factory({"active_order_limit": 10})
        rule: ActiveOrderRule = ActiveOrderRule(mock_risk_engine, setting)
        mock_risk_engine.get_all_active_orders.return_value = active_orders_factory(15)

        result: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result is False
        mock_risk_engine.write_log.assert_called_once()

    def test_check_allowed_boundary_case(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict],
        active_orders_factory: Callable[[int], list[OrderData]]
    ) -> None:
        """测试边界条件：恰好在上限前一笔"""
        setting: dict = setting_factory({"active_order_limit": 10})
        rule: ActiveOrderRule = ActiveOrderRule(mock_risk_engine, setting)
        mock_risk_engine.get_all_active_orders.return_value = active_orders_factory(9)

        result: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result is True
        mock_risk_engine.write_log.assert_not_called()

    def test_check_allowed_with_limit_one(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict],
        active_orders_factory: Callable[[int], list[OrderData]]
    ) -> None:
        """测试上限为1时的行为"""
        setting: dict = setting_factory({"active_order_limit": 1})
        rule: ActiveOrderRule = ActiveOrderRule(mock_risk_engine, setting)

        # 无活动委托时允许
        mock_risk_engine.get_all_active_orders.return_value = []
        assert rule.check_allowed(sample_order_request, "CTP") is True

        # 有1个活动委托时拒绝
        mock_risk_engine.get_all_active_orders.return_value = active_orders_factory(1)
        assert rule.check_allowed(sample_order_request, "CTP") is False

    def test_check_allowed_with_large_limit(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict],
        active_orders_factory: Callable[[int], list[OrderData]]
    ) -> None:
        """测试大上限值的行为"""
        setting: dict = setting_factory({"active_order_limit": 1000})
        rule: ActiveOrderRule = ActiveOrderRule(mock_risk_engine, setting)
        mock_risk_engine.get_all_active_orders.return_value = active_orders_factory(500)

        result: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result is True
        mock_risk_engine.write_log.assert_not_called()

    def test_log_message_format(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict],
        active_orders_factory: Callable[[int], list[OrderData]]
    ) -> None:
        """测试日志消息格式正确"""
        setting: dict = setting_factory({"active_order_limit": 5})
        rule: ActiveOrderRule = ActiveOrderRule(mock_risk_engine, setting)
        mock_risk_engine.get_all_active_orders.return_value = active_orders_factory(5)

        rule.check_allowed(sample_order_request, "CTP")

        log_msg: str = mock_risk_engine.write_log.call_args[0][0]
        assert "活动委托数量" in log_msg
        assert "5" in log_msg
        assert "上限" in log_msg

    def test_multiple_checks(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict],
        active_orders_factory: Callable[[int], list[OrderData]]
    ) -> None:
        """测试多次连续检查"""
        setting: dict = setting_factory({"active_order_limit": 10})
        rule: ActiveOrderRule = ActiveOrderRule(mock_risk_engine, setting)

        # 第一次检查：5个活动委托
        mock_risk_engine.get_all_active_orders.return_value = active_orders_factory(5)
        assert rule.check_allowed(sample_order_request, "CTP") is True

        # 第二次检查：10个活动委托
        mock_risk_engine.get_all_active_orders.return_value = active_orders_factory(10)
        assert rule.check_allowed(sample_order_request, "CTP") is False

        # 第三次检查：3个活动委托
        mock_risk_engine.get_all_active_orders.return_value = active_orders_factory(3)
        assert rule.check_allowed(sample_order_request, "CTP") is True

    def test_rule_engine_integration(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试与 RiskEngine 的集成"""
        rule: ActiveOrderRule = ActiveOrderRule(mock_risk_engine, setting_factory({}))

        # 验证 risk_engine 属性正确设置
        assert rule.risk_engine == mock_risk_engine

        # 验证调用了 risk_engine 的方法
        mock_risk_engine.get_all_active_orders.return_value = []
        rule.check_allowed(sample_order_request, "CTP")
        mock_risk_engine.get_all_active_orders.assert_called()

    def test_different_gateway_names(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict],
        active_orders_factory: Callable[[int], list[OrderData]]
    ) -> None:
        """测试不同网关名称不影响检查"""
        rule: ActiveOrderRule = ActiveOrderRule(mock_risk_engine, setting_factory({}))
        mock_risk_engine.get_all_active_orders.return_value = active_orders_factory(5)

        # 不同网关名称应该返回相同结果
        assert rule.check_allowed(sample_order_request, "CTP") is True
        assert rule.check_allowed(sample_order_request, "OES") is True
        assert rule.check_allowed(sample_order_request, "IB") is True
