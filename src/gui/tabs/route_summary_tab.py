from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                           QTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
                           QHeaderView, QLabel, QRadioButton, QButtonGroup,
                           QProgressBar, QMessageBox)
from netaddr import IPRange, IPNetwork, IPAddress, cidr_merge
from ...utils.text_utils import TextUtils
from ...utils.async_utils import AsyncTaskManager
from ...utils.logger import logger
from PyQt6.QtCore import Qt
class RouteSummaryTab(QWidget):
    def __init__(self):
        super().__init__()
        # 创建异步任务管理器
        self.task_manager = AsyncTaskManager()
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
        # self.exact_mode.setChecked(True)

        # 移除选项卡切换时的自动汇总
        # self.exact_mode.toggled.connect(self.summarize_routes)
        # self.inexact_mode.toggled.connect(self.summarize_routes)

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

        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 设置为不确定模式
        self.progress_bar.setVisible(False)
        result_layout.addWidget(self.progress_bar)

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
        # 检查IP范围大小
        total_ips = self.count_total_ips(networks)

        # 如果IP数量超过100万，显示警告
        if total_ips > 1000000:
            reply = QMessageBox.warning(
                self,
                "大范围警告",
                f"您输入的IP范围包含超过 {total_ips:,} 个IP地址，处理可能需要较长时间。\n\n"
                f"建议使用非精确汇总模式处理大范围IP。\n\n"
                f"是否继续?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # 显示进度条
        self.progress_bar.setVisible(True)
        self.stats_label.setText("正在处理...")

        # 启动异步任务
        self.task_manager.run_task(
            "exact_summary",
            self.perform_exact_summary_task,
            self.handle_summary_result,
            networks
        )

    def count_total_ips(self, networks):
        """计算网络列表中的总IP数量"""
        total = 0
        for net in networks:
            if isinstance(net, IPRange):
                total += net.last - net.first + 1
            else:
                total += net.size
        return total

    def perform_exact_summary_task(self, networks):
        """在后台线程中执行精确汇总任务"""
        logger.info(f"开始精确汇总，网络数量: {len(networks)}")

        # 优化的精确汇总算法
        original_inputs = []
        ip_networks = []
        total_original_ips = 0

        # 第一步：将所有网络转换为CIDR块
        for net in networks:
            if isinstance(net, IPRange):
                # 计算IP数量
                ip_count = net.last - net.first + 1
                total_original_ips += ip_count
                range_str = f"{IPAddress(net.first)}-{IPAddress(net.last)}"
                original_inputs.append(range_str)

                # 使用cidr_merge直接将IPRange转换为最优CIDR块集合
                # 这比逐个IP转换效率高得多
                cidrs = net.cidrs()
                ip_networks.extend(cidrs)

            else:  # 已经是IPNetwork
                total_original_ips += net.size
                original_inputs.append(str(net))
                ip_networks.append(net)

        # 第二步：合并CIDR块
        summarized = cidr_merge(ip_networks)
        logger.info(f"精确汇总完成，原始IP数量: {total_original_ips}，汇总后条目数: {len(summarized)}")

        # 返回结果
        return {
            "summarized": summarized,
            "total_original_ips": total_original_ips,
            "original_inputs": original_inputs
        }

    def handle_summary_result(self, result, error):
        """处理汇总结果"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)

        if error:
            self.show_error(f"汇总错误: {error}")
            return

        try:
            # 获取结果数据
            summarized = result["summarized"]
            total_original_ips = result["total_original_ips"]

            # 检查是否是非精确汇总的结果
            is_inexact = "extra_ips" in result

            # 更新统计信息
            if is_inexact:
                total_summarized_ips = result["total_summarized_ips"]
                extra_ips = result["extra_ips"]
                extra_percent = (extra_ips / total_original_ips * 100) if total_original_ips > 0 else 0

                self.stats_label.setText(
                    f"原始IP数量: {total_original_ips:,} | "
                    f"汇总后IP数量: {total_summarized_ips:,} | "
                    f"额外包含IP数量: {extra_ips:,} ({extra_percent:.2f}%) | "
                    f"汇总后路由条目数: {len(summarized)}"
                )
            else:
                self.stats_label.setText(
                    f"原始IP数量: {total_original_ips:,} | "
                    f"汇总后路由条目数: {len(summarized)}"
                )

            # 更新结果表格
            self.result_table.setRowCount(len(summarized))
            for i, network in enumerate(summarized):
                summary_item = QTableWidgetItem(str(network))
                self.result_table.setItem(i, 0, summary_item)

                # 信息显示
                if is_inexact and len(summarized) == 1:
                    # 非精确汇总且只有一个结果时，显示额外包含的IP信息
                    extra_percent = (extra_ips / total_original_ips * 100) if total_original_ips > 0 else 0
                    info = (f"包含 {network.size:,} 个IP地址 "
                           f"(额外包含 {extra_ips:,} 个IP，{extra_percent:.2f}%)")
                else:
                    # 精确汇总或多个结果时，只显示包含的IP数量
                    info = f"包含 {network.size:,} 个IP地址"
                    if network.size == 1:
                        info = "单个IP地址"

                details_item = QTableWidgetItem(info)
                self.result_table.setItem(i, 1, details_item)

        except Exception as e:
            import traceback
            logger.error(f"处理汇总结果错误: {traceback.format_exc()}")
            self.show_error(f"处理结果错误: {str(e)}")

    def perform_inexact_summary(self, networks):
        """执行非精确汇总"""
        try:
            # 显示进度条
            self.progress_bar.setVisible(True)
            self.stats_label.setText("正在处理...")

            # 启动异步任务
            self.task_manager.run_task(
                "inexact_summary",
                self.perform_inexact_summary_task,
                self.handle_summary_result,
                networks
            )
        except Exception as e:
            logger.error(f"非精确汇总错误: {str(e)}")
            self.progress_bar.setVisible(False)
            self.show_error(f"汇总错误: {str(e)}")

    def perform_inexact_summary_task(self, networks):
        """在后台线程中执行非精确汇总任务"""
        logger.info(f"开始非精确汇总，网络数量: {len(networks)}")

        # 计算总IP数和找出最小/最大IP地址
        total_original_ips = 0
        min_ip = None
        max_ip = None

        # 首先，将所有网络转换为整数范围
        for net in networks:
            if isinstance(net, IPRange):
                total_original_ips += net.last - net.first + 1
                if min_ip is None or net.first < min_ip:
                    min_ip = net.first
                if max_ip is None or net.last > max_ip:
                    max_ip = net.last
            else:  # IPNetwork
                total_original_ips += net.size
                net_first = int(net.network)
                net_last = int(net.broadcast)
                if min_ip is None or net_first < min_ip:
                    min_ip = net_first
                if max_ip is None or net_last > max_ip:
                    max_ip = net_last

        # 强制使用单一CIDR块进行非精确汇总
        # 计算需要的前缀长度
        range_size = max_ip - min_ip + 1
        prefix_length = 32
        while (1 << (32 - prefix_length)) < range_size:
            prefix_length -= 1
            if prefix_length <= 0:
                prefix_length = 0
                break

        # 创建包含整个范围的CIDR块
        # 需要找到正确的网络地址（向下对齐到CIDR边界）
        network_address = min_ip & (0xFFFFFFFF << (32 - prefix_length))
        single_cidr = IPNetwork(f"{IPAddress(network_address)}/{prefix_length}")

        # 确保这个CIDR块确实包含了整个范围
        if int(single_cidr.network) <= min_ip and int(single_cidr.broadcast) >= max_ip:
            summarized = [single_cidr]
        else:
            # 如果计算出的CIDR块不包含整个范围，减小前缀长度
            while prefix_length > 0:
                prefix_length -= 1
                network_address = min_ip & (0xFFFFFFFF << (32 - prefix_length))
                single_cidr = IPNetwork(f"{IPAddress(network_address)}/{prefix_length}")
                if int(single_cidr.network) <= min_ip and int(single_cidr.broadcast) >= max_ip:
                    summarized = [single_cidr]
                    break

            # 如果仍然无法找到单一CIDR块，使用0.0.0.0/0
            if prefix_length <= 0:
                summarized = [IPNetwork("0.0.0.0/0")]

        # 计算额外包含的IP数量
        total_summarized_ips = sum(net.size for net in summarized)
        extra_ips = total_summarized_ips - total_original_ips

        logger.info(f"非精确汇总完成，原始IP数量: {total_original_ips}，汇总后条目数: {len(summarized)}，额外包含IP数量: {extra_ips}")

        return {
            "summarized": summarized,
            "total_original_ips": total_original_ips,
            "total_summarized_ips": total_summarized_ips,
            "extra_ips": extra_ips
        }

    def summarize_routes(self):
        """根据选择的模执行路由汇总"""
        # 停止任何正在运行的任务
        self.task_manager.stop_all_tasks()
        self.progress_bar.setVisible(False)

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
                error_msg = "以下条目解析失败：\n" + "\n".join(
                    f"{entry}: {error}" for entry, error in failed_entries
                )
                self.show_error(error_msg)

        except Exception as e:
            logger.error(f"汇总路由错误: {str(e)}")
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
