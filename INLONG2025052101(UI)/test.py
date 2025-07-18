# # # import sys
# # # import ctypes
# # # import winreg
# # # import subprocess
# # # import time
# # # from PyQt5.QtWidgets import (
# # #     QApplication, QMainWindow, QWidget, QVBoxLayout, QGroupBox, QRadioButton,
# # #     QPushButton, QLabel, QMessageBox, QHBoxLayout, QSizePolicy
# # # )
# # # from PyQt5.QtCore import Qt
# # # from PyQt5.QtGui import QFont, QIcon
# # #
# # #
# # # class DpiScalingApp(QMainWindow):
# # #     def __init__(self):
# # #         super().__init__()
# # #
# # #         # 检查管理员权限
# # #         if not self.is_admin():
# # #             self.request_admin()
# # #
# # #         # 初始化UI
# # #         self.init_ui()
# # #
# # #         # 获取当前缩放比例
# # #         self.current_scaling = self.get_current_scaling()
# # #         self.update_current_label()
# # #
# # #         # 设置窗口属性
# # #         self.setWindowTitle("Windows 10 屏幕缩放设置工具")
# # #         self.setWindowIcon(QIcon(self.get_icon()))
# # #         self.setMinimumSize(500, 400)
# # #
# # #     def get_icon(self):
# # #         # 创建简单的应用程序图标
# # #         return QIcon(":/icons/app_icon.png")
# # #
# # #     def is_admin(self):
# # #         """检查是否以管理员身份运行"""
# # #         try:
# # #             return ctypes.windll.shell32.IsUserAnAdmin()
# # #         except:
# # #             return False
# # #
# # #     def request_admin(self):
# # #         """请求管理员权限"""
# # #         ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
# # #         sys.exit(0)
# # #
# # #     def get_current_scaling(self):
# # #         """获取当前系统缩放比例"""
# # #         try:
# # #             # 获取屏幕DC
# # #             hdc = ctypes.windll.user32.GetDC(0)
# # #             # 获取每英寸点数 (DPI)
# # #             dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # 88 = LOGPIXELSX
# # #             # 释放DC
# # #             ctypes.windll.user32.ReleaseDC(0, hdc)
# # #
# # #             # 计算缩放比例 (100% = 96 DPI)
# # #             scaling = round(dpi / 96 * 100)
# # #             return min(max(scaling, 100), 500)  # 限制在100%-500%之间
# # #         except:
# # #             return 100
# # #
# # #     def set_scaling(self, scale_percent):
# # #         """设置系统缩放比例并立即生效"""
# # #         try:
# # #             # 转换为注册表值 (100% = 1, 125% = 2, 150% = 3, 175% = 4, 200% = 5)
# # #             scale_map = {
# # #                 100: 1,
# # #                 125: 2,
# # #                 150: 3,
# # #                 175: 4,
# # #                 200: 5
# # #             }
# # #
# # #             if scale_percent in scale_map:
# # #                 scale_value = scale_map[scale_percent]
# # #             else:
# # #                 # 对于非标准缩放比例，使用自定义DPI
# # #                 scale_value = 0
# # #                 dpi_value = int(96 * (scale_percent / 100))
# # #
# # #                 # 设置自定义DPI
# # #                 key = winreg.OpenKey(
# # #                     winreg.HKEY_CURRENT_USER,
# # #                     "Control Panel\\Desktop",
# # #                     0,
# # #                     winreg.KEY_WRITE
# # #                 )
# # #                 winreg.SetValueEx(key, "LogPixels", 0, winreg.REG_DWORD, dpi_value)
# # #                 winreg.CloseKey(key)
# # #
# # #             # 设置缩放比例
# # #             key = winreg.OpenKey(
# # #                 winreg.HKEY_CURRENT_USER,
# # #                 "Control Panel\\Desktop",
# # #                 0,
# # #                 winreg.KEY_WRITE
# # #             )
# # #
# # #             # 设置DPI缩放值
# # #             winreg.SetValueEx(key, "Win8DpiScaling", 0, winreg.REG_DWORD, 1)
# # #             winreg.SetValueEx(key, "LogPixels", 0, winreg.REG_DWORD, int(96 * (scale_percent / 100)))
# # #             winreg.CloseKey(key)
# # #
# # #             # 设置PerMonitorSettings
# # #             try:
# # #                 key = winreg.OpenKey(
# # #                     winreg.HKEY_CURRENT_USER,
# # #                     "Control Panel\\Desktop\\PerMonitorSettings",
# # #                     0,
# # #                     winreg.KEY_WRITE
# # #                 )
# # #
# # #                 # 获取所有显示器设置
# # #                 monitor_count = 0
# # #                 try:
# # #                     while True:
# # #                         monitor_name = winreg.EnumKey(key, monitor_count)
# # #                         monitor_count += 1
# # #                         monitor_key = winreg.OpenKey(key, monitor_name, 0, winreg.KEY_WRITE)
# # #
# # #                         # 设置缩放比例
# # #                         winreg.SetValueEx(monitor_key, "DpiValue", 0, winreg.REG_DWORD, scale_value)
# # #                         winreg.SetValueEx(monitor_key, "EffectiveDpi", 0, winreg.REG_DWORD,
# # #                                           int(96 * (scale_percent / 100)))
# # #
# # #                         winreg.CloseKey(monitor_key)
# # #                 except OSError:
# # #                     pass  # 没有更多显示器
# # #
# # #                 winreg.CloseKey(key)
# # #             except:
# # #                 pass
# # #
# # #             # 通知系统设置已更改
# # #             ctypes.windll.user32.SystemParametersInfoW(0x001A, 0, None, 0)  # SPI_SETNONCLIENTMETRICS
# # #             ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001E, 0, 0, 0, 1000, None)  # WM_SETTINGCHANGE
# # #
# # #             # 重启Explorer进程以实现立即生效
# # #             self.restart_explorer()
# # #
# # #             return True
# # #         except Exception as e:
# # #             QMessageBox.critical(self, "错误", f"设置失败: {str(e)}")
# # #             return False
# # #
# # #     def restart_explorer(self):
# # #         """重启Windows Explorer进程以实现立即生效"""
# # #         try:
# # #             # 终止Explorer进程
# # #             subprocess.call("taskkill /f /im explorer.exe", shell=True)
# # #             time.sleep(1)  # 等待进程完全终止
# # #
# # #             # 重新启动Explorer
# # #             subprocess.Popen("explorer.exe", shell=True)
# # #             time.sleep(1)  # 给Explorer启动时间
# # #         except Exception as e:
# # #             print(f"重启Explorer时出错: {str(e)}")
# # #
# # #     def apply_scaling(self):
# # #         """应用用户选择的缩放比例"""
# # #         scale_percent = int(self.sender().property("scale_percent"))
# # #
# # #         if scale_percent == self.current_scaling:
# # #             QMessageBox.information(self, "提示", "缩放比例未改变")
# # #             return
# # #
# # #         # 确认对话框
# # #         reply = QMessageBox.question(
# # #             self,
# # #             "确认设置",
# # #             f"确定要将缩放比例设置为 {scale_percent}% 吗？\n\n"
# # #             "桌面将短暂闪烁（资源管理器重启）",
# # #             QMessageBox.Yes | QMessageBox.No
# # #         )
# # #
# # #         if reply == QMessageBox.No:
# # #             return
# # #
# # #         if self.set_scaling(scale_percent):
# # #             QMessageBox.information(
# # #                 self,
# # #                 "成功",
# # #                 f"已成功设置缩放比例为 {scale_percent}%\n\n"
# # #                 "缩放设置已立即生效！"
# # #             )
# # #             self.current_scaling = scale_percent
# # #             self.update_current_label()
# # #
# # #     def init_ui(self):
# # #         """初始化用户界面"""
# # #         # 创建中央部件
# # #         central_widget = QWidget()
# # #         self.setCentralWidget(central_widget)
# # #
# # #         # 主布局
# # #         main_layout = QVBoxLayout(central_widget)
# # #         main_layout.setSpacing(20)
# # #         main_layout.setContentsMargins(30, 30, 30, 30)
# # #
# # #         # 标题
# # #         title_label = QLabel("Windows 10 屏幕缩放设置工具")
# # #         title_font = QFont("Segoe UI", 16, QFont.Bold)
# # #         title_label.setFont(title_font)
# # #         title_label.setAlignment(Qt.AlignCenter)
# # #         title_label.setStyleSheet("color: #2c3e50;")
# # #         main_layout.addWidget(title_label)
# # #
# # #         # 当前设置
# # #         self.current_label = QLabel()
# # #         self.current_label.setAlignment(Qt.AlignCenter)
# # #         self.current_label.setStyleSheet("font-size: 14px; color: #3498db; font-weight: bold;")
# # #         main_layout.addWidget(self.current_label)
# # #
# # #         # 分隔线
# # #         separator = QLabel()
# # #         separator.setFrameShape(QLabel.HLine)
# # #         separator.setStyleSheet("background-color: #bdc3c7;")
# # #         main_layout.addWidget(separator)
# # #
# # #         # 缩放选项组
# # #         scale_group = QGroupBox("选择缩放比例")
# # #         scale_group.setStyleSheet("""
# # #             QGroupBox {
# # #                 font-size: 14px;
# # #                 font-weight: bold;
# # #                 border: 1px solid #bdc3c7;
# # #                 border-radius: 5px;
# # #                 margin-top: 10px;
# # #             }
# # #             QGroupBox::title {
# # #                 subcontrol-origin: margin;
# # #                 left: 10px;
# # #                 padding: 0 5px;
# # #             }
# # #         """)
# # #
# # #         scale_layout = QVBoxLayout(scale_group)
# # #         scale_layout.setSpacing(15)
# # #
# # #         # 缩放选项
# # #         scales = [100, 125, 150, 175, 200]
# # #         self.scale_buttons = []
# # #
# # #         for scale in scales:
# # #             btn = QPushButton(f"{scale}%")
# # #             btn.setProperty("scale_percent", scale)
# # #             btn.setFixedHeight(40)
# # #             btn.setStyleSheet("""
# # #                 QPushButton {
# # #                     font-size: 14px;
# # #                     font-weight: bold;
# # #                     background-color: #ecf0f1;
# # #                     border: 1px solid #bdc3c7;
# # #                     border-radius: 5px;
# # #                     padding: 5px;
# # #                 }
# # #                 QPushButton:hover {
# # #                     background-color: #d6dbdf;
# # #                 }
# # #                 QPushButton:pressed {
# # #                     background-color: #bdc3c7;
# # #                 }
# # #             """)
# # #             btn.clicked.connect(self.apply_scaling)
# # #             scale_layout.addWidget(btn)
# # #             self.scale_buttons.append(btn)
# # #
# # #         main_layout.addWidget(scale_group)
# # #
# # #         # 信息提示
# # #         info_label = QLabel(
# # #             "注意：\n"
# # #             "• 此工具需要管理员权限运行\n"
# # #             "• 设置后会立即生效，无需注销或重启\n"
# # #             "• 某些应用程序可能需要重新启动才能适应新的缩放比例\n"
# # #             "• 更改时桌面会短暂闪烁（资源管理器重启）"
# # #         )
# # #         info_label.setStyleSheet("""
# # #             font-size: 12px;
# # #             color: #7f8c8d;
# # #             background-color: #f9f9f9;
# # #             border-left: 3px solid #3498db;
# # #             padding: 10px;
# # #         """)
# # #         info_label.setWordWrap(True)
# # #         main_layout.addWidget(info_label)
# # #
# # #         # 底部状态栏
# # #         status_bar = QWidget()
# # #         status_layout = QHBoxLayout(status_bar)
# # #         status_layout.setContentsMargins(0, 0, 0, 0)
# # #
# # #         author_label = QLabel("© 2023 Windows 系统工具")
# # #         author_label.setStyleSheet("font-size: 11px; color: #7f8c8d;")
# # #
# # #         admin_label = QLabel()
# # #         admin_label.setAlignment(Qt.AlignRight)
# # #         admin_label.setStyleSheet("font-size: 11px;")
# # #
# # #         if self.is_admin():
# # #             admin_label.setText("管理员权限 ✓")
# # #             admin_label.setStyleSheet("font-size: 11px; color: #27ae60; font-weight: bold;")
# # #         else:
# # #             admin_label.setText("需要管理员权限")
# # #             admin_label.setStyleSheet("font-size: 11px; color: #e74c3c; font-weight: bold;")
# # #
# # #         status_layout.addWidget(author_label)
# # #         status_layout.addStretch()
# # #         status_layout.addWidget(admin_label)
# # #
# # #         main_layout.addWidget(status_bar)
# # #
# # #     def update_current_label(self):
# # #         """更新当前缩放比例标签"""
# # #         self.current_label.setText(f"当前缩放比例: {self.current_scaling}%")
# # #
# # #         # 高亮当前选中的比例按钮
# # #         for btn in self.scale_buttons:
# # #             scale = btn.property("scale_percent")
# # #             if scale == self.current_scaling:
# # #                 btn.setStyleSheet("""
# # #                     QPushButton {
# # #                         font-size: 14px;
# # #                         font-weight: bold;
# # #                         background-color: #3498db;
# # #                         color: white;
# # #                         border: 1px solid #2980b9;
# # #                         border-radius: 5px;
# # #                         padding: 5px;
# # #                     }
# # #                     QPushButton:hover {
# # #                         background-color: #2980b9;
# # #                     }
# # #                     QPushButton:pressed {
# # #                         background-color: #1c6ea4;
# # #                     }
# # #                 """)
# # #             else:
# # #                 btn.setStyleSheet("""
# # #                     QPushButton {
# # #                         font-size: 14px;
# # #                         font-weight: bold;
# # #                         background-color: #ecf0f1;
# # #                         border: 1px solid #bdc3c7;
# # #                         border-radius: 5px;
# # #                         padding: 5px;
# # #                     }
# # #                     QPushButton:hover {
# # #                         background-color: #d6dbdf;
# # #                     }
# # #                     QPushButton:pressed {
# # #                         background-color: #bdc3c7;
# # #                     }
# # #                 """)
# # #
# # #
# # # if __name__ == "__main__":
# # #     # 启用高DPI缩放
# # #     if hasattr(Qt, 'AA_EnableHighDpiScaling'):
# # #         QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
# # #     if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
# # #         QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
# # #
# # #     app = QApplication(sys.argv)
# # #     app.setStyle("Fusion")  # 使用Fusion样式
# # #
# # #     # 检查管理员权限
# # #     if ctypes.windll.shell32.IsUserAnAdmin() == 0:
# # #         # 请求管理员权限
# # #         ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
# # #         sys.exit()
# # #
# # #     window = DpiScalingApp()
# # #     window.show()
# #
# #
# # import os
# # import sys
# # from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton,
# #                              QVBoxLayout, QWidget, QMessageBox)
# # from PyQt5.QtCore import QSettings
# #
# #
# # class DPIWindow(QMainWindow):
# #     def __init__(self):
# #         super().__init__()
# #         self.settings = QSettings("MyCompany", "DPISettings")
# #
# #         # 获取当前缩放值（默认1.0=100%）
# #         self.current_scale = float(self.settings.value("DPI_Scale", 1.0))
# #
# #         self.initUI()
# #         self.update_title()
# #
# #     def initUI(self):
# #         central_widget = QWidget()
# #         layout = QVBoxLayout()
# #
# #         self.scale_btn = QPushButton(f"切换缩放到125% (当前: {int(self.current_scale * 100)}%)")
# #         self.scale_btn.clicked.connect(self.change_scale)
# #
# #         layout.addWidget(self.scale_btn)
# #         central_widget.setLayout(layout)
# #         self.setCentralWidget(central_widget)
# #
# #     def change_scale(self):
# #         new_scale = 1.25  # 目标缩放值
# #
# #         # 保存新设置
# #         self.settings.setValue("DPI_Scale", new_scale)
# #
# #         # 提示用户重启
# #         QMessageBox.information(
# #             self,
# #             "缩放设置已更改",
# #             "应用程序需要重启以使新的缩放设置(125%)生效",
# #             QMessageBox.Ok
# #         )
# #         QApplication.quit()
# #
# #     def update_title(self):
# #         self.setWindowTitle(f"DPI缩放示例 (当前缩放: {int(self.current_scale * 100)}%)")
# #
# #
# # def main():
# #     # 读取保存的缩放设置
# #     settings = QSettings("MyCompany", "DPISettings")
# #     scale_factor = float(settings.value("DPI_Scale", 1.0))
# #
# #     # 设置环境变量
# #     if scale_factor > 1:
# #         os.environ["QT_SCALE_FACTOR"] = str(scale_factor)
# #
# #     app = QApplication(sys.argv)
# #     window = DPIWindow()
# #     window.show()
# #     sys.exit(app.exec_())
# #
# #
# # if __name__ == "__main__":
#
# #
# # import sys
# # from PyQt5.QtWidgets import QApplication, QMainWindow, QListWidget, QVBoxLayout, QWidget
# # from PyQt5.QtSerialPort import QSerialPortInfo
# #
# #
# # class SerialPortScanner(QMainWindow):
# #     def __init__(self):
# #         super().__init__()
# #         self.setWindowTitle("USB串口设备扫描器")
# #         self.setGeometry(100, 100, 500, 400)
# #
# #         # 创建UI组件
# #         self.port_list = QListWidget()
# #
# #         # 设置布局
# #         layout = QVBoxLayout()
# #         layout.addWidget(self.port_list)
# #
# #         container = QWidget()
# #         container.setLayout(layout)
# #         self.setCentralWidget(container)
# #
# #         # 扫描可用串口
# #         self.scan_serial_ports()
# #
# #     def scan_serial_ports(self):
# #         """扫描并显示所有可用的USB串口设备"""
# #         self.port_list.clear()
# #
# #         # 获取所有可用串口
# #         ports = QSerialPortInfo.availablePorts()
# #
# #         if not ports:
# #             self.port_list.addItem("未检测到串口设备")
# #             return
# #
# #         for port_info in ports:
# #             # 筛选USB串口（通常有供应商和产品ID）
# #             if port_info.hasVendorIdentifier() and port_info.hasProductIdentifier():
# #                 # 获取详细信息
# #                 vid = port_info.vendorIdentifier()
# #                 pid = port_info.productIdentifier()
# #                 port_name = port_info.portName()
# #                 description = port_info.description()
# #                 manufacturer = port_info.manufacturer()
# #
# #                 # 显示在列表中
# #                 item_text = (
# #                     f"端口: {port_name}\n"
# #                     f"描述: {description}\n"
# #                     f"制造商: {manufacturer}\n"
# #                     f"VID: 0x{vid:04X}, PID: 0x{pid:04X}"
# #                 )
# #                 self.port_list.addItem(item_text)
# #
# #
# # if __name__ == "__main__":
# #     app = QApplication(sys.argv)
# #     window = SerialPortScanner()
# #     window.show()
# #     sys.exit(app.exec_())
#
# from PyQt5.QtWidgets import (
#     QGroupBox, QTreeView, QVBoxLayout, QAbstractItemView
# )
# from PyQt5.QtGui import QStandardItemModel, QStandardItem
# from PyQt5.QtCore import Qt, QModelIndex
#
#
# class TreeViewGroup(QGroupBox):
#     def __init__(self, groupbox, title=None, headers=None, parent=None):
#         """
#         在指定的 QGroupBox 上创建 QTreeView
#
#         参数:
#             groupbox (QGroupBox): 要放置树形视图的GroupBox容器
#             title (str): GroupBox标题(如果为空则使用原GroupBox标题)
#             headers (list): 列标题列表
#             parent (QWidget): 父组件
#         """
#         super().__init__(parent)
#
#         # 保存对原始GroupBox的引用
#         self.groupbox = groupbox
#
#         # 设置标题(如果提供了新标题)
#         if title:
#             self.groupbox.setTitle(title)
#
#         # 创建布局(如果原GroupBox没有布局)
#         if self.groupbox.layout() is None:
#             self.groupbox.setLayout(QVBoxLayout())
#             self.groupbox.layout().setContentsMargins(5, 15, 5, 5)
#
#         # 创建树形视图
#         self.tree_view = QTreeView()
#         self.tree_view.setSelectionBehavior(QAbstractItemView.SelectRows)
#         self.tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
#         self.tree_view.setAlternatingRowColors(True)
#
#         # 添加到GroupBox布局
#         self.groupbox.layout().addWidget(self.tree_view)
#
#         # 创建模型
#         self.model = QStandardItemModel()
#         self.tree_view.setModel(self.model)
#
#         # 设置列标题
#         if headers:
#             self.set_headers(headers)
#
#     def set_headers(self, headers):
#         """设置列标题"""
#         self.model.setHorizontalHeaderLabels(headers)
#
#     def add_top_level_item(self, text, data=None, icon=None):
#         """添加顶级项"""
#         item = QStandardItem(text)
#         if data:
#             item.setData(data, Qt.UserRole)
#         if icon:
#             item.setIcon(icon)
#         self.model.appendRow(item)
#         return item
#
#     def add_child_item(self, parent_item, text, data=None, icon=None):
#         """添加子项"""
#         if not parent_item:
#             return self.add_top_level_item(text, data, icon)
#
#         item = QStandardItem(text)
#         if data:
#             item.setData(data, Qt.UserRole)
#         if icon:
#             item.setIcon(icon)
#         parent_item.appendRow(item)
#         return item
#
#     def add_items(self, parent, items):
#         """
#         递归添加树形结构
#
#         参数:
#             parent: 父项(如果是顶级则设为None)
#             items: 项目列表，格式为:
#                    [text, data, [child1, child2, ...]] 或
#                    [text, data] 或
#                    text
#         """
#         if not items:
#             return
#
#         if not isinstance(items, (list, tuple)):
#             # 单个项目
#             item = QStandardItem(items)
#             if parent:
#                 parent.appendRow(item)
#             else:
#                 self.model.appendRow(item)
#             return
#
#         # 处理项目列表
#         for item_data in items:
#             if isinstance(item_data, (list, tuple)):
#                 text = item_data[0]
#                 data = item_data[1] if len(item_data) > 1 else None
#                 children = item_data[2] if len(item_data) > 2 else None
#             else:
#                 text = item_data
#                 data = None
#                 children = None
#
#             item = QStandardItem(text)
#             if data:
#                 item.setData(data, Qt.UserRole)
#
#             if parent:
#                 parent.appendRow(item)
#             else:
#                 self.model.appendRow(item)
#
#             # 递归添加子项
#             if children:
#                 self.add_items(item, children)
#
#     def clear(self):
#         """清空树"""
#         self.model.clear()
#
#     def expand_all(self):
#         """展开所有节点"""
#         self.tree_view.expandAll()
#
#     def collapse_all(self):
#         """折叠所有节点"""
#         self.tree_view.collapseAll()
#
#     def get_selected_item(self):
#         """获取当前选中的项"""
#         index = self.tree_view.currentIndex()
#         if index.isValid():
#             return self.model.itemFromIndex(index)
#         return None
#
#     def set_column_width(self, column, width):
#         """设置列宽"""
#         self.tree_view.setColumnWidth(column, width)
#
#     def set_header_hidden(self, hidden=True):
#         """设置是否隐藏表头"""
#         self.tree_view.header().setHidden(hidden)
#
#     def set_selection_mode(self, mode):
#         """设置选择模式"""
#         self.tree_view.setSelectionMode(mode)
#
#
# # 使用示例
# if __name__ == "__main__":
#     import sys
#     from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QGroupBox
#     from PyQt5.QtGui import QIcon
#
#
#     class MainWindow(QMainWindow):
#         def __init__(self):
#             super().__init__()
#             self.setWindowTitle("TreeView in GroupBox Demo")
#             self.setGeometry(300, 300, 600, 400)
#
#             # 创建主控件和布局
#             central_widget = QWidget()
#             self.setCentralWidget(central_widget)
#             main_layout = QHBoxLayout(central_widget)
#
#             # 创建左侧分组框
#             left_group = QGroupBox("设备列表")
#             main_layout.addWidget(left_group, 1)
#
#             # 创建右侧分组框
#             right_group = QGroupBox("用户列表")
#             main_layout.addWidget(right_group, 1)
#
#             # 在左侧分组框上创建树视图
#             device_tree = TreeViewGroup(
#                 groupbox=left_group,
#                 headers=["设备名称", "状态"]
#             )
#
#             # 在右侧分组框上创建树视图
#             user_tree = TreeViewGroup(
#                 groupbox=right_group,
#                 title="用户管理",
#                 headers=["用户名", "角色"]
#             )
#
#             # 添加设备数据(使用add_items方法)
#             devices = [
#                 ["服务器", "server-group", [
#                     ["Web服务器", "web-server", [
#                         ["Nginx", "nginx"],
#                         ["Apache", "apache"]
#                     ]],
#                     ["数据库服务器", "db-server", [
#                         ["MySQL", "mysql"],
#                         ["PostgreSQL", "postgres"]
#                     ]]
#                 ]],
#                 ["工作站", "workstation", [
#                     ["工程师工作站", "engineer"],
#                     ["设计师工作站", "designer"]
#                 ]]
#             ]
#             device_tree.add_items(None, devices)
#
#             # 添加用户数据(使用单独添加方法)
#             users = user_tree.add_top_level_item("管理员")
#             user_tree.add_child_item(users, "admin", "超级管理员")
#             user_tree.add_child_item(users, "sysadmin", "系统管理员")
#
#             editors = user_tree.add_top_level_item("编辑")
#             user_tree.add_child_item(editors, "editor1", "内容编辑")
#             user_tree.add_child_item(editors, "editor2", "图片编辑")
#
#             viewers = user_tree.add_top_level_item("查看者")
#             user_tree.add_child_item(viewers, "viewer1", "只读访问")
#
#             # 设置列宽
#             device_tree.set_column_width(0, 200)
#             user_tree.set_column_width(0, 150)
#
#             # 展开所有节点
#             device_tree.expand_all()
#             user_tree.expand_all()
#
#             self.show()
#
#
#     app = QApplication(sys.argv)
#     window = MainWindow()
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTreeView, QFileSystemModel, QWidget,
    QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QFont


