# # # # # # # # # import sys
# # # # # # # # # import ctypes
# # # # # # # # # import winreg
# # # # # # # # # import subprocess
# # # # # # # # # import time
# # # # # # # # # from PyQt5.QtWidgets import (
# # # # # # # # #     QApplication, QMainWindow, QWidget, QVBoxLayout, QGroupBox, QRadioButton,
# # # # # # # # #     QPushButton, QLabel, QMessageBox, QHBoxLayout, QSizePolicy
# # # # # # # # # )
# # # # # # # # # from PyQt5.QtCore import Qt
# # # # # # # # # from PyQt5.QtGui import QFont, QIcon
# # # # # # # # #
# # # # # # # # #
# # # # # # # # # class DpiScalingApp(QMainWindow):
# # # # # # # # #     def __init__(self):
# # # # # # # # #         super().__init__()
# # # # # # # # #
# # # # # # # # #         # 检查管理员权限
# # # # # # # # #         if not self.is_admin():
# # # # # # # # #             self.request_admin()
# # # # # # # # #
# # # # # # # # #         # 初始化UI
# # # # # # # # #         self.init_ui()
# # # # # # # # #
# # # # # # # # #         # 获取当前缩放比例
# # # # # # # # #         self.current_scaling = self.get_current_scaling()
# # # # # # # # #         self.update_current_label()
# # # # # # # # #
# # # # # # # # #         # 设置窗口属性
# # # # # # # # #         self.setWindowTitle("Windows 10 屏幕缩放设置工具")
# # # # # # # # #         self.setWindowIcon(QIcon(self.get_icon()))
# # # # # # # # #         self.setMinimumSize(500, 400)
# # # # # # # # #
# # # # # # # # #     def get_icon(self):
# # # # # # # # #         # 创建简单的应用程序图标
# # # # # # # # #         return QIcon(":/icons/app_icon.png")
# # # # # # # # #
# # # # # # # # #     def is_admin(self):
# # # # # # # # #         """检查是否以管理员身份运行"""
# # # # # # # # #         try:
# # # # # # # # #             return ctypes.windll.shell32.IsUserAnAdmin()
# # # # # # # # #         except:
# # # # # # # # #             return False
# # # # # # # # #
# # # # # # # # #     def request_admin(self):
# # # # # # # # #         """请求管理员权限"""
# # # # # # # # #         ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
# # # # # # # # #         sys.exit(0)
# # # # # # # # #
# # # # # # # # #     def get_current_scaling(self):
# # # # # # # # #         """获取当前系统缩放比例"""
# # # # # # # # #         try:
# # # # # # # # #             # 获取屏幕DC
# # # # # # # # #             hdc = ctypes.windll.user32.GetDC(0)
# # # # # # # # #             # 获取每英寸点数 (DPI)
# # # # # # # # #             dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # 88 = LOGPIXELSX
# # # # # # # # #             # 释放DC
# # # # # # # # #             ctypes.windll.user32.ReleaseDC(0, hdc)
# # # # # # # # #
# # # # # # # # #             # 计算缩放比例 (100% = 96 DPI)
# # # # # # # # #             scaling = round(dpi / 96 * 100)
# # # # # # # # #             return min(max(scaling, 100), 500)  # 限制在100%-500%之间
# # # # # # # # #         except:
# # # # # # # # #             return 100
# # # # # # # # #
# # # # # # # # #     def set_scaling(self, scale_percent):
# # # # # # # # #         """设置系统缩放比例并立即生效"""
# # # # # # # # #         try:
# # # # # # # # #             # 转换为注册表值 (100% = 1, 125% = 2, 150% = 3, 175% = 4, 200% = 5)
# # # # # # # # #             scale_map = {
# # # # # # # # #                 100: 1,
# # # # # # # # #                 125: 2,
# # # # # # # # #                 150: 3,
# # # # # # # # #                 175: 4,
# # # # # # # # #                 200: 5
# # # # # # # # #             }
# # # # # # # # #
# # # # # # # # #             if scale_percent in scale_map:
# # # # # # # # #                 scale_value = scale_map[scale_percent]
# # # # # # # # #             else:
# # # # # # # # #                 # 对于非标准缩放比例，使用自定义DPI
# # # # # # # # #                 scale_value = 0
# # # # # # # # #                 dpi_value = int(96 * (scale_percent / 100))
# # # # # # # # #
# # # # # # # # #                 # 设置自定义DPI
# # # # # # # # #                 key = winreg.OpenKey(
# # # # # # # # #                     winreg.HKEY_CURRENT_USER,
# # # # # # # # #                     "Control Panel\\Desktop",
# # # # # # # # #                     0,
# # # # # # # # #                     winreg.KEY_WRITE
# # # # # # # # #                 )
# # # # # # # # #                 winreg.SetValueEx(key, "LogPixels", 0, winreg.REG_DWORD, dpi_value)
# # # # # # # # #                 winreg.CloseKey(key)
# # # # # # # # #
# # # # # # # # #             # 设置缩放比例
# # # # # # # # #             key = winreg.OpenKey(
# # # # # # # # #                 winreg.HKEY_CURRENT_USER,
# # # # # # # # #                 "Control Panel\\Desktop",
# # # # # # # # #                 0,
# # # # # # # # #                 winreg.KEY_WRITE
# # # # # # # # #             )
# # # # # # # # #
# # # # # # # # #             # 设置DPI缩放值
# # # # # # # # #             winreg.SetValueEx(key, "Win8DpiScaling", 0, winreg.REG_DWORD, 1)
# # # # # # # # #             winreg.SetValueEx(key, "LogPixels", 0, winreg.REG_DWORD, int(96 * (scale_percent / 100)))
# # # # # # # # #             winreg.CloseKey(key)
# # # # # # # # #
# # # # # # # # #             # 设置PerMonitorSettings
# # # # # # # # #             try:
# # # # # # # # #                 key = winreg.OpenKey(
# # # # # # # # #                     winreg.HKEY_CURRENT_USER,
# # # # # # # # #                     "Control Panel\\Desktop\\PerMonitorSettings",
# # # # # # # # #                     0,
# # # # # # # # #                     winreg.KEY_WRITE
# # # # # # # # #                 )
# # # # # # # # #
# # # # # # # # #                 # 获取所有显示器设置
# # # # # # # # #                 monitor_count = 0
# # # # # # # # #                 try:
# # # # # # # # #                     while True:
# # # # # # # # #                         monitor_name = winreg.EnumKey(key, monitor_count)
# # # # # # # # #                         monitor_count += 1
# # # # # # # # #                         monitor_key = winreg.OpenKey(key, monitor_name, 0, winreg.KEY_WRITE)
# # # # # # # # #
# # # # # # # # #                         # 设置缩放比例
# # # # # # # # #                         winreg.SetValueEx(monitor_key, "DpiValue", 0, winreg.REG_DWORD, scale_value)
# # # # # # # # #                         winreg.SetValueEx(monitor_key, "EffectiveDpi", 0, winreg.REG_DWORD,
# # # # # # # # #                                           int(96 * (scale_percent / 100)))
# # # # # # # # #
# # # # # # # # #                         winreg.CloseKey(monitor_key)
# # # # # # # # #                 except OSError:
# # # # # # # # #                     pass  # 没有更多显示器
# # # # # # # # #
# # # # # # # # #                 winreg.CloseKey(key)
# # # # # # # # #             except:
# # # # # # # # #                 pass
# # # # # # # # #
# # # # # # # # #             # 通知系统设置已更改
# # # # # # # # #             ctypes.windll.user32.SystemParametersInfoW(0x001A, 0, None, 0)  # SPI_SETNONCLIENTMETRICS
# # # # # # # # #             ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001E, 0, 0, 0, 1000, None)  # WM_SETTINGCHANGE
# # # # # # # # #
# # # # # # # # #             # 重启Explorer进程以实现立即生效
# # # # # # # # #             self.restart_explorer()
# # # # # # # # #
# # # # # # # # #             return True
# # # # # # # # #         except Exception as e:
# # # # # # # # #             QMessageBox.critical(self, "错误", f"设置失败: {str(e)}")
# # # # # # # # #             return False
# # # # # # # # #
# # # # # # # # #     def restart_explorer(self):
# # # # # # # # #         """重启Windows Explorer进程以实现立即生效"""
# # # # # # # # #         try:
# # # # # # # # #             # 终止Explorer进程
# # # # # # # # #             subprocess.call("taskkill /f /im explorer.exe", shell=True)
# # # # # # # # #             time.sleep(1)  # 等待进程完全终止
# # # # # # # # #
# # # # # # # # #             # 重新启动Explorer
# # # # # # # # #             subprocess.Popen("explorer.exe", shell=True)
# # # # # # # # #             time.sleep(1)  # 给Explorer启动时间
# # # # # # # # #         except Exception as e:
# # # # # # # # #             print(f"重启Explorer时出错: {str(e)}")
# # # # # # # # #
# # # # # # # # #     def apply_scaling(self):
# # # # # # # # #         """应用用户选择的缩放比例"""
# # # # # # # # #         scale_percent = int(self.sender().property("scale_percent"))
# # # # # # # # #
# # # # # # # # #         if scale_percent == self.current_scaling:
# # # # # # # # #             QMessageBox.information(self, "提示", "缩放比例未改变")
# # # # # # # # #             return
# # # # # # # # #
# # # # # # # # #         # 确认对话框
# # # # # # # # #         reply = QMessageBox.question(
# # # # # # # # #             self,
# # # # # # # # #             "确认设置",
# # # # # # # # #             f"确定要将缩放比例设置为 {scale_percent}% 吗？\n\n"
# # # # # # # # #             "桌面将短暂闪烁（资源管理器重启）",
# # # # # # # # #             QMessageBox.Yes | QMessageBox.No
# # # # # # # # #         )
# # # # # # # # #
# # # # # # # # #         if reply == QMessageBox.No:
# # # # # # # # #             return
# # # # # # # # #
# # # # # # # # #         if self.set_scaling(scale_percent):
# # # # # # # # #             QMessageBox.information(
# # # # # # # # #                 self,
# # # # # # # # #                 "成功",
# # # # # # # # #                 f"已成功设置缩放比例为 {scale_percent}%\n\n"
# # # # # # # # #                 "缩放设置已立即生效！"
# # # # # # # # #             )
# # # # # # # # #             self.current_scaling = scale_percent
# # # # # # # # #             self.update_current_label()
# # # # # # # # #
# # # # # # # # #     def init_ui(self):
# # # # # # # # #         """初始化用户界面"""
# # # # # # # # #         # 创建中央部件
# # # # # # # # #         central_widget = QWidget()
# # # # # # # # #         self.setCentralWidget(central_widget)
# # # # # # # # #
# # # # # # # # #         # 主布局
# # # # # # # # #         main_layout = QVBoxLayout(central_widget)
# # # # # # # # #         main_layout.setSpacing(20)
# # # # # # # # #         main_layout.setContentsMargins(30, 30, 30, 30)
# # # # # # # # #
# # # # # # # # #         # 标题
# # # # # # # # #         title_label = QLabel("Windows 10 屏幕缩放设置工具")
# # # # # # # # #         title_font = QFont("Segoe UI", 16, QFont.Bold)
# # # # # # # # #         title_label.setFont(title_font)
# # # # # # # # #         title_label.setAlignment(Qt.AlignCenter)
# # # # # # # # #         title_label.setStyleSheet("color: #2c3e50;")
# # # # # # # # #         main_layout.addWidget(title_label)
# # # # # # # # #
# # # # # # # # #         # 当前设置
# # # # # # # # #         self.current_label = QLabel()
# # # # # # # # #         self.current_label.setAlignment(Qt.AlignCenter)
# # # # # # # # #         self.current_label.setStyleSheet("font-size: 14px; color: #3498db; font-weight: bold;")
# # # # # # # # #         main_layout.addWidget(self.current_label)
# # # # # # # # #
# # # # # # # # #         # 分隔线
# # # # # # # # #         separator = QLabel()
# # # # # # # # #         separator.setFrameShape(QLabel.HLine)
# # # # # # # # #         separator.setStyleSheet("background-color: #bdc3c7;")
# # # # # # # # #         main_layout.addWidget(separator)
# # # # # # # # #
# # # # # # # # #         # 缩放选项组
# # # # # # # # #         scale_group = QGroupBox("选择缩放比例")
# # # # # # # # #         scale_group.setStyleSheet("""
# # # # # # # # #             QGroupBox {
# # # # # # # # #                 font-size: 14px;
# # # # # # # # #                 font-weight: bold;
# # # # # # # # #                 border: 1px solid #bdc3c7;
# # # # # # # # #                 border-radius: 5px;
# # # # # # # # #                 margin-top: 10px;
# # # # # # # # #             }
# # # # # # # # #             QGroupBox::title {
# # # # # # # # #                 subcontrol-origin: margin;
# # # # # # # # #                 left: 10px;
# # # # # # # # #                 padding: 0 5px;
# # # # # # # # #             }
# # # # # # # # #         """)
# # # # # # # # #
# # # # # # # # #         scale_layout = QVBoxLayout(scale_group)
# # # # # # # # #         scale_layout.setSpacing(15)
# # # # # # # # #
# # # # # # # # #         # 缩放选项
# # # # # # # # #         scales = [100, 125, 150, 175, 200]
# # # # # # # # #         self.scale_buttons = []
# # # # # # # # #
# # # # # # # # #         for scale in scales:
# # # # # # # # #             btn = QPushButton(f"{scale}%")
# # # # # # # # #             btn.setProperty("scale_percent", scale)
# # # # # # # # #             btn.setFixedHeight(40)
# # # # # # # # #             btn.setStyleSheet("""
# # # # # # # # #                 QPushButton {
# # # # # # # # #                     font-size: 14px;
# # # # # # # # #                     font-weight: bold;
# # # # # # # # #                     background-color: #ecf0f1;
# # # # # # # # #                     border: 1px solid #bdc3c7;
# # # # # # # # #                     border-radius: 5px;
# # # # # # # # #                     padding: 5px;
# # # # # # # # #                 }
# # # # # # # # #                 QPushButton:hover {
# # # # # # # # #                     background-color: #d6dbdf;
# # # # # # # # #                 }
# # # # # # # # #                 QPushButton:pressed {
# # # # # # # # #                     background-color: #bdc3c7;
# # # # # # # # #                 }
# # # # # # # # #             """)
# # # # # # # # #             btn.clicked.connect(self.apply_scaling)
# # # # # # # # #             scale_layout.addWidget(btn)
# # # # # # # # #             self.scale_buttons.append(btn)
# # # # # # # # #
# # # # # # # # #         main_layout.addWidget(scale_group)
# # # # # # # # #
# # # # # # # # #         # 信息提示
# # # # # # # # #         info_label = QLabel(
# # # # # # # # #             "注意：\n"
# # # # # # # # #             "• 此工具需要管理员权限运行\n"
# # # # # # # # #             "• 设置后会立即生效，无需注销或重启\n"
# # # # # # # # #             "• 某些应用程序可能需要重新启动才能适应新的缩放比例\n"
# # # # # # # # #             "• 更改时桌面会短暂闪烁（资源管理器重启）"
# # # # # # # # #         )
# # # # # # # # #         info_label.setStyleSheet("""
# # # # # # # # #             font-size: 12px;
# # # # # # # # #             color: #7f8c8d;
# # # # # # # # #             background-color: #f9f9f9;
# # # # # # # # #             border-left: 3px solid #3498db;
# # # # # # # # #             padding: 10px;
# # # # # # # # #         """)
# # # # # # # # #         info_label.setWordWrap(True)
# # # # # # # # #         main_layout.addWidget(info_label)
# # # # # # # # #
# # # # # # # # #         # 底部状态栏
# # # # # # # # #         status_bar = QWidget()
# # # # # # # # #         status_layout = QHBoxLayout(status_bar)
# # # # # # # # #         status_layout.setContentsMargins(0, 0, 0, 0)
# # # # # # # # #
# # # # # # # # #         author_label = QLabel("© 2023 Windows 系统工具")
# # # # # # # # #         author_label.setStyleSheet("font-size: 11px; color: #7f8c8d;")
# # # # # # # # #
# # # # # # # # #         admin_label = QLabel()
# # # # # # # # #         admin_label.setAlignment(Qt.AlignRight)
# # # # # # # # #         admin_label.setStyleSheet("font-size: 11px;")
# # # # # # # # #
# # # # # # # # #         if self.is_admin():
# # # # # # # # #             admin_label.setText("管理员权限 ✓")
# # # # # # # # #             admin_label.setStyleSheet("font-size: 11px; color: #27ae60; font-weight: bold;")
# # # # # # # # #         else:
# # # # # # # # #             admin_label.setText("需要管理员权限")
# # # # # # # # #             admin_label.setStyleSheet("font-size: 11px; color: #e74c3c; font-weight: bold;")
# # # # # # # # #
# # # # # # # # #         status_layout.addWidget(author_label)
# # # # # # # # #         status_layout.addStretch()
# # # # # # # # #         status_layout.addWidget(admin_label)
# # # # # # # # #
# # # # # # # # #         main_layout.addWidget(status_bar)
# # # # # # # # #
# # # # # # # # #     def update_current_label(self):
# # # # # # # # #         """更新当前缩放比例标签"""
# # # # # # # # #         self.current_label.setText(f"当前缩放比例: {self.current_scaling}%")
# # # # # # # # #
# # # # # # # # #         # 高亮当前选中的比例按钮
# # # # # # # # #         for btn in self.scale_buttons:
# # # # # # # # #             scale = btn.property("scale_percent")
# # # # # # # # #             if scale == self.current_scaling:
# # # # # # # # #                 btn.setStyleSheet("""
# # # # # # # # #                     QPushButton {
# # # # # # # # #                         font-size: 14px;
# # # # # # # # #                         font-weight: bold;
# # # # # # # # #                         background-color: #3498db;
# # # # # # # # #                         color: white;
# # # # # # # # #                         border: 1px solid #2980b9;
# # # # # # # # #                         border-radius: 5px;
# # # # # # # # #                         padding: 5px;
# # # # # # # # #                     }
# # # # # # # # #                     QPushButton:hover {
# # # # # # # # #                         background-color: #2980b9;
# # # # # # # # #                     }
# # # # # # # # #                     QPushButton:pressed {
# # # # # # # # #                         background-color: #1c6ea4;
# # # # # # # # #                     }
# # # # # # # # #                 """)
# # # # # # # # #             else:
# # # # # # # # #                 btn.setStyleSheet("""
# # # # # # # # #                     QPushButton {
# # # # # # # # #                         font-size: 14px;
# # # # # # # # #                         font-weight: bold;
# # # # # # # # #                         background-color: #ecf0f1;
# # # # # # # # #                         border: 1px solid #bdc3c7;
# # # # # # # # #                         border-radius: 5px;
# # # # # # # # #                         padding: 5px;
# # # # # # # # #                     }
# # # # # # # # #                     QPushButton:hover {
# # # # # # # # #                         background-color: #d6dbdf;
# # # # # # # # #                     }
# # # # # # # # #                     QPushButton:pressed {
# # # # # # # # #                         background-color: #bdc3c7;
# # # # # # # # #                     }
# # # # # # # # #                 """)
# # # # # # # # #
# # # # # # # # #
# # # # # # # # # if __name__ == "__main__":
# # # # # # # # #     # 启用高DPI缩放
# # # # # # # # #     if hasattr(Qt, 'AA_EnableHighDpiScaling'):
# # # # # # # # #         QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
# # # # # # # # #     if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
# # # # # # # # #         QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
# # # # # # # # #
# # # # # # # # #     app = QApplication(sys.argv)
# # # # # # # # #     app.setStyle("Fusion")  # 使用Fusion样式
# # # # # # # # #
# # # # # # # # #     # 检查管理员权限
# # # # # # # # #     if ctypes.windll.shell32.IsUserAnAdmin() == 0:
# # # # # # # # #         # 请求管理员权限
# # # # # # # # #         ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
# # # # # # # # #         sys.exit()
# # # # # # # # #
# # # # # # # # #     window = DpiScalingApp()
# # # # # # # # #     window.show()
# # # # # # # #
# # # # # # # #
# # # # # # # # import os
# # # # # # # # import sys
# # # # # # # # from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton,
# # # # # # # #                              QVBoxLayout, QWidget, QMessageBox)
# # # # # # # # from PyQt5.QtCore import QSettings
# # # # # # # #
# # # # # # # #
# # # # # # # # class DPIWindow(QMainWindow):
# # # # # # # #     def __init__(self):
# # # # # # # #         super().__init__()
# # # # # # # #         self.settings = QSettings("MyCompany", "DPISettings")
# # # # # # # #
# # # # # # # #         # 获取当前缩放值（默认1.0=100%）
# # # # # # # #         self.current_scale = float(self.settings.value("DPI_Scale", 1.0))
# # # # # # # #
# # # # # # # #         self.initUI()
# # # # # # # #         self.update_title()
# # # # # # # #
# # # # # # # #     def initUI(self):
# # # # # # # #         central_widget = QWidget()
# # # # # # # #         layout = QVBoxLayout()
# # # # # # # #
# # # # # # # #         self.scale_btn = QPushButton(f"切换缩放到125% (当前: {int(self.current_scale * 100)}%)")
# # # # # # # #         self.scale_btn.clicked.connect(self.change_scale)
# # # # # # # #
# # # # # # # #         layout.addWidget(self.scale_btn)
# # # # # # # #         central_widget.setLayout(layout)
# # # # # # # #         self.setCentralWidget(central_widget)
# # # # # # # #
# # # # # # # #     def change_scale(self):
# # # # # # # #         new_scale = 1.25  # 目标缩放值
# # # # # # # #
# # # # # # # #         # 保存新设置
# # # # # # # #         self.settings.setValue("DPI_Scale", new_scale)
# # # # # # # #
# # # # # # # #         # 提示用户重启
# # # # # # # #         QMessageBox.information(
# # # # # # # #             self,
# # # # # # # #             "缩放设置已更改",
# # # # # # # #             "应用程序需要重启以使新的缩放设置(125%)生效",
# # # # # # # #             QMessageBox.Ok
# # # # # # # #         )
# # # # # # # #         QApplication.quit()
# # # # # # # #
# # # # # # # #     def update_title(self):
# # # # # # # #         self.setWindowTitle(f"DPI缩放示例 (当前缩放: {int(self.current_scale * 100)}%)")
# # # # # # # #
# # # # # # # #
# # # # # # # # def main():
# # # # # # # #     # 读取保存的缩放设置
# # # # # # # #     settings = QSettings("MyCompany", "DPISettings")
# # # # # # # #     scale_factor = float(settings.value("DPI_Scale", 1.0))
# # # # # # # #
# # # # # # # #     # 设置环境变量
# # # # # # # #     if scale_factor > 1:
# # # # # # # #         os.environ["QT_SCALE_FACTOR"] = str(scale_factor)
# # # # # # # #
# # # # # # # #     app = QApplication(sys.argv)
# # # # # # # #     window = DPIWindow()
# # # # # # # #     window.show()
# # # # # # # #     sys.exit(app.exec_())
# # # # # # # #
# # # # # # # #
# # # # # # # # if __name__ == "__main__":
# # # # # # #
# # # # # # # #
# # # # # # # # import sys
# # # # # # # # from PyQt5.QtWidgets import QApplication, QMainWindow, QListWidget, QVBoxLayout, QWidget
# # # # # # # # from PyQt5.QtSerialPort import QSerialPortInfo
# # # # # # # #
# # # # # # # #
# # # # # # # # class SerialPortScanner(QMainWindow):
# # # # # # # #     def __init__(self):
# # # # # # # #         super().__init__()
# # # # # # # #         self.setWindowTitle("USB串口设备扫描器")
# # # # # # # #         self.setGeometry(100, 100, 500, 400)
# # # # # # # #
# # # # # # # #         # 创建UI组件
# # # # # # # #         self.port_list = QListWidget()
# # # # # # # #
# # # # # # # #         # 设置布局
# # # # # # # #         layout = QVBoxLayout()
# # # # # # # #         layout.addWidget(self.port_list)
# # # # # # # #
# # # # # # # #         container = QWidget()
# # # # # # # #         container.setLayout(layout)
# # # # # # # #         self.setCentralWidget(container)
# # # # # # # #
# # # # # # # #         # 扫描可用串口
# # # # # # # #         self.scan_serial_ports()
# # # # # # # #
# # # # # # # #     def scan_serial_ports(self):
# # # # # # # #         """扫描并显示所有可用的USB串口设备"""
# # # # # # # #         self.port_list.clear()
# # # # # # # #
# # # # # # # #         # 获取所有可用串口
# # # # # # # #         ports = QSerialPortInfo.availablePorts()
# # # # # # # #
# # # # # # # #         if not ports:
# # # # # # # #             self.port_list.addItem("未检测到串口设备")
# # # # # # # #             return
# # # # # # # #
# # # # # # # #         for port_info in ports:
# # # # # # # #             # 筛选USB串口（通常有供应商和产品ID）
# # # # # # # #             if port_info.hasVendorIdentifier() and port_info.hasProductIdentifier():
# # # # # # # #                 # 获取详细信息
# # # # # # # #                 vid = port_info.vendorIdentifier()
# # # # # # # #                 pid = port_info.productIdentifier()
# # # # # # # #                 port_name = port_info.portName()
# # # # # # # #                 description = port_info.description()
# # # # # # # #                 manufacturer = port_info.manufacturer()
# # # # # # # #
# # # # # # # #                 # 显示在列表中
# # # # # # # #                 item_text = (
# # # # # # # #                     f"端口: {port_name}\n"
# # # # # # # #                     f"描述: {description}\n"
# # # # # # # #                     f"制造商: {manufacturer}\n"
# # # # # # # #                     f"VID: 0x{vid:04X}, PID: 0x{pid:04X}"
# # # # # # # #                 )
# # # # # # # #                 self.port_list.addItem(item_text)
# # # # # # # #
# # # # # # # #
# # # # # # # # if __name__ == "__main__":
# # # # # # # #     app = QApplication(sys.argv)
# # # # # # # #     window = SerialPortScanner()
# # # # # # # #     window.show()
# # # # # # # #     sys.exit(app.exec_())
# # # # # # #
# # # # # # # from PyQt5.QtWidgets import (
# # # # # # #     QGroupBox, QTreeView, QVBoxLayout, QAbstractItemView
# # # # # # # )
# # # # # # # from PyQt5.QtGui import QStandardItemModel, QStandardItem
# # # # # # # from PyQt5.QtCore import Qt, QModelIndex
# # # # # # #
# # # # # # #
# # # # # # # class TreeViewGroup(QGroupBox):
# # # # # # #     def __init__(self, groupbox, title=None, headers=None, parent=None):
# # # # # # #         """
# # # # # # #         在指定的 QGroupBox 上创建 QTreeView
# # # # # # #
# # # # # # #         参数:
# # # # # # #             groupbox (QGroupBox): 要放置树形视图的GroupBox容器
# # # # # # #             title (str): GroupBox标题(如果为空则使用原GroupBox标题)
# # # # # # #             headers (list): 列标题列表
# # # # # # #             parent (QWidget): 父组件
# # # # # # #         """
# # # # # # #         super().__init__(parent)
# # # # # # #
# # # # # # #         # 保存对原始GroupBox的引用
# # # # # # #         self.groupbox = groupbox
# # # # # # #
# # # # # # #         # 设置标题(如果提供了新标题)
# # # # # # #         if title:
# # # # # # #             self.groupbox.setTitle(title)
# # # # # # #
# # # # # # #         # 创建布局(如果原GroupBox没有布局)
# # # # # # #         if self.groupbox.layout() is None:
# # # # # # #             self.groupbox.setLayout(QVBoxLayout())
# # # # # # #             self.groupbox.layout().setContentsMargins(5, 15, 5, 5)
# # # # # # #
# # # # # # #         # 创建树形视图
# # # # # # #         self.tree_view = QTreeView()
# # # # # # #         self.tree_view.setSelectionBehavior(QAbstractItemView.SelectRows)
# # # # # # #         self.tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
# # # # # # #         self.tree_view.setAlternatingRowColors(True)
# # # # # # #
# # # # # # #         # 添加到GroupBox布局
# # # # # # #         self.groupbox.layout().addWidget(self.tree_view)
# # # # # # #
# # # # # # #         # 创建模型
# # # # # # #         self.model = QStandardItemModel()
# # # # # # #         self.tree_view.setModel(self.model)
# # # # # # #
# # # # # # #         # 设置列标题
# # # # # # #         if headers:
# # # # # # #             self.set_headers(headers)
# # # # # # #
# # # # # # #     def set_headers(self, headers):
# # # # # # #         """设置列标题"""
# # # # # # #         self.model.setHorizontalHeaderLabels(headers)
# # # # # # #
# # # # # # #     def add_top_level_item(self, text, data=None, icon=None):
# # # # # # #         """添加顶级项"""
# # # # # # #         item = QStandardItem(text)
# # # # # # #         if data:
# # # # # # #             item.setData(data, Qt.UserRole)
# # # # # # #         if icon:
# # # # # # #             item.setIcon(icon)
# # # # # # #         self.model.appendRow(item)
# # # # # # #         return item
# # # # # # #
# # # # # # #     def add_child_item(self, parent_item, text, data=None, icon=None):
# # # # # # #         """添加子项"""
# # # # # # #         if not parent_item:
# # # # # # #             return self.add_top_level_item(text, data, icon)
# # # # # # #
# # # # # # #         item = QStandardItem(text)
# # # # # # #         if data:
# # # # # # #             item.setData(data, Qt.UserRole)
# # # # # # #         if icon:
# # # # # # #             item.setIcon(icon)
# # # # # # #         parent_item.appendRow(item)
# # # # # # #         return item
# # # # # # #
# # # # # # #     def add_items(self, parent, items):
# # # # # # #         """
# # # # # # #         递归添加树形结构
# # # # # # #
# # # # # # #         参数:
# # # # # # #             parent: 父项(如果是顶级则设为None)
# # # # # # #             items: 项目列表，格式为:
# # # # # # #                    [text, data, [child1, child2, ...]] 或
# # # # # # #                    [text, data] 或
# # # # # # #                    text
# # # # # # #         """
# # # # # # #         if not items:
# # # # # # #             return
# # # # # # #
# # # # # # #         if not isinstance(items, (list, tuple)):
# # # # # # #             # 单个项目
# # # # # # #             item = QStandardItem(items)
# # # # # # #             if parent:
# # # # # # #                 parent.appendRow(item)
# # # # # # #             else:
# # # # # # #                 self.model.appendRow(item)
# # # # # # #             return
# # # # # # #
# # # # # # #         # 处理项目列表
# # # # # # #         for item_data in items:
# # # # # # #             if isinstance(item_data, (list, tuple)):
# # # # # # #                 text = item_data[0]
# # # # # # #                 data = item_data[1] if len(item_data) > 1 else None
# # # # # # #                 children = item_data[2] if len(item_data) > 2 else None
# # # # # # #             else:
# # # # # # #                 text = item_data
# # # # # # #                 data = None
# # # # # # #                 children = None
# # # # # # #
# # # # # # #             item = QStandardItem(text)
# # # # # # #             if data:
# # # # # # #                 item.setData(data, Qt.UserRole)
# # # # # # #
# # # # # # #             if parent:
# # # # # # #                 parent.appendRow(item)
# # # # # # #             else:
# # # # # # #                 self.model.appendRow(item)
# # # # # # #
# # # # # # #             # 递归添加子项
# # # # # # #             if children:
# # # # # # #                 self.add_items(item, children)
# # # # # # #
# # # # # # #     def clear(self):
# # # # # # #         """清空树"""
# # # # # # #         self.model.clear()
# # # # # # #
# # # # # # #     def expand_all(self):
# # # # # # #         """展开所有节点"""
# # # # # # #         self.tree_view.expandAll()
# # # # # # #
# # # # # # #     def collapse_all(self):
# # # # # # #         """折叠所有节点"""
# # # # # # #         self.tree_view.collapseAll()
# # # # # # #
# # # # # # #     def get_selected_item(self):
# # # # # # #         """获取当前选中的项"""
# # # # # # #         index = self.tree_view.currentIndex()
# # # # # # #         if index.isValid():
# # # # # # #             return self.model.itemFromIndex(index)
# # # # # # #         return None
# # # # # # #
# # # # # # #     def set_column_width(self, column, width):
# # # # # # #         """设置列宽"""
# # # # # # #         self.tree_view.setColumnWidth(column, width)
# # # # # # #
# # # # # # #     def set_header_hidden(self, hidden=True):
# # # # # # #         """设置是否隐藏表头"""
# # # # # # #         self.tree_view.header().setHidden(hidden)
# # # # # # #
# # # # # # #     def set_selection_mode(self, mode):
# # # # # # #         """设置选择模式"""
# # # # # # #         self.tree_view.setSelectionMode(mode)
# # # # # # #
# # # # # # #
# # # # # # # # 使用示例
# # # # # # # if __name__ == "__main__":
# # # # # # #     import sys
# # # # # # #     from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QGroupBox
# # # # # # #     from PyQt5.QtGui import QIcon
# # # # # # #
# # # # # # #
# # # # # # #     class MainWindow(QMainWindow):
# # # # # # #         def __init__(self):
# # # # # # #             super().__init__()
# # # # # # #             self.setWindowTitle("TreeView in GroupBox Demo")
# # # # # # #             self.setGeometry(300, 300, 600, 400)
# # # # # # #
# # # # # # #             # 创建主控件和布局
# # # # # # #             central_widget = QWidget()
# # # # # # #             self.setCentralWidget(central_widget)
# # # # # # #             main_layout = QHBoxLayout(central_widget)
# # # # # # #
# # # # # # #             # 创建左侧分组框
# # # # # # #             left_group = QGroupBox("设备列表")
# # # # # # #             main_layout.addWidget(left_group, 1)
# # # # # # #
# # # # # # #             # 创建右侧分组框
# # # # # # #             right_group = QGroupBox("用户列表")
# # # # # # #             main_layout.addWidget(right_group, 1)
# # # # # # #
# # # # # # #             # 在左侧分组框上创建树视图
# # # # # # #             device_tree = TreeViewGroup(
# # # # # # #                 groupbox=left_group,
# # # # # # #                 headers=["设备名称", "状态"]
# # # # # # #             )
# # # # # # #
# # # # # # #             # 在右侧分组框上创建树视图
# # # # # # #             user_tree = TreeViewGroup(
# # # # # # #                 groupbox=right_group,
# # # # # # #                 title="用户管理",
# # # # # # #                 headers=["用户名", "角色"]
# # # # # # #             )
# # # # # # #
# # # # # # #             # 添加设备数据(使用add_items方法)
# # # # # # #             devices = [
# # # # # # #                 ["服务器", "server-group", [
# # # # # # #                     ["Web服务器", "web-server", [
# # # # # # #                         ["Nginx", "nginx"],
# # # # # # #                         ["Apache", "apache"]
# # # # # # #                     ]],
# # # # # # #                     ["数据库服务器", "db-server", [
# # # # # # #                         ["MySQL", "mysql"],
# # # # # # #                         ["PostgreSQL", "postgres"]
# # # # # # #                     ]]
# # # # # # #                 ]],
# # # # # # #                 ["工作站", "workstation", [
# # # # # # #                     ["工程师工作站", "engineer"],
# # # # # # #                     ["设计师工作站", "designer"]
# # # # # # #                 ]]
# # # # # # #             ]
# # # # # # #             device_tree.add_items(None, devices)
# # # # # # #
# # # # # # #             # 添加用户数据(使用单独添加方法)
# # # # # # #             users = user_tree.add_top_level_item("管理员")
# # # # # # #             user_tree.add_child_item(users, "admin", "超级管理员")
# # # # # # #             user_tree.add_child_item(users, "sysadmin", "系统管理员")
# # # # # # #
# # # # # # #             editors = user_tree.add_top_level_item("编辑")
# # # # # # #             user_tree.add_child_item(editors, "editor1", "内容编辑")
# # # # # # #             user_tree.add_child_item(editors, "editor2", "图片编辑")
# # # # # # #
# # # # # # #             viewers = user_tree.add_top_level_item("查看者")
# # # # # # #             user_tree.add_child_item(viewers, "viewer1", "只读访问")
# # # # # # #
# # # # # # #             # 设置列宽
# # # # # # #             device_tree.set_column_width(0, 200)
# # # # # # #             user_tree.set_column_width(0, 150)
# # # # # # #
# # # # # # #             # 展开所有节点
# # # # # # #             device_tree.expand_all()
# # # # # # #             user_tree.expand_all()
# # # # # # #
# # # # # # #             self.show()
# # # # # # #
# # # # # # #
# # # # # # #     app = QApplication(sys.argv)
# # # # # # #     window = MainWindow()
# # # # # # import sys
# # # # # # from PyQt5.QtWidgets import (
# # # # # #     QApplication, QMainWindow, QTreeView, QFileSystemModel, QWidget,
# # # # # #     QVBoxLayout, QLabel, QPushButton, QHBoxLayout
# # # # # # )
# # # # # # from PyQt5.QtCore import Qt, QDir
# # # # # # from PyQt5.QtGui import QFont
# # # # # #
# # # # # #
# # # # # # class TreeViewExample(QMainWindow):
# # # # # #     def __init__(self):
# # # # # #         super().__init__()
# # # # # #         self.setWindowTitle("QTreeView选中节点颜色解决方案")
# # # # # #         self.setGeometry(300, 300, 800, 500)
# # # # # #
# # # # # #         # 创建主控件
# # # # # #         main_widget = QWidget()
# # # # # #         self.setCentralWidget(main_widget)
# # # # # #         main_layout = QVBoxLayout(main_widget)
# # # # # #         main_layout.setContentsMargins(20, 20, 20, 20)
# # # # # #         main_layout.setSpacing(20)
# # # # # #
# # # # # #         # 标题
# # # # # #         title_label = QLabel("QTreeView选中节点颜色一致性解决方案")
# # # # # #         title_label.setFont(QFont("Arial", 16, QFont.Bold))
# # # # # #         title_label.setAlignment(Qt.AlignCenter)
# # # # # #         title_label.setStyleSheet("color: #2c3e50; padding: 10px;")
# # # # # #         main_layout.addWidget(title_label)
# # # # # #
# # # # # #         # 说明文本
# # # # # #         description = QLabel(
# # # # # #             "本示例展示了如何使QTreeView的选中节点在获得焦点和失去焦点时保持相同颜色。\n"
# # # # # #             "默认行为：失去焦点时选中节点变为灰色。解决方案：使用样式表统一两种状态的颜色。"
# # # # # #         )
# # # # # #         description.setFont(QFont("Arial", 10))
# # # # # #         description.setAlignment(Qt.AlignCenter)
# # # # # #         description.setStyleSheet("color: #7f8c8d; background: #f8f9fa; padding: 15px; border-radius: 8px;")
# # # # # #         main_layout.addWidget(description)
# # # # # #
# # # # # #         # 创建树视图和按钮的容器
# # # # # #         content_widget = QWidget()
# # # # # #         content_layout = QHBoxLayout(content_widget)
# # # # # #         content_layout.setSpacing(20)
# # # # # #
# # # # # #         # 左侧树视图
# # # # # #         tree_container = QWidget()
# # # # # #         tree_layout = QVBoxLayout(tree_container)
# # # # # #         tree_layout.setContentsMargins(0, 0, 0, 0)
# # # # # #
# # # # # #         tree_label = QLabel("文件系统树视图")
# # # # # #         tree_label.setFont(QFont("Arial", 10, QFont.Bold))
# # # # # #         tree_layout.addWidget(tree_label)
# # # # # #
# # # # # #         self.tree_view = QTreeView()
# # # # # #         self.tree_view.setFont(QFont("Arial", 10))
# # # # # #         self.tree_view.setSelectionMode(QTreeView.SingleSelection)
# # # # # #         self.tree_view.setAnimated(True)
# # # # # #
# # # # # #         # 设置文件系统模型
# # # # # #         model = QFileSystemModel()
# # # # # #         model.setRootPath(QDir.rootPath())
# # # # # #         self.tree_view.setModel(model)
# # # # # #         self.tree_view.setRootIndex(model.index(QDir.rootPath()))
# # # # # #
# # # # # #         # 设置样式表：统一选中状态颜色
# # # # # #         self.tree_view.setStyleSheet("""
# # # # # #             QTreeView {
# # # # # #                 background-color: #ffffff;
# # # # # #                 border: 1px solid #dcdde1;
# # # # # #                 border-radius: 5px;
# # # # # #                 outline: 0;
# # # # # #             }
# # # # # #             QTreeView::item {
# # # # # #                 height: 28px;
# # # # # #                 padding: 5px;
# # # # # #                 border: none;
# # # # # #             }
# # # # # #             QTreeView::item:selected:active,
# # # # # #             QTreeView::item:selected:!active {
# # # # # #                 background: #3498db;
# # # # # #                 color: white;
# # # # # #                 border: none;
# # # # # #             }
# # # # # #             QTreeView::item:hover {
# # # # # #                 background: #d6eaf8;
# # # # # #                 color: #2c3e50;
# # # # # #             }
# # # # # #             QTreeView::branch:has-siblings:!adjoins-item,
# # # # # #             QTreeView::branch:has-siblings:adjoins-item,
# # # # # #             QTreeView::branch:!has-children:!has-siblings:adjoins-item,
# # # # # #             QTreeView::branch:closed:has-children:has-siblings,
# # # # # #             QTreeView::branch:open:has-children:has-siblings {
# # # # # #                 background: none;
# # # # # #             }
# # # # # #         """)
# # # # # #
# # # # # #         tree_layout.addWidget(self.tree_view)
# # # # # #         content_layout.addWidget(tree_container, 2)  # 占2份空间
# # # # # #
# # # # # #         # 右侧控制面板
# # # # # #         control_panel = QWidget()
# # # # # #         control_layout = QVBoxLayout(control_panel)
# # # # # #         control_layout.setContentsMargins(20, 20, 20, 20)
# # # # # #         control_layout.setSpacing(15)
# # # # # #
# # # # # #         panel_label = QLabel("控制面板")
# # # # # #         panel_label.setFont(QFont("Arial", 10, QFont.Bold))
# # # # # #         panel_label.setAlignment(Qt.AlignCenter)
# # # # # #         control_layout.addWidget(panel_label)
# # # # # #
# # # # # #         # 添加说明框
# # # # # #         explanation = QLabel(
# # # # # #             "<b>解决方案说明：</b><br>"
# # # # # #             "使用样式表同时设置两个伪状态：<br>"
# # # # # #             "<code>QTreeView::item:selected:active</code> 和<br>"
# # # # # #             "<code>QTreeView::item:selected:!active</code><br><br>"
# # # # # #             "这样无论视图是否获得焦点，<br>"
# # # # # #             "选中节点都将显示为相同的颜色。"
# # # # # #         )
# # # # # #         explanation.setFont(QFont("Arial", 9))
# # # # # #         explanation.setStyleSheet("background: #ecf0f1; padding: 15px; border-radius: 8px;")
# # # # # #         explanation.setAlignment(Qt.AlignLeft | Qt.AlignTop)
# # # # # #         control_layout.addWidget(explanation)
# # # # # #
# # # # # #         # 添加焦点切换按钮
# # # # # #         focus_btn = QPushButton("切换焦点")
# # # # # #         focus_btn.setFont(QFont("Arial", 10))
# # # # # #         focus_btn.setStyleSheet("""
# # # # # #             QPushButton {
# # # # # #                 background: #3498db;
# # # # # #                 color: white;
# # # # # #                 border: none;
# # # # # #                 padding: 10px;
# # # # # #                 border-radius: 5px;
# # # # # #             }
# # # # # #             QPushButton:hover {
# # # # # #                 background: #2980b9;
# # # # # #             }
# # # # # #         """)
# # # # # #         focus_btn.clicked.connect(self.toggle_focus)
# # # # # #         control_layout.addWidget(focus_btn)
# # # # # #
# # # # # #         # 添加状态指示器
# # # # # #         self.status_label = QLabel("当前状态：视图获得焦点")
# # # # # #         self.status_label.setFont(QFont("Arial", 9))
# # # # # #         self.status_label.setStyleSheet("color: #27ae60; padding: 10px 0;")
# # # # # #         control_layout.addWidget(self.status_label)
# # # # # #
# # # # # #         # 添加颜色说明
# # # # # #         colors_label = QLabel(
# # # # # #             "<b>颜色说明：</b><br>"
# # # # # #             "• 选中节点：<span style='background:#3498db; color:white;'>&nbsp;蓝色&nbsp;</span><br>"
# # # # # #             "• 悬停节点：<span style='background:#d6eaf8;'>&nbsp;浅蓝色&nbsp;</span><br>"
# # # # # #             "• 普通节点：白色背景"
# # # # # #         )
# # # # # #         colors_label.setFont(QFont("Arial", 9))
# # # # # #         colors_label.setStyleSheet("padding: 15px 0;")
# # # # # #         control_layout.addWidget(colors_label)
# # # # # #
# # # # # #         control_layout.addStretch(1)
# # # # # #         content_layout.addWidget(control_panel, 1)  # 占1份空间
# # # # # #
# # # # # #         main_layout.addWidget(content_widget)
# # # # # #
# # # # # #         # 底部信息
# # # # # #         footer = QLabel("PyQt5 QTreeView样式表示例 | 解决方案：统一选中状态颜色")
# # # # # #         footer.setFont(QFont("Arial", 8))
# # # # # #         footer.setAlignment(Qt.AlignCenter)
# # # # # #         footer.setStyleSheet("color: #7f8c8d; padding: 10px;")
# # # # # #         main_layout.addWidget(footer)
# # # # # #
# # # # # #     def toggle_focus(self):
# # # # # #         if self.tree_view.hasFocus():
# # # # # #             self.tree_view.clearFocus()
# # # # # #             self.status_label.setText("当前状态：视图失去焦点")
# # # # # #             self.status_label.setStyleSheet("color: #e74c3c; padding: 10px 0;")
# # # # # #         else:
# # # # # #             self.tree_view.setFocus()
# # # # # #             self.status_label.setText("当前状态：视图获得焦点")
# # # # # #             self.status_label.setStyleSheet("color: #27ae60; padding: 10px 0;")
# # # # # #
# # # # # #
# # # # # # if __name__ == "__main__":
# # # # # #     app = QApplication(sys.argv)
# # # # # #     app.setStyle("Fusion")  # 使用Fusion样式以获得更好的跨平台体验
# # # # # #
# # # # # #     # 设置应用程序样式
# # # # # #     app.setStyleSheet("""
# # # # # #         QMainWindow {
# # # # # #             background-color: #ecf0f1;
# # # # # #         }
# # # # # #     """)
# # # # # #
# # # # # #     window = TreeViewExample()
# # # # # #     window.show()
# # # # #
# # # # #
# # # # # # from loguru import logger
# # # # # # import os
# # # # # #
# # # # # # # 确保日志目录存在
# # # # # # log_dir = "./Log/core_Log"
# # # # # # os.makedirs(log_dir, exist_ok=True)
# # # # # #
# # # # # # # 最小化配置测试
# # # # # # logger.add(
# # # # # #     os.path.join(log_dir, "minimal_test.log"),
# # # # # #     format="{time} {message}",
# # # # # #     level="DEBUG",
# # # # # #     catch=True
# # # # # # )
# # # # # #
# # # # # # logger.info("最小配置测试通过")
# # # # # import os
# # # # # import sys
# # # # # import ctypes
# # # # # from ctypes import wintypes, Structure, POINTER, byref
# # # # # import cv2
# # # # # import numpy as np
# # # # #
# # # # # # 1. 加载海康SDK核心库
# # # # # try:
# # # # #     retval = os.getcwd()
# # # # #     os.chdir(r'./lib22/win')
# # # # #     # 请确保这些DLL文件在程序目录或系统PATH中
# # # # #     hcnetsdk = ctypes.WinDLL("./HCNetSDK.dll")
# # # # #     playsdk = ctypes.WinDLL("./PlayCtrl.dll")
# # # # # except OSError as e:
# # # # #     print(f"加载SDK失败: {e}")
# # # # #     print("请从海康开放平台下载最新Windows SDK: https://open.hikvision.com/download")
# # # # #     sys.exit(1)
# # # # #
# # # # # # 2. 定义常量（部分关键常量）
# # # # # NET_DVR_LOGIN_ERROR = {
# # # # #     1: "用户名或密码错误",
# # # # #     2: "权限不足",
# # # # #     3: "登录超时",
# # # # #     4: "设备不在线",
# # # # #     5: "IP地址错误",
# # # # #     6: "网络连接失败",
# # # # #     7: "端口错误",
# # # # #     8: "设备忙"
# # # # # }
# # # # #
# # # # # # 预置位操作命令
# # # # # GOTO_PRESET = 8  # 调用预置点
# # # # # SET_PRESET = 9  # 设置预置点
# # # # # DEL_PRESET = 10  # 删除预置点
# # # # #
# # # # #
# # # # # # 3. 定义SDK所需的结构体
# # # # # class NET_DVR_DEVICEINFO_V30(Structure):
# # # # #     _fields_ = [
# # # # #         ("sSerialNumber", ctypes.c_byte * 48),
# # # # #         ("byAlarmInPortNum", ctypes.c_byte),
# # # # #         ("byAlarmOutPortNum", ctypes.c_byte),
# # # # #         ("byDiskNum", ctypes.c_byte),
# # # # #         ("byDVRType", ctypes.c_byte),
# # # # #         ("byChanNum", ctypes.c_byte),
# # # # #         ("byStartChan", ctypes.c_byte),
# # # # #         ("byAudioChanNum", ctypes.c_byte),
# # # # #         ("byIPChanNum", ctypes.c_byte),
# # # # #         ("byZeroChanNum", ctypes.c_byte),
# # # # #         ("byMainProto", ctypes.c_byte),
# # # # #         ("bySubProto", ctypes.c_byte),
# # # # #         ("bySupport", ctypes.c_byte),
# # # # #         ("bySupport1", ctypes.c_byte),
# # # # #         ("bySupport2", ctypes.c_byte),
# # # # #         ("wDevType", ctypes.c_uint16),
# # # # #         ("bySupport3", ctypes.c_byte),
# # # # #         ("byMultiStreamProto", ctypes.c_byte),
# # # # #         ("byStartDChan", ctypes.c_byte),
# # # # #         ("byStartDTalkChan", ctypes.c_byte),
# # # # #         ("byHighDChanNum", ctypes.c_byte),
# # # # #         ("bySupport4", ctypes.c_byte),
# # # # #         ("byLanguageType", ctypes.c_byte),
# # # # #         ("byVoiceInChanNum", ctypes.c_byte),
# # # # #         ("byStartVoiceInChanNo", ctypes.c_byte),
# # # # #         ("byRes3", ctypes.c_byte * 2),
# # # # #         ("byMirrorChanNum", ctypes.c_byte),
# # # # #         ("wStartMirrorChanNo", ctypes.c_uint16),
# # # # #         ("byRes2", ctypes.c_byte * 2)
# # # # #     ]
# # # # #
# # # # #
# # # # # # 4. 初始化SDK
# # # # # def init_sdk():
# # # # #     # 设置SDK日志路径 (可选)
# # # # #     hcnetsdk.NET_DVR_SetLogToFile(3, b"./sdk_logs/", True)
# # # # #
# # # # #     # 初始化SDK
# # # # #     if not hcnetsdk.NET_DVR_Init():
# # # # #         error_code = hcnetsdk.NET_DVR_GetLastError()
# # # # #         print(f"SDK初始化失败! 错误码: {error_code}")
# # # # #         return False
# # # # #
# # # # #     # 设置连接超时和重连参数
# # # # #     hcnetsdk.NET_DVR_SetConnectTime(2000, 1)  # 超时2秒，重试1次
# # # # #     hcnetsdk.NET_DVR_SetReconnect(10000, True)  # 10秒重连
# # # # #
# # # # #     print("SDK初始化成功")
# # # # #     return True
# # # # #
# # # # #
# # # # # # 5. 登录设备
# # # # # def login_device(ip, username, password, port=8000):
# # # # #     # 配置登录信息
# # # # #     device_info = NET_DVR_DEVICEINFO_V30()
# # # # #
# # # # #     # 登录设备
# # # # #     user_id = hcnetsdk.NET_DVR_Login_V30(
# # # # #         ip.encode('utf-8'),
# # # # #         port,
# # # # #         username.encode('utf-8'),
# # # # #         password.encode('utf-8'),
# # # # #         byref(device_info)
# # # # #     )
# # # # #
# # # # #     if user_id < 0:
# # # # #         error_code = hcnetsdk.NET_DVR_GetLastError()
# # # # #         error_msg = NET_DVR_LOGIN_ERROR.get(error_code, f"未知错误: {error_code}")
# # # # #         print(f"登录失败! {error_msg}")
# # # # #         return -1
# # # # #
# # # # #     print(f"登录成功! 用户ID: {user_id}")
# # # # #     print(f"设备型号: {bytes(device_info.byDVRType).decode(errors='ignore')}")
# # # # #     print(f"通道数: {device_info.byChanNum}")
# # # # #     return user_id
# # # # #
# # # # #
# # # # # # 6. 预置位操作
# # # # # def control_preset(user_id, channel, preset_id, command):
# # # # #     """
# # # # #     预置位操作
# # # # #     :param user_id: 登录返回的用户ID
# # # # #     :param channel: 通道号 (通常为1)
# # # # #     :param preset_id: 预置位编号 (1-255)
# # # # #     :param command: 操作命令 (GOTO_PRESET/SET_PRESET/DEL_PRESET)
# # # # #     """
# # # # #     if not hcnetsdk.NET_DVR_PTZPreset_Other(user_id, channel, command, preset_id):
# # # # #         error_code = hcnetsdk.NET_DVR_GetLastError()
# # # # #         print(f"预置位操作失败! 错误码: {error_code}")
# # # # #         return False
# # # # #
# # # # #     actions = {GOTO_PRESET: "调用", SET_PRESET: "设置", DEL_PRESET: "删除"}
# # # # #     print(f"预置位{preset_id} {actions.get(command, '操作')}成功!")
# # # # #     return True
# # # # #
# # # # #
# # # # # # 7. 实时视频流回调函数
# # # # # @ctypes.CFUNCTYPE(None, ctypes.c_long, ctypes.c_uint, POINTER(ctypes.c_byte), ctypes.c_uint, ctypes.c_ulong)
# # # # # def real_data_callback(lRealHandle, dwDataType, pBuffer, dwBufSize, pUser):
# # # # #     if dwDataType == 0:  # 原始码流数据
# # # # #         # 这里可以保存或处理视频流
# # # # #         pass
# # # # #
# # # # #
# # # # # # 8. 启动实时视频流
# # # # # def start_real_play(user_id, channel=1):
# # # # #     """
# # # # #     启动实时视频流
# # # # #     :return: 播放句柄
# # # # #     """
# # # # #     # 启动预览
# # # # #     real_handle = hcnetsdk.NET_DVR_RealPlay_V40(
# # # # #         user_id,
# # # # #         byref(ctypes.c_long(channel)),  # 通道号
# # # # #         real_data_callback,
# # # # #         None  # 用户数据
# # # # #     )
# # # # #
# # # # #     if real_handle < 0:
# # # # #         error_code = hcnetsdk.NET_DVR_GetLastError()
# # # # #         print(f"启动实时预览失败! 错误码: {error_code}")
# # # # #         return -1
# # # # #
# # # # #     print(f"实时视频流已启动! 句柄: {real_handle}")
# # # # #     return real_handle
# # # # #
# # # # #
# # # # # # 9. 使用OpenCV显示视频流 (需要额外配置)
# # # # # def display_video_stream(user_id):
# # # # #     # 创建RTSP URL
# # # # #     rtsp_url = f"rtsp://{username}:{password}@{ip}:554/Streaming/Channels/101"
# # # # #
# # # # #     # 使用OpenCV捕获视频流
# # # # #     cap = cv2.VideoCapture(rtsp_url)
# # # # #
# # # # #     if not cap.isOpened():
# # # # #         print("无法打开视频流")
# # # # #         return
# # # # #
# # # # #     print("按 'q' 键退出视频播放")
# # # # #     while True:
# # # # #         ret, frame = cap.read()
# # # # #         if not ret:
# # # # #             print("视频流中断")
# # # # #             break
# # # # #
# # # # #         cv2.imshow('海康摄像头', frame)
# # # # #         if cv2.waitKey(1) & 0xFF == ord('q'):
# # # # #             break
# # # # #
# # # # #     cap.release()
# # # # #     cv2.destroyAllWindows()
# # # # #
# # # # #
# # # # # # 10. 主程序
# # # # # if __name__ == "__main__":
# # # # #     # 设备配置 (修改为您的设备信息)
# # # # #     ip = "192.168.1.64"
# # # # #     username = "admin"
# # # # #     password = "yl202501"
# # # # #     port = 8000
# # # # #
# # # # #     # 初始化SDK
# # # # #     if not init_sdk():
# # # # #         sys.exit(1)
# # # # #
# # # # #     # 登录设备
# # # # #     user_id = login_device(ip, username, password, port)
# # # # #     if user_id < 0:
# # # # #         sys.exit(1)
# # # # #
# # # # #     try:
# # # # #         # 示例1: 调用预置位1
# # # # #         control_preset(user_id, 1, 1, GOTO_PRESET)
# # # # #
# # # # #         # 示例2: 设置预置位2 (当前位置保存为2号预置位)
# # # # #         #control_preset(user_id, 1, 2, SET_PRESET)
# # # # #
# # # # #         # 示例3: 删除预置位3
# # # # #         # control_preset(user_id, 1, 3, DEL_PRESET)
# # # # #
# # # # #         # 启动实时视频流 (可选)
# # # # #         # real_handle = start_real_play(user_id)
# # # # #
# # # # #         # 使用OpenCV显示视频流 (更简单的方式)
# # # # #         #display_video_stream(user_id)
# # # # #
# # # # #     finally:
# # # # #         # 退出登录
# # # # #         hcnetsdk.NET_DVR_Logout(user_id)
# # # # #         # 清理SDK
# # # # #         hcnetsdk.NET_DVR_Cleanup()
# # # #
# # # #
# # # # from PyQt5.QtCore import QThread, pyqtSignal
# # # # import sys
# # # # import time
# # # # from PyQt5.QtWidgets import QApplication, QProgressDialog  # 确保这里包含QProgressDialog
# # # #
# # # # class WorkerThread(QThread):
# # # #     finished = pyqtSignal()
# # # #
# # # #     def long_running_task():
# # # #         """模拟耗时任务"""
# # # #         time.sleep(3)  # 模拟3秒耗时操作
# # # #     def run(self):
# # # #         long_running_task()
# # # #         self.finished.emit()
# # # #
# # # # def long_running_task():
# # # #     """模拟耗时任务"""
# # # #     time.sleep(3)  # 模拟3秒耗时操作
# # # # if __name__ == "__main__":
# # # #     app = QApplication(sys.argv)
# # # #
# # # #     # 创建进度对话框 - 现在QProgressDialog已定义
# # # #     progress = QProgressDialog("正在处理...", "取消", 0, 0, None)
# # # #     progress.setWindowTitle("请稍候")
# # # #     progress.setWindowModality(2)  # 2 = Qt.WindowModal
# # # #     progress.setCancelButton(None)  # 隐藏取消按钮
# # # #     progress.setMinimumDuration(0)  # 立即显示对话框
# # # #     progress.show()
# # # #
# # # #     # 确保UI更新
# # # #     QApplication.processEvents()
# # # #
# # # #     # 执行耗时操作
# # # #     long_running_task()
# # # #
# # # #     # 关闭进度对话框
# # # #     progress.close()
# # # #
# # # #     sys.exit(app.exec_())
# # # from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
# # # from PyQt5.QtCore import QTimer
# # #
# # # class LongPressButton(QPushButton):
# # #     def __init__(self, text="Press Me", parent=None):
# # #         super().__init__(text, parent)
# # #         self.long_press_threshold = 1000  # 长按时间阈值（毫秒）
# # #         self.timer = QTimer(self)
# # #         self.timer.timeout.connect(self._on_long_press)
# # #         self.is_pressed = False  # 标记按钮是否被按下
# # #
# # #     def mousePressEvent(self, event):
# # #         """按钮按下时启动计时器"""
# # #         super().mousePressEvent(event)
# # #         self.is_pressed = True
# # #         self.timer.start(self.long_press_threshold)  # 启动计时器
# # #
# # #     def mouseReleaseEvent(self, event):
# # #         """按钮释放时停止计时器"""
# # #         super().mouseReleaseEvent(event)
# # #         self.timer.stop()  # 停止计时器
# # #         if self.is_pressed:
# # #             # 如果按下时间不足阈值，视为短按
# # #             print("Short press")
# # #         self.is_pressed = False
# # #
# # #     def _on_long_press(self):
# # #         """计时器超时，触发长按事件"""
# # #         #self.timer.stop()
# # #         if self.is_pressed:
# # #             print("Long press detected!")
# # #             # 在这里执行长按操作
# # #             #self.is_pressed = False  # 防止重复触发
# # #
# # # if __name__ == "__main__":
# # #     app = QApplication([])
# # #     window = QWidget()
# # #     layout = QVBoxLayout()
# # #
# # #     btn = LongPressButton("Press and Hold")
# # #     layout.addWidget(btn)
# # #
# # #     window.setLayout(layout)
# # #     window.show()
# # #     app.exec_()
# #
# # s = "G1 F2400 #535345"
# # parts = s.split()  # 分割字符串
# #
# # f_value = None
# # e_value = None
# #
# # for part in parts:
# #     if part.startswith('F'):
# #         f_value = float(part[1:])  # 提取F后内容并转为数值
# #     elif part.startswith('E'):
# #         e_value = float(part[1:])  # 提取E后内容并转为数值
# #
# # print("F 后面的值:", f_value)  # 输出: 2400.0
# # print("E 后面的值:", e_value)  # 输出: -3.0
#
# class StringList:
#     def __init__(self, initial_list=None):
#         """
#         初始化字符串列表
#         :param initial_list: 初始列表（可选），默认为空列表
#         """
#         self.items = initial_list[:] if initial_list else []
#
#     def append(self, string):
#         """
#         在列表末尾添加字符串
#         :param string: 要添加的字符串
#         """
#         self.items.append(string)
#
#     def insert(self, index, string):
#         """
#         在指定位置插入字符串
#         :param index: 插入位置的索引
#         :param string: 要插入的字符串
#         """
#         if index < 0:
#             index = 0
#         elif index > len(self.items):
#             index = len(self.items)
#         self.items.insert(index, string)
#
#     def remove(self, string):
#         """
#         删除列表中第一个匹配的字符串
#         :param string: 要删除的字符串
#         :return: 成功删除返回True，未找到返回False
#         """
#         if string in self.items:
#             self.items.remove(string)
#             return True
#         return False
#
#     def remove_all(self, string):
#         """
#         删除列表中所有匹配的字符串
#         :param string: 要删除的字符串
#         :return: 删除的元素数量
#         """
#         count = self.items.count(string)
#         self.items = [item for item in self.items if item != string]
#         return count
#
#     def remove_at(self, index):
#         """
#         删除指定索引位置的元素
#         :param index: 要删除的元素的索引
#         :return: 被删除的元素
#         :raises IndexError: 如果索引超出范围
#         """
#         if 0 <= index < len(self.items):
#             return self.items.pop(index)
#         raise IndexError("Index out of range")
#
#     def contains(self, string):
#         """
#         判断列表中是否包含指定字符串
#         :param string: 要查找的字符串
#         :return: 存在返回True，否则返回False
#         """
#         return string in self.items
#
#     def count(self, string):
#         """
#         统计指定字符串在列表中出现的次数
#         :param string: 要统计的字符串
#         :return: 出现次数
#         """
#         return self.items.count(string)
#
#     def index_of(self, string):
#         """
#         查找指定字符串的索引
#         :param string: 要查找的字符串
#         :return: 第一个匹配项的索引，未找到返回-1
#         """
#         try:
#             return self.items.index(string)
#         except ValueError:
#             return -1
#
#     def clear(self):
#         """清空列表"""
#         self.items.clear()
#
#     def size(self):
#         """返回列表中的元素数量"""
#         return len(self.items)
#
#     def is_empty(self):
#         """判断列表是否为空"""
#         return len(self.items) == 0
#
#     def to_list(self):
#         """返回列表的副本"""
#         return self.items[:]
#
#     def __str__(self):
#         """返回列表的字符串表示"""
#         return str(self.items)
#
#     def __contains__(self, string):
#         """支持 in 操作符"""
#         return string in self.items
#
#     def __len__(self):
#         """支持 len() 函数"""
#         return len(self.items)
#
#
# # 示例用法
# if __name__ == "__main__":
#     # 创建字符串列表
#     fruits = StringList([])
#     print("初始列表:", fruits)
#
#     # 添加元素
#     fruits.append("date")
#     fruits.insert(1, "grape")
#     print("添加后:", fruits)
#
#     # 删除元素
#     fruits.remove("banana")
#     print("删除banana后:", fruits)
#
#     # 添加重复元素
#     fruits.append("apple")
#     fruits.append("apple")
#     print("添加重复apple后:", fruits)
#
#     # 删除所有匹配项
#     removed_count = fruits.remove_all("apple")
#     print(f"删除了 {removed_count} 个apple")
#     print("删除所有apple后:", fruits)
#
#     # 检查元素存在性
#     print("'cherry' 存在吗?", fruits.contains("cherry"))
#     print("'orange' 存在吗?", fruits.contains("orange"))
#     print("'date' 在列表中吗?", "date" in fruits)  # 使用 in 操作符
#
#     # 索引操作
#     index = fruits.index_of("cherry")
#     print("'cherry' 的索引位置:", index)
#
#     # 按索引删除
#     removed_item = fruits.remove_at(0)
#     print(f"删除了索引0的元素: '{removed_item}'")
#     print("删除后:", fruits)
#
#     # 其他操作
#     print("列表大小:", fruits.size())
#     print("列表为空吗?", fruits.is_empty())
#
#     # 清空列表
#     fruits.clear()
#     print("清空后:", fruits)
#     print("列表为空吗?", fruits.is_empty())

