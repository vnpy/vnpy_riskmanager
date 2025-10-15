"""CancelLimitRule 测试用例"""
from collections.abc import Callable
from unittest.mock import Mock, patch


from vnpy.trader.object import CancelRequest
from vnpy.trader.constant import Exchange

from vnpy_riskmanager.rules.cancel_limit_rule import CancelLimitRule


class TestCancelLimitRule:
    """撤单频率控制规则测试"""

    def test_init_with_default_setting(self, mock_risk_engine: Mock) -> None:
        """测试使用默认配置初始化"""
        rule: CancelLimitRule = CancelLimitRule(mock_risk_engine, {})
        assert rule.cancel_limit == 10
        assert rule.cancel_window == 1
        assert len(rule.records) == 0

    def test_init_with_custom_setting(self, mock_risk_engine: Mock) -> None:
        """测试使用自定义配置初始化"""
        setting: dict = {"cancel_limit": 20, "cancel_window": 5}
        rule: CancelLimitRule = CancelLimitRule(mock_risk_engine, setting)
        assert rule.cancel_limit == 20
        assert rule.cancel_window == 5
        assert len(rule.records) == 0

    def test_check_cancel_allowed_first_cancel(
        self,
        mock_risk_engine: Mock,
        sample_cancel_request: CancelRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试首次撤单允许通过"""
        rule: CancelLimitRule = CancelLimitRule(mock_risk_engine, setting_factory({}))

        result: bool = rule.check_cancel_allowed(sample_cancel_request)

        assert result is True
        assert len(rule.records[sample_cancel_request.vt_symbol]) == 1
        mock_risk_engine.write_log.assert_not_called()

    def test_check_cancel_allowed_below_limit(
        self,
        mock_risk_engine: Mock,
        sample_cancel_request: CancelRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试撤单次数低于上限时允许通过"""
        setting: dict = setting_factory({"cancel_limit": 10, "cancel_window": 1})
        rule: CancelLimitRule = CancelLimitRule(mock_risk_engine, setting)

        # 连续5次撤单
        for i in range(5):
            result: bool = rule.check_cancel_allowed(sample_cancel_request)
            assert result is True
            assert len(rule.records[sample_cancel_request.vt_symbol]) == i + 1

        mock_risk_engine.write_log.assert_not_called()

    def test_check_cancel_allowed_at_limit(
        self,
        mock_risk_engine: Mock,
        sample_cancel_request: CancelRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试撤单次数达到上限时拒绝"""
        setting: dict = setting_factory({"cancel_limit": 10, "cancel_window": 1})
        rule: CancelLimitRule = CancelLimitRule(mock_risk_engine, setting)

        # 前10次撤单允许
        for _ in range(10):
            assert rule.check_cancel_allowed(sample_cancel_request) is True

        # 第11次拒绝
        result: bool = rule.check_cancel_allowed(sample_cancel_request)
        assert result is False

        mock_risk_engine.write_log.assert_called_once()
        log_msg: str = mock_risk_engine.write_log.call_args[0][0]
        assert "撤单过于频繁" in log_msg
        assert sample_cancel_request.vt_symbol in log_msg
        assert "10" in log_msg

    def test_sliding_window_cleanup(
        self,
        mock_risk_engine: Mock,
        sample_cancel_request: CancelRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试滑动窗口自动清理旧记录"""
        setting: dict = setting_factory({"cancel_limit": 5, "cancel_window": 1})
        rule: CancelLimitRule = CancelLimitRule(mock_risk_engine, setting)

        with patch("time.time") as mock_time:
            # 第1秒：5次撤单
            mock_time.return_value = 1000.0
            for _ in range(5):
                assert rule.check_cancel_allowed(sample_cancel_request) is True

            # 第6次应该拒绝
            assert rule.check_cancel_allowed(sample_cancel_request) is False

            # 第3秒：旧记录应该被清理
            mock_time.return_value = 1002.5
            result: bool = rule.check_cancel_allowed(sample_cancel_request)
            assert result is True

            # 验证旧记录已清除，只有1条新记录
            assert len(rule.records[sample_cancel_request.vt_symbol]) == 1

    def test_multiple_symbols_isolated(
        self,
        mock_risk_engine: Mock,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试不同合约的撤单统计相互独立"""
        setting: dict = setting_factory({"cancel_limit": 5, "cancel_window": 1})
        rule: CancelLimitRule = CancelLimitRule(mock_risk_engine, setting)

        req1: CancelRequest = CancelRequest(
            orderid="123",
            symbol="IF2501",
            exchange=Exchange.CFFEX
        )

        req2: CancelRequest = CancelRequest(
            orderid="456",
            symbol="IC2501",
            exchange=Exchange.CFFEX
        )

        # 合约1：5次撤单
        for _ in range(5):
            assert rule.check_cancel_allowed(req1) is True

        # 合约2：5次撤单
        for _ in range(5):
            assert rule.check_cancel_allowed(req2) is True

        # 两个合约的记录独立
        assert len(rule.records[req1.vt_symbol]) == 5
        assert len(rule.records[req2.vt_symbol]) == 5

        # 合约1第6次拒绝
        assert rule.check_cancel_allowed(req1) is False

        # 合约2第6次也拒绝
        assert rule.check_cancel_allowed(req2) is False

    def test_time_window_boundary(
        self,
        mock_risk_engine: Mock,
        sample_cancel_request: CancelRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试时间窗口边界条件"""
        setting: dict = setting_factory({"cancel_limit": 3, "cancel_window": 2})
        rule: CancelLimitRule = CancelLimitRule(mock_risk_engine, setting)

        with patch("time.time") as mock_time:
            # t=0: 第1次
            mock_time.return_value = 0.0
            assert rule.check_cancel_allowed(sample_cancel_request) is True

            # t=0.5: 第2次
            mock_time.return_value = 0.5
            assert rule.check_cancel_allowed(sample_cancel_request) is True

            # t=1.0: 第3次
            mock_time.return_value = 1.0
            assert rule.check_cancel_allowed(sample_cancel_request) is True

            # t=1.5: 第4次（前3次都在窗口内），拒绝
            mock_time.return_value = 1.5
            assert rule.check_cancel_allowed(sample_cancel_request) is False

            # t=2.1: 第1次记录过期，允许
            mock_time.return_value = 2.1
            assert rule.check_cancel_allowed(sample_cancel_request) is True

    def test_window_cleanup_logic(
        self,
        mock_risk_engine: Mock,
        sample_cancel_request: CancelRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试窗口清理逻辑的正确性"""
        setting: dict = setting_factory({"cancel_limit": 5, "cancel_window": 1})
        rule: CancelLimitRule = CancelLimitRule(mock_risk_engine, setting)

        with patch("time.time") as mock_time:
            # 在不同时间点添加记录
            timestamps: list[float] = [1.0, 1.2, 1.4, 1.6, 1.8]
            for t in timestamps:
                mock_time.return_value = t
                rule.check_cancel_allowed(sample_cancel_request)

            # t=2.5: 清理逻辑使用 > 比较，所以 2.5 - 1.0 = 1.5 > 1，会清除
            # 2.5 - 1.4 = 1.1 > 1，也会清除
            # 2.5 - 1.6 = 0.9 < 1，保留
            mock_time.return_value = 2.5
            rule.check_cancel_allowed(sample_cancel_request)

            # 窗口内应该有3个记录（1.6, 1.8, 2.5）
            timestamps_in_window = list(rule.records[sample_cancel_request.vt_symbol])
            assert len(timestamps_in_window) == 3
            assert timestamps_in_window[0] == 1.6

    def test_rapid_cancels(
        self,
        mock_risk_engine: Mock,
        sample_cancel_request: CancelRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试快速连续撤单"""
        setting: dict = setting_factory({"cancel_limit": 10, "cancel_window": 1})
        rule: CancelLimitRule = CancelLimitRule(mock_risk_engine, setting)

        with patch("time.time") as mock_time:
            # 在同一时刻连续撤单
            mock_time.return_value = 1000.0
            for _ in range(10):
                result: bool = rule.check_cancel_allowed(sample_cancel_request)
                assert result is True

            # 第11次拒绝
            assert rule.check_cancel_allowed(sample_cancel_request) is False

    def test_limit_one(
        self,
        mock_risk_engine: Mock,
        sample_cancel_request: CancelRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试上限为1的极端情况"""
        setting: dict = setting_factory({"cancel_limit": 1, "cancel_window": 1})
        rule: CancelLimitRule = CancelLimitRule(mock_risk_engine, setting)

        # 第1次允许
        assert rule.check_cancel_allowed(sample_cancel_request) is True

        # 第2次拒绝
        assert rule.check_cancel_allowed(sample_cancel_request) is False

    def test_large_window(
        self,
        mock_risk_engine: Mock,
        sample_cancel_request: CancelRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试大时间窗口"""
        setting: dict = setting_factory({"cancel_limit": 100, "cancel_window": 60})
        rule: CancelLimitRule = CancelLimitRule(mock_risk_engine, setting)

        with patch("time.time") as mock_time:
            # 60秒内100次撤单
            base_time: float = 1000.0
            for i in range(100):
                mock_time.return_value = base_time + i * 0.5
                assert rule.check_cancel_allowed(sample_cancel_request) is True

            # 第101次拒绝
            mock_time.return_value = base_time + 50
            assert rule.check_cancel_allowed(sample_cancel_request) is False

            # 61秒后，第1次记录过期，允许新撤单
            mock_time.return_value = base_time + 61
            assert rule.check_cancel_allowed(sample_cancel_request) is True

    def test_log_message_format(
        self,
        mock_risk_engine: Mock,
        sample_cancel_request: CancelRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试日志消息格式"""
        setting: dict = setting_factory({"cancel_limit": 3, "cancel_window": 2})
        rule: CancelLimitRule = CancelLimitRule(mock_risk_engine, setting)

        # 触发限制
        for _ in range(4):
            rule.check_cancel_allowed(sample_cancel_request)

        log_msg: str = mock_risk_engine.write_log.call_args[0][0]
        assert "撤单过于频繁" in log_msg
        assert sample_cancel_request.vt_symbol in log_msg
        assert "2秒" in log_msg
        assert "3次" in log_msg

    def test_deque_performance(
        self,
        mock_risk_engine: Mock,
        sample_cancel_request: CancelRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试 deque 的性能特性"""
        setting: dict = setting_factory({"cancel_limit": 1000, "cancel_window": 10})
        rule: CancelLimitRule = CancelLimitRule(mock_risk_engine, setting)

        with patch("time.time") as mock_time:
            # 添加大量记录
            base_time: float = 1000.0
            for i in range(1000):
                mock_time.return_value = base_time + i * 0.01
                rule.check_cancel_allowed(sample_cancel_request)

            # 验证记录数量
            assert len(rule.records[sample_cancel_request.vt_symbol]) == 1000

            # 时间前进到 base_time + 15
            # 只有 current_t - timestamp > 10 的记录会被清除
            # 1015 - 1009.99 = 5.01，不会清除
            # 1015 - 1004.99 = 10.01 > 10，会清除
            # 所以保留 1005.0 及以后的记录（500条）加上新的1条
            mock_time.return_value = base_time + 15
            rule.check_cancel_allowed(sample_cancel_request)

            # 窗口内应该有501条记录（从 1005.0 到 1009.99 的500条 + 新的1015）
            assert len(rule.records[sample_cancel_request.vt_symbol]) == 501

    def test_defaultdict_behavior(
        self,
        mock_risk_engine: Mock,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试 defaultdict 的行为"""
        rule: CancelLimitRule = CancelLimitRule(mock_risk_engine, setting_factory({}))

        req: CancelRequest = CancelRequest(
            orderid="999",
            symbol="NEW_SYMBOL",
            exchange=Exchange.CFFEX
        )

        # 访问不存在的 symbol 应该自动创建 deque
        result: bool = rule.check_cancel_allowed(req)

        assert result is True
        assert req.vt_symbol in rule.records
        assert len(rule.records[req.vt_symbol]) == 1

    def test_integration_with_risk_engine(
        self,
        mock_risk_engine: Mock,
        sample_cancel_request: CancelRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试与 RiskEngine 的集成"""
        rule: CancelLimitRule = CancelLimitRule(mock_risk_engine, setting_factory({}))

        assert rule.risk_engine == mock_risk_engine

        # 触发限制，验证日志调用
        for _ in range(11):
            rule.check_cancel_allowed(sample_cancel_request)

        mock_risk_engine.write_log.assert_called()

    def test_concurrent_symbols(
        self,
        mock_risk_engine: Mock,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试多合约并发撤单"""
        setting: dict = setting_factory({"cancel_limit": 5, "cancel_window": 1})
        rule: CancelLimitRule = CancelLimitRule(mock_risk_engine, setting)

        symbols: list[str] = ["IF2501", "IC2501", "IH2501"]

        # 每个合约撤单5次
        for symbol in symbols:
            req: CancelRequest = CancelRequest(
                orderid="123",
                symbol=symbol,
                exchange=Exchange.CFFEX
            )
            for _ in range(5):
                assert rule.check_cancel_allowed(req) is True

        # 验证每个合约都有独立记录
        for symbol in symbols:
            vt_symbol: str = f"{symbol}.CFFEX"
            assert len(rule.records[vt_symbol]) == 5

    def test_time_precision(
        self,
        mock_risk_engine: Mock,
        sample_cancel_request: CancelRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试时间精度"""
        setting: dict = setting_factory({"cancel_limit": 5, "cancel_window": 0.1})
        rule: CancelLimitRule = CancelLimitRule(mock_risk_engine, setting)

        with patch("time.time") as mock_time:
            # 0.1秒内5次撤单
            mock_time.return_value = 1000.0
            for _ in range(5):
                assert rule.check_cancel_allowed(sample_cancel_request) is True

            # 第6次拒绝
            assert rule.check_cancel_allowed(sample_cancel_request) is False

            # 0.15秒后允许
            mock_time.return_value = 1000.15
            assert rule.check_cancel_allowed(sample_cancel_request) is True

    def test_rejected_cancels_still_counted(
        self,
        mock_risk_engine: Mock,
        sample_cancel_request: CancelRequest,
        setting_factory: Callable[[dict], dict]
    ) -> None:
        """测试被拒绝的撤单不计入记录"""
        setting: dict = setting_factory({"cancel_limit": 3, "cancel_window": 1})
        rule: CancelLimitRule = CancelLimitRule(mock_risk_engine, setting)

        # 前3次允许
        for _ in range(3):
            rule.check_cancel_allowed(sample_cancel_request)

        assert len(rule.records[sample_cancel_request.vt_symbol]) == 3

        # 第4次拒绝，但不计入记录
        rule.check_cancel_allowed(sample_cancel_request)

        # 记录应该还是3条
        assert len(rule.records[sample_cancel_request.vt_symbol]) == 3
