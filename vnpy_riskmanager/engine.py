import importlib
import traceback
from collections.abc import Callable
from typing import Any
from pathlib import Path
from glob import glob
from types import ModuleType

try:
    import winsound
except ImportError:
    winsound = None     # type: ignore

from vnpy.event import Event, EventEngine
from vnpy.trader.event import (
    EVENT_TICK,
    EVENT_ORDER,
    EVENT_TRADE,
    EVENT_TIMER,
    EVENT_LOG
)
from vnpy.trader.object import (
    OrderRequest,
    TickData,
    OrderData,
    TradeData,
    ContractData,
    LogData
)
from vnpy.trader.engine import BaseEngine, MainEngine
from vnpy.trader.utility import load_json, save_json
from vnpy.trader.logger import ERROR

from .template import RuleTemplate
from .base import APP_NAME, EVENT_RISK_RULE, EVENT_RISK_NOTIFY


class RiskEngine(BaseEngine):
    """风控引擎"""

    setting_filename: str = "risk_manager_setting.json"

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """构造函数"""
        super().__init__(main_engine, event_engine, APP_NAME)

        self.rules: dict[str, RuleTemplate] = {}
        self.setting: dict = load_json(self.setting_filename)

        self.field_name_map: dict = {}      # 规则字段名称映射

        # 缓存：记录哪些规则需要哪些回调
        self.tick_rules: list[RuleTemplate] = []
        self.order_rules: list[RuleTemplate] = []
        self.trade_rules: list[RuleTemplate] = []
        self.timer_rules: list[RuleTemplate] = []

        self.load_rules()
        self.register_events()
        self.patch_functions()

    def load_rules(self) -> None:
        """加载本地工具"""
        path_1: Path = Path(__file__).parent.joinpath("rules")
        self.load_rules_from_folder(path_1, "vnpy_riskmanager.rules")

        path_2: Path = Path.cwd().joinpath("rules")
        self.load_rules_from_folder(path_2, "rules")

    def load_rules_from_folder(self, folder_path: Path, module_name: str) -> None:
        """从文件夹加载本地工具"""
        pathname: str = str(folder_path.joinpath("*.py"))

        for filepath in glob(pathname):
            filename: str = Path(filepath).stem
            name: str = f"{module_name}.{filename}"
            self.load_rules_from_module(name)

    def load_rules_from_module(self, module_name: str) -> None:
        """从模块加载本地工具"""
        try:
            module: ModuleType = importlib.import_module(module_name)

            for name in dir(module):
                value: Any = getattr(module, name)
                if (
                    isinstance(value, type)
                    and issubclass(value, RuleTemplate)
                    and value is not RuleTemplate
                ):
                    self.add_rule(value)
        except Exception:
            msg: str = f"Local tool [{module_name}] load failed: {traceback.format_exc()}"
            print(msg)

    def add_rule(self, rule_class: type[RuleTemplate]) -> None:
        """注册规则"""
        rule_setting: dict = self.setting.get(rule_class.name, {})
        rule: RuleTemplate = rule_class(self, rule_setting)
        self.rules[rule.name] = rule

        # 更新字段名称映射
        self.field_name_map.update(rule.parameters)
        self.field_name_map.update(rule.variables)

    def patch_functions(self) -> None:
        """动态替换主引擎函数"""
        self._send_order: Callable[[OrderRequest, str], str] = self.main_engine.send_order
        self.main_engine.send_order = self.send_order

    def register_events(self) -> None:
        """检测规则需要的事件类型并注册"""
        # 遍历所有规则，检测并缓存需要回调的规则
        for rule in self.rules.values():
            if self.needs_callback(rule, "on_tick"):
                self.tick_rules.append(rule)
            if self.needs_callback(rule, "on_order"):
                self.order_rules.append(rule)
            if self.needs_callback(rule, "on_trade"):
                self.trade_rules.append(rule)
            if self.needs_callback(rule, "on_timer"):
                self.timer_rules.append(rule)

        # 按需注册事件监听
        if self.tick_rules:
            self.event_engine.register(EVENT_TICK, self.process_tick_event)
        if self.order_rules:
            self.event_engine.register(EVENT_ORDER, self.process_order_event)
        if self.trade_rules:
            self.event_engine.register(EVENT_TRADE, self.process_trade_event)
        if self.timer_rules:
            self.event_engine.register(EVENT_TIMER, self.process_timer_event)

    def needs_callback(self, rule: RuleTemplate, method_name: str) -> bool:
        """检测规则是否重写了某个回调方法"""
        rule_method = getattr(rule, method_name)
        base_method = getattr(RuleTemplate, method_name)
        return rule_method.__func__ is not base_method

    def process_tick_event(self, event: Event) -> None:
        """处理行情事件"""
        tick: TickData = event.data
        for rule in self.tick_rules:
            rule.on_tick(tick)

    def process_order_event(self, event: Event) -> None:
        """处理委托事件"""
        order: OrderData = event.data
        for rule in self.order_rules:
            rule.on_order(order)

    def process_trade_event(self, event: Event) -> None:
        """处理成交事件"""
        trade: TradeData = event.data
        for rule in self.trade_rules:
            rule.on_trade(trade)

    def process_timer_event(self, event: Event) -> None:
        """处理定时事件"""
        for rule in self.timer_rules:
            rule.on_timer()

    def send_order(self, req: OrderRequest, gateway_name: str) -> str:
        """下单请求风控检查"""
        result: bool = self.check_allowed(req, gateway_name)
        if not result:
            return ""

        return self._send_order(req, gateway_name)

    def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许发单"""
        for rule in self.rules.values():
            if (
                rule.active                                         # 启用规则
                and not rule.check_allowed(req, gateway_name)       # 检查规则是否允许
            ):
                return False
        return True

    def write_log(self, msg: str) -> None:
        """输出风控日志"""
        log: LogData = LogData(
            msg="委托被拦截，" + msg,
            level=ERROR,
            gateway_name=APP_NAME,
        )
        self.event_engine.put(Event(EVENT_LOG, log))

        # 推送风险通知事件
        self.event_engine.put(Event(EVENT_RISK_NOTIFY, msg))

        # 输出拦截日志后播放声音
        if winsound:
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)

    def get_contract(self, vt_symbol: str) -> ContractData | None:
        """查询合约信息（供规则调用）"""
        return self.main_engine.get_contract(vt_symbol)

    def put_rule_event(self, rule: RuleTemplate) -> None:
        """推送规则事件"""
        data: dict[str, Any] = rule.get_data()
        event: Event = Event(EVENT_RISK_RULE, data)
        self.event_engine.put(event)

    def update_rule_setting(self, rule_name: str, rule_setting: dict) -> None:
        """更新指定规则的参数"""
        self.setting[rule_name] = rule_setting

        # 更新到规则对象
        rule: RuleTemplate = self.rules[rule_name]
        rule.update_setting(rule_setting)
        rule.put_event()

        # 保存配置到文件
        save_json(self.setting_filename, self.setting)

    def get_all_rule_names(self) -> list[str]:
        """获取所有规则类名"""
        return list(self.rules.keys())

    def get_rule_data(self, rule_name: str) -> dict[str, Any]:
        """获取指定规则的数据"""
        rule: RuleTemplate = self.rules[rule_name]
        return rule.get_data()

    def get_field_name(self, field: str) -> str:
        """获取字段名称"""
        name: str = self.field_name_map.get(field, field)
        return name
