from typing import cast

from vnpy.trader.constant import Direction, Exchange, Offset, OrderType, Product
from vnpy.trader.object import ContractData, OrderRequest

from vnpy_riskmanager.engine import RiskEngine
from vnpy_riskmanager.rules.duplicate_order_rule import DuplicateOrderRule
from vnpy_riskmanager.rules.order_size_rule import OrderSizeRule
from vnpy_riskmanager.rules.order_validity_rule import OrderValidityRule


LEGAL_VOLUME: float = 1
LEGAL_PRICE: float = 2


class FakeRiskEngine:
    def __init__(self, contract: ContractData) -> None:
        self.contract: ContractData = contract

    def get_contract(self, vt_symbol: str) -> ContractData | None:
        if vt_symbol == self.contract.vt_symbol:
            return self.contract
        return None

    def write_log(self, msg: str) -> None:
        return None

    def put_rule_event(self, rule: object) -> None:
        return None


def make_contract() -> ContractData:
    return ContractData(
        symbol="rb2510",
        exchange=Exchange.SHFE,
        name="rb2510",
        product=Product.FUTURES,
        size=10,
        pricetick=1,
        min_volume=1,
        max_volume=100,
        gateway_name="CTP",
    )


def make_request(volume: float, price: float) -> OrderRequest:
    return OrderRequest(
        symbol="rb2510",
        exchange=Exchange.SHFE,
        direction=Direction.LONG,
        type=OrderType.LIMIT,
        volume=volume,
        price=price,
        offset=Offset.OPEN,
    )


def make_engine(contract: ContractData) -> FakeRiskEngine:
    return FakeRiskEngine(contract)


class TestRiskRules:
    def test_order_size_rejects_oversized_volume(self) -> None:
        contract: ContractData = make_contract()
        rule: OrderSizeRule = OrderSizeRule(cast(RiskEngine, make_engine(contract)), {})
        volume: float = float(rule.order_volume_limit + 1)

        allowed: bool = rule.check_allowed(make_request(volume, LEGAL_PRICE), "CTP")

        assert allowed is False

    def test_order_validity_rejects_invalid_price_tick(self) -> None:
        contract: ContractData = make_contract()
        rule: OrderValidityRule = OrderValidityRule(cast(RiskEngine, make_engine(contract)), {})

        allowed: bool = rule.check_allowed(make_request(LEGAL_VOLUME, 2.5), "CTP")

        assert allowed is False

    def test_duplicate_order_rejects_at_limit(self) -> None:
        contract: ContractData = make_contract()
        rule: DuplicateOrderRule = DuplicateOrderRule(cast(RiskEngine, make_engine(contract)), {})
        request: OrderRequest = make_request(LEGAL_VOLUME, LEGAL_PRICE)

        for _ in range(rule.duplicate_order_limit - 1):
            assert rule.check_allowed(request, "CTP") is True

        allowed: bool = rule.check_allowed(request, "CTP")

        assert allowed is False

    def test_legal_order_is_allowed(self) -> None:
        contract: ContractData = make_contract()
        request: OrderRequest = make_request(LEGAL_VOLUME, LEGAL_PRICE)
        engine: FakeRiskEngine = make_engine(contract)

        assert OrderSizeRule(cast(RiskEngine, engine), {}).check_allowed(request, "CTP") is True
        assert OrderValidityRule(cast(RiskEngine, engine), {}).check_allowed(request, "CTP") is True
        assert DuplicateOrderRule(cast(RiskEngine, engine), {}).check_allowed(request, "CTP") is True
