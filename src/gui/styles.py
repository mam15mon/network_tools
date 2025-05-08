"""
UI样式管理模块
提供统一的样式定义和主题管理功能
"""
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from qt_material import apply_stylesheet
import darkdetect

class StyleManager:
    """样式管理器类"""

    # 默认字体 - 使用系统默认字体族
    DEFAULT_FONT = ""  # 空字符串表示使用系统默认字体
    DEFAULT_FONT_SIZE = 10

    # 主题定义
    THEMES = {
        "light": "light_blue.xml",
        "dark": "dark_blue.xml"
    }

    # 按钮样式
    BUTTON_STYLES = {
        "default": """
            /* 默认按钮样式 - 蓝色 */
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 5px 10px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #3a7bc8;
            }
            QPushButton:pressed {
                background-color: #2a6cb8;
            }
        """,
        "import": """
            /* 导入按钮 - 绿色 */
            QPushButton.import-btn {
                background-color: #50c878;
            }
            QPushButton.import-btn:hover {
                background-color: #40a768;
            }
        """,
        "generate": """
            /* 生成配置按钮 - 橙色 */
            QPushButton.generate-btn {
                background-color: #ff8c00;
            }
            QPushButton.generate-btn:hover {
                background-color: #e67e00;
            }
        """
    }

    @classmethod
    def get_default_font(cls, size=None):
        """获取默认字体"""
        font = QFont()  # 创建默认字体
        if cls.DEFAULT_FONT:
            font.setFamily(cls.DEFAULT_FONT)
        font.setPointSize(size or cls.DEFAULT_FONT_SIZE)
        return font

    @classmethod
    def get_monospace_font(cls, size=10):
        """获取等宽字体"""
        font = QFont("Courier New", size)
        font.setStyleHint(QFont.StyleHint.Monospace)
        return font

    @classmethod
    def apply_theme(cls, app=None, current_theme=None):
        """应用主题"""
        app = app or QApplication.instance()
        is_dark = darkdetect.isDark()
        new_theme = cls.THEMES["dark"] if is_dark else cls.THEMES["light"]

        # 如果主题没有变化，不重新应用
        if current_theme == new_theme:
            return current_theme

        extra = {
            'font_family': cls.DEFAULT_FONT,
            'font_size': '13px',
            'line_height': '13px',
            'density_scale': '-1',
        }

        # 应用新样式
        apply_stylesheet(
            app,
            theme=new_theme,
            invert_secondary=('light' in new_theme),
            extra=extra
        )

        # 应用按钮样式
        all_button_styles = "".join(cls.BUTTON_STYLES.values())
        app.setStyleSheet(app.styleSheet() + all_button_styles)

        return new_theme
