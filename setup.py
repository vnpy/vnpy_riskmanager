from setuptools import setup, find_packages
from Cython.Build import cythonize
from setuptools.extension import Extension


def get_version():
    """从 __init__.py 读取版本号"""
    with open("vnpy_riskmanager/__init__.py", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split('"')[1]
    return "1.0.0"


# 定义需要编译的 Cython 扩展
extensions = [
    Extension(
        "vnpy_riskmanager.template",
        ["vnpy_riskmanager/template.pyx"],
    ),
    Extension(
        "vnpy_riskmanager.rules.active_order_rule_cy",
        ["vnpy_riskmanager/rules/active_order_rule_cy.pyx"],
    ),
    # 以下规则尚未实现，暂时注释掉
    # Extension(
    #     "vnpy_riskmanager.rules.order_size_rule",
    #     ["vnpy_riskmanager/rules/order_size_rule.pyx"],
    # ),
    # Extension(
    #     "vnpy_riskmanager.rules.order_flow_rule",
    #     ["vnpy_riskmanager/rules/order_flow_rule.pyx"],
    # ),
    # Extension(
    #     "vnpy_riskmanager.rules.cancel_limit_rule",
    #     ["vnpy_riskmanager/rules/cancel_limit_rule.pyx"],
    # ),
    # Extension(
    #     "vnpy_riskmanager.rules.order_validity_rule",
    #     ["vnpy_riskmanager/rules/order_validity_rule.pyx"],
    # ),
    # Extension(
    #     "vnpy_riskmanager.rules.duplicate_order_rule",
    #     ["vnpy_riskmanager/rules/duplicate_order_rule.pyx"],
    # ),
    # Extension(
    #     "vnpy_riskmanager.rules.daily_limit_rule",
    #     ["vnpy_riskmanager/rules/daily_limit_rule.pyx"],
    # ),
    # Extension(
    #     "vnpy_riskmanager.rules.rolling_window_rule",
    #     ["vnpy_riskmanager/rules/rolling_window_rule.pyx"],
    # ),
]

# Cython 编译配置
compiler_directives = {
    "language_level": "3",          # Python 3 语法
    "boundscheck": False,            # 禁用边界检查（性能优化）
    "wraparound": False,             # 禁用负索引（性能优化）
    "cdivision": True,               # C 风格除法（不检查除零）
    "initializedcheck": False,       # 禁用初始化检查
    "embedsignature": True,          # 嵌入函数签名（便于调试）
}

setup(
    name="vnpy_riskmanager",
    version=get_version(),
    packages=find_packages(),
    ext_modules=cythonize(
        extensions,
        compiler_directives=compiler_directives,
        annotate=False,  # 设为 True 可生成 HTML 性能分析文件
    ),
    package_data={
        "vnpy_riskmanager": ["*.pxd", "*.pyx"],  # 包含 Cython 源文件
    },
    zip_safe=False,  # Cython 扩展不支持 zip 打包
)
