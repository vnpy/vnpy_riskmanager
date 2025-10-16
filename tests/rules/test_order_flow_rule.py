"""OrderFlowRule 测试用例"""
from collections.abc import Callable
from unittest.mock import Mock


from vnpy.trader.object import OrderRequest

from vnpy_riskmanager.rules.order_flow_rule import OrderFlowRule


class TestOrderFlowRule:
    """委托流速控制规则测试"""

    def test_init_with_default_setting(self, mock_risk_engine: Mock) -> None:
        """测试使用默认配置初始化"""
        rule: OrderFlowRule = OrderFlowRule(mock_risk_engine, {})
        assert rule.order_flow_limit == 10
        assert rule.order_flow_clear == 1
        assert rule.order_flow_count == 0
        assert rule.order_flow_timer == 0

    def test_init_with_custom_setting(self, mock_risk_engine: Mock) -> None:
        """测试使用自定义配置初始化"""
        setting: dict = {"order_flow_limit": 20, "order_flow_clear": 3}
        rule: OrderFlowRule = OrderFlowRule(mock_risk_engine, setting)
        assert rule.order_flow_limit == 20
        assert rule.order_flow_clear == 3
        assert rule.order_flow_count == 0
        assert rule.order_flow_timer == 0

    def test_check_allowed_first_order(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试第一笔委托允许通过"""
        rule: OrderFlowRule = OrderFlowRule(mock_risk_engine, setting_factory({}))

        result: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result is True
        assert rule.order_flow_count == 1
        mock_risk_engine.write_log.assert_not_called()

    def test_check_allowed_below_limit(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试流速未达上限时允许下单"""
        setting: dict = setting_factory({"order_flow_limit": 10})
        rule: OrderFlowRule = OrderFlowRule(mock_risk_engine, setting)

        # 连续5笔委托
        for i in range(5):
            result: bool = rule.check_allowed(sample_order_request, "CTP")
            assert result is True
            assert rule.order_flow_count == i + 1

        mock_risk_engine.write_log.assert_not_called()

    def test_check_allowed_at_limit(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试流速等于上限时允许通过"""
        setting: dict = setting_factory({"order_flow_limit": 10})
        rule: OrderFlowRule = OrderFlowRule(mock_risk_engine, setting)

        # 恰好10笔委托
        for _ in range(10):
            result: bool = rule.check_allowed(sample_order_request, "CTP")
            assert result is True

        assert rule.order_flow_count == 10
        mock_risk_engine.write_log.assert_not_called()

    def test_check_allowed_above_limit(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试流速超过上限时拒绝下单"""
        setting: dict = setting_factory({"order_flow_limit": 10})
        rule: OrderFlowRule = OrderFlowRule(mock_risk_engine, setting)

        # 前10笔允许
        for _ in range(10):
            assert rule.check_allowed(sample_order_request, "CTP") is True

        # 第11笔拒绝
        result: bool = rule.check_allowed(sample_order_request, "CTP")
        assert result is False
        assert rule.order_flow_count == 11

        mock_risk_engine.write_log.assert_called_once()
        log_msg: str = mock_risk_engine.write_log.call_args[0][0]
        assert "委托流速过快" in log_msg
        assert "10" in log_msg

    def test_on_timer_reset_counter(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试定时器重置流速计数"""
        setting: dict = setting_factory({"order_flow_limit": 10, "order_flow_clear": 1})
        rule: OrderFlowRule = OrderFlowRule(mock_risk_engine, setting)

        # 发送5笔委托
        for _ in range(5):
            rule.check_allowed(sample_order_request, "CTP")
        assert rule.order_flow_count == 5

        # 触发定时器（1秒后）
        rule.on_timer()
        assert rule.order_flow_count == 0
        assert rule.order_flow_timer == 0

    def test_on_timer_with_longer_clear_period(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试更长清零周期的定时器行为"""
        setting: dict = setting_factory({"order_flow_limit": 10, "order_flow_clear": 3})
        rule: OrderFlowRule = OrderFlowRule(mock_risk_engine, setting)

        rule.order_flow_count = 5

        # 第1秒
        rule.on_timer()
        assert rule.order_flow_timer == 1
        assert rule.order_flow_count == 5

        # 第2秒
        rule.on_timer()
        assert rule.order_flow_timer == 2
        assert rule.order_flow_count == 5

        # 第3秒 - 应该清零
        rule.on_timer()
        assert rule.order_flow_timer == 0
        assert rule.order_flow_count == 0

    def test_multiple_periods(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试跨多个周期的行为"""
        setting: dict = setting_factory({"order_flow_limit": 5, "order_flow_clear": 1})
        rule: OrderFlowRule = OrderFlowRule(mock_risk_engine, setting)

        # 第一个周期：5笔委托
        for _ in range(5):
            assert rule.check_allowed(sample_order_request, "CTP") is True

        # 第6笔应该拒绝
        assert rule.check_allowed(sample_order_request, "CTP") is False

        # 定时器清零
        rule.on_timer()

        # 第二个周期：又可以发5笔
        for _ in range(5):
            assert rule.check_allowed(sample_order_request, "CTP") is True

        # 第6笔再次拒绝
        assert rule.check_allowed(sample_order_request, "CTP") is False

    def test_boundary_condition(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试边界条件"""
        setting: dict = setting_factory({"order_flow_limit": 1})
        rule: OrderFlowRule = OrderFlowRule(mock_risk_engine, setting)

        # 第1笔允许
        assert rule.check_allowed(sample_order_request, "CTP") is True
        assert rule.order_flow_count == 1

        # 第2笔拒绝
        assert rule.check_allowed(sample_order_request, "CTP") is False
        assert rule.order_flow_count == 2

    def test_log_message_format(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试日志消息格式"""
        setting: dict = setting_factory({"order_flow_limit": 5, "order_flow_clear": 2})
        rule: OrderFlowRule = OrderFlowRule(mock_risk_engine, setting)

        # 超过限制
        for _ in range(6):
            rule.check_allowed(sample_order_request, "CTP")

        log_msg: str = mock_risk_engine.write_log.call_args[0][0]
        assert "委托流速过快" in log_msg
        assert "2秒" in log_msg
        assert "5笔" in log_msg

    def test_counter_increment(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试计数器正确递增"""
        rule: OrderFlowRule = OrderFlowRule(mock_risk_engine, setting_factory({}))

        for i in range(1, 11):
            rule.check_allowed(sample_order_request, "CTP")
            assert rule.order_flow_count == i

    def test_timer_increment(
        self,
        mock_risk_engine: Mock,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试定时器计数器正确递增"""
        setting: dict = setting_factory({"order_flow_clear": 5})
        rule: OrderFlowRule = OrderFlowRule(mock_risk_engine, setting)

        for i in range(1, 5):
            rule.on_timer()
            assert rule.order_flow_timer == i

        # 第5秒应该清零
        rule.on_timer()
        assert rule.order_flow_timer == 0

    def test_timer_without_orders(
        self,
        mock_risk_engine: Mock,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试无委托时定时器行为"""
        setting: dict = setting_factory({"order_flow_clear": 2})
        rule: OrderFlowRule = OrderFlowRule(mock_risk_engine, setting)

        assert rule.order_flow_count == 0
        rule.on_timer()
        assert rule.order_flow_timer == 1
        rule.on_timer()
        assert rule.order_flow_timer == 0
        assert rule.order_flow_count == 0

    def test_rejected_orders_still_counted(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试被拒绝的委托仍然计数"""
        setting: dict = setting_factory({"order_flow_limit": 5})
        rule: OrderFlowRule = OrderFlowRule(mock_risk_engine, setting)

        # 前5笔允许
        for _ in range(5):
            rule.check_allowed(sample_order_request, "CTP")

        # 第6笔拒绝，但计数增加
        rule.check_allowed(sample_order_request, "CTP")
        assert rule.order_flow_count == 6

        # 第7笔继续拒绝
        result: bool = rule.check_allowed(sample_order_request, "CTP")
        assert result is False
        assert rule.order_flow_count == 7

    def test_large_flow_limit(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试大流速限制"""
        setting: dict = setting_factory({"order_flow_limit": 1000})
        rule: OrderFlowRule = OrderFlowRule(mock_risk_engine, setting)

        for _ in range(500):
            result: bool = rule.check_allowed(sample_order_request, "CTP")
            assert result is True

        assert rule.order_flow_count == 500

    def test_integration_with_risk_engine(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试与 RiskEngine 的集成"""
        rule: OrderFlowRule = OrderFlowRule(mock_risk_engine, setting_factory({}))

        assert rule.risk_engine == mock_risk_engine

        # 触发限制后验证日志调用
        for _ in range(11):
            rule.check_allowed(sample_order_request, "CTP")

        mock_risk_engine.write_log.assert_called()

    def test_different_gateways(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试不同网关不影响流速统计"""
        setting: dict = setting_factory({"order_flow_limit": 5})
        rule: OrderFlowRule = OrderFlowRule(mock_risk_engine, setting)

        # 混合不同网关
        rule.check_allowed(sample_order_request, "CTP")
        rule.check_allowed(sample_order_request, "OES")
        rule.check_allowed(sample_order_request, "IB")

        # 计数应该累加，不区分网关
        assert rule.order_flow_count == 3
