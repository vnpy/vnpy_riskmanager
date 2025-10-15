from typing import TYPE_CHECKING

from vnpy.trader.object import OrderRequest, ContractData

from ..template import RuleTemplate

if TYPE_CHECKING:
    from ..engine import RiskEngine


class OrderValidityRule(RuleTemplate):
    """委托指令合法性监控"""

    def __init__(self, risk_engine: "RiskEngine", setting: dict) -> None:
        super().__init__(risk_engine, setting)

    def init_rule(self, setting: dict) -> None:
        """初始化风控规则"""
        self.check_contract_exists: bool = setting.get("check_contract_exists", True)
        self.check_price_tick: bool = setting.get("check_price_tick", True)
        self.check_volume_limit: bool = setting.get("check_volume_limit", False)
        self.max_order_volume: int = setting.get("max_order_volume", 1000)

    def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许委托"""
        # 检查合约是否存在
        if self.check_contract_exists:
            contract: ContractData | None = self.risk_engine.get_contract(req.vt_symbol)
            if not contract:
                self.write_log(f"委托失败：合约 {req.vt_symbol} 不存在")
                return False

            # 检查价格是否为 pricetick 的整数倍
            if self.check_price_tick:
                if contract.pricetick > 0:
                    price_tick: float = contract.pricetick
                    remainder: float = req.price % price_tick
                    if abs(remainder) > 1e-6 and abs(remainder - price_tick) > 1e-6:
                        self.write_log(
                            f"委托失败：价格 {req.price} 不是最小变动价位 {price_tick} 的整数倍"
                        )
                        return False

        # 检查委托数量上限
        if self.check_volume_limit:
            if req.volume > self.max_order_volume:
                self.write_log(
                    f"委托失败：数量 {req.volume} 超过单笔最大限制 {self.max_order_volume}"
                )
                return False

        return True

