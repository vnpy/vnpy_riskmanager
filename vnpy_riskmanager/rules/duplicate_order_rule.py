from collections import defaultdict

from vnpy.trader.object import OrderRequest

from ..template import RuleTemplate


class DuplicateOrderRule(RuleTemplate):
    """重复报单检查风控规则"""

    name: str = "重复报单检查"

    parameters: dict[str, str] = {
        "duplicate_order_limit": "重复报单上限",
    }

    variables: dict[str, str] = {
        "duplicate_order_count": "重复报单笔数"
    }

    def on_init(self) -> None:
        """初始化"""
        # 默认参数
        self.duplicate_order_limit: int = 10

        # 重复报单统计
        self.duplicate_order_count: dict[str, int] = defaultdict(int)

    def check_allowed(self, req: OrderRequest, gateway_name: str) -> bool:
        """检查是否允许委托"""
        req_str: str = self.format_req(req)
        self.duplicate_order_count[req_str] += 1
        self.put_event()

        duplicate_order_count: int = self.duplicate_order_count[req_str]
        if duplicate_order_count >= self.duplicate_order_limit:
            self.write_log(f"重复报单笔数{duplicate_order_count}达到上限{self.duplicate_order_limit}：{req}")
            return False

        return True

    def format_req(self, req: OrderRequest) -> str:
        """将委托请求转为字符串"""
        return f"{req.vt_symbol}|{req.type.value}|{req.direction.value}|{req.offset.value}|{req.volume}@{req.price}"
