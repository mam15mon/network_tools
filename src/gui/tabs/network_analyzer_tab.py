from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                           QPushButton, QFileDialog, QLabel, QHBoxLayout, QLineEdit, QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt
from warnings import filterwarnings
import os
filterwarnings("ignore")
from scapy.layers.inet import TCP, IP, UDP
from scapy.all import *
import re
from netaddr import IPAddress

class SortableTableWidgetItem(QTableWidgetItem):
    """可排序的表格项"""
    def __init__(self, value, sort_value=None):
        super().__init__(str(value))
        self._sort_value = sort_value if sort_value is not None else value
        self.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def __lt__(self, other):
        if isinstance(self._sort_value, tuple):  # IP:port tuple
            return (self._sort_value[0], self._sort_value[1]) < (other._sort_value[0], other._sort_value[1])
        return self._sort_value < other._sort_value

def parse_ip_port(address):
    """解析IP地址和端口"""
    try:
        if ':' not in address:
            return (0, 0)
        
        ip, port = address.rsplit(':', 1)
        return (int(IPAddress(ip)), int(port))
    except:
        return (0, 0)

def parse_size(size_str):
    """解析流量大小，统一转换为字节"""
    try:
        if isinstance(size_str, (int, float)):
            return float(size_str)
            
        size_str = str(size_str).upper()
        if 'GB' in size_str:
            return float(size_str.replace('GB', '')) * 1024 * 1024 * 1024
        elif 'MB' in size_str:
            return float(size_str.replace('MB', '')) * 1024 * 1024
        elif 'KB' in size_str:
            return float(size_str.replace('KB', '')) * 1024
        elif 'B' in size_str:
            return float(size_str.replace('B', ''))
        else:
            return float(size_str)
    except (ValueError, TypeError):
        return 0

