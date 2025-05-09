import requests
import re
import threading
from PyQt6.QtCore import QObject, pyqtSignal

class IPFetcher(QObject):
    """异步获取IP的类"""
    ip_fetched = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._default_ip = "192.168.1.1"

    def fetch_async(self):
        """异步获取IP"""
        threading.Thread(target=self._fetch_ip, daemon=True).start()

    def _fetch_ip(self):
        """在后台线程中获取IP"""
        ip = self._get_public_ip()
        self.ip_fetched.emit(ip)

    def _get_public_ip(self):
        """获取公网IP的实际方法"""
        try:
            apis = [
                'https://ip.3322.net',
                'https://myip.ipip.net',
                'https://ddns.oray.com/checkip'
            ]

            for api in apis:
                try:
                    response = requests.get(api, timeout=2)
                    if response.status_code == 200:
                        ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', response.text)
                        if ip_match:
                            return ip_match.group(1)
                except:
                    continue
        except:
            pass
        return self._default_ip

def get_public_ip():
    """获取默认IP的同步方法（不进行网络请求）"""
    return "192.168.1.1"
