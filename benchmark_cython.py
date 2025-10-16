"""
Cython 性能基准测试

对比 Cython 优化后的风控规则性能提升
"""
import time
from unittest.mock import MagicMock

from vnpy.trader.object import (
    OrderRequest,
    CancelRequest,
    Direction,
    Offset,
    OrderType,
)
from vnpy.trader.constant import Exchange

# 导入 Cython 编译后的规则类
from vnpy_riskmanager.rules.order_size_rule import OrderSizeRule
from vnpy_riskmanager.rules.order_flow_rule import OrderFlowRule
from vnpy_riskmanager.rules.active_order_rule import ActiveOrderRule
from vnpy_riskmanager.rules.cancel_limit_rule import CancelLimitRule
from vnpy_riskmanager.rules.order_validity_rule import OrderValidityRule
from vnpy_riskmanager.rules.duplicate_order_rule import DuplicateOrderRule
from vnpy_riskmanager.rules.daily_limit_rule import DailyLimitRule
from vnpy_riskmanager.rules.rolling_window_rule import RollingWindowRule


def create_mock_engine() -> MagicMock:
    """创建模拟风控引擎"""
    engine = MagicMock()
    engine.write_log = MagicMock()
    engine.get_all_active_orders = MagicMock(return_value=[])
    engine.get_contract = MagicMock(return_value=None)
    return engine


def create_order_request() -> OrderRequest:
    """创建模拟委托请求"""
    req = OrderRequest(
        symbol="rb2505",
        exchange=Exchange.SHFE,
        direction=Direction.LONG,
        type=OrderType.LIMIT,
        volume=10,
        price=3500.0,
        offset=Offset.OPEN,
    )
    return req


def create_cancel_request() -> CancelRequest:
    """创建模拟撤单请求"""
    req = CancelRequest(
        orderid="rb2505.SHFE.123456",
        symbol="rb2505",
        exchange=Exchange.SHFE,
    )
    return req


def benchmark_order_size_rule(iterations: int = 100000) -> None:
    """基准测试：OrderSizeRule"""
    engine = create_mock_engine()
    setting = {"order_size_limit": 100}
    rule = OrderSizeRule(engine, setting)
    req = create_order_request()

    start = time.perf_counter()
    for _ in range(iterations):
        rule.check_allowed(req, "CTP")
    end = time.perf_counter()

    elapsed = end - start
    ops = iterations / elapsed
    print(
        f"OrderSizeRule: {iterations:,} 次调用耗时 {elapsed:.4f}s "
        f"| {ops:,.0f} ops/s"
    )


def benchmark_order_flow_rule(iterations: int = 100000) -> None:
    """基准测试：OrderFlowRule"""
    engine = create_mock_engine()
    setting = {"order_flow_limit": 10, "order_flow_clear": 1}
    rule = OrderFlowRule(engine, setting)
    req = create_order_request()

    start = time.perf_counter()
    for _ in range(iterations):
        rule.check_allowed(req, "CTP")
    end = time.perf_counter()

    elapsed = end - start
    ops = iterations / elapsed
    print(
        f"OrderFlowRule: {iterations:,} 次调用耗时 {elapsed:.4f}s "
        f"| {ops:,.0f} ops/s"
    )


def benchmark_active_order_rule(iterations: int = 100000) -> None:
    """基准测试：ActiveOrderRule"""
    engine = create_mock_engine()
    setting = {"active_order_limit": 10}
    rule = ActiveOrderRule(engine, setting)
    req = create_order_request()

    start = time.perf_counter()
    for _ in range(iterations):
        rule.check_allowed(req, "CTP")
    end = time.perf_counter()

    elapsed = end - start
    ops = iterations / elapsed
    print(
        f"ActiveOrderRule: {iterations:,} 次调用耗时 {elapsed:.4f}s "
        f"| {ops:,.0f} ops/s"
    )


