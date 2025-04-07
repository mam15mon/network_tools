from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                           QTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
                           QHeaderView, QLabel, QRadioButton, QButtonGroup)
from netaddr import IPRange, IPNetwork, IPAddress, cidr_merge
from ...utils.text_utils import TextUtils
from PyQt6.QtCore import Qt
class RouteSummaryTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        
        # 创建汇总模式选择区域
        mode_group = QGroupBox("汇总模式")
        mode_layout = QHBoxLayout()
        
        self.mode_buttons = QButtonGroup(self)
        self.exact_mode = QRadioButton("精确汇总")
        self.inexact_mode = QRadioButton("非精确汇总")
        self.exact_mode.setChecked(True)
        
        self.exact_mode.toggled.connect(self.summarize_routes)
        self.inexact_mode.toggled.connect(self.summarize_routes)
        
        self.mode_buttons.addButton(self.exact_mode)
        self.mode_buttons.addButton(self.inexact_mode)
        
        mode_layout.addWidget(self.exact_mode)
        mode_layout.addWidget(self.inexact_mode)
        mode_layout.addStretch()
        self.summary_button = QPushButton("汇总")
        self.summary_button.setFixedWidth(80)  # 设置固定宽度
        self.summary_button.clicked.connect(self.summarize_routes)
        mode_layout.addWidget(self.summary_button)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # 创建输入区域
        input_group = QGroupBox("路由条目")
        input_layout = QVBoxLayout()
        
        self.route_input = QTextEdit()
        self.route_input.setPlaceholderText(TextUtils.ROUTE_SUMMARY_HELP)
        input_layout.addWidget(self.route_input)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 创建结果区域
        result_group = QGroupBox("汇总结果")
        result_layout = QVBoxLayout()
        
        self.stats_label = QLabel()
        result_layout.addWidget(self.stats_label)
        
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(2)
        self.result_table.setHorizontalHeaderLabels(["汇总网段", "其他信息"])
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.result_table.setColumnWidth(0, 60)
        
        # 设置选择模式和行为
        self.result_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.result_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        
        # 重写按键事件
        self.result_table.keyPressEvent = self.table_key_press_event
        
        result_layout.addWidget(self.result_table)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)

    def perform_exact_summary(self, networks):
        """执行精确汇总"""
        try:
            original_inputs = []
            ip_networks = []
            total_original_entries = len(networks)
            original_ip_map = {}
            ip32_to_original = {}

            for net in networks:
                if isinstance(net, IPRange):
                    range_str = f"{IPAddress(net.first)}-{IPAddress(net.last)}"
                    original_inputs.append(range_str)
                    
                    range_networks = []
                    for ip in range(net.first, net.last + 1):
                        ip_net = IPNetwork(f"{IPAddress(ip)}/32")
                        ip_networks.append(ip_net)
                        range_networks.append(ip_net)
                        ip32_to_original[str(ip_net)] = range_str
                    
                    original_ip_map[range_str] = range_networks
                else:
                    original_inputs.append(str(net))
                    ip_networks.append(net)
                    original_ip_map[str(net)] = [net]
            
            summarized = cidr_merge(ip_networks)
            
            # 更新统计信息
            self.stats_label.setText(
                f"原始路由条目数: {total_original_entries} | "
                f"汇总后路由条目数: {len(summarized)}"
            )
            
            # 更新结果表格
            self.result_table.setRowCount(len(summarized))
            for i, network in enumerate(summarized):
                summary_item = QTableWidgetItem(str(network))
                self.result_table.setItem(i, 0, summary_item)
                
                # 找出这个汇总网段包含的/32网段
                contained_networks = set()
                for ip_net in ip_networks:
                    if str(ip_net) in ip32_to_original and ip_net in network:
                        contained_networks.add(ip32_to_original[str(ip_net)])
                    elif ip_net in network:
                        contained_networks.add(str(ip_net))
                
                # 包含的原始网段列
                count_text = f"{len(contained_networks)} 个原始网段"
                details = "包含以下原始网段:\n" + "\n".join(
                    f"• {net}" for net in contained_networks
                )
                
                details_item = QTableWidgetItem(count_text)
                details_item.setToolTip(details)
                self.result_table.setItem(i, 1, details_item)
                
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            self.show_error(f"汇总错误: {str(e)}")

    def perform_inexact_summary(self, networks):
        """执行非精确汇总"""
        try:
            # 找到最小和最大IP地址
            min_ip = min(net.first if isinstance(net, IPRange) else net.first for net in networks)
            max_ip = max(net.last if isinstance(net, IPRange) else net.last for net in networks)
            
            # 计算掩码长度
            diff = max_ip ^ min_ip
            prefix_len = 32 - diff.bit_length()
            
            # 创建包含所有IP的最小网络
            summary_net = IPNetwork(f"{str(IPAddress(min_ip))}/{prefix_len}")
            
            # 计算原始IP集合
            original_ips = set()
            for net in networks:
                if isinstance(net, IPRange):
                    original_ips.update(range(net.first, net.last + 1))
                else:
                    original_ips.update(range(net.first, net.last + 1))
            
            # 计算汇总网段的所有IP
            summary_ips = set(range(summary_net.first, summary_net.last + 1))
            
            # 计算额外包含的IP
            extra_ips = summary_ips - original_ips
            
            # 将额外IP转换为范围
            extra_ranges = []
            if extra_ips:
                sorted_ips = sorted(extra_ips)
                start = sorted_ips[0]
                prev = start
                for curr in sorted_ips[1:] + [None]:
                    if curr is None or curr != prev + 1:
                        if start == prev:
                            extra_ranges.append(str(IPAddress(start)))
                        else:
                            extra_ranges.append(f"{IPAddress(start)}-{IPAddress(prev)}")
                        if curr is not None:
                            start = curr
                    prev = curr
            
            # 更新统计信息
            self.stats_label.setText(
                f"原始IP数量: {len(original_ips):,} | "
                f"汇总后IP数量: {len(summary_ips):,} | "
                f"额外包含IP数量: {len(extra_ips):,} "
                f"({(len(extra_ips)/len(summary_ips)*100):.2f}%)"
            )
            
            # 更新结果表格
            self.result_table.setRowCount(1)
            self.result_table.setItem(0, 0, QTableWidgetItem(str(summary_net)))
            
            # 添加额外包含的IP范围信息
            if extra_ranges:
                details = "额外包含以下IP范围:\n" + "\n".join(f"• {r}" for r in extra_ranges)
                count_text = f"{len(extra_ips)} 个额外IP"
            else:
                details = "无额外包含的IP"
                count_text = "无额外IP"
            
            details_item = QTableWidgetItem(count_text)
            details_item.setToolTip(details)
            self.result_table.setItem(0, 1, details_item)

        except Exception as e:
            print(f"非精确汇总出错: {str(e)}")
            import traceback
            print(traceback.format_exc())
            self.show_error(f"非精确汇总错误: {str(e)}")

    def summarize_routes(self):
        """根据选择的模执行路由汇总"""
        text = self.route_input.toPlainText()
        if not text.strip():
            self.clear_results()
            return
            
        try:
            # 使用TextUtils解析输入文本
            entries = TextUtils.split_text(text)
            networks = []
            failed_entries = []
            
            # 解析每个条目
            for entry in entries:
                try:
                    network = TextUtils.parse_ip_range(entry)
                    if network:
                        networks.append(network)
                except ValueError as e:
                    failed_entries.append((entry, str(e)))
            
            if not networks:
                raise ValueError("没有有效的路由条目")
                
            # 执行汇总
            if self.exact_mode.isChecked():
                self.perform_exact_summary(networks)
            else:
                self.perform_inexact_summary(networks)
                
            # 显示解析失败的条目
            if failed_entries:
                error_msg = "以下目解析失败：\n" + "\n".join(
                    f"{entry}: {error}" for entry, error in failed_entries
                )
                self.show_error(error_msg)
                
        except Exception as e:
            self.show_error(str(e))

    def clear_results(self):
        """清空结果显示"""
        self.stats_label.clear()
        self.result_table.setRowCount(0)

    def show_error(self, message):
        """显示错误信息"""
        self.stats_label.setText(f"错误: {message}")
        self.result_table.setRowCount(0)

    def copy_selected_cells(self):
        """复制选中的单元格内容"""
        selected_ranges = self.result_table.selectedRanges()
        if not selected_ranges:
            return

        text_lines = []
        for range_ in selected_ranges:
            for row in range(range_.topRow(), range_.bottomRow() + 1):
                row_texts = []
                for col in range(range_.leftColumn(), range_.rightColumn() + 1):
                    item = self.result_table.item(row, col)
                    if item is not None:
                        row_texts.append(item.text())
                    else:
                        row_texts.append('')
                text_lines.append('\t'.join(row_texts))
        
        # 将内容复制到剪贴板
        if text_lines:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText('\n'.join(text_lines))

    def table_key_press_event(self, event):
        """处理表格的按键事件"""
        if event.key() == Qt.Key.Key_C and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.copy_selected_cells()
        else:
            QTableWidget.keyPressEvent(self.result_table, event)
