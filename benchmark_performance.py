"""
性能测试：Python版本 vs Cython版本
对比所有风控规则的 check_allowed 函数的性能差异
"""
import time
import sys
import os
from typing import Any, Dict, List

# 设置UTF-8编码
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')


class MockContract:
    """模拟合约对象"""
    def __init__(self):
        self.pricetick: float = 0.1
        self.max_volume: float = 100.0
        self.min_volume: float = 1.0
        self.size: float = 10.0


class MockRiskEngine:
    """模拟风控引擎"""
    
    def __init__(self):
        self.logs: List[str] = []
        self.events: List[Any] = []
        self.contract = MockContract()
    
    def write_log(self, msg: str) -> None:
        """记录日志"""
        self.logs.append(msg)
    
    def put_rule_event(self, rule: Any) -> None:
        """推送规则事件"""
        pass
    
    def get_contract(self, vt_symbol: str) -> Any | None:
        """查询合约"""
        if "FAIL" in vt_symbol:
            return None
        return self.contract


class MockOrderRequest:
    """模拟委托请求"""
    
    def __init__(
        self,
        symbol: str = "IF2401",
        volume: float = 1.0,
        price: float = 4000.0,
        reference: str = ""
    ):
        self.vt_symbol: str = symbol
        self.volume: float = volume
        self.price: float = price
        self.reference: str = reference or f"{symbol}_{volume}@{price}"
        
        # 模拟枚举类型
        class Type:
            value = "LIMIT"
        class Direction:
            value = "LONG"
        class Offset:
            value = "OPEN"
        
        self.type = Type()
        self.direction = Direction()
        self.offset = Offset()

    def __str__(self) -> str:
        return self.reference


def benchmark_rule(
    rule_class: type,
    rule_name: str,
    iterations: int,
    config: Dict[str, Any]
) -> dict:
    """
    性能测试函数
    
    Args:
        rule_class: 规则类
        rule_name: 规则名称
        iterations: 迭代次数
        config: 测试配置
    
    Returns:
        测试结果字典
    """
    print(f"\n{'='*60}")
    print(f"测试 {rule_name} - {config['name']}")
    print(f"{'='*60}")
    
    # 创建规则实例
    mock_engine = MockRiskEngine()
    setting = {"active": True, **config["settings"]}
    rule = rule_class(mock_engine, setting)
    
    # 预热
    warmup_req = config["requests_pass"][0]
    for _ in range(1000):
        rule.check_allowed(warmup_req, "CTP")
    
    print(f"迭代次数: {iterations:,}")
    print()
    
    # --- 场景1: 检查通过 ---
    print("场景1: 检查通过 (快速路径)")
    config["setup_pass"](rule)
    requests_pass = config["requests_pass"]
    
    start_time = time.perf_counter()
    for i in range(iterations):
        rule.check_allowed(requests_pass[i % len(requests_pass)], "CTP")
    elapsed_time = time.perf_counter() - start_time
    
    ops_per_sec = iterations / elapsed_time
    time_per_call_ns = (elapsed_time / iterations) * 1_000_000_000
    
    print(f"  总耗时: {elapsed_time:.4f} 秒")
    print(f"  每次调用: {time_per_call_ns:.2f} 纳秒")
    print(f"  吞吐量: {ops_per_sec:,.0f} 次/秒")
    
    result_1 = {
        "elapsed_time": elapsed_time,
        "ops_per_sec": ops_per_sec,
        "time_per_call_ns": time_per_call_ns
    }
    
    # --- 场景2: 检查失败 ---
    print("\n场景2: 检查失败 (触发日志)")
    config["setup_fail"](rule)
    requests_fail = config["requests_fail"]
    mock_engine.logs.clear()
    
    fail_iterations = iterations // 10
    start_time = time.perf_counter()
    for i in range(fail_iterations):
        rule.check_allowed(requests_fail[i % len(requests_fail)], "CTP")
    elapsed_time = time.perf_counter() - start_time
    
    ops_per_sec = fail_iterations / elapsed_time
    time_per_call_ns = (elapsed_time / fail_iterations) * 1_000_000_000
    
    print(f"  总耗时: {elapsed_time:.4f} 秒")
    print(f"  每次调用: {time_per_call_ns:.2f} 纳秒")
    print(f"  吞吐量: {ops_per_sec:,.0f} 次/秒")
    print(f"  日志数量: {len(mock_engine.logs):,}")
    
    result_2 = {
        "elapsed_time": elapsed_time,
        "ops_per_sec": ops_per_sec,
        "time_per_call_ns": time_per_call_ns
    }
    
    return {"scenario_1": result_1, "scenario_2": result_2}