class TreeViewExample(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QTreeView选中节点颜色解决方案")
        self.setGeometry(300, 300, 800, 500)

        # 创建主控件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 标题
        title_label = QLabel("QTreeView选中节点颜色一致性解决方案")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; padding: 10px;")
        main_layout.addWidget(title_label)

        # 说明文本
        description = QLabel(
            "本示例展示了如何使QTreeView的选中节点在获得焦点和失去焦点时保持相同颜色。\n"
            "默认行为：失去焦点时选中节点变为灰色。解决方案：使用样式表统一两种状态的颜色。"
        )
        description.setFont(QFont("Arial", 10))
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("color: #7f8c8d; background: #f8f9fa; padding: 15px; border-radius: 8px;")
        main_layout.addWidget(description)

        # 创建树视图和按钮的容器
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(20)

        # 左侧树视图
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(0, 0, 0, 0)

        tree_label = QLabel("文件系统树视图")
        tree_label.setFont(QFont("Arial", 10, QFont.Bold))
        tree_layout.addWidget(tree_label)

        self.tree_view = QTreeView()
        self.tree_view.setFont(QFont("Arial", 10))
        self.tree_view.setSelectionMode(QTreeView.SingleSelection)
        self.tree_view.setAnimated(True)

        # 设置文件系统模型
        model = QFileSystemModel()
        model.setRootPath(QDir.rootPath())
        self.tree_view.setModel(model)
        self.tree_view.setRootIndex(model.index(QDir.rootPath()))

        # 设置样式表：统一选中状态颜色
        self.tree_view.setStyleSheet("""
            QTreeView {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 5px;
                outline: 0;
            }
            QTreeView::item {
                height: 28px;
                padding: 5px;
                border: none;
            }
            QTreeView::item:selected:active,
            QTreeView::item:selected:!active {
                background: #3498db;
                color: white;
                border: none;
            }
            QTreeView::item:hover {
                background: #d6eaf8;
                color: #2c3e50;
            }
            QTreeView::branch:has-siblings:!adjoins-item,
            QTreeView::branch:has-siblings:adjoins-item,
            QTreeView::branch:!has-children:!has-siblings:adjoins-item,
            QTreeView::branch:closed:has-children:has-siblings,
            QTreeView::branch:open:has-children:has-siblings {
                background: none;
            }
        """)

        tree_layout.addWidget(self.tree_view)
        content_layout.addWidget(tree_container, 2)  # 占2份空间

        # 右侧控制面板
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(20, 20, 20, 20)
        control_layout.setSpacing(15)

        panel_label = QLabel("控制面板")
        panel_label.setFont(QFont("Arial", 10, QFont.Bold))
        panel_label.setAlignment(Qt.AlignCenter)
        control_layout.addWidget(panel_label)

        # 添加说明框
        explanation = QLabel(
            "<b>解决方案说明：</b><br>"
            "使用样式表同时设置两个伪状态：<br>"
            "<code>QTreeView::item:selected:active</code> 和<br>"
            "<code>QTreeView::item:selected:!active</code><br><br>"
            "这样无论视图是否获得焦点，<br>"
            "选中节点都将显示为相同的颜色。"
        )
        explanation.setFont(QFont("Arial", 9))
        explanation.setStyleSheet("background: #ecf0f1; padding: 15px; border-radius: 8px;")
        explanation.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        control_layout.addWidget(explanation)

        # 添加焦点切换按钮
        focus_btn = QPushButton("切换焦点")
        focus_btn.setFont(QFont("Arial", 10))
        focus_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        focus_btn.clicked.connect(self.toggle_focus)
        control_layout.addWidget(focus_btn)

        # 添加状态指示器
        self.status_label = QLabel("当前状态：视图获得焦点")
        self.status_label.setFont(QFont("Arial", 9))
        self.status_label.setStyleSheet("color: #27ae60; padding: 10px 0;")
        control_layout.addWidget(self.status_label)

        # 添加颜色说明
        colors_label = QLabel(
            "<b>颜色说明：</b><br>"
            "• 选中节点：<span style='background:#3498db; color:white;'>&nbsp;蓝色&nbsp;</span><br>"
            "• 悬停节点：<span style='background:#d6eaf8;'>&nbsp;浅蓝色&nbsp;</span><br>"
            "• 普通节点：白色背景"
        )
        colors_label.setFont(QFont("Arial", 9))
        colors_label.setStyleSheet("padding: 15px 0;")
        control_layout.addWidget(colors_label)

        control_layout.addStretch(1)
        content_layout.addWidget(control_panel, 1)  # 占1份空间

        main_layout.addWidget(content_widget)

        # 底部信息
        footer = QLabel("PyQt5 QTreeView样式表示例 | 解决方案：统一选中状态颜色")
        footer.setFont(QFont("Arial", 8))
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #7f8c8d; padding: 10px;")
        main_layout.addWidget(footer)

    def toggle_focus(self):
        if self.tree_view.hasFocus():
            self.tree_view.clearFocus()
            self.status_label.setText("当前状态：视图失去焦点")
            self.status_label.setStyleSheet("color: #e74c3c; padding: 10px 0;")
        else:
            self.tree_view.setFocus()
            self.status_label.setText("当前状态：视图获得焦点")
            self.status_label.setStyleSheet("color: #27ae60; padding: 10px 0;")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # 使用Fusion样式以获得更好的跨平台体验

    # 设置应用程序样式
    app.setStyleSheet("""
        QMainWindow {
            background-color: #ecf0f1;
        }
    """)

    window = TreeViewExample()
    window.show()
    sys.exit(app.exec_())