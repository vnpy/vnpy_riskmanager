from typing import Any

from vnpy.event import EventEngine, Event
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import QtWidgets, QtCore

from ..engine import RiskEngine, APP_NAME, EVENT_RISK_RULE


class RuleWidget(QtWidgets.QGroupBox):
    """用于设置参数和显示变量的规则控件。"""

    def __init__(self, rule_name: str, risk_engine: RiskEngine) -> None:
        """构造函数"""
        super().__init__(rule_name)

        self.rule_name: str = rule_name
        self.risk_engine: RiskEngine = risk_engine

        self.data: dict[str, Any] = {}

        self.tree: QtWidgets.QTreeWidget = QtWidgets.QTreeWidget()
        self.items: dict[str, QtWidgets.QTreeWidgetItem] = {}

        self.init_ui()

    def init_ui(self) -> None:
        """初始化UI界面"""
        self.tree.setHeaderLabels(["分类", "名称", " ", " "])
        self.tree.setColumnWidth(0, 120)
        self.tree.setColumnWidth(1, 150)
        self.tree.setColumnWidth(2, 100)
        self.tree.setColumnWidth(3, 100)

        editor_button: QtWidgets.QPushButton = QtWidgets.QPushButton("修改风控参数")
        editor_button.clicked.connect(self.open_editor)

        vbox: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.tree)
        vbox.addWidget(editor_button)
        self.setLayout(vbox)

    def init_tree(self, data: dict) -> None:
        """初始化树状图结构"""
        # 参数部分
        parameter_root: QtWidgets.QTreeWidgetItem = QtWidgets.QTreeWidgetItem(self.tree, ["参数"])
        parameters: dict = data["parameters"]
        for field, value in parameters.items():
            name: str = self.risk_engine.get_field_name(field)
            item: QtWidgets.QTreeWidgetItem = QtWidgets.QTreeWidgetItem(parameter_root, ["", name, str(value)])
            self.items[field] = item

        # 变量部分
        variable_root = QtWidgets.QTreeWidgetItem(self.tree, ["变量"])
        variables: dict = data["variables"]
        for field, value in variables.items():
            name = self.risk_engine.get_field_name(field)

            if isinstance(value, dict):
                item = QtWidgets.QTreeWidgetItem(variable_root, ["", name])
                self.items[field] = item

                for k, v in value.items():
                    sub_item: QtWidgets.QTreeWidgetItem = QtWidgets.QTreeWidgetItem(item, ["", "", k, str(v)])
                    self.items[f"{field}.{k}"] = sub_item
            else:
                item = QtWidgets.QTreeWidgetItem(variable_root, ["", name, str(value)])
                self.items[field] = item

    def update_data(self, data: dict) -> None:
        """更新规则数据"""
        if not self.data:
            self.init_tree(data)
        self.data = data

        # 参数部分
        parameters: dict = data["parameters"]

        for field, value in parameters.items():
            item: QtWidgets.QTreeWidgetItem = self.items.get(field)
            item.setText(2, str(value))

        # 变量部分
        variables: dict = data["variables"]

        for field, value in variables.items():
            if isinstance(value, dict):
                item = self.items[field]

                for k, v in value.items():
                    sub_item: QtWidgets.QTreeWidgetItem = self.items.get(f"{field}.{k}")
                    if sub_item:
                        sub_item.setText(3, str(v))
                    else:
                        sub_item = QtWidgets.QTreeWidgetItem(item, ["", "", k, str(v)])
                        self.items[f"{field}.{k}"] = sub_item
            else:
                item = self.items[field]
                item.setText(2, str(value))

        self.tree.expandAll()

    def open_editor(self) -> None:
        """打开参数编辑对话框"""
        if not self.data:
            return

        parameters: dict = self.data["parameters"]
        dialog: RuleEditor = RuleEditor(self.rule_name, self.risk_engine, parameters)
        result: int = dialog.exec()

        if result == QtWidgets.QDialog.DialogCode.Accepted:
            rule_setting: dict = dialog.get_setting()
            self.risk_engine.update_rule_setting(self.rule_name, rule_setting)