def compare_results(py_results: dict, cy_results: dict, rule_name: str):
    """对比并输出结果"""
    print("\n" + "="*60)
    print(f"性能对比汇总 - {rule_name}")
    print("="*60)
    
    py_time_1 = py_results["scenario_1"]["time_per_call_ns"]
    cy_time_1 = cy_results["scenario_1"]["time_per_call_ns"]
    speedup_1 = py_time_1 / cy_time_1 if cy_time_1 else float('inf')
    
    print("\n场景1: 检查通过 (快速路径)")
    print("-" * 60)
    print(f"Python版本:  {py_time_1:>8.2f} 纳秒/次  "
          f"{py_results['scenario_1']['ops_per_sec']:>12,.0f} 次/秒")
    print(f"Cython版本:  {cy_time_1:>8.2f} 纳秒/次  "
          f"{cy_results['scenario_1']['ops_per_sec']:>12,.0f} 次/秒")
    print(f"性能提升:    {speedup_1:.2f}x")
    
    py_time_2 = py_results["scenario_2"]["time_per_call_ns"]
    cy_time_2 = cy_results["scenario_2"]["time_per_call_ns"]
    speedup_2 = py_time_2 / cy_time_2 if cy_time_2 else float('inf')

    print("\n场景2: 检查失败 (触发日志)")
    print("-" * 60)
    print(f"Python版本:  {py_time_2:>8.2f} 纳秒/次  "
          f"{py_results['scenario_2']['ops_per_sec']:>12,.0f} 次/秒")
    print(f"Cython版本:  {cy_time_2:>8.2f} 纳秒/次  "
          f"{cy_results['scenario_2']['ops_per_sec']:>12,.0f} 次/秒")
    print(f"性能提升:    {speedup_2:.2f}x")
    
    print("\n" + "="*60)
    avg_speedup = (speedup_1 + speedup_2) / 2
    print(f"平均性能提升: {avg_speedup:.2f}x")
    
    if avg_speedup >= 3.0:
        rating = "[+++] 优秀"
    elif avg_speedup >= 2.0:
        rating = "[++] 良好"
    elif avg_speedup >= 1.5:
        rating = "[+] 不错"
    else:
        rating = "[=] 适中"
    print(f"性能评级: {rating}")


