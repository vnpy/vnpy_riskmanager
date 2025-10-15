"""OrderValidityRule 测试用例"""
from unittest.mock import Mock

from vnpy.trader.object import OrderRequest, ContractData
from vnpy.trader.constant import Exchange, Product

from vnpy_riskmanager.rules.order_validity_rule import OrderValidityRule


class TestOrderValidityRule:
    """委托指令合法性监控规则测试"""

    def test_init_with_default_setting(self, mock_risk_engine: Mock) -> None:
        """测试使用默认配置初始化"""
        rule: OrderValidityRule = OrderValidityRule(mock_risk_engine, {})
        assert rule.check_contract_exists is True
        assert rule.check_price_tick is True
        assert rule.check_volume_limit is False
        assert rule.max_order_volume == 1000

    def test_init_with_custom_setting(self, mock_risk_engine: Mock) -> None:
        """测试使用自定义配置初始化"""
        setting: dict = {
            "check_contract_exists": False,
            "check_price_tick": False,
            "check_volume_limit": True,
            "max_order_volume": 500
        }
        rule: OrderValidityRule = OrderValidityRule(mock_risk_engine, setting)
        assert rule.check_contract_exists is False
        assert rule.check_price_tick is False
        assert rule.check_volume_limit is True
        assert rule.max_order_volume == 500

    def test_contract_not_exists(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试合约不存在时拦截"""
        mock_risk_engine.get_contract = Mock(return_value=None)
        rule: OrderValidityRule = OrderValidityRule(mock_risk_engine, {})

        result: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result is False
        mock_risk_engine.write_log.assert_called_once()
        assert "合约" in str(mock_risk_engine.write_log.call_args)
        assert "不存在" in str(mock_risk_engine.write_log.call_args)

    def test_price_tick_valid(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试价格为 pricetick 整数倍时通过"""
        contract: ContractData = ContractData(
            symbol="IF2501",
            exchange=Exchange.CFFEX,
            name="沪深300指数期货",
            product=Product.FUTURES,
            size=300.0,
            pricetick=0.2,
            gateway_name="CTP"
        )
        mock_risk_engine.get_contract = Mock(return_value=contract)

        # 价格是 0.2 的整数倍
        sample_order_request.price = 4000.0
        rule: OrderValidityRule = OrderValidityRule(mock_risk_engine, {})

        result: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result is True
        mock_risk_engine.write_log.assert_not_called()

    def test_price_tick_invalid(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试价格不是 pricetick 整数倍时拦截"""
        contract: ContractData = ContractData(
            symbol="IF2501",
            exchange=Exchange.CFFEX,
            name="沪深300指数期货",
            product=Product.FUTURES,
            size=300.0,
            pricetick=0.2,
            gateway_name="CTP"
        )
        mock_risk_engine.get_contract = Mock(return_value=contract)

        # 价格不是 0.2 的整数倍
        sample_order_request.price = 4000.1
        rule: OrderValidityRule = OrderValidityRule(mock_risk_engine, {})

        result: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result is False
        mock_risk_engine.write_log.assert_called_once()
        assert "价格" in str(mock_risk_engine.write_log.call_args)
        assert "最小变动价位" in str(mock_risk_engine.write_log.call_args)

    def test_volume_limit_pass(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试数量在限制内时通过"""
        setting: dict = {"check_contract_exists": False, "check_volume_limit": True, "max_order_volume": 100}
        rule: OrderValidityRule = OrderValidityRule(mock_risk_engine, setting)

        sample_order_request.volume = 50.0
        result: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result is True
        mock_risk_engine.write_log.assert_not_called()

    def test_volume_limit_exceed(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试数量超过限制时拦截"""
        setting: dict = {"check_contract_exists": False, "check_volume_limit": True, "max_order_volume": 100}
        rule: OrderValidityRule = OrderValidityRule(mock_risk_engine, setting)

        sample_order_request.volume = 150.0
        result: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result is False
        mock_risk_engine.write_log.assert_called_once()
        assert "数量" in str(mock_risk_engine.write_log.call_args)
        assert "超过" in str(mock_risk_engine.write_log.call_args)

    def test_all_checks_disabled(
        self,
        mock_risk_engine: Mock,
        sample_order_request: OrderRequest
    ) -> None:
        """测试所有检查关闭时直接通过"""
        setting: dict = {
            "check_contract_exists": False,
            "check_price_tick": False,
            "check_volume_limit": False
        }
        rule: OrderValidityRule = OrderValidityRule(mock_risk_engine, setting)

        result: bool = rule.check_allowed(sample_order_request, "CTP")

        assert result is True
        mock_risk_engine.write_log.assert_not_called()