class RuleEditor(QtWidgets.QDialog):
    """用于编辑规则参数的对话框"""

    def __init__(self, rule_name: str, risk_engine: RiskEngine, parameters: dict) -> None:
        """"""
        super().__init__()

        self.rule_name: str = rule_name
        self.risk_engine: RiskEngine = risk_engine
        self.parameters: dict = parameters

        self.widgets: dict[str, QtWidgets.QWidget] = {}

        self.init_ui()

    def init_ui(self) -> None:
        """初始化UI界面"""
        self.setWindowTitle(f"{self.rule_name} - 参数编辑")

        form: QtWidgets.QFormLayout = QtWidgets.QFormLayout()

        for field, value in self.parameters.items():
            name: str = self.risk_engine.get_field_name(field)
            value_type: type = type(value)

            # 布尔值使用下拉框
            if value_type is bool:
                widget: QtWidgets.QWidget = QtWidgets.QComboBox()
                widget.addItems(["True", "False"])
                if value:
                    widget.setCurrentText("True")
                else:
                    widget.setCurrentText("False")
            # 整数使用SpinBox
            elif value_type is int:
                widget = QtWidgets.QSpinBox()
                widget.setRange(-1_000_000_000, 1_000_000_000)
                widget.setValue(value)
            # 浮点数使用DoubleSpinBox
            elif value_type is float:
                widget = QtWidgets.QDoubleSpinBox()
                widget.setDecimals(6)
                widget.setRange(-1_000_000_000, 1_000_000_000)
                widget.setValue(value)
            # 其他类型使用LineEdit
            else:
                widget = QtWidgets.QLineEdit(str(value))

            form.addRow(name, widget)
            self.widgets[field] = widget

        ok_button: QtWidgets.QPushButton = QtWidgets.QPushButton("确定")
        ok_button.clicked.connect(self.accept)

        cancel_button: QtWidgets.QPushButton = QtWidgets.QPushButton("取消")
        cancel_button.clicked.connect(self.reject)

        hbox: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(ok_button)
        hbox.addWidget(cancel_button)

        vbox: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        vbox.addLayout(form)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

    def get_setting(self) -> dict:
        """获取当前所有参数配置"""
        rule_setting: dict = {}

        for field, widget in self.widgets.items():
            if isinstance(widget, QtWidgets.QComboBox):
                value: Any = (widget.currentText() == "True")
            elif isinstance(widget, QtWidgets.QSpinBox):
                value = widget.value()
            elif isinstance(widget, QtWidgets.QDoubleSpinBox):
                value = widget.value()
            else:
                value = widget.text()
            rule_setting[field] = value

        return rule_setting


class RiskManager(QtWidgets.QWidget):
    """风控管理器"""

    signal: QtCore.Signal = QtCore.Signal(Event)

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """构造函数"""
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine
        self.rm_engine: RiskEngine = main_engine.get_engine(APP_NAME)

        self.rule_widgets: dict[str, RuleWidget] = {}

        self.init_ui()
        self.register_event()

    def init_ui(self) -> None:
        """初始化UI界面"""
        self.setWindowTitle("交易风控")

        rule_names: list[str] = self.rm_engine.get_all_rule_names()

        self.list_widget: QtWidgets.QListWidget = QtWidgets.QListWidget()
        self.list_widget.addItems(rule_names)

        self.stacked_widget: QtWidgets.QStackedWidget = QtWidgets.QStackedWidget()
        for rule_name in rule_names:
            rule_widget: RuleWidget = RuleWidget(rule_name, self.rm_engine)
            self.stacked_widget.addWidget(rule_widget)
            self.rule_widgets[rule_name] = rule_widget

            data: dict = self.rm_engine.get_rule_data(rule_name)
            rule_widget.update_data(data)

        splitter: QtWidgets.QSplitter = QtWidgets.QSplitter()
        splitter.addWidget(self.list_widget)
        splitter.addWidget(self.stacked_widget)

        vbox: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        vbox.addWidget(splitter)
        self.setLayout(vbox)

        self.list_widget.currentRowChanged.connect(self.stacked_widget.setCurrentIndex)
        self.list_widget.setCurrentRow(0)

    def register_event(self) -> None:
        """创建并启动用于刷新监控变量的定时器"""
        self.signal.connect(self.process_rule_event)
        self.event_engine.register(EVENT_RISK_RULE, self.signal.emit)

    def process_rule_event(self, event: Event) -> None:
        """定时更新所有规则控件的监控变量"""
        data: dict = event.data

        rule_name: str = data["name"]
        rule_widget: RuleWidget | None = self.rule_widgets.get(rule_name)
        if rule_widget:
            rule_widget.update_data(data)
