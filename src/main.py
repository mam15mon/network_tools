import os
import sys
import warnings

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon
from src.gui.main_window import NetworkToolGUI

# 过滤 Qt 字体警告
warnings.filterwarnings("ignore", category=UserWarning, module="fontTools")

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))
    
    # 设置应用图标
    icon_path = os.path.join(project_root, 'resources', 'icons', 'app.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = NetworkToolGUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()