def benchmark_cancel_limit_rule(iterations: int = 100000) -> None:
    """基准测试：CancelLimitRule（最复杂的规则）"""
    engine = create_mock_engine()
    setting = {"cancel_limit": 10, "cancel_window": 1}
    rule = CancelLimitRule(engine, setting)
    req = create_cancel_request()

    start = time.perf_counter()
    for _ in range(iterations):
        rule.check_cancel_allowed(req)
    end = time.perf_counter()

    elapsed = end - start
    ops = iterations / elapsed
    print(
        f"CancelLimitRule: {iterations:,} 次调用耗时 {elapsed:.4f}s "
        f"| {ops:,.0f} ops/s"
    )


def benchmark_order_validity_rule(iterations: int = 100000) -> None:
    """基准测试：OrderValidityRule"""
    engine = create_mock_engine()
    setting = {
        "check_contract_exists": False,
        "check_price_tick": False,
        "check_volume_limit": True,
        "max_order_volume": 1000
    }
    rule = OrderValidityRule(engine, setting)
    req = create_order_request()

    start = time.perf_counter()
    for _ in range(iterations):
        rule.check_allowed(req, "CTP")
    end = time.perf_counter()

    elapsed = end - start
    ops = iterations / elapsed
    print(
        f"OrderValidityRule: {iterations:,} 次调用耗时 {elapsed:.4f}s "
        f"| {ops:,.0f} ops/s"
    )


def benchmark_duplicate_order_rule(iterations: int = 100000) -> None:
    """基准测试：DuplicateOrderRule"""
    engine = create_mock_engine()
    setting = {"max_duplicate_orders": 3, "duplicate_window": 1.0}
    rule = DuplicateOrderRule(engine, setting)
    req = create_order_request()

    start = time.perf_counter()
    for _ in range(iterations):
        rule.check_allowed(req, "CTP")
    end = time.perf_counter()

    elapsed = end - start
    ops = iterations / elapsed
    print(
        f"DuplicateOrderRule: {iterations:,} 次调用耗时 {elapsed:.4f}s "
        f"| {ops:,.0f} ops/s"
    )


def benchmark_daily_limit_rule(iterations: int = 100000) -> None:
    """基准测试：DailyLimitRule"""
    engine = create_mock_engine()
    setting = {"daily_order_limit": 1000000, "daily_cancel_limit": 500000}
    rule = DailyLimitRule(engine, setting)
    req = create_order_request()

    start = time.perf_counter()
    for _ in range(iterations):
        rule.check_allowed(req, "CTP")
    end = time.perf_counter()

    elapsed = end - start
    ops = iterations / elapsed
    print(
        f"DailyLimitRule: {iterations:,} 次调用耗时 {elapsed:.4f}s "
        f"| {ops:,.0f} ops/s"
    )


def benchmark_rolling_window_rule(iterations: int = 100000) -> None:
    """基准测试：RollingWindowRule"""
    engine = create_mock_engine()
    setting = {
        "rolling_window_seconds": 1.0,
        "rolling_order_limit": 1000,
        "rolling_cancel_limit": 1000
    }
    rule = RollingWindowRule(engine, setting)
    req = create_order_request()

    start = time.perf_counter()
    for _ in range(iterations):
        rule.check_allowed(req, "CTP")
    end = time.perf_counter()

    elapsed = end - start
    ops = iterations / elapsed
    print(
        f"RollingWindowRule: {iterations:,} 次调用耗时 {elapsed:.4f}s "
        f"| {ops:,.0f} ops/s"
    )


if __name__ == "__main__":
    print("=" * 60)
    print("Cython 风控规则性能基准测试")
    print("=" * 60)
    print()

    benchmark_order_size_rule()
    benchmark_order_flow_rule()
    benchmark_active_order_rule()
    benchmark_cancel_limit_rule()
    benchmark_order_validity_rule()
    benchmark_duplicate_order_rule()
    benchmark_daily_limit_rule()
    benchmark_rolling_window_rule()

    print()
    print("=" * 60)
    print("测试完成")
    print("=" * 60)
