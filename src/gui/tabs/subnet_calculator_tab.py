from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                           QLineEdit, QComboBox, QLabel, QTableWidget,
                           QTableWidgetItem, QHeaderView)
import ipaddress

from ...utils.ip_utils import IPUtils
from . import get_public_ip

class SubnetCalculatorTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        # 设置默认公网IP
        self.ip_input.setText(get_public_ip())
        
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        
        # 创建输入区域
        input_group = QGroupBox("输入")
        input_layout = QHBoxLayout()
        
        # IP地址输入
        ip_layout = QVBoxLayout()
        ip_label = QLabel("IP地址:")
        self.ip_input = QLineEdit()
        self.ip_input.textChanged.connect(self.calculate_subnet)
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(self.ip_input)
        
        # 掩码选择
        mask_layout = QVBoxLayout()
        mask_label = QLabel("掩码长度:")
        self.mask_combo = QComboBox()
        for i in range(0, 33):
            self.mask_combo.addItem(f"/{i}", i)
        self.mask_combo.setCurrentText("/24")  # 默认选择/24
        self.mask_combo.currentIndexChanged.connect(self.calculate_subnet)
        mask_layout.addWidget(mask_label)
        mask_layout.addWidget(self.mask_combo)
        
        input_layout.addLayout(ip_layout)
        input_layout.addLayout(mask_layout)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 创建基本信息显示区域
        basic_group = QGroupBox("基本信息")
        basic_layout = QVBoxLayout()
        
        # 创建基本信息表格
        self.basic_table = QTableWidget()
        self.basic_table.setColumnCount(2)
        self.basic_table.setHorizontalHeaderLabels(["项目", "信息"])
        self.basic_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.basic_table.verticalHeader().setVisible(False)
        self.basic_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.basic_table.setAlternatingRowColors(True)
        basic_layout.addWidget(self.basic_table)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # 创建子网列表显示区域
        subnet_group = QGroupBox("子网列表")
        subnet_layout = QVBoxLayout()
        
        # 创建子网列表表格
        self.subnet_table = QTableWidget()
        self.subnet_table.setColumnCount(3)
        self.subnet_table.setHorizontalHeaderLabels(["网络地址", "可用IP范围", "广播地址"])
        self.subnet_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.subnet_table.verticalHeader().setVisible(False)
        self.subnet_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.subnet_table.setAlternatingRowColors(True)
        subnet_layout.addWidget(self.subnet_table)
        
        subnet_group.setLayout(subnet_layout)
        layout.addWidget(subnet_group)

    def calculate_subnet(self):
        """计算子网信息"""
        try:
            ip = self.ip_input.text().strip()
            if not ip:
                self.clear_results()
                return
                
            prefix = self.mask_combo.currentData()
            subnet_info = IPUtils.calculate_subnet_info(ip, prefix)
            
            # 更新基本信息表格
            basic_info = [
                ("IP地址", ip),
                ("网络地址", subnet_info['network_address']),
                ("可用IP范围", subnet_info['ip_range']),
                ("广播地址", subnet_info['broadcast_address']),
                ("总主机数", subnet_info['total_hosts']),
                ("可用主机数", subnet_info['usable_hosts']),
                ("子网掩码", subnet_info['netmask']),
                ("反掩码", subnet_info['hostmask']),
                ("二进制掩码", subnet_info['binary_netmask']),
                ("IP类别", subnet_info['ip_class']),
                ("掩码长度", subnet_info['prefix_length']),
                # 添加详细信息
                ("CIDR格式", f"{ip}/{subnet_info['prefix_length']}"),
                ("二进制ID", subnet_info['binary_id']),
                ("整数ID", subnet_info['integer_id']),
                ("十六进制ID", subnet_info['hex_id']),
                ("反向解析", subnet_info['reverse_dns']),
                ("IPv4映射地址", subnet_info['ipv4_mapped']),
                ("6to4前缀", subnet_info['6to4_prefix'])
            ]
            
            self.basic_table.setRowCount(len(basic_info))
            for row, (label, value) in enumerate(basic_info):
                self.basic_table.setItem(row, 0, QTableWidgetItem(label))
                self.basic_table.setItem(row, 1, QTableWidgetItem(str(value)))
            
            # 更新子网列表
            self.update_subnet_list(ip, prefix)
            
        except Exception as e:
            self.show_error(str(e))

    def update_subnet_list(self, ip: str, prefix: int):
        """更新子网列表"""
        try:
            network = ipaddress.IPv4Network(f'{ip}/{prefix}', strict=False)
            
            # 根据掩码长度确定要显示的子网范围
            if prefix <= 7:
                base_network = ipaddress.IPv4Network('0.0.0.0/0')
                title = f"所有可能的 /{prefix} 子网"
            elif prefix <= 15:
                a_class = f"{ip.split('.')[0]}.0.0.0/8"
                base_network = ipaddress.IPv4Network(a_class)
                title = f"A类网络 {a_class} 下所有可能的 /{prefix} 子网"
            elif prefix <= 23:
                b_class = '.'.join(ip.split('.')[:2]) + '.0.0/16'
                base_network = ipaddress.IPv4Network(b_class)
                title = f"B类网络 {b_class} 下所有可能的 /{prefix} 子网"
            else:
                c_class = '.'.join(ip.split('.')[:3]) + '.0/24'
                base_network = ipaddress.IPv4Network(c_class)
                title = f"C类网络 {c_class} 下所有可能的 /{prefix} 子网"
            
            subnets = list(base_network.subnets(new_prefix=prefix))
            
            # 更新子网表格
            self.subnet_table.setRowCount(len(subnets))
            for i, subnet in enumerate(subnets):
                if prefix == 31:
                    ip_range = "不适用"
                else:
                    ip_range = f"{subnet.network_address + 1} - {subnet.broadcast_address - 1}"
                
                self.subnet_table.setItem(i, 0, QTableWidgetItem(str(subnet.network_address)))
                self.subnet_table.setItem(i, 1, QTableWidgetItem(ip_range))
                self.subnet_table.setItem(i, 2, QTableWidgetItem(str(subnet.broadcast_address)))
            
        except Exception as e:
            self.show_error(f"生成子网列表错误: {str(e)}")

    def clear_results(self):
        """清空结果显示"""
        self.basic_table.setRowCount(0)
        self.subnet_table.setRowCount(0)

    def show_error(self, message: str):
        """显示错误信息"""
        self.basic_table.setRowCount(1)
        self.basic_table.setItem(0, 0, QTableWidgetItem("错误"))
        self.basic_table.setItem(0, 1, QTableWidgetItem(message))
        self.subnet_table.setRowCount(0)