def main():
    """主测试流程"""
    print("="*60)
    print("vnpy_riskmanager 性能基准测试")
    print("Python版本 vs Cython版本")
    print("="*60)

    # --- 导入所有规则 ---
    try:
        from vnpy_riskmanager.rules.active_order_rule import ActiveOrderRule as PyActiveOrderRule
        from vnpy_riskmanager.rules.active_order_rule_cy import ActiveOrderRule as CyActiveOrderRule
        from vnpy_riskmanager.rules.daily_limit_rule import DailyLimitRule as PyDailyLimitRule
        from vnpy_riskmanager.rules.daily_limit_rule_cy import DailyLimitRule as CyDailyLimitRule
        from vnpy_riskmanager.rules.duplicate_order_rule import DuplicateOrderRule as PyDuplicateOrderRule
        from vnpy_riskmanager.rules.duplicate_order_rule_cy import DuplicateOrderRule as CyDuplicateOrderRule
        from vnpy_riskmanager.rules.order_size_rule import OrderSizeRule as PyOrderSizeRule
        from vnpy_riskmanager.rules.order_size_rule_cy import OrderSizeRule as CyOrderSizeRule
        from vnpy_riskmanager.rules.order_validity_rule import OrderValidityRule as PyOrderValidityRule
        from vnpy_riskmanager.rules.order_validity_rule_cy import OrderValidityRule as CyOrderValidityRule
        print("\n[OK] 成功导入所有规则模块 (Python 和 Cython)")
    except ImportError as e:
        print(f"\n[FAIL] 无法导入规则模块: {e}")
        print("\n请先编译 Cython 模块:")
        print("  python setup.py build_ext --inplace")
        return False

    # --- 测试配置 ---
    iterations = 100000
    
    rules_to_test = [
        {
            "name": "活动委托检查",
            "py_class": PyActiveOrderRule,
            "cy_class": CyActiveOrderRule,
            "settings": {"active_order_limit": 50},
            "setup_pass": lambda rule: setattr(rule, 'active_order_count', 0),
            "requests_pass": [MockOrderRequest(f"IF{i}") for i in range(100)],
            "setup_fail": lambda rule: setattr(rule, 'active_order_count', rule.active_order_limit),
            "requests_fail": [MockOrderRequest(f"IF{i}") for i in range(100)],
        },
        {
            "name": "每日上限检查",
            "py_class": PyDailyLimitRule,
            "cy_class": CyDailyLimitRule,
            "settings": {"total_order_limit": 200},
            "setup_pass": lambda rule: setattr(rule, 'total_order_count', 0),
            "requests_pass": [MockOrderRequest(f"RB{i}") for i in range(100)],
            "setup_fail": lambda rule: setattr(rule, 'total_order_count', rule.total_order_limit),
            "requests_fail": [MockOrderRequest(f"RB{i}") for i in range(100)],
        },
        {
            "name": "重复报单检查",
            "py_class": PyDuplicateOrderRule,
            "cy_class": CyDuplicateOrderRule,
            "settings": {"duplicate_order_limit": 10},
            "setup_pass": lambda rule: rule.on_init(),
            "requests_pass": [MockOrderRequest(reference=f"req_{i}") for i in range(100)],
            "setup_fail": lambda rule: rule.on_init(),
            "requests_fail": [MockOrderRequest(reference="DUPLICATE_REQ")] * 20,
        },
        {
            "name": "委托规模检查",
            "py_class": PyOrderSizeRule,
            "cy_class": CyOrderSizeRule,
            "settings": {"order_volume_limit": 50, "order_value_limit": 2_000_000},
            "setup_pass": lambda rule: None,
            "requests_pass": [MockOrderRequest(volume=10, price=4000)],
            "setup_fail": lambda rule: None,
            "requests_fail": [MockOrderRequest(volume=60, price=4000)], # Exceeds volume
        },
        {
            "name": "委托指令检查",
            "py_class": PyOrderValidityRule,
            "cy_class": CyOrderValidityRule,
            "settings": {},
            "setup_pass": lambda rule: None,
            "requests_pass": [MockOrderRequest(price=4000.1)],  # Valid pricetick
            "setup_fail": lambda rule: None,
            "requests_fail": [MockOrderRequest(price=4000.15)], # Invalid pricetick
        },
    ]

    print(f"\n测试配置: {iterations:,} 次迭代/场景")

    # --- 运行所有测试 ---
    for config in rules_to_test:
        py_results = benchmark_rule(config["py_class"], "Python 版本", iterations, config)
        cy_results = benchmark_rule(config["cy_class"], "Cython 版本", iterations, config)
        compare_results(py_results, cy_results, config["name"])
        
    return True


if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n" + "="*60)
        print("所有测试完成！")
        print("="*60)
        sys.exit(0)
    else:
        sys.exit(1)

