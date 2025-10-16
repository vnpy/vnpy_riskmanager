import importlib
import inspect
import pkgutil
from collections.abc import Callable

from vnpy.event import Event, EventEngine
from vnpy.trader.event import EVENT_TICK, EVENT_ORDER, EVENT_TRADE, EVENT_TIMER
from vnpy.trader.object import OrderRequest, CancelRequest, TickData, OrderData, TradeData, ContractData
from vnpy.trader.engine import BaseEngine, MainEngine
from vnpy.trader.utility import load_json

from . import rules
from .template import RuleTemplate
from .base import APP_NAME


class RiskEngine(BaseEngine):
    """风控引擎"""

    setting_filename: str = "risk_manager_setting.json"

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """构造函数"""
        super().__init__(main_engine, event_engine, APP_NAME)

        self.rules: list[RuleTemplate] = []
        self.setting: dict = load_json(self.setting_filename)

        # 缓存：记录哪些规则需要哪些回调
        self.tick_rules: list[RuleTemplate] = []
        self.order_rules: list[RuleTemplate] = []
        self.trade_rules: list[RuleTemplate] = []
        self.timer_rules: list[RuleTemplate] = []

        self.load_rules()
        self.register_rule_events()
        self.patch_functions()

    def load_rules(self) -> None:
        """加载风控规则"""
        rule_classes: list[type[RuleTemplate]] = []

        package_path = rules.__path__
        package_name = rules.__name__

        for _, module_name, _ in pkgutil.iter_modules(package_path, prefix=f"{package_name}."):
            module = importlib.import_module(module_name)
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, RuleTemplate) and obj is not RuleTemplate:
                    rule_classes.append(obj)

        for rule_class in rule_classes:
            rule: RuleTemplate = rule_class(self, self.setting)
            self.rules.append(rule)

    def patch_functions(self) -> None:
        """动态替换主引擎函数"""
        self._send_order: Callable[[OrderRequest, str], str] = self.main_engine.send_order
        self.main_engine.send_order = self.send_order

        self._cancel_order: Callable[[CancelRequest, str], None] = self.main_engine.cancel_order
        self.main_engine.cancel_order = self.cancel_order

    def register_rule_events(self) -> None:
        """检测规则需要的事件类型并注册"""
        # 遍历所有规则，检测并缓存需要回调的规则
        for rule in self.rules:
            if self._needs_callback(rule, "on_tick"):
                self.tick_rules.append(rule)
            if self._needs_callback(rule, "on_order"):
                self.order_rules.append(rule)
            if self._needs_callback(rule, "on_trade"):
                self.trade_rules.append(rule)
            if self._needs_callback(rule, "on_timer"):
                self.timer_rules.append(rule)

        # 按需注册事件监听
        if self.tick_rules:
            self.event_engine.register(EVENT_TICK, self._process_tick_event)
        if self.order_rules:
            self.event_engine.register(EVENT_ORDER, self._process_order_event)
        if self.trade_rules:
            self.event_engine.register(EVENT_TRADE, self._process_trade_event)
        if self.timer_rules:
            self.event_engine.register(EVENT_TIMER, self._process_timer_event)

    def _needs_callback(self, rule: RuleTemplate, method_name: str) -> bool:
        """检测规则是否重写了某个回调方法"""
        rule_method = getattr(rule, method_name)
        base_method = getattr(RuleTemplate, method_name)
        return rule_method.__func__ is not base_method

    def _process_tick_event(self, event: Event) -> None:
        """处理行情事件"""
        tick: TickData = event.data
        for rule in self.tick_rules:
            rule.on_tick(tick)

    def _process_order_event(self, event: Event) -> None:
        """处理委托事件"""
        order: OrderData = event.data
        for rule in self.order_rules:
            rule.on_order(order)

    def _process_trade_event(self, event: Event) -> None:
        """处理成交事件"""
        trade: TradeData = event.data
        for rule in self.trade_rules:
            rule.on_trade(trade)

    def _process_timer_event(self, event: Event) -> None:
        """处理定时事件"""
        for rule in self.timer_rules:
            rule.on_timer()

    def send_order(self, req: OrderRequest, gateway_name: str) -> str:
        """下单请求风控检查"""
        result: bool = self.check_send_allowed(req, gateway_name)
        if not result:
            return ""

        return self._send_order(req, gateway_name)

    def cancel_order(self, req: CancelRequest, gateway_name: str) -> None:
        """撤单请求风控检查"""
        result: bool = self.check_cancel_allowed(req)
        if not result:
            return

        self._cancel_order(req, gateway_name)

    def check_send_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许发单"""
        for rule in self.rules:
            if not rule.check_allowed(req, gateway_name):
                return False
        return True

    def check_cancel_allowed(self, req: CancelRequest) -> bool:
        """检查是否允许撤单"""
        for rule in self.rules:
            if not rule.check_cancel_allowed(req):
                return False
        return True

    def get_all_active_orders(self) -> list[OrderData]:
        """查询所有活动委托（供规则调用）"""
        return self.main_engine.get_all_active_orders()     # type: ignore

    def get_contract(self, vt_symbol: str) -> ContractData | None:
        """查询合约信息（供规则调用）"""
        return self.main_engine.get_contract(vt_symbol)
