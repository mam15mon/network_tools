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
            # 使用 ip.sb 判断IP归属地
            ip_sb_url = f"https://api.ip.sb/geoip/{ip}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            check_response = requests.get(ip_sb_url, timeout=5, headers=headers)
            check_data = check_response.json()
            
            print("ip.sb API响应:")
            print(check_data)
            
            is_china_ip = check_data.get('country_code') == 'CN'
            
            if is_china_ip:
                # 使用国内API (api.vore.top)
                vore_url = f"https://api.vore.top/api/IPdata?ip={ip}"
                response = requests.get(vore_url, timeout=5)
                data = response.json()
                
                print("\nvore.top API响应:")
                print(data)
                
                if data.get('code') == 200:
                    ipdata = data['ipdata']
                    adcode = data['adcode']
                    fields = {
                        "text": "IP地址",
                        "location": "地理位置",
                        "info1": "省份",
                        "info2": "城市",
                        "isp": "运营商",
                        "asn_number": "AS编号"
                    }
                    data_source = {
                        "text": data['ipinfo']['text'],
                        "location": adcode['o'],
                        "info1": ipdata['info1'],
                        "info2": ipdata['info2'],
                        "isp": ipdata['isp'],
                        "asn_number": f"AS{check_data.get('asn', '')}"
                    }
                else:
                    raise Exception("API返回错误")
            else:
                # 直接使用已经获取到的 ip.sb 数据
                fields = {
                    "ip": "IP地址",
                    "country": "国家/地区",
                    "isp": "运营商",
                    "organization": "所属组织",
                    "asn_number": "AS编号",
                    "asn_organization": "AS组织",
                    "timezone": "时区"
                }
                data_source = {
                    "ip": check_data['ip'],
                    "country": check_data['country'],
                    "isp": check_data.get('isp', ''),
                    "organization": check_data.get('organization', ''),
                    "asn_number": f"AS{check_data.get('asn', '')}",
                    "asn_organization": check_data.get('asn_organization', ''),
                    "timezone": check_data.get('timezone', '')
                }
            
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