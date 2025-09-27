import importlib
import inspect
import pkgutil
from collections.abc import Callable

from vnpy.event import EventEngine
from vnpy.trader.object import OrderRequest, CancelRequest
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

        self.load_rules()
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
            rule: RuleTemplate = rule_class(
                self.main_engine, self.event_engine, self.setting
            )
            self.rules.append(rule)

    def patch_functions(self) -> None:
        """动态替换主引擎函数"""
        self._send_order: Callable[[OrderRequest, str], str] = self.main_engine.send_order
        self.main_engine.send_order = self.send_order

        self._cancel_order: Callable[[CancelRequest, str], None] = self.main_engine.cancel_order
        self.main_engine.cancel_order = self.cancel_order

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
