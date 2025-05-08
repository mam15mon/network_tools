import os
import sys
import warnings
import traceback

# 设置项目根目录
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon, QFont
from src.gui.main_window import NetworkToolGUI
from src.config import AppConfig
from src.utils.logger import logger
from src.gui.styles import StyleManager

# 过滤 Qt 字体警告
warnings.filterwarnings("ignore", category=UserWarning, module="fontTools")

def exception_hook(exctype, value, tb):
    """全局异常处理钩子"""
    # 记录异常到日志
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    logger.error(f"未捕获的异常: {error_msg}")

    # 显示错误对话框
    if QApplication.instance():
        QMessageBox.critical(
            None,
            "应用程序错误",
            f"发生了一个未处理的错误:\n{value}\n\n详细信息已记录到日志文件。"
        )

    # 调用原始的异常处理器
    sys.__excepthook__(exctype, value, tb)

def main():
    # 设置全局异常处理
    sys.excepthook = exception_hook

    # 记录应用启动
    logger.info(f"应用启动 - 版本 {AppConfig.APP_VERSION}")

    # 创建应用实例
    app = QApplication(sys.argv)
    app.setFont(StyleManager.get_default_font())

    # 设置应用图标
    icon_path = AppConfig.get_icon_path('app.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        logger.debug(f"应用图标已设置: {icon_path}")

    try:
        # 创建并显示主窗口
        window = NetworkToolGUI()
        window.show()
        logger.info("主窗口已显示")

        # 运行应用
        return_code = app.exec()
        logger.info(f"应用退出，返回码: {return_code}")
        sys.exit(return_code)
    except Exception as e:
        logger.critical(f"应用启动失败: {str(e)}")
        QMessageBox.critical(None, "启动错误", f"应用启动失败: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()