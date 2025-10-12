"""
Cython 性能基准测试

对比 Cython 优化后的风控规则性能提升
"""
import time
from unittest.mock import MagicMock

from vnpy.trader.object import OrderRequest, CancelRequest, Direction, Offset, OrderType
from vnpy.trader.constant import Exchange

# 导入 Cython 编译后的规则类
from vnpy_riskmanager.rules.order_size_rule import OrderSizeRule
from vnpy_riskmanager.rules.order_flow_rule import OrderFlowRule
from vnpy_riskmanager.rules.active_order_rule import ActiveOrderRule
from vnpy_riskmanager.rules.cancel_limit_rule import CancelLimitRule


def create_mock_engine():
    """创建模拟风控引擎"""
    engine = MagicMock()
    engine.write_log = MagicMock()
    engine.get_all_active_orders = MagicMock(return_value=[])
    return engine


def create_order_request():
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


def create_cancel_request():
    """创建模拟撤单请求"""
    req = CancelRequest(
        orderid="rb2505.SHFE.123456",
        symbol="rb2505",
        exchange=Exchange.SHFE,
    )
    return req


def benchmark_order_size_rule(iterations: int = 100000):
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
    print(f"OrderSizeRule: {iterations:,} 次调用耗时 {elapsed:.4f}s | {ops:,.0f} ops/s")


def benchmark_order_flow_rule(iterations: int = 100000):
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
    print(f"OrderFlowRule: {iterations:,} 次调用耗时 {elapsed:.4f}s | {ops:,.0f} ops/s")


def benchmark_active_order_rule(iterations: int = 100000):
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
    print(f"ActiveOrderRule: {iterations:,} 次调用耗时 {elapsed:.4f}s | {ops:,.0f} ops/s")


def benchmark_cancel_limit_rule(iterations: int = 100000):
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
    print(f"CancelLimitRule: {iterations:,} 次调用耗时 {elapsed:.4f}s | {ops:,.0f} ops/s")


if __name__ == "__main__":
    print("=" * 60)
    print("Cython 风控规则性能基准测试")
    print("=" * 60)
    print()

    benchmark_order_size_rule()
    benchmark_order_flow_rule()
    benchmark_active_order_rule()
    benchmark_cancel_limit_rule()

    print()
    print("=" * 60)
    print("测试完成")
    print("=" * 60)
