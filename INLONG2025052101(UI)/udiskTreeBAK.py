# import os
# import ctypes
# import string
#
#
# def get_usb_drives():
#     """获取所有U盘盘符"""
#     drives = []
#     bitmask = ctypes.windll.kernel32.GetLogicalDrives()
#     for letter in string.ascii_uppercase:
#         if bitmask & 1:
#             drive = letter + ':\\'
#             if ctypes.windll.kernel32.GetDriveTypeW(drive) == 2:  # DRIVE_REMOVABLE
#                 drives.append(drive)
#         bitmask >>= 1
#     return drives
#
# def get_all_directories(drive):
#     """获取指定驱动器中的所有目录"""
#     directories = []
#     for root, dirs, files in os.walk(drive):
#         for dir_name in dirs:
#             directories.append(os.path.join(root, dir_name))
#     return directories
#
#
# if __name__ == "__main__":
#     # 获取所有U盘
#     usb_drives = get_usb_drives()
#
#     if not usb_drives:
#         print("没有检测到U盘")
#     else:
#         for drive in usb_drives:
#             print(f"\n正在扫描U盘 {drive}...")
#             try:
#                 dirs = get_all_directories(drive)
#                 print(f"找到 {len(dirs)} 个目录:")
#                 for i, dir_path in enumerate(dirs[:10]):  # 只显示前10个目录
#                     print(f"  {i + 1}. {dir_path}")
#                 if len(dirs) > 10:
#                     print(f"  ...(共 {len(dirs)} 个目录)")
#             except Exception as e:
#                 print(f"扫描U盘 {drive} 时出错: {e}")
import os
import sys
import ctypes
import string
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTreeView,
                             QVBoxLayout, QWidget, QLabel, QPushButton,
                             QHeaderView, QMenu, QLineEdit, QHBoxLayout)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtCore import Qt


class USBFileExplorer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('U盘文件浏览器')
        self.setGeometry(300, 300, 800, 600)

        # 创建UI组件
        self.tree_view = QTreeView()
        self.refresh_btn = QPushButton('刷新')
        self.status_label = QLabel('准备就绪')
        self.path_label = QLabel('当前选中: 无')
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入文件名搜索...")

        # 设置树形视图
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['U盘文件结构'])
        self.tree_view.setModel(self.model)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setSelectionBehavior(QTreeView.SelectRows)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        self.tree_view.clicked.connect(self.show_selected_path)  # 新增点击事件

        # 设置图标
        self.folder_icon = QIcon.fromTheme("folder")
        self.file_icon = QIcon.fromTheme("text-x-generic")

        # 布局
        main_layout = QVBoxLayout()

        # 搜索框布局
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(self.refresh_btn)

        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.tree_view)
        main_layout.addWidget(self.path_label)
        main_layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # 连接信号
        self.refresh_btn.clicked.connect(self.refresh_usb_tree)

        # 初始刷新
        self.refresh_usb_tree()

    def get_usb_drives(self):
        """获取所有U盘盘符"""
        drives = []
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drive = letter + ':\\'
                if ctypes.windll.kernel32.GetDriveTypeW(drive) == 2:  # DRIVE_REMOVABLE
                    drives.append(drive)
            bitmask >>= 1
        return drives

    def populate_tree(self, parent_item, path):
        """递归填充树形结构，包含文件和目录"""
        try:
            for entry in os.scandir(path):
                if entry.is_dir():
                    # 添加目录项
                    dir_item = QStandardItem(self.folder_icon, entry.name)
                    dir_item.setData(entry.path, Qt.UserRole + 1)
                    parent_item.appendRow(dir_item)
                    self.populate_tree(dir_item, entry.path)  # 递归处理子目录
                else:
                    # 添加文件项
                    file_item = QStandardItem(self.file_icon, entry.name)
                    file_item.setData(entry.path, Qt.UserRole + 1)
                    parent_item.appendRow(file_item)
        except PermissionError:
            error_item = QStandardItem("无权限访问")
            error_item.setForeground(Qt.red)
            parent_item.appendRow(error_item)
        except Exception as e:
            error_item = QStandardItem(f"访问错误: {str(e)}")
            error_item.setForeground(Qt.red)
            parent_item.appendRow(error_item)

    def refresh_usb_tree(self):
        """刷新U盘树形列表"""
        self.model.clear()

        usb_drives = self.get_usb_drives()
        if not usb_drives:
            self.status_label.setText("没有检测到U盘")
            self.path_label.setText("当前选中: 无")
            return

        self.status_label.setText(f"找到 {len(usb_drives)} 个U盘，正在加载...")
        QApplication.processEvents()  # 更新UI

        for drive in usb_drives:
            drive_item = QStandardItem(self.folder_icon, drive)
            drive_item.setData(drive, Qt.UserRole + 1)
            self.model.appendRow(drive_item)
            self.populate_tree(drive_item, drive)

        self.status_label.setText(f"加载完成，共 {len(usb_drives)} 个U盘")
        self.tree_view.expandToDepth(1)  # 默认展开第一层

    def show_selected_path(self, index):
        """显示当前选中项的路径"""
        path = self.get_selected_path()
        if path:
            if os.path.isdir(path):
                self.path_label.setText(f"当前选中目录: {path}")
            else:
                filename = os.path.basename(path)
                self.path_label.setText(f"当前选中文件: {filename}\n完整路径: {path}")
        else:
            self.path_label.setText("当前选中: 无")

    def get_selected_path(self):
        """获取当前选中项的完整路径"""
        selected_indexes = self.tree_view.selectedIndexes()
        if not selected_indexes:
            return None

        selected_item = self.model.itemFromIndex(selected_indexes[0])
        return selected_item.data(Qt.UserRole + 1)

    def get_selected_file_info(self):
        """获取选中文件的路径和文件名信息"""
        path = self.get_selected_path()
        if not path:
            return None, None

        return path, os.path.basename(path)

    def show_context_menu(self, position):
        """显示右键菜单"""
        index = self.tree_view.indexAt(position)
        if not index.isValid():
            return

        item = self.model.itemFromIndex(index)
        path = item.data(Qt.UserRole + 1)

        menu = QMenu()

        if os.path.isdir(path):
            open_action = menu.addAction("打开目录")
            menu.addSeparator()
        else:
            open_action = menu.addAction("打开文件")
            menu.addSeparator()
            copy_path_action = menu.addAction("复制文件路径")

        refresh_action = menu.addAction("刷新")
        menu.addSeparator()
        properties_action = menu.addAction("属性")

        action = menu.exec_(self.tree_view.viewport().mapToGlobal(position))

        if action == open_action:
            os.startfile(path)  # Windows下打开文件或目录
        elif action == copy_path_action:
            clipboard = QApplication.clipboard()
            clipboard.setText(path)
            self.status_label.setText("已复制文件路径到剪贴板")
        elif action == refresh_action:
            parent_item = item.parent() or item
            parent_path = parent_item.data(Qt.UserRole + 1)
            parent_item.removeRows(0, parent_item.rowCount())
            self.populate_tree(parent_item, parent_path)
            self.tree_view.expand(index.parent())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    explorer = USBFileExplorer()
    explorer.show()
    sys.exit(app.exec_())