"""测试共享 fixtures"""
from typing import Callable
from unittest.mock import Mock, MagicMock

import pytest

from vnpy.trader.object import OrderRequest, CancelRequest, OrderData
from vnpy.trader.constant import Direction, Offset, OrderType, Exchange, Status


@pytest.fixture
def mock_event_engine() -> Mock:
    """Mock EventEngine"""
    return Mock()


@pytest.fixture
def mock_main_engine() -> Mock:
    """Mock MainEngine"""
    engine: Mock = Mock()
    engine.get_all_active_orders = Mock(return_value=[])
    engine.get_contract = Mock(return_value=None)
    return engine


@pytest.fixture
def mock_risk_engine(mock_main_engine: Mock, mock_event_engine: Mock) -> Mock:
    """Mock RiskEngine"""
    risk_engine: Mock = Mock()
    risk_engine.main_engine = mock_main_engine
    risk_engine.event_engine = mock_event_engine
    risk_engine.write_log = Mock()
    risk_engine.get_all_active_orders = Mock(return_value=[])
    risk_engine.get_contract = Mock(return_value=None)
    return risk_engine


@pytest.fixture
def setting_factory() -> Callable[[dict], dict]:
    """配置字典工厂"""
    def factory(overrides: dict | None = None) -> dict:
        default: dict = {
            "active_order_limit": 10,
            "order_size_limit": 100,
            "order_flow_limit": 10,
            "order_flow_clear": 1,
            "cancel_limit": 10,
            "cancel_window": 1,
        }
        if overrides:
            default.update(overrides)
        return default
    return factory


@pytest.fixture
def sample_order_request() -> OrderRequest:
    """标准委托请求"""
    req: OrderRequest = OrderRequest(
        symbol="IF2501",
        exchange=Exchange.CFFEX,
        direction=Direction.LONG,
        type=OrderType.LIMIT,
        volume=10.0,
        price=4000.0,
        offset=Offset.OPEN,
        reference="test_order"
    )
    return req


@pytest.fixture
def sample_cancel_request() -> CancelRequest:
    """标准撤单请求"""
    req: CancelRequest = CancelRequest(
        orderid="123456",
        symbol="IF2501",
        exchange=Exchange.CFFEX
    )
    return req


@pytest.fixture
def active_orders_factory() -> Callable[[int], list[OrderData]]:
    """活动委托数据工厂"""
    def factory(count: int) -> list[OrderData]:
        orders: list[OrderData] = []
        for i in range(count):
            order: OrderData = OrderData(
                symbol="IF2501",
                exchange=Exchange.CFFEX,
                orderid=f"order_{i}",
                type=OrderType.LIMIT,
                direction=Direction.LONG,
                offset=Offset.OPEN,
                price=4000.0,
                volume=10.0,
                traded=0.0,
                status=Status.NOTTRADED,
                datetime=None,
                gateway_name="CTP"
            )
            orders.append(order)
        return orders
    return factory
