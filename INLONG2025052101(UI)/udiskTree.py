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
                             QHeaderView, QMenu, QLineEdit, QHBoxLayout, QGroupBox, QAbstractItemView, QFrame)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon, QFont
from PyQt5.QtCore import Qt, QObject


class USBFileExplorer(QGroupBox):

    def __init__(self, groupbox, title=None, headers=None, parent=None):
        """
        在指定的 QGroupBox 上创建 QTreeView

        参数:
            groupbox (QGroupBox): 要放置树形视图的GroupBox容器
            title (str): GroupBox标题(如果为空则使用原GroupBox标题)
            headers (list): 列标题列表
            parent (QWidget): 父组件
        """
        super().__init__(parent)
        self.selectfilename=''
        # 保存对原始GroupBox的引用
        self.groupbox = groupbox

        # 设置标题(如果提供了新标题)
        if title:
            self.groupbox.setTitle(title)

        # 创建布局(如果原GroupBox没有布局)
        if self.groupbox.layout() is None:
            self.groupbox.setLayout(QVBoxLayout())
            self.groupbox.layout().setContentsMargins(5, 15, 5, 5)

        # 创建树形视图
        self.tree_view = QTreeView()
        self.tree_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tree_view.setAlternatingRowColors(True)
        # 其他视觉效果优化
        self.tree_view.setHeaderHidden(True)  # 隐藏标题

        # 创建模型
        # 设置树形视图
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['U盘文件结构'])
        self.tree_view.setModel(self.model)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setSelectionBehavior(QTreeView.SelectRows)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        #self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        self.tree_view.clicked.connect(self.show_selected_path)  # 新增点击事件
        # 添加到GroupBox布局
        self.groupbox.layout().addWidget(self.tree_view)
        # 设置图标
        self.folder_icon = QIcon.fromTheme("folder")
        self.file_icon = QIcon.fromTheme("text-x-generic")

        # # 连接信号
        # self.refresh_btn.clicked.connect(self.refresh_usb_tree)
        # # 初始刷新
        self.refresh_usb_tree()

    def apply_styles(self):
        # 禁用交替行颜色
        self.tree_view.setAlternatingRowColors(False)
        self.tree_view.setFont(QFont("", 15))
        self.tree_view.setSelectionMode(QTreeView.SingleSelection)
        self.tree_view.setAnimated(True)        # 设置整体透明样式表
        # 设置样式表：统一选中状态颜色
        self.tree_view.setStyleSheet("""
                    QTreeView {
                        border-radius: 8px;
                        border: 3px solid rgba(255, 255, 255, 0.2);
                        background-color: rgba(255, 255, 255, 0.1);
                        padding: 1px;  /* 避免文字贴边 */
                        outline: 0;
                    }
                    QTreeView::item {
                        background: transparent;
                        color: white;
                        padding: 1px;
                    }
                    QTreeView::item:selected:active,
                    QTreeView::item:selected:!active {
                        background: rgba(255, 255, 255, 0.3);  /* 选中项高亮 */
                        color: black;
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
                    
                    /* ===== 垂直滚动条样式 ===== */
                    QScrollBar:vertical {
                        width: 25px;  /* 加宽滚动条宽度 */
                        background: rgba(255, 255, 255, 0.3);
                        border: 1px solid rgba(80, 100, 140, 150);
                        border-radius: 6px;
                        margin: 2px;
                    }
                    
                    /* 垂直滚动条滑块 */
                    QScrollBar::handle:vertical {
                        background: rgba(120, 150, 220, 180);
                        border-radius: 5px;
                        min-height: 40px;  /* 滑块最小高度 */
                    }
                    
                    /* 垂直滚动条滑块悬停 */
                    QScrollBar::handle:vertical:hover {
                        background: rgba(150, 180, 240, 220);
                    }
                    
                    /* 垂直滚动条滑块按下 */
                    QScrollBar::handle:vertical:pressed {
                        background: rgba(100, 130, 200, 200);
                    }
                    
                    /* 垂直滚动条向上箭头 */
                    QScrollBar::sub-line:vertical {
                        height: 20px;
                        subcontrol-position: top;
                        subcontrol-origin: margin;
                        background: rgba(70, 90, 130, 180);
                        border-top-left-radius: 5px;
                        border-top-right-radius: 5px;
                    }
                    
                    /* 垂直滚动条向下箭头 */
                    QScrollBar::add-line:vertical {
                        height: 20px;
                        subcontrol-position: bottom;
                        subcontrol-origin: margin;
                        background: rgba(70, 90, 130, 180);
                        border-bottom-left-radius: 5px;
                        border-bottom-right-radius: 5px;
                    }
                    
                    /* 垂直滚动条箭头悬停 */
                    QScrollBar::sub-line:vertical:hover,
                    QScrollBar::add-line:vertical:hover {
                        background: rgba(90, 110, 150, 200);
                    }
                    
                    /* 垂直滚动条箭头图标 */
                    QScrollBar::up-arrow:vertical,
                    QScrollBar::down-arrow:vertical {
                        width: 25px;
                        height: 25px;
                        background: rgba(255, 255, 255, 0.3);
                    }
                    
                    /* 滚动条空白区域 */
                    QScrollBar::add-page:vertical, 
                    QScrollBar::sub-page:vertical {
                        background: transparent;
                    }
                    
                    /* ===== 水平滚动条样式 ===== */
                    QScrollBar:horizontal {
                        height: 18px;
                        background: rgba(40, 45, 60, 180);
                        border: 1px solid rgba(80, 100, 140, 150);
                        border-radius: 6px;
                        margin: 2px;
                    }
                """)

        # 关键属性设置
        self.tree_view.setAttribute(Qt.WA_TranslucentBackground)  # 启用透明背景
        self.tree_view.viewport().setAttribute(Qt.WA_TranslucentBackground)  # 视口透明
        self.tree_view.setFrameShape(QFrame.NoFrame)  # 移除边框

        # 其他视觉效果优化
        self.tree_view.setHeaderHidden(True)  # 隐藏标题
        self.tree_view.setIndentation(30)  # 缩进大小
        self.tree_view.setAnimated(True)  # 启用动画
        self.tree_view.setAutoFillBackground(False)  # 禁止自动填充背景
        # 启用滚动条始终可见（可选）
        self.tree_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tree_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

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
                    if  entry.name.lower().endswith('.gcode'):
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
        self.apply_styles()
        model = self.tree_view.model()
        if model:  # 检查模型是否存在
            model.removeRows(0, model.rowCount())  # 删除所有行
        usb_drives = self.get_usb_drives()
        if not usb_drives:
            return
        QApplication.processEvents()  # 更新UI
        for drive in usb_drives:
            drive_item = QStandardItem(self.folder_icon, drive)
            drive_item.setData(drive, Qt.UserRole + 1)
            self.model.appendRow(drive_item)
            self.populate_tree(drive_item, drive)

        self.apply_styles()
        #self.tree_view.collapse_all()
        self.tree_view.expandToDepth(0)  # 默认展开第一层
    def show_selected_path(self, index):
        """显示当前选中项的路径"""
        path = self.get_selected_path()
        if path:
            if os.path.isdir(path):
                print(f"当前选中目录: {path}")
            else:
                filename = os.path.basename(path)
                self.selectfilename=filename
        else:
            print("当前选中: 无")

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