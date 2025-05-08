from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, 
                           QTextEdit, QTableWidget, QTableWidgetItem,
                           QHeaderView)
import ipaddress
from ...utils.text_utils import TextUtils  # 添加导入

class MaskConverterTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        
        # 创建输入区域
        input_group = QGroupBox("输入")
        input_layout = QVBoxLayout()
        
        self.mask_input = QTextEdit()
        self.mask_input.setPlaceholderText(TextUtils.MASK_CONVERTER_HELP)
        
        self.mask_input.textChanged.connect(self.convert_mask)
        input_layout.addWidget(self.mask_input)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 创建结果显示区域
        result_group = QGroupBox("转换结果")
        result_layout = QVBoxLayout()
        
        # 创建结果表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["CIDR格式", "掩码格式", "反掩码格式"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.result_table.setAlternatingRowColors(True)
        result_layout.addWidget(self.result_table)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)

    def convert_mask(self):
        """转换掩码格式"""
        input_text = self.mask_input.toPlainText().strip()
        if not input_text:
            self.result_table.setRowCount(0)
            return
            
        entries = []
        # 使用TextUtils处理输入文本
        for line in TextUtils.split_text(input_text):
            try:
                if ' ' in line:  # 掩码格式
                    ip, mask = line.split()
                    if not self.is_valid_netmask(mask):
                        raise ValueError(f"无效的子网掩码: {mask}")
                    network = ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
                else:  # CIDR格式或单IP
                    if '/' not in line:
                        line += '/32'
                    network = ipaddress.IPv4Network(line, strict=False)
                    
                entries.append((
                    f"{network.network_address}/{network.prefixlen}",
                    f"{network.network_address} {network.netmask}",
                    f"{network.network_address} {network.hostmask}"
                ))
                
            except Exception as e:
                entries.append((f"错误: {line}", str(e), ""))
        
        # 更新表格
        self.result_table.setRowCount(len(entries))
        for i, (cidr, mask, hostmask) in enumerate(entries):
            self.result_table.setItem(i, 0, QTableWidgetItem(cidr))
            self.result_table.setItem(i, 1, QTableWidgetItem(mask))
            self.result_table.setItem(i, 2, QTableWidgetItem(hostmask))

    def is_valid_netmask(self, mask: str) -> bool:
        """验证是否为有效的子网掩码"""
        try:
            # 将掩码转换为二进制字符串
            mask_parts = [format(int(x), '08b') for x in mask.split('.')]
            mask_binary = ''.join(mask_parts)
            
            # 检查是否正好32位
            if len(mask_binary) != 32:
                return False
            
            # 检查是否为连续的1后跟连续的0
            one_seen = False
            zero_seen = False
            
            for bit in mask_binary:
                if bit == '1':
                    if zero_seen:  # 如果之前已经看到0，现在又看到1，则无效
                        return False
                    one_seen = True
                else:  # bit == '0'
                    if one_seen:  # 已经看到过1，现在开始看到0
                        zero_seen = True
            
            return True
            
        except Exception:
            return False