class NetworkAnalyzerTab(QWidget):
    def __init__(self):
        super().__init__()
        self.flows = []
        self.summary = []
        self.initUI()

    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # 顶部控制区域
        top_layout = QHBoxLayout()
        
        # 文件选择区域
        file_layout = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText('选择PCAP文件...')
        self.file_path.setReadOnly(True)
        
        self.select_btn = QPushButton('选择文件')
        self.select_btn.clicked.connect(self.select_file)
        
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(self.select_btn)
        
        # 搜索区域
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('输入搜索关键词...')
        self.search_input.textChanged.connect(self.filter_results)
        
        search_layout.addWidget(QLabel('搜索:'))
        search_layout.addWidget(self.search_input)
        
        # 将文件选择和搜索添加到顶部布局
        top_layout.addLayout(file_layout, stretch=2)
        top_layout.addLayout(search_layout, stretch=1)
        
        layout.addLayout(top_layout)
        
        # 添加表格
        self.table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.table)
        
        # 添加统计信息标签
        self.stats_label = QLabel('统计信息：等待分析文件...')
        layout.addWidget(self.stats_label)
        
        self.setLayout(layout)

    def setup_table(self):
        """设置表格"""
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            '协议', '源地址', '目标地址', '标志位', 
            '流量大小', '正向计数', '反向计数'
        ])
        
        # 启用排序
        self.table.setSortingEnabled(True)
        
        # 设置表头
        header = self.table.horizontalHeader()
        header.setSectionsClickable(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        # 设置选择模式
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)

    def select_file(self):
        """选择pcap文件"""
        fname, _ = QFileDialog.getOpenFileName(
            self, 
            '选择PCAP文件', 
            '', 
            'PCAP files (*.pcap *.pcapng);;All files (*.*)'
        )
        if fname:
            # 检查文件大小
            file_size = os.path.getsize(fname) / (1024 * 1024)  # 转换为MB
            if file_size > 100:  # 如果文件大于100MB
                reply = QMessageBox.question(
                    self, 
                    '大文件警告',
                    f'文件大小为 {file_size:.1f}MB，分析可能需要较长时间。是否继续？',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
                
            self.file_path.setText(fname)
            self.analyze_pcap(fname)

    def read_pcap(self, pcap):
        """读取pcap文件"""
        flows = list()
        try:
            packets = rdpcap(pcap)
            for packet in packets:
                if packet.haslayer(IP):
                    if packet.haslayer(TCP):
                        flows.append([
                            "TCP", 
                            f"{packet[IP].src}:{packet[TCP].sport}", 
                            f"{packet[IP].dst}:{packet[TCP].dport}",
                            packet.sprintf('%TCP.flags%'), 
                            packet.sprintf('%IP.len%')
                        ])
                    elif packet.haslayer(UDP):
                        flows.append([
                            "UDP", 
                            f"{packet[IP].src}:{packet[UDP].sport}", 
                            f"{packet[IP].dst}:{packet[UDP].dport}",
                            '--', 
                            packet.sprintf('%IP.len%')
                        ])
            return flows
        except Exception as e:
            self.stats_label.setText(f'错误: {str(e)}')
            return []

    def reverse_socket(self, socket):
        """反转源目标地址"""
        return [socket[0], socket[2], socket[1], socket[3], socket[4]]

    def increment_count(self, socket, flow_list, counter_position):
        """增加计数"""
        for sockets in range(len(flow_list)):
            if (flow_list[sockets][0] == socket[0] and 
                flow_list[sockets][1] == socket[1] and 
                flow_list[sockets][2] == socket[2]):
                if len(flow_list[sockets]) == counter_position - 1:
                    flow_list[sockets].append(1)
                elif len(flow_list[sockets]) >= counter_position:
                    flow_list[sockets][counter_position - 1] += 1

    def increment_size(self, socket, flow_list):
        """增加流量大小"""
        for sockets in range(len(flow_list)):
            if (flow_list[sockets][0] == socket[0] and 
                flow_list[sockets][1] == socket[1] and 
                flow_list[sockets][2] == socket[2]):
                flow_list[sockets][4] = int(flow_list[sockets][4]) + int(socket[4])

    def add_tcp_flags(self, socket, flow_list):
        """添加TCP标志位"""
        for sockets in range(len(flow_list)):
            if (flow_list[sockets][0] == socket[0] and 
                flow_list[sockets][1] == socket[1] and 
                flow_list[sockets][2] == socket[2]):
                for flag in socket[3]:
                    if flag not in flow_list[sockets][3]:
                        flow_list[sockets][3] = flow_list[sockets][3] + flag

    def summarize_packets(self, flows):
        """汇总数据包信息"""
        flows_with_count = list()
        flows_without_count = list()
        for flow in flows:
            rsocket = self.reverse_socket(flow)
            short_flow = [flow[0], flow[1], flow[2]]
            reverse_short_flow = [flow[0], flow[2], flow[1]]
            if short_flow not in flows_without_count:
                if reverse_short_flow not in flows_without_count:
                    forward_socket_with_count = flow.copy()
                    forward_socket_with_count.append(1)
                    flows_with_count.append(forward_socket_with_count)
                    flows_without_count.append(short_flow)
                else:
                    self.increment_count(rsocket, flows_with_count, 7)
                    self.increment_size(rsocket, flows_with_count)
                    self.add_tcp_flags(rsocket, flows_with_count)
            else:
                self.increment_count(flow, flows_with_count, 6)
                self.increment_size(flow, flows_with_count)
                self.add_tcp_flags(flow, flows_with_count)
        return flows_with_count

    def format_size(self, bytes_size):
        """格式化字节大小显示"""
        try:
            bytes_size = int(bytes_size)
            if bytes_size >= 1024 * 1024 * 1024:
                return f"{bytes_size/1024/1024/1024:.2f} GB"
            elif bytes_size >= 1024 * 1024:
                return f"{bytes_size/1024/1024:.2f} MB"
            elif bytes_size >= 1024:
                return f"{bytes_size/1024:.2f} KB"
            else:
                return f"{bytes_size} B"
        except (ValueError, TypeError):
            return "0 B"

    def update_table(self, summary):
        """更新表格显示"""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(summary))
        
        for row, flow in enumerate(summary):
            # 协议列
            self.table.setItem(row, 0, SortableTableWidgetItem(flow[0]))
            
            # 源地址和目标地址列 - 使用netaddr进行IP排序
            self.table.setItem(row, 1, 
                SortableTableWidgetItem(flow[1], parse_ip_port(flow[1])))
            self.table.setItem(row, 2, 
                SortableTableWidgetItem(flow[2], parse_ip_port(flow[2])))
            
            # 标志位列
            self.table.setItem(row, 3, SortableTableWidgetItem(flow[3]))
            
            # 流量大小列 - 转换为合适的单位显示，但保持字节数用于排序
            try:
                size = int(flow[4])
                if size >= 1024 * 1024 * 1024:
                    display_size = f"{size/1024/1024/1024:.2f} GB"
                elif size >= 1024 * 1024:
                    display_size = f"{size/1024/1024:.2f} MB"
                elif size >= 1024:
                    display_size = f"{size/1024:.2f} KB"
                else:
                    display_size = f"{size} B"
                self.table.setItem(row, 4, 
                    SortableTableWidgetItem(display_size, size))
            except ValueError:
                self.table.setItem(row, 4, 
                    SortableTableWidgetItem(flow[4], 0))
            
            # 计数列
            for col in [5, 6]:
                if col < len(flow):
                    self.table.setItem(row, col, 
                        SortableTableWidgetItem(flow[col], int(flow[col])))
                else:
                    self.table.setItem(row, col, 
                        SortableTableWidgetItem('0', 0))
        
        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()
        
        # 更新统计信息
        total_flows = len(summary)
        tcp_flows = sum(1 for flow in summary if flow[0] == 'TCP')
        udp_flows = sum(1 for flow in summary if flow[0] == 'UDP')
        total_bytes = sum(int(flow[4]) for flow in summary)
        
        # 计算百分比
        tcp_percent = (tcp_flows / total_flows * 100) if total_flows > 0 else 0
        udp_percent = (udp_flows / total_flows * 100) if total_flows > 0 else 0
        
        stats = (f'统计信息：\n'
                f'总流量数: {total_flows:,}\n'
                f'TCP流量: {tcp_flows:,} ({tcp_percent:.1f}%)\n'
                f'UDP流量: {udp_flows:,} ({udp_percent:.1f}%)\n'
                f'总流量: {self.format_size(total_bytes)} ({total_bytes:,} bytes)')
        self.stats_label.setText(stats)

    def filter_results(self):
        """过滤搜索结果"""
        search_text = self.search_input.text().lower()
        if not search_text:
            self.update_table(self.summary)
            return
            
        filtered_summary = [
            flow for flow in self.summary 
            if any(search_text in str(item).lower() for item in flow)
        ]
        self.update_table(filtered_summary)

    def analyze_pcap(self, pcap_file):
        """分析pcap文件并显示结果"""
        self.flows = self.read_pcap(pcap_file)
        if self.flows:
            self.summary = self.summarize_packets(self.flows)
            self.update_table(self.summary)