import sys
import winreg
import ctypes
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGroupBox, QRadioButton, QScrollArea,
    QDesktopWidget, QMessageBox
)
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import Qt, QSize


class DisplayScalingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Windows 显示缩放设置助手")
        self.setWindowIcon(QIcon(self.create_scaling_icon()))
        self.setMinimumSize(800, 600)

        # 获取当前缩放比例
        self.current_scaling = self.get_current_scaling()

        # 创建主界面
        self.init_ui()

        # 设置窗口居中
        self.center_window()

    def center_window(self):
        """将窗口居中显示"""
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2,
                  (screen.height() - size.height()) // 2)

    def create_scaling_icon(self):
        """创建一个简单的缩放图标"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)

        return pixmap

    def get_current_scaling(self):
        """获取当前系统缩放比例"""
        try:
            # 获取主显示器的DPI
            user32 = ctypes.windll.user32
            hdc = user32.GetDC(0)
            dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSY
            user32.ReleaseDC(0, hdc)

            # 计算缩放比例
            scaling = round(dpi / 96 * 100)

            # 映射到Windows的标准选项
            options = [100, 125, 150, 175, 200, 225, 250]
            closest = min(options, key=lambda x: abs(x - scaling))
            return closest
        except:
            return 100

    def set_scaling(self, scaling):
        """设置缩放比例（需要管理员权限）"""
        try:
            # 计算DPI值 (100% = 96)
            dpi = int(96 * (scaling / 100))

            # 打开注册表
            key_path = r"Control Panel\Desktop"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)

            # 设置DPI值
            winreg.SetValueEx(key, "LogPixels", 0, winreg.REG_DWORD, dpi)

            # 设置其他相关值
            winreg.SetValueEx(key, "Win8DpiScaling", 0, winreg.REG_DWORD, 1)

            # 关闭注册表
            winreg.CloseKey(key)

            # 提示用户需要注销
            QMessageBox.information(
                self,
                "设置成功",
                f"已成功设置缩放比例为 {scaling}%！\n\n"
                "为使更改生效，您需要注销并重新登录Windows。\n"
                "是否现在注销？",
                QMessageBox.Yes | QMessageBox.No
            )

            return True
        except Exception as e:
            QMessageBox.critical(
                self,
                "设置失败",
                f"无法更改缩放设置：{str(e)}\n\n"
                "请确保以管理员身份运行此程序。"
            )
            return False

    def open_windows_settings(self):
        """打开Windows显示设置"""
        try:
            subprocess.Popen("ms-settings:display")
        except:
            QMessageBox.warning(
                self,
                "无法打开设置",
                "无法打开Windows显示设置，请手动打开设置应用。"
            )

    def create_scaling_option(self, value, description):
        """创建一个缩放选项控件"""
        group = QGroupBox(f"{value}% - {description}")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #0078D7;
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 24px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        layout = QVBoxLayout()

        # 添加描述标签
        if value == 100:
            desc = "标准大小 - 推荐用于1920×1080分辨率"
        elif value == 125:
            desc = "中等放大 - 推荐用于2K分辨率显示器"
        elif value == 150:
            desc = "较大放大 - 推荐用于4K分辨率显示器"
        else:
            desc = f"{value}% 缩放比例"

        label = QLabel(desc)
        label.setWordWrap(True)
        label.setStyleSheet("font-size: 13px;")
        layout.addWidget(label)

        # 添加预览图像
        preview = QLabel()
        pixmap = QPixmap(f":/preview_{value}.png")  # 在实际应用中替换为真实图片
        if pixmap.isNull():
            # 创建占位图像
            pixmap = QPixmap(300, 150)
            pixmap.fill(Qt.white)
            # 添加文本
            painter = QPainter(pixmap)
            painter.setFont(QFont("Arial", 12))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, f"{value}% 缩放预览")
            painter.end()
        preview.setPixmap(pixmap.scaledToWidth(300))
        preview.setAlignment(Qt.AlignCenter)
        layout.addWidget(preview)

        # 添加单选按钮
        radio = QRadioButton(f"选择 {value}% 缩放")
        radio.setStyleSheet("font-size: 13px;")
        radio.setChecked(value == self.current_scaling)
        radio.value = value
        radio.toggled.connect(lambda checked, v=value: self.on_scaling_selected(v) if checked else None)

        layout.addWidget(radio)
        group.setLayout(layout)

        return group

    def on_scaling_selected(self, value):
        """当选择缩放比例时"""
        self.selected_scaling = value

    def init_ui(self):
        """初始化用户界面"""
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title = QLabel("显示缩放设置")
        title_font = QFont("Arial", 20, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #0078D7;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # 当前设置信息
        info = QLabel(f"当前缩放设置: {self.current_scaling}%")
        info.setFont(QFont("Arial", 12))
        info.setStyleSheet("background-color: #F0F8FF; padding: 10px; border-radius: 5px;")
        info.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(info)

        # 添加说明
        instructions = QLabel(
            "更改文本、应用和其他项目的大小。\n"
            "选择缩放比例以获得最佳显示效果。"
        )
        instructions.setFont(QFont("Arial", 11))
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #555555;")
        main_layout.addWidget(instructions)

        # 创建滚动区域用于缩放选项
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(10)

        # 添加缩放选项
        scaling_options = [
            (100, "推荐"),
            (125, "推荐"),
            (150, "推荐"),
            (175, "较大"),
            (200, "非常大"),
            (225, "非常大"),
            (250, "非常大")
        ]

        for value, desc in scaling_options:
            option = self.create_scaling_option(value, desc)
            scroll_layout.addWidget(option)

        # 添加占位符以填充空间
        scroll_layout.addStretch()

        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)  # 1 表示扩展

        # 按钮区域
        button_layout = QHBoxLayout()

        # 打开Windows设置按钮
        win_settings_btn = QPushButton("打开Windows显示设置")
        win_settings_btn.setIcon(QIcon.fromTheme("preferences-system"))
        win_settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #E1E1E1;
                border: 1px solid #B0B0B0;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #D0D0D0;
            }
        """)
        win_settings_btn.clicked.connect(self.open_windows_settings)
        button_layout.addWidget(win_settings_btn)

        button_layout.addStretch()

        # 应用按钮
        apply_btn = QPushButton("应用缩放设置")
        apply_btn.setIcon(QIcon.fromTheme("dialog-ok"))
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                border-radius: 5px;
                padding: 8px 24px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0066B4;
            }
            QPushButton:disabled {
                background-color: #A0A0A0;
            }
        """)
        apply_btn.clicked.connect(self.apply_scaling)
        button_layout.addWidget(apply_btn)

        main_layout.addLayout(button_layout)

        main_widget.setLayout(main_layout)

        # 初始化选中的缩放比例
        self.selected_scaling = self.current_scaling

    def apply_scaling(self):
        """应用选中的缩放比例"""
        if self.selected_scaling == self.current_scaling:
            QMessageBox.information(
                self,
                "无需更改",
                f"当前缩放比例已经是 {self.selected_scaling}%，无需更改。"
            )
            return

        if QMessageBox.question(
                self,
                "确认更改",
                f"您确定要将缩放比例更改为 {self.selected_scaling}% 吗？\n\n"
                "注意：更改后需要注销并重新登录Windows才能使设置生效。",
                QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            self.set_scaling(self.selected_scaling)


if __name__ == "__main__":
    # 检查管理员权限
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False

    if not is_admin:
        # 请求管理员权限
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()

    app = QApplication(sys.argv)
    window = DisplayScalingApp()
    window.show()
    sys.exit(app.exec_())