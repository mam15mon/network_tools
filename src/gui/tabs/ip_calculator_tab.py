from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                           QLineEdit, QPushButton, QLabel, QTableWidget,
                           QTableWidgetItem, QHeaderView)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import requests
from . import get_public_ip

class IPCalculatorTab(QWidget):
    """IP定位查询选项卡"""
    def __init__(self):
        super().__init__()
        self.setup_ui()
        # 设置默认公网IP
        self.ip_query_input.setText(get_public_ip())
        
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        
        # 创建输入区域
        input_group = QGroupBox("IP地址")
        input_layout = QHBoxLayout()
        
        self.ip_query_input = QLineEdit()
        self.query_button = QPushButton("查询")
        self.query_button.clicked.connect(self.query_ip_info)
        
        input_layout.addWidget(self.ip_query_input)
        input_layout.addWidget(self.query_button)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 创建结果显示区域
        result_group = QGroupBox("查询结果")
        result_layout = QVBoxLayout()
        
        # 创建表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(2)
        self.result_table.setHorizontalHeaderLabels(["项目", "信息"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.result_table.setAlternatingRowColors(True)
        
        result_layout.addWidget(self.result_table)
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        # 创建错误信息标签
        self.error_label = QLabel()
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.hide()
        layout.addWidget(self.error_label)

    def query_ip_info(self):
        """查询IP信息"""
        ip = self.ip_query_input.text().strip()
        if not ip:
            self.show_error("请输入有效的IP地址!")
            return
        
        # 禁用查询按钮并更改文本
        self.query_button.setEnabled(False)
        self.query_button.setText("查询中...")
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            data_source = None
            fields = None
            
            # 尝试多个API，按优先级顺序
            apis = [
                {
                    'url': f'https://realip.cc/?ip={ip}',
                    'handler': lambda data: {
                        'fields': {
                            'ip': 'IP地址',
                            'country': '国家',
                            'province': '省份',
                            'city': '城市',
                            'isp': '运营商',
                            'time_zone': '时区',
                            'latitude': '纬度',
                            'longitude': '经度'
                        },
                        'data': {
                            'ip': data['ip'],
                            'country': data['country'],
                            'province': data['province'],
                            'city': data['city'],
                            'isp': data['isp'],
                            'time_zone': data['time_zone'],
                            'latitude': data['latitude'],
                            'longitude': data['longitude']
                        }
                    }
                },
                {
                    'url': f'https://api.ip.sb/geoip/{ip}',
                    'handler': lambda data: {
                        'fields': {
                            'ip': 'IP地址',
                            'country': '国家',
                            'region': '地区',
                            'city': '城市',
                            'isp': '运营商',
                            'timezone': '时区',
                            'latitude': '纬度',
                            'longitude': '经度'
                        },
                        'data': {
                            'ip': data['ip'],
                            'country': data['country'],
                            'region': data['region'],
                            'city': data['city'],
                            'isp': data['isp'],
                            'timezone': data['timezone'],
                            'latitude': data['latitude'],
                            'longitude': data['longitude']
                        }
                    }
                },
                {
                    'url': f'https://api.ip2location.io/?ip={ip}',
                    'handler': lambda data: {
                        'fields': {
                            'ip': 'IP地址',
                            'country_name': '国家',
                            'region_name': '地区',
                            'city_name': '城市',
                            'time_zone': '时区',
                            'latitude': '纬度',
                            'longitude': '经度'
                        },
                        'data': {
                            'ip': data['ip'],
                            'country_name': data['country_name'],
                            'region_name': data['region_name'],
                            'city_name': data['city_name'],
                            'time_zone': data['time_zone'],
                            'latitude': data['latitude'],
                            'longitude': data['longitude']
                        }
                    }
                },
                {
                    'url': f'https://whois.pconline.com.cn/ipJson.jsp?ip={ip}&json=true',
                    'handler': lambda data: {
                        'fields': {
                            'ip': 'IP地址',
                            'addr': '地理位置',
                            'pro': '省份',
                            'city': '城市',
                            'region': '地区'
                        },
                        'data': {
                            'ip': data['ip'],
                            'addr': data['addr'],
                            'pro': data['pro'],
                            'city': data['city'],
                            'region': data['region']
                        }
                    }
                }
            ]
            
            for api in apis:
                try:
                    response = requests.get(api['url'], headers=headers, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        print(f"\n{api['url']} API响应:")
                        print(data)
                        result = api['handler'](data)
                        fields = result['fields']
                        data_source = result['data']
                        break
                except Exception as e:
                    print(f"API {api['url']} 调用失败: {str(e)}")
                    continue
            
            # 所有API都失败时使用ip2region本地查询
            if not data_source:
                from XdbSearchIP import XdbSearcher
                db_path = 'resources/ip2region.xdb'
                try:
                    # 使用文件缓存方式查询
                    searcher = XdbSearcher(dbfile=db_path)
                    region_str = searcher.searchByIPStr(ip)
                    fields = {
                        'ip': 'IP地址',
                        'region': '地理位置'
                    }
                    data_source = {
                        'ip': ip,
                        'region': region_str
                    }
                    print("\n使用ip2region本地查询:")
                    print(data_source)
                except Exception as e:
                    print(f"ip2region查询失败: {str(e)}")
                    raise
                finally:
                    searcher.close()
            
            print("\n最终使用的数据源:")
            print(data_source)
            
            # 清空错误信息
            self.error_label.hide()
            
            # 设置表格行数
            valid_fields = [(key, label) for key, label in fields.items() if key in data_source and data_source[key]]
            self.result_table.setRowCount(len(valid_fields))
            
            # 填充数据
            for row, (key, label) in enumerate(valid_fields):
                label_item = QTableWidgetItem(label)
                value_item = QTableWidgetItem(str(data_source[key]))
                
                font = QFont("Microsoft YaHei", 10)
                label_item.setFont(font)
                value_item.setFont(font)
                
                label_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                value_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                
                self.result_table.setItem(row, 0, label_item)
                self.result_table.setItem(row, 1, value_item)
            
            self.result_table.show()
                
        except Exception as e:
            self.show_error(f"查询出错: {str(e)}")
        finally:
            # 恢复查询按钮状态
            self.query_button.setEnabled(True)
            self.query_button.setText("查询")

    def show_error(self, message: str):
        """显示错误信息"""
        self.error_label.setText(message)
        self.error_label.show()
        self.result_table.setRowCount(0)  # 清空表格
