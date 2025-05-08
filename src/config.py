"""
应用程序配置管理模块
提供集中的配置管理功能
"""
import os
import json
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QTabWidget

class AppConfig:
    """应用程序配置类"""

    # 应用程序基本信息
    APP_NAME = "网络工具集"
    APP_VERSION = "1.0.0"
    COMPANY_NAME = "NetworkTools"

    # 资源路径
    @classmethod
    def get_project_root(cls):
        """获取项目根目录"""
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    @classmethod
    def get_resource_path(cls, *paths):
        """获取资源文件路径"""
        return os.path.join(cls.get_project_root(), 'resources', *paths)

    @classmethod
    def get_ip_db_path(cls):
        """获取IP数据库路径"""
        return cls.get_resource_path('ip2region.xdb')

    @classmethod
    def get_icon_path(cls, icon_name):
        """获取图标路径"""
        return cls.get_resource_path('icons', icon_name)

    # 设置管理
    @classmethod
    def get_settings(cls):
        """获取QSettings实例"""
        return QSettings(cls.COMPANY_NAME, cls.APP_NAME)

    @classmethod
    def save_setting(cls, key, value):
        """保存设置"""
        settings = cls.get_settings()
        settings.setValue(key, value)

    @classmethod
    def load_setting(cls, key, default=None):
        """加载设置"""
        settings = cls.get_settings()
        return settings.value(key, default)

    @classmethod
    def save_window_state(cls, window):
        """保存窗口状态"""
        settings = cls.get_settings()
        settings.setValue("window/geometry", window.saveGeometry())
        settings.setValue("window/state", window.saveState())
        settings.setValue("window/last_tab", window.centralWidget().currentIndex())

    @classmethod
    def restore_window_state(cls, window):
        """恢复窗口状态"""
        settings = cls.get_settings()
        if settings.contains("window/geometry"):
            window.restoreGeometry(settings.value("window/geometry"))
        if settings.contains("window/state"):
            window.restoreState(settings.value("window/state"))

        # 恢复上次使用的选项卡
        last_tab = settings.value("window/last_tab", 0, type=int)
        if window.centralWidget() and isinstance(window.centralWidget(), QTabWidget):
            if 0 <= last_tab < window.centralWidget().count():
                window.centralWidget().setCurrentIndex(last_tab)
