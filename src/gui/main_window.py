from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QApplication, QWidget,
                            QVBoxLayout, QLabel)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt, pyqtSignal
import os
import importlib

from src.config import AppConfig
from src.gui.styles import StyleManager

class TabLoader(QWidget):
    """选项卡加载器，用于实现懒加载"""

    # 加载完成信号
    loaded = pyqtSignal(QWidget)

    def __init__(self, tab_class, tab_name):
        super().__init__()
        self.tab_class = tab_class
        self.tab_name = tab_name
        self.instance = None
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 添加加载提示
        label = QLabel(f"正在加载 {self.tab_name}...")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

    def load_tab(self):
        """加载实际的选项卡"""
        if self.instance is None:
            # 动态导入模块
            try:
                self.instance = self.tab_class()
                self.loaded.emit(self.instance)
            except Exception as e:
                # 加载失败时显示错误信息
                layout = QVBoxLayout(self)
                layout.addWidget(QLabel(f"加载失败: {str(e)}"))
                print(f"加载选项卡失败: {str(e)}")
        return self.instance


class NetworkToolGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # 设置窗口基本属性
        self.setWindowTitle(AppConfig.APP_NAME)
        self.setMinimumSize(800, 600)
        self.setFont(StyleManager.get_default_font())

        # 设置窗口图标
        icon_path = AppConfig.get_icon_path('app.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 初始化UI
        self.init_ui()

        # 存储当前主题状态
        self._current_theme = None

        # 应用系统主题
        self._current_theme = StyleManager.apply_theme()

        # 监听系统主题变化
        app = QApplication.instance()
        app.paletteChanged.connect(self.on_system_theme_changed)

        # 恢复窗口状态
        AppConfig.restore_window_state(self)

    def init_ui(self):
        """初始化UI"""
        # 创建中央部件
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)

        # 注册选项卡切换事件
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # 创建并添加各个选项卡
        self.create_tabs()

        # 设置中央部件
        self.setCentralWidget(self.tab_widget)

        # 将窗口居中显示
        self.center_window()

    def create_tabs(self):
        """创建所有选项卡"""
        # 定义选项卡配置
        self.tab_configs = [
            {"name": "子网计算", "module": "src.gui.tabs.subnet_calculator_tab", "class": "SubnetCalculatorTab"},
            {"name": "IP定位", "module": "src.gui.tabs.ip_calculator_tab", "class": "IPCalculatorTab"},
            {"name": "路由汇总", "module": "src.gui.tabs.route_summary_tab", "class": "RouteSummaryTab"},
            {"name": "掩码转换", "module": "src.gui.tabs.mask_converter_tab", "class": "MaskConverterTab"},
            {"name": "NAT解析", "module": "src.gui.tabs.nat_parser_tab", "class": "NatParserTab"},
            {"name": "VSR配置", "module": "src.gui.tabs.vsr_config_tab", "class": "VSRConfigTab"},
            {"name": "网络分析", "module": "src.gui.tabs.network_analyzer_tab", "class": "NetworkAnalyzerTab"}
        ]

        # 存储选项卡加载器
        self.tab_loaders = []

        # 添加选项卡占位符
        for config in self.tab_configs:
            # 创建加载器占位符
            loader = TabLoader(
                lambda cfg=config: self.load_tab_class(cfg["module"], cfg["class"]),
                config["name"]
            )
            self.tab_loaders.append(loader)
            self.tab_widget.addTab(loader, config["name"])

        # 立即加载第一个选项卡
        if self.tab_loaders:
            self.load_tab(0)

    def load_tab_class(self, module_name, class_name):
        """动态加载选项卡类"""
        try:
            module = importlib.import_module(module_name)
            return getattr(module, class_name)()
        except Exception as e:
            print(f"加载选项卡失败: {module_name}.{class_name} - {str(e)}")
            raise

    def load_tab(self, index):
        """加载指定索引的选项卡"""
        if 0 <= index < len(self.tab_loaders):
            loader = self.tab_loaders[index]
            if loader.instance is None:
                # 开始加载
                instance = loader.load_tab()
                if instance:
                    # 替换加载器为实际选项卡
                    self.tab_widget.removeTab(index)
                    self.tab_widget.insertTab(index, instance, self.tab_configs[index]["name"])
                    self.tab_widget.setCurrentIndex(index)

    def on_tab_changed(self, index):
        """选项卡切换事件处理"""
        # 保存当前选项卡索引
        AppConfig.save_setting("window/last_tab", index)

        # 加载选项卡内容
        self.load_tab(index)

    def center_window(self):
        """将窗口居中显示"""
        # 获取屏幕几何信息
        screen = self.screen().availableGeometry()
        # 计算窗口居中位置
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        # 移动窗口
        self.move(x, y)

    def on_system_theme_changed(self):
        """系统主题变化时的处理"""
        QApplication.processEvents()  # 处理所有待处理的事件
        self._current_theme = StyleManager.apply_theme(QApplication.instance(), self._current_theme)

    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 保存窗口状态
        AppConfig.save_window_state(self)
        event.accept()
