import re
import threading
from PyQt6.QtCore import QObject, pyqtSignal, QUrl

class IPFetcher(QObject):
    """异步获取IP的类"""
    ip_fetched = pyqtSignal(str)
    fetch_started = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._default_ip = "192.168.1.1"
        self._timer = None
        from PyQt6.QtCore import QTimer

        # 创建定时器，延迟获取IP，避免启动时阻塞
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._get_ip_safe)

    def fetch_async(self):
        """异步获取IP"""
        # 使用定时器延迟获取IP，避免启动时阻塞
        if self._timer:
            self._timer.start(1000)  # 1秒后开始获取IP

    def _get_ip_safe(self):
        """安全地获取IP"""
        try:
            from PyQt6.QtCore import QThread, QObject
            from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

            # 使用Qt的网络API而不是requests
            self.manager = QNetworkAccessManager()
            self.manager.finished.connect(self._handle_response)

            # 尝试第一个API
            self.manager.get(QNetworkRequest(QUrl("https://ip.3322.net")))
        except Exception as e:
            print(f"获取IP出错: {str(e)}")
            self.ip_fetched.emit(self._default_ip)

    def _handle_response(self, reply):
        """处理网络响应"""
        try:
            if reply.error() == QNetworkReply.NetworkError.NoError:
                data = reply.readAll().data().decode('utf-8')
                ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', data)
                if ip_match:
                    self.ip_fetched.emit(ip_match.group(1))
                    return

            # 如果第一个API失败，尝试第二个
            if reply.url().toString() == "https://ip.3322.net":
                self.manager.get(QNetworkRequest(QUrl("https://myip.ipip.net")))
            elif reply.url().toString() == "https://myip.ipip.net":
                self.manager.get(QNetworkRequest(QUrl("https://ddns.oray.com/checkip")))
            else:
                # 所有API都失败，使用默认IP
                self.ip_fetched.emit(self._default_ip)
        except Exception as e:
            print(f"处理IP响应出错: {str(e)}")
            self.ip_fetched.emit(self._default_ip)

def get_public_ip():
    """获取默认IP的同步方法（不进行网络请求）"""
    return "192.168.1.1"
