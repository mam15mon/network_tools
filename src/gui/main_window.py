from PyQt6.QtWidgets import QMainWindow, QTabWidget, QApplication
from PyQt6.QtGui import QFont, QIcon
from qt_material import apply_stylesheet
import darkdetect
import os

from src.gui.tabs.nat_parser_tab import NatParserTab
from src.gui.tabs.ip_calculator_tab import IPCalculatorTab
from src.gui.tabs.subnet_calculator_tab import SubnetCalculatorTab
from src.gui.tabs.route_summary_tab import RouteSummaryTab
from src.gui.tabs.mask_converter_tab import MaskConverterTab
from src.gui.tabs.vsr_config_tab import VSRConfigTab
from src.gui.tabs.network_analyzer_tab import NetworkAnalyzerTab

class NetworkToolGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 设置窗口基本属性
        self.setWindowTitle('网络工具集')
        self.setMinimumSize(800, 600)
        self.setFont(QFont("Microsoft YaHei", 10))
        
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'icons', 'app.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 初始化UI
        self.init_ui()
        
        # 存储当前主题状态
        self._current_theme = None
        
        # 应用系统主题
        self.apply_theme()
        
        # 监听系统主题变化
        app = QApplication.instance()
        app.paletteChanged.connect(self.on_system_theme_changed)
    
    def init_ui(self):
        """初始化UI"""
        # 创建中央部件
        central_widget = QTabWidget()
        central_widget.setDocumentMode(True)
        central_widget.setMovable(True)
        central_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # 创建并添加各个选项卡
        self.create_tabs(central_widget)
        
        # 设置中央部件
        self.setCentralWidget(central_widget)
        
        # 将窗口居中显示
        self.center_window()
    
    def create_tabs(self, tab_widget: QTabWidget):
        """创建所有选项卡"""
    
        
        # 子网计算选项卡
        subnet_tab = SubnetCalculatorTab()
        tab_widget.addTab(subnet_tab, "子网计算")
        
        # IP定位查询选项卡
        ip_tab = IPCalculatorTab()
        tab_widget.addTab(ip_tab, "IP定位")
        # 路由汇总选项卡
        route_tab = RouteSummaryTab()
        tab_widget.addTab(route_tab, "路由汇总")
        
        # 掩码转换选项卡
        mask_tab = MaskConverterTab()
        tab_widget.addTab(mask_tab, "掩码转换")
        
        # NAT解析选项卡
        nat_tab = NatParserTab()
        tab_widget.addTab(nat_tab, "NAT解析")

        # VSR配置生成选项卡
        vsr_tab = VSRConfigTab()
        tab_widget.addTab(vsr_tab, "VSR配置")
        
        # 添加网络分析选项卡
        network_tab = NetworkAnalyzerTab()
        tab_widget.addTab(network_tab, "网络分析")
    
    def center_window(self):
        """将窗口居中显示"""
        # 获取屏幕几何信息
        screen = self.screen().availableGeometry()
        # 计算窗口居中位置
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        # 移动窗口
        self.move(x, y)
    
    def apply_theme(self):
        """应用主题"""
        is_dark = darkdetect.isDark()
        new_theme = 'dark_blue.xml' if is_dark else 'light_blue.xml'
        
        # 如果主题没有变化，不重新应用
        if self._current_theme == new_theme:
            return
        
        self._current_theme = new_theme
        
        extra = {
            'font_family': 'Microsoft YaHei',
            'font_size': '13px',
            'line_height': '13px',
            'density_scale': '-1',
        }
        
        # 应用新样式
        apply_stylesheet(
            QApplication.instance(),
            theme=new_theme,
            invert_secondary=('light' in new_theme),
            extra=extra
        )
    
    def on_system_theme_changed(self):
        """系统主题变化时的处理"""
        QApplication.processEvents()  # 处理所有待处理的事件
        self.apply_theme()