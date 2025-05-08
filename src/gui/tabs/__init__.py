import requests
import re

def get_public_ip():
    """获取公网IP的通用方法"""
    try:
        apis = [
            'https://ip.3322.net',
            'https://myip.ipip.net',
            'https://ddns.oray.com/checkip'
        ]
        
        for api in apis:
            try:
                response = requests.get(api, timeout=3)
                if response.status_code == 200:
                    ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', response.text)
                    if ip_match:
                        return ip_match.group(1)
            except:
                continue
    except:
        pass
    return "1.1.1.1"
