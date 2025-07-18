import re
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QTextEdit, QFileDialog,
                             QMessageBox, QCheckBox, QGroupBox, QDoubleSpinBox)


class GcodeFilterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("英龙智造科技(南京)有限公司Gcode Z坐标拼接工具")
        self.setGeometry(600, 200, 800, 600)

        # 主部件和布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # 文件选择区域
        file_layout = QHBoxLayout()
        self.file_label = QLabel("未选择文件")
        file_button = QPushButton("导入Gcode文件")
        file_button.setFixedSize(150, 60)  # 推荐使用这个方法
        file_button.clicked.connect(self.open_file)
        file_layout.addWidget(self.file_label, 4)
        file_layout.addWidget(file_button, 1)

        # Z坐标输入区域
        z_layout = QHBoxLayout()
        z_layout.addWidget(QLabel("Z坐标阈值:"))
        self.z_input = QDoubleSpinBox()
        self.z_input.setDecimals(3)  # 3位小数精度
        self.z_input.setRange(-1000.0, 1000.0)
        self.z_input.setValue(0.0)
        z_layout.addWidget(self.z_input)

        # 容差设置区域
        tolerance_layout = QHBoxLayout()
        tolerance_layout.addWidget(QLabel("容差范围 (±):"))
        self.tolerance_input = QDoubleSpinBox()
        self.tolerance_input.setDecimals(3)
        self.tolerance_input.setRange(0.001, 1.0)
        self.tolerance_input.setValue(0.01)  # 默认容差0.01
        self.tolerance_input.setSingleStep(0.001)
        tolerance_layout.addWidget(self.tolerance_input)

        # G命令选项区域
        gcode_group = QGroupBox("处理哪些G命令?")
        gcode_layout = QVBoxLayout()
        self.g0_check = QCheckBox("G0 (快速移动)")
        self.g0_check.setChecked(True)
        self.g1_check = QCheckBox("G1 (线性移动)")
        self.g1_check.setChecked(True)
        self.g2g3_check = QCheckBox("G2/G3 (圆弧移动)")
        self.g2g3_check.setChecked(True)
        gcode_layout.addWidget(self.g0_check)
        gcode_layout.addWidget(self.g1_check)
        gcode_layout.addWidget(self.g2g3_check)
        gcode_group.setLayout(gcode_layout)

        # 处理按钮
        process_button = QPushButton("处理并保存文件")
        process_button.setFixedSize(800, 80)  # 推荐使用这个方法
        process_button.clicked.connect(self.process_file)

        # 日志显示区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("操作日志将显示在这里...")

        # 添加到主布局
        main_layout.addLayout(file_layout)
        main_layout.addLayout(z_layout)
        main_layout.addLayout(tolerance_layout)
        main_layout.addWidget(gcode_group)
        main_layout.addWidget(process_button)
        main_layout.addWidget(self.log_area)

        # 文件路径变量
        self.file_path = ""

        # 状态栏
        self.statusBar().showMessage("就绪")

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Gcode文件", "", "Gcode文件 (*.gcode *.gco *.g);;所有文件 (*.*)"
        )
        if file_path:
            self.file_path = file_path
            self.file_label.setText(file_path.split("/")[-1])
            self.log_area.append(f"已导入文件: {file_path}")

    def process_file(self):
        # 验证输入
        if not self.file_path:
            QMessageBox.warning(self, "警告", "请先选择Gcode文件")
            return

        # 获取Z阈值和容差
        z_threshold = self.z_input.value()
        tolerance = self.tolerance_input.value()

        # 检查是否选择了至少一种G命令
        if not (self.g0_check.isChecked() or
                self.g1_check.isChecked() or
                self.g2g3_check.isChecked()):
            QMessageBox.warning(self, "警告", "请至少选择一种要处理的G命令类型")
            return

        # 构建G命令正则表达式
        gcode_patterns = []
        if self.g0_check.isChecked():
            gcode_patterns.append(r'[gG]0?\b')  # 匹配 G0 或 G0
        if self.g1_check.isChecked():
            gcode_patterns.append(r'[gG]1?\b')  # 匹配 G1 或 G1
        if self.g2g3_check.isChecked():
            gcode_patterns.append(r'[gG][23]\b')  # 匹配 G2 或 G3

        gcode_regex = re.compile('|'.join(gcode_patterns))
        z_pattern = re.compile(r'[zZ](-?\d*\.?\d+)')
        x_pattern = re.compile(r'[xX](-?\d*\.?\d+)')
        y_pattern = re.compile(r'[yY](-?\d*\.?\d+)')
        e_pattern = re.compile(r'[eE](-?\d*\.?\d+)')

        # 读取文件内容
        try:
            with open(self.file_path, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            self.log_area.append(f"读取文件错误: {str(e)}")
            return

        # 处理文件
        saved_lines = []
        removed_count = 0
        search_exist=False
        z_match=0
        x_match=0
        y_match=0
        e_match=0
        pre_z_match=0
        pre_x_match=0
        pre_y_match=0
        pre_e_match=0
        for line in lines:
            original_line = line.strip()
            if not original_line:
                saved_lines.append(line)
                continue
            if not search_exist:

                # 检查是否为选中的G命令类型
                if gcode_regex.search(original_line):
                    # 查找Z坐标值
                    z_match = z_pattern.search(original_line)
                    x_match = x_pattern.search(original_line)
                    y_match = y_pattern.search(original_line)
                    e_match = e_pattern.search(original_line)

                    if z_match:
                        try:
                            z_value = float(z_match.group(1))
                            # 使用容差范围检查Z值
                            if (z_threshold - tolerance)<z_value < (z_threshold + tolerance):
                                removed_count += 1
                                search_exist=True
                                saved_lines.append('M107 \n')
                                saved_lines.append('G1 F3000 \n')
                                saved_lines.append('G28 X\n')
                                saved_lines.append('G28 Y\n')
                                #cmd = f'G92 X{float(pre_x_match.group(1))} Y{float(pre_y_match.group(1))}\n'
                                #saved_lines.append(cmd)
                                cmd = f'G92 E{float(pre_e_match.group(1))} \n'
                                saved_lines.append(cmd)
                                saved_lines.append(line)
                                continue
                            else:
                                if z_pattern.search(original_line) is not None:
                                    pre_z_match =z_pattern.search(original_line)
                                if x_pattern.search(original_line) is not None:
                                    pre_x_match =x_pattern.search(original_line)
                                if y_pattern.search(original_line) is not None:
                                    pre_y_match =y_pattern.search(original_line)
                                if e_pattern.search(original_line) is not None:
                                    pre_e_match =e_pattern.search(original_line)

                        except ValueError:
                            pass  # 保持无法解析的行
                    else:
                        if e_pattern.search(original_line) is not None:
                            pre_e_match = e_pattern.search(original_line)

            else:
                # 保留该行
                saved_lines.append(line)

        # 保存文件
        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存处理后的文件", self.file_path.replace('.gcode', '_filtered.gcode'),
            "Gcode文件 (*.gcode *.gco *.g);;所有文件 (*.*)"
        )

        if not save_path:
            return  # 用户取消保存

        try:
            with open(save_path, 'w') as f:
                f.writelines(saved_lines)
            self.log_area.append(f"文件处理完成! 已移除 {removed_count} 行")
            self.log_area.append(f"Z阈值: {z_threshold} ± {tolerance}")
            self.log_area.append(f"已保存到: {save_path}")
            QMessageBox.information(self, "完成", "文件处理并保存成功!")
        except Exception as e:
            self.log_area.append(f"保存文件错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"保存文件时出错: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GcodeFilterApp()
    window.show()
    sys.exit(app.exec_())