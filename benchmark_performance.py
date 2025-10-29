"""
性能测试：Python版本 vs Cython版本
对比 check_allowed 函数的性能差异
"""
import time
import sys
import os
from typing import Any

# 设置UTF-8编码
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')


class MockRiskEngine:
    """模拟风控引擎"""
    
    def __init__(self):
        self.logs = []
        self.events = []
    
    def write_log(self, msg: str) -> None:
        """记录日志"""
        self.logs.append(msg)
    
    def put_rule_event(self, rule: Any) -> None:
        """推送规则事件"""
        pass
    
    def get_contract(self, vt_symbol: str) -> None:
        """查询合约"""
        return None


class MockOrderRequest:
    """模拟委托请求"""
    
    def __init__(self, symbol: str = "IF2401"):
        self.vt_symbol = symbol
        self.volume = 1
        self.price = 4000.0
        self.reference = "test"
        
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


def benchmark_rule(rule_class, rule_name: str, iterations: int = 100000) -> dict:
    """
    性能测试函数
    
    Args:
        rule_class: 规则类
        rule_name: 规则名称
        iterations: 迭代次数
    
    Returns:
        测试结果字典
    """
    print(f"\n{'='*60}")
    print(f"测试 {rule_name}")
    print(f"{'='*60}")
    
    # 创建规则实例
    mock_engine = MockRiskEngine()
    setting = {"active": True, "active_order_limit": 50}
    rule = rule_class(mock_engine, setting)
    
    # 创建测试请求
    requests = [MockOrderRequest(f"IF240{i%10}") for i in range(100)]
    gateway_name = "CTP"
    
    # 预热（避免初始化开销影响测试）
    for _ in range(1000):
        rule.check_allowed(requests[0], gateway_name)
    
    print(f"迭代次数: {iterations:,}")
    print(f"活动委托上限: {rule.active_order_limit}")
    print()
    
    # 测试1: 未超限情况（应该很快）
    print("场景1: 未超限检查（快速通过）")
    rule.active_order_count = 0  # 重置
    
    start_time = time.perf_counter()
    for i in range(iterations):
        result = rule.check_allowed(requests[i % 100], gateway_name)
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
    
    # 测试2: 达到上限情况（需要写日志）
    print("\n场景2: 达到上限检查（触发日志）")
    rule.active_order_count = rule.active_order_limit  # 达到上限
    mock_engine.logs.clear()
    
    start_time = time.perf_counter()
    for i in range(iterations // 10):  # 减少迭代次数，因为写日志较慢
        result = rule.check_allowed(requests[i % 100], gateway_name)
    elapsed_time = time.perf_counter() - start_time
    
    ops_per_sec = (iterations // 10) / elapsed_time
    time_per_call_ns = (elapsed_time / (iterations // 10)) * 1_000_000_000
    
    print(f"  总耗时: {elapsed_time:.4f} 秒")
    print(f"  每次调用: {time_per_call_ns:.2f} 纳秒")
    print(f"  吞吐量: {ops_per_sec:,.0f} 次/秒")
    print(f"  日志数量: {len(mock_engine.logs):,}")
    
    result_2 = {
        "elapsed_time": elapsed_time,
        "ops_per_sec": ops_per_sec,
        "time_per_call_ns": time_per_call_ns
    }
    
    return {
        "scenario_1": result_1,
        "scenario_2": result_2
    }


def compare_results(py_results: dict, cy_results: dict):
    """对比并输出结果"""
    print("\n" + "="*60)
    print("性能对比汇总")
    print("="*60)
    
    print("\n场景1: 未超限检查（快速通过）")
    print("-" * 60)
    
    py_time_1 = py_results["scenario_1"]["time_per_call_ns"]
    cy_time_1 = cy_results["scenario_1"]["time_per_call_ns"]
    speedup_1 = py_time_1 / cy_time_1
    
    print(f"Python版本:  {py_time_1:>8.2f} 纳秒/次  "
          f"{py_results['scenario_1']['ops_per_sec']:>12,.0f} 次/秒")
    print(f"Cython版本:  {cy_time_1:>8.2f} 纳秒/次  "
          f"{cy_results['scenario_1']['ops_per_sec']:>12,.0f} 次/秒")
    print(f"性能提升:    {speedup_1:.2f}x")
    
    print("\n场景2: 达到上限检查（触发日志）")
    print("-" * 60)
    
    py_time_2 = py_results["scenario_2"]["time_per_call_ns"]
    cy_time_2 = cy_results["scenario_2"]["time_per_call_ns"]
    speedup_2 = py_time_2 / cy_time_2
    
    print(f"Python版本:  {py_time_2:>8.2f} 纳秒/次  "
          f"{py_results['scenario_2']['ops_per_sec']:>12,.0f} 次/秒")
    print(f"Cython版本:  {cy_time_2:>8.2f} 纳秒/次  "
          f"{cy_results['scenario_2']['ops_per_sec']:>12,.0f} 次/秒")
    print(f"性能提升:    {speedup_2:.2f}x")
    
    print("\n" + "="*60)
    print("总体评估")
    print("="*60)
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
    
    # 计算实际场景下的延迟差异
    print("\n实际场景影响分析:")
    print("-" * 60)
    
    # 假设实盘每秒100次风控检查
    trades_per_sec = 100
    py_latency_us = (py_time_1 / 1000) * trades_per_sec
    cy_latency_us = (cy_time_1 / 1000) * trades_per_sec
    latency_reduction = py_latency_us - cy_latency_us
    
    print(f"假设每秒100次风控检查:")
    print(f"  Python版本总延迟:  {py_latency_us:.2f} 微秒/秒")
    print(f"  Cython版本总延迟:  {cy_latency_us:.2f} 微秒/秒")
    print(f"  延迟降低:          {latency_reduction:.2f} 微秒/秒")
    print(f"  每次减少:          {latency_reduction/trades_per_sec:.3f} 微秒")


def main():
    """主测试流程"""
    print("="*60)
    print("vnpy_riskmanager 性能基准测试")
    print("Python版本 vs Cython版本")
    print("="*60)
    
    try:
        # 导入Python版本
        from vnpy_riskmanager.rules.active_order_rule import ActiveOrderRule as PyActiveOrderRule
        print("\n[OK] 成功导入 Python 版本")
    except ImportError as e:
        print(f"\n[FAIL] 无法导入 Python 版本: {e}")
        return False
    
    try:
        # 导入Cython版本
        from vnpy_riskmanager.rules.active_order_rule_cy import ActiveOrderRule as CyActiveOrderRule
        print("[OK] 成功导入 Cython 版本")
    except ImportError as e:
        print(f"\n[FAIL] 无法导入 Cython 版本: {e}")
        print("\n请先编译 Cython 模块:")
        print("  python setup.py build_ext --inplace")
        return False
    
    # 设置迭代次数
    iterations = 100000
    print(f"\n测试配置: {iterations:,} 次迭代")
    
    # 测试Python版本
    py_results = benchmark_rule(PyActiveOrderRule, "Python 版本", iterations)
    
    # 测试Cython版本
    cy_results = benchmark_rule(CyActiveOrderRule, "Cython 版本", iterations)
    
    # 对比结果
    compare_results(py_results, cy_results)
    
    return True


if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n" + "="*60)
        print("测试完成！")
        print("="*60)
        sys.exit(0)
    else:
        sys.exit(1)

