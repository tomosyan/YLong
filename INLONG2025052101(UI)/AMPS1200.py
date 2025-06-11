import ctypes
import queue
import re
import subprocess
import threading
import time
from shutil import copyfile

import cv2
import numpy as np

from setup import Ui_MainWindow
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QButtonGroup, QListWidgetItem, QLabel
import psutil
import os
import gcoder
import printcore
from loguru import logger
from serial import SerialException
from Operational_sqlite import Sqlite
from gcodefile_main import ui_dialog_file
from log_main import ui_dialog_log
from keboard_main import ui_dialog

from HCNetSDK import *
from PlayCtrl import *
import re

# 查找内存泄漏
# leaking_objects = objgraph.show_backrefs(objgraph.by_type('str'), max_depth=5)
# print(leaking_objects)
logger.add("./Log/AMS_Log/file_{time}.log", format="{time} {level} {message}", level="DEBUG", rotation="00:00",
           retention="15 days", filter=lambda record: record["extra"].get("name") == "a", catch=True, enqueue=True)

logger_a = logger.bind(name="a")
logger_d = logger.bind(name="d")
Operational_Sqlite = Sqlite()
##调试开关
DEBUG =0
class FrameProcessor(QObject):
    update_signal = pyqtSignal(QPixmap)  # 用于跨线程更新UI的信号

    def __init__(self):
        super().__init__()
        self.frame_queue = queue.Queue(maxsize=5)  # 限制队列大小防止内存爆炸
        self.running = True
        self.processing_thread = threading.Thread(target=self.process_frames)
        self.processing_thread.start()
        self.g_width=0
        self.g_height=0
        self.myobject=None
    def setSize(self,object):
        self.g_width=object.width()
        self.g_height=object.height()
        self.myobject=object
    def yuv_to_rgb(self,yuv_data, width, height):
        # 将YUV数据转换为RGB格式
        yuv_image = np.frombuffer(yuv_data, dtype=np.uint8).reshape((height * 3 // 2, width))
        bgr_image = cv2.cvtColor(yuv_image, cv2.COLOR_YUV2RGB_I420)
        return bgr_image

    def bgr_to_qimage(self,bgr_data,nwidth,nheight):
        # 将BGR数据转换为QImage对象
        height, width, channel = bgr_data.shape
        bytes_per_line = channel * width
        q_image = QImage(bgr_data.data, width, height, bytes_per_line, QImage.Format_BGR888)
        scaled = q_image.scaled(nwidth,nheight, Qt.KeepAspectRatio|Qt.SmoothTransformation)
        return scaled
    def add_frame(self, pBuf, nSize, nWidth, nHeight, nType, sFileName, flag_jt):
        try:
            # 复制数据而不是直接引用，因为回调函数中的缓冲区可能会被重用
            frame_data = {
                'buffer': bytes(pBuf[:nSize]),  # 复制数据
                'width': nWidth,
                'height': nHeight,
                'type': nType,
                'filename': sFileName,
                'save_jpeg': flag_jt
            }
            self.frame_queue.put(frame_data, block=False)
        except queue.Full:
            # 队列满时丢弃最老的帧
            try:
                #self.frame_queue.get_nowait()
                #self.frame_queue.put(frame_data, block=False)
                time.sleep(0.01)  # 短暂等待
            except queue.Empty:
                pass

    def process_frames(self):
        while self.running:
            try:
                QThread.msleep(20)
                frame_data = self.frame_queue.get(timeout=0.003)

                # YUV转RGB
                bgr_image = self.yuv_to_rgb(frame_data['buffer'], frame_data['width'], frame_data['height'])

                #
                #print("%d  %d ", self.label_showcamera_2.width(), self.label_showcamera_2.height())
                #qt_image = self.bgr_to_qimage(bgr_image,self.label_showcamera_2.width() ,self.label_showcamera_2.height())
                self.setSize(self.myobject)
                qt_image = self.bgr_to_qimage(bgr_image, self.g_width,self.g_width)
                qt_pixmap = QPixmap.fromImage(qt_image)

                # 通过信号更新UI
                self.update_signal.emit(qt_pixmap)

                # 如果需要保存JPEG
                # if frame_data['save_jpeg']:
                #     lRet = self.Playctrldll.PlayM4_ConvertToJpegFile(
                #         frame_data['buffer'], len(frame_data['buffer']),
                #         frame_data['width'], frame_data['height'], frame_data['type'],
                #         c_char_p(frame_data['filename'].encode()))
                #
                #     if lRet == 0:
                #         logger_a.info('PlayM4_ConvertToJpegFile fail, error code is:' +
                #                       str(self.Playctrldll.PlayM4_GetLastError(1)))
                #     else:
                #         logger_a.info('PlayM4_ConvertToJpegFile success')

            except queue.Empty:
                continue
            except Exception as e:
                logger_a.error(f"Frame processing error: {str(e)}")

    def stop(self):
        self.running = False
        self.processing_thread.join()
class Ui_mainwindow(QtWidgets.QMainWindow, Ui_MainWindow):
    event_loadGcode_OK = pyqtSignal(str)  # 创建槽信号
    def __init__(self):
        super(Ui_mainwindow, self).__init__()
        self.setupUi(self)
        self.is_fullscreen = False
        # 初始化全屏标签
        self.fullscreen_label = None
        #当前碰头和热床的温度
        self.current_pengtou_temp=0
        self.current_bed_temp=0

        #界面美化函数
        self.css_ui()

        #初始化数据
        self.choose_err_int = None
        self.choose_name = ""
        self.choose_local_name = ""
        self.choose_gcodefile = ""
        self.flag_printing = 0  # 是否在打印过程
        self.status_thread = None
        self.statuscheck = None

        self.current_E_jichu = 0.0
        self.total_E = 0.0
        self.print_time = 0  # 已打印时间
        self.print_left_time = 0  # 剩余打印时间
        self.print_total_time = 0  # 总打印时间
        self.rece_E_flag = 0
        self.rece_E_flag = 0

        self.set_bed_flag = None
        self.set_ext_flag = None
        self.PID_flag = None
        self.sss_flag = None
        self.fff_flag = None
        self.fsfs_flag = None
        self.sendline_flag = None
        self.sendpid_flag = None


        # 开启温度监控定时器
        self.local_position = None
        self.temp_see = QtCore.QTimer()
        self.temp_see.timeout.connect(self.temp_see_control)
        self.temp_see.start(1000)
        self.flag_printing = 0  # 是否在打印过程
        self.time_tole_3h = 0
        self.time_tole_10min = 0

        self.keyboard = ui_dialog()
        self.keyboard.hide()


        self.monitor_interval = 3
        self.sdprinting = 0
        self.m105_waitcycles = 0

        self.flag_openclose_camera = 0

        self.temp_time = 0


        #剩余时间初始化0s
        self.label_totletime.setText("")
        #gcode初始化
        self.label_16.setText("")
        # #进度条置0隐藏
        self.progressBar.setMaximum(100)
        self.progressBar.setMinimum(0)
        self.progressBar.setValue(0)
        self.progressBar.hide()
        #总时间隐藏
        self.label_titlesy.hide()
        self.label_sy.hide()
        #去掉多余控件
        self.label_30.hide()
        self.label_35.hide()

        # 初始化核心串口
        self.p = printcore.printcore()
        self.p.changeValue.connect(self.setvalue_lineedit)
        self.p.changeValue_xyz.connect(self.set_xyz_line)
        self.p.changeValue_time.connect(self.set_time_line)
        #self.p.printer_offline.connect(self.sys_rest)

        self.p.Evevt_jichuliang.connect(self.jisuan_print_time)

        self.p.zdiff.connect(self.zdiff_level)

        self.p.dibanlevel.connect(self.level_value)

        self.p.system_state.connect(self.print_system_state)

        self.p.changeValue_motoroff.connect(self.runoutordu)

        self.event_loadGcode_OK.connect(self.loadGcode_ui_log)


        self.update_log()

        self.connect()

        self.flag_D = False

        # print time
        self.timer_use_left = QtCore.QTimer()
        self.timer_use_left.timeout.connect(self.set_timer_line)
        self.timer_use_left.setInterval(60000)

        try:
            # pass
            cam_file = open("./File/ip_address.txt", "r")
            camera_infor = cam_file.readlines()
            cam_file.close()
            cam_admin = camera_infor[0].split("=")[1]
            cam_psd = camera_infor[1].split("=")[1]
            self.cam_ip = camera_infor[2].split("=")[1]
            cam_mesk = camera_infor[3].split("=")[1]
            cam_getway = camera_infor[4].split("=")[1]
            cam_dns = camera_infor[5].split("=")[1]
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(
                e.__traceback__.tb_lineno))

        #摄像头
        # 登录的设备信息
        # '''
        retval = os.getcwd()
        os.chdir(r'./lib22/win')
        self.Objdll = ctypes.CDLL(r'./HCNetSDK.dll')  # 加载网络库
        self.Playctrldll = ctypes.CDLL(r'./PlayCtrl.dll')  # 加载播放库
        os.chdir(retval)
        #print(self.cam_ip.encode("utf-8"))
        self.DEV_IP = create_string_buffer(bytes(self.cam_ip.encode("utf-8")))
        #self.DEV_IP = create_string_buffer(b'192.168.1.64')
        self.DEV_PORT = 8000
        self.DEV_USER_NAME = create_string_buffer(b'admin')
        self.DEV_PASSWORD = create_string_buffer(b'yl202501')
        self.funcRealDataCallBack_V30 = None  # 实时预览回调函数，需要定义为全局的
        self.PlayCtrl_Port = c_long(-1)  # 播放句柄
        self.flag_jt = 0
        self.SetSDKInitCfg()  # 设置组件库和SSL库加载路径
        # 初始化DLL
        returndata = self.Objdll.NET_DVR_Init()
        if returndata != 1:
            logger_a.info(str(returndata))
        # 启用SDK写日志
        self.Objdll.NET_DVR_SetLogToFile(3, bytes('./SdkLog_Python/', encoding="utf-8"), False)
        # 获取一个播放句柄
        if not self.Playctrldll.PlayM4_GetPort(byref(self.PlayCtrl_Port)):
            logger_a.info(u'获取播放库句柄失败')
        logger_a.info(u'获取播放库句柄成功')
        # 登录设备
        (self.lUserId, device_info) = self.LoginDev(self.Objdll)
        if self.lUserId < 0:
            err = self.Objdll.NET_DVR_GetLastError()
            logger_a.info('Login device fail, error code is: %d' % self.Objdll.NET_DVR_GetLastError())
            # 释放资源
            self.Objdll.NET_DVR_Cleanup()

        logger_a.info('Login device succesed')
        # 定义码流回调函数
        self.funcRealDataCallBack_V30 = REALDATACALLBACK(self.RealDataCallBack_V30)
        # 开启预览
        lRealPlayHandle = self.OpenPreview(self.Objdll, self.lUserId, self.funcRealDataCallBack_V30)
        if lRealPlayHandle < 0:
            logger_a.info('Open preview fail, error code is: %d' % self.Objdll.NET_DVR_GetLastError())
            # 登出设备
            self.Objdll.NET_DVR_Logout(self.lUserId)
            # 释放资源
            self.Objdll.NET_DVR_Cleanup()

        logger_a.info('Open preview successed')

        self.pushButton_jp.clicked.connect(self.capture_photo)
        self.pushButton_closecamera.clicked.connect(self.video_button)

        # 创建按钮组
        self.distance_group = QButtonGroup(self)
        self.distance_group.setExclusive(True)  # 设置互斥

        for i in range(2, 6):
            button = getattr(self, f"pushButton_microzup_{i}")
            button.setStyleSheet('''
                QPushButton {
                    background: white;
                    color:black;
                    border-radius: 30px;
                    background-color: white;
                }
                QPushButton:checked {
                    background: rgba(242,95,13,0.8);
                }
                QPushButton:hover {
                    background: rgba(255,255,255,0.2);
                }
            ''')

        # 添加按钮到组中
        for i in range(8, 14):
            button = getattr(self, f"pushButton_microzup_{i}")
            self.distance_group.addButton(button)
            button.setCheckable(True)  # 设置按钮可选中
            button.setStyleSheet('''
                QPushButton {
                    background: white;
                    color:black;
                    border-radius: 30px;
                    border: 0px solid rgba(0,0,0,0.05);
                }
                QPushButton:checked {
                    background: rgba(242,95,13,0.8);
                }
                QPushButton:hover {
                    background: rgba(255,255,255,0.2);
                }
            ''')
            # 设置第一个按钮为选中状态
            if i == 8:
                button.setChecked(True)
        # 连接按钮点击信号
        self.distance_group.buttonClicked.connect(self.on_distance_button_clicked)
        # 初始化distance_use
        self.distance_use = 0.1
        # 创建按钮组
        self.bt_tp_group = QButtonGroup(self)
        self.bt_tp_group.setExclusive(True)  # 设置互斥
        # 添加按钮到组中
        for i in range(1, 56):
            button = getattr(self, f"pushButton_{i}")
            button.setStyleSheet('''
                QPushButton {
                    background: rgba(0,0,0,0.2);
                    border-radius: 25px;
                    border: 0px solid rgba(0,0,0,0.05);
                    color: #FFFFFF;
                    font-size: 14px;
                    padding: 0px;
                }
                QPushButton:hover {
                    background: rgba(255,255,255,0.2);
                }
                QPushButton:pressed {
                    background: rgba(255,255,255,0.4);
                }
                QPushButton:checked {
                    background: rgba(242,95,13,0.8);
                }
            ''')
            self.bt_tp_group.addButton(button)
            button.setCheckable(True)  # 设置按钮可选中
        # 连接按钮点击信号
        self.bt_tp_group.buttonClicked.connect(self.on_tp_button_clicked)
        self.label_showcamera.hide()
        self.frame_processor = FrameProcessor()
        self.frame_processor.setSize(self.label_showcamera_2)
        self.frame_processor.update_signal.connect(self.update_ui)
        # 读取系统配置
        self.read_settings()
        # 引导弹窗
        if self.comboBox.currentText() == "中文":
            self.ui_log_power = ui_dialog_log("yindao", "CN",
                                              "\n请按下绿色物理按钮来使能电机驱动")
        else:
            self.ui_log_power = ui_dialog_log("yindao", "EN",
                                              "powered firstly \n \n please press the green button \n enable the "
                                              "motor of xyz")
        self.ui_log_power.pushButton.clicked.connect(self.exit_log_poweron)
        self.ui_log_power.pushButton_2.clicked.connect(self.exit_log_poweron_2)
        self.ui_log_power.show()
        self.flag_pause = 0

    ##打印剩余时间显示
    def set_lefttime(self,m_left_time):
        self.label_sy.setText(m_left_time)
        logger_a.info(f"left_time:left time show {m_left_time}!")

    def read_settings(self):
        # 获取当前脚本所在目录的路径
        dir_path = os.path.dirname(os.path.abspath(__file__))
        # 构建相对路径
        file_path = os.path.join(dir_path, 'relative_path_to_file')
        settings = QSettings("./File/config.ini", QSettings.IniFormat)
        self.s_systemverID = settings.value("System/systemverID")
        self.s_softwareID = settings.value("System/softwareID")
        self.s_controlID = settings.value("System/controlID")
        self.s_IP = settings.value("System/IP")
        self.s_authorization = settings.value("System/authorization")
        self.s_langID = settings.value("System/langID")
        self.s_devID =settings.value("Device/deviceID")

        self.label_3.setText(self.s_systemverID)
        self.label_4.setText(self.s_softwareID)
        self.label_7.setText(self.s_controlID)
        self.label_8.setText(self.s_IP)
        self.label_10.setText(self.s_authorization)
        #self.comboBox.setCurrentText(self.s_langID)
        self.label_bhtext.setText(self.s_devID)

    #报故处理
    def runoutordu(self, a):
        try:
            b = a.replace("\n", "")
            v = [[b, 'None', 'True', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())]]
            Operational_Sqlite.insert_dates(
                "insert into 'print_information' (title, inf, status, time) values (?,?, ?,?)", v)
            self.update_log()
            #if a == "filament exchange sucess, wait gcode":
            #    logger_a.info("收到指令开始打印")
            #    self.ui_log_duandu.deleteLater()
            #    self.brokening = False
            #    self.blocking = False
            #    self.printfile()
#
            #    # if self.label_start.text() == "START":
            #    #     self.label_start.setText("开始")
            #if a == "filament exchange fail, broken":
            #    if self.label_start.text() != "START" and self.label_start.text() != "开始":
            #        self.changeValue_runoutFlag.emit("1")
            #if a == "filament error, broken":
            #    print("line:",a)
            #    print("self.brokening:",self.brokening)
            #    print("self.label_start:",self.label_start.text())
            #    if not self.brokening:
            #        if self.label_start.text() != "START" and self.label_start.text() != "开始":
            #            self.changeValue_runoutFlag.emit("1")
            #            self.brokening = True
            #if a == "filament exchange fail, block":
            #    if self.label_start.text() != "START" and self.label_start.text() != "开始":
            #        self.changeValue_runoutFlag.emit("2")
            #if a == "filament error, block":
            #    if not self.blocking:
            #        if self.label_start.text() != "START" and self.label_start.text() != "开始":
            #            self.changeValue_runoutFlag.emit("2")
            #        self.blocking = True
#
            #if a == "filament exchange fail, block":
            #    if self.label_start.text() != "START" and self.label_start.text() != "开始":
            #        self.changeValue_runoutFlag.emit("3")
            #if a == "filament error, block":
            #    if not self.blocking:
            #        if self.label_start.text() != "START" and self.label_start.text() != "开始":
            #            self.changeValue_runoutFlag.emit("3")
            #        self.blocking = True

            if a == "LOBOTICS MOTOR POWER OFF":
                if self.pushButton_startprint.text() == "PAUSE" or self.pushButton_startprint.text() == "暂停":
                    self.exit_log_cancelprint()  # 先关闭  然后弹窗
                    if self.comboBox.currentText() == "中文":
                        self.ui_log_motorpoweroff = ui_dialog_log("zhuyi", "CN", "\n电机驱动电源已断开")
                    else:
                        self.ui_log_motorpoweroff = ui_dialog_log("zhuyi", "EN", "INLONG MOTOR POWER OFF")
                    self.ui_log_motorpoweroff.pushButton.clicked.connect(self.exit_log_runout)
                    self.ui_log_motorpoweroff.pushButton_2.clicked.connect(self.exit_log_runout)
                    self.ui_log_motorpoweroff.show()
                else:
                    if self.comboBox.currentText() == "中文":
                        self.ui_log_motorpoweroff = ui_dialog_log("zhuyi", "CN", "\n电机驱动电源已断开")
                    else:
                        self.ui_log_motorpoweroff = ui_dialog_log("zhuyi", "EN", "INLONG MOTOR POWER OFF")
                    self.ui_log_motorpoweroff.pushButton.clicked.connect(self.exit_log_runout)
                    self.ui_log_motorpoweroff.pushButton_2.clicked.connect(self.exit_log_runout)
                    self.ui_log_motorpoweroff.show()
            if "LOBOTICS X" in a:
                if self.pushButton_startprint.text() == "PAUSE" or self.pushButton_startprint.text() == "暂停":
                    self.exit_log_cancelprint()  # 先关闭  然后弹窗
                    if self.comboBox.currentText() == "中文":
                        self.ui_log_motorpoweroff = ui_dialog_log("zhuyi", "CN", "X电机驱动错误!")
                    else:
                        self.ui_log_motorpoweroff = ui_dialog_log("zhuyi", "EN", "X motor error!")
                    self.ui_log_motorpoweroff.pushButton.clicked.connect(self.exit_log_runout)
                    self.ui_log_motorpoweroff.pushButton_2.clicked.connect(self.exit_log_runout)
                    self.ui_log_motorpoweroff.show()
                else:
                    if self.comboBox.currentText() == "中文":
                        self.ui_log_motorpoweroff = ui_dialog_log("zhuyi", "CN", "X电机驱动错误!")
                    else:
                        self.ui_log_motorpoweroff = ui_dialog_log("zhuyi", "EN", "X motor error!")
                    self.ui_log_motorpoweroff.pushButton.clicked.connect(self.exit_log_runout)
                    self.ui_log_motorpoweroff.pushButton_2.clicked.connect(self.exit_log_runout)
                    self.ui_log_motorpoweroff.show()
            if "LOBOTICS Y" in a:
                if self.pushButton_startprint.text() == "PAUSE" or self.pushButton_startprint.text() == "暂停":
                    self.exit_log_cancelprint()  # 先关闭  然后弹窗
                    if self.comboBox.currentText() == "中文":
                        self.ui_log_motorpoweroff = ui_dialog_log("zhuyi", "CN", "Y电机驱动错误!")
                    else:
                        self.ui_log_motorpoweroff = ui_dialog_log("zhuyi", "EN", "Y motor error!")
                    self.ui_log_motorpoweroff.pushButton.clicked.connect(self.exit_log_runout)
                    self.ui_log_motorpoweroff.pushButton_2.clicked.connect(self.exit_log_runout)
                    self.ui_log_motorpoweroff.show()
                else:
                    if self.comboBox.currentText() == "中文":
                        self.ui_log_motorpoweroff = ui_dialog_log("zhuyi", "CN", "Y电机驱动错误!")
                    else:
                        self.ui_log_motorpoweroff = ui_dialog_log("zhuyi", "EN", "Y motor error!")
                    self.ui_log_motorpoweroff.pushButton.clicked.connect(self.exit_log_runout)
                    self.ui_log_motorpoweroff.pushButton_2.clicked.connect(self.exit_log_runout)
                    self.ui_log_motorpoweroff.show()
            if "LOBOTICS Z" in a:#LOBOTICS Z
                    print("  9898989819999999999:",a)
                    if self.pushButton_startprint.text() == "PAUSE" or self.pushButton_startprint.text() == "暂停":
                        self.exit_log_cancelprint()  # 先关闭  然后弹窗
                        if self.comboBox.currentText() == "中文":
                            self.ui_log_motorpoweroff = ui_dialog_log("zhuyi", "CN", "Z电机驱动错误!")
                        else:
                            self.ui_log_motorpoweroff = ui_dialog_log("zhuyi", "EN", "Z motor error!")
                        self.ui_log_motorpoweroff.pushButton.clicked.connect(self.exit_log_runout)
                        self.ui_log_motorpoweroff.pushButton_2.clicked.connect(self.exit_log_runout)
                        self.ui_log_motorpoweroff.show()
                    else:
                        if self.comboBox.currentText() == "中文":
                            self.ui_log_motorpoweroff = ui_dialog_log("zhuyi", "CN", "Z电机驱动错误!")
                        else:
                            self.ui_log_motorpoweroff = ui_dialog_log("zhuyi", "EN", "Z motor error!")
                        self.ui_log_motorpoweroff.pushButton.clicked.connect(self.exit_log_runout)
                        self.ui_log_motorpoweroff.pushButton_2.clicked.connect(self.exit_log_runout)
                        self.ui_log_motorpoweroff.show()
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def exit_log_runout(self):
        try:
            self.p.send_now("G250 S110")  # 峰鸣消音
            self.p.send_now("G250 S21")  # 蓝灯
            self.ui_log_motorpoweroff.deleteLater()
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def print_system_state(self, a):
        try:
            aaaa =a
            if "STA" in a:
                a = a.split("STA:")[1].replace("\n", "")
                a = int(a)
                state = bin(a).replace("0b", "").zfill(24)
                if state[-1] == "1":  # X原点
                    pass
                else:
                    pass
                if state[-2] == "1":  # Z原点
                    pass
                else:
                    pass
                if state[-3] == "1":  # Y原点
                    pass
                else:
                    pass
                if state[-5] == "1":  # X轴故障
                    self.label_errx.setStyleSheet('border-image:None;background-color: rgb(0, 255, 0);')
                else:
                    self.label_errx.setStyleSheet('border-image:None;background-color: rgb(255, 0, 0);')
                if state[-6] == "1":  # Y轴故障
                    self.label_erry.setStyleSheet('border-image:None;background-color: rgb(0, 255, 0);')
                else:
                    self.label_erry.setStyleSheet('border-image:None;background-color: rgb(255, 0, 0);')
                if state[-7] == "1":  # Z轴故障
                    self.label_errz.setStyleSheet('border-image:None;background-color: rgb(0, 255, 0);')
                else:
                    self.label_errz.setStyleSheet('border-image:None;background-color: rgb(255, 0, 0);')
                if state[-9] == "1":  # E轴故障
                    self.label_erre.setStyleSheet('border-image:None;background-color: rgb(255, 0, 0);')
                else:
                    self.label_erre.setStyleSheet('border-image:None;background-color: rgb(0, 255, 0);')

                if state[-11] == "1":  # 断料检测
                    #print("*/********************line:",aaaa)
                    #print("454545445545454:",state[-11])
                    self.label_38.setStyleSheet('background-color: red;border-radius: 8px;')

                else:
                    #print("*/********************2line:", a)
                    #print("454545445545454-2:", state[-11])
                    self.label_38.setStyleSheet('background-color: green;border-radius: 8px;')

        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def restart_dwm(self):
        # 找到 dwm.exe 的 PID
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            if proc.info['name'] == 'dwm.exe':
                pid = proc.info['pid']
                break
        else:
            logger_a.info('无法找到 dwm.exe')
            return

            # 重启 dwm.exe
        try:
            os.kill(pid, 9)  # 强制杀死进程
            logger_a.info(f'重启了 dwm.exe (PID: {pid})')
        except Exception as e:
            logger_a.info(f'重启失败dwm.exe: {e}')

    # 超过10分钟加热未打印降温   打印时间
    def temp_see_control(self):
        try:
            self.temp_time += 1
            if self.temp_time >= 3600:
                for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                    # print(proc.info['name'])
                    if proc.info['name'] == 'dwm.exe':
                        # print(proc.info['pid'])
                        mem_info = proc.memory_info().rss  # bytes
                        # print(mem_info)
                        if mem_info > 1024 * 1024:  # resident set size, physical memory used by process
                            self.restart_dwm()
                        else:
                            logger_a.info("dwm.exe内存占用：" + str(mem_info))
                            break  # 只重启一次，避免多次重启
                self.temp_time = 0
            left = self.label_sy.text()
            if left != "" and self.p.printing and self.p.online:
                if "h" in left and "m" in left and "s" in left:
                    left_setText = int(left.split("h")[0]) * 3600 + \
                                   int(left.split("m")[0].split("  ")[1]) * 60 + \
                                   int(left.split("s")[0].split("  ")[2])
                    if left_setText == 0:
                        self.label_sy.setText("0s")
                        str(left)
                        return
                    left_setText -= 1
                    self.label_sy.setText(self.second_string_time(left_setText))
                if "h" not in left and "m" in left and "s" in left:
                    left_setText = int(left.split("m")[0]) * 60 + \
                                   int(left.split("s")[0].split("  ")[1])
                    if left_setText == 0:
                        self.label_sy.setText("0s")
                        self.set_lefttime(self.second_string_time(left_setText))
                        return
                    left_setText -= 1
                    self.label_sy.setText(self.second_string_time(left_setText))
                    self.set_lefttime(self.second_string_time(left_setText))
                if "h" not in left and "m" not in left and "s" in left:
                    left_setText = int(left.split("s")[0])
                    if left_setText == 0:
                        self.label_sy.setText("0s")
                        self.set_lefttime(self.second_string_time(left_setText))
                        return
                    left_setText -= 1
                    if self.label_sy.text() == "0s":
                        return
                    self.label_sy.setText(self.second_string_time(left_setText))
                    self.set_lefttime(self.second_string_time(left_setText))
            # print(self.flag_printing)
            ###底板和碰头温度异常提示窗口
            if not self.flag_printing:
                if self.label_xyz.text() == self.local_position:
                    wendu = self.lineEdit_extru.text().split("℃")[0]
                    # 喷头温度异常弹窗
                    try:
                        if float(wendu) > 400:
                            self.p.send_now("G250 S889\n")  # 亮红灯
                            if self.checkBox_language.currentText() == "中文":
                                self.ui_log = ui_dialog_log("zhuyi", "CN", "喷头温度异常")
                            else:
                                self.ui_log = ui_dialog_log("zhuyi", "EN", "Abnormal temperature of sprinkler head")
                        else:
                            if self.ui_log != None:
                                self.ui_log.close()  # 关闭弹窗
                            self.ui_log = None  # 清除弹窗引用
                    except Exception as e:
                        print(e)
                    if wendu != "":
                        if float(wendu) > 100:
                            self.time_tole_10min += 1
                        else:
                            self.time_tole_10min = 0
                        # print("计时温度是：", self.time_tole_10min)
                        if self.time_tole_10min > 600:
                            self.p.send_now("M104 S0")
                            self.time_tole_10min = 0
                    wendudiban = self.lineEdit_bed.text().split("℃")[0]
                    if float(wendudiban) > 150:
                        self.p.send_now("G250 S889\n")  # 亮红灯
                        if self.checkBox_language.currentText() == "中文":
                            self.ui_log = ui_dialog_log("zhuyi", "CN", "底板温度异常")
                        else:
                            self.ui_log = ui_dialog_log("zhuyi", "EN", "Abnormal bottom plate temperature")
                    else:
                        if self.ui_log != None:
                            self.ui_log.close()  # 关闭弹窗
                        self.ui_log = None  # 清除弹窗引用
                    if wendudiban != "":
                        if float(wendudiban) > 50:
                            self.time_tole_3h += 1
                        else:
                            self.time_tole_3h = 0
                        if self.time_tole_3h > 600 * 6:
                            self.p.send_now("M190 S0")
                            self.time_tole_3h = 0
                else:
                    self.local_position = self.label_xyz.text()
                    self.time_tole_10min = 0
            self.label_date2.setText(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            if self.p.paused:
                wendu = self.lineEdit_extru.text().split("℃")[0]
                if float(wendu) < 100:
                    self.p.send_now("M107\n")

        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(
                e.__traceback__.tb_lineno))

    def level_value(self, a):  # 开启底板调平qwqew
        try:
            if "POS" in a:
                temp = a.split("Z: ")
                temp[1] = str(round(float(temp[1]), 2))
                # 更新对应按钮的文本
                button_num = int(temp[0].split(" ")[1])
                button = getattr(self, f"pushButton_{button_num}")
                button.setText(temp[1])
            elif "|BEDLEVEL| done" in a:
                temp_b = a.split("height: ")[1].replace("mm", "").split(" min height:")
                temp_e = float(temp_b[0]) - float(temp_b[1])
                self.label_max.setText("MAX:" + temp_b[0])
                self.label_max_2.setText("MIN:" +temp_b[1])
                if temp_e > 0.8:
                    v = [["热床平面度超差", "热床平面度误差大于0.8mm，软件补偿效果较差，请确认原因并及时调整。\n当前误差值：" + str(round(temp_e, 4)), 'True',
                          time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())]]
                    Operational_Sqlite.insert_dates(
                        "insert into 'print_information' (title, inf, status, time) values (?,?, "
                        "?,?)", v)
                    self.update_log()
            #elif "fail done" in a:
            #    self.label_15.hide()
            #    self.pushButton_level.setStyleSheet("border-image: url(.//Image/pushoff.png);color: white")
            #elif "|PID|" in a:
            #    self.pushButton_PID.setStyleSheet("border-image: url(.//Image/pushoff.png);color:white")
            #    self.label_15.hide()
        except Exception as e:
            print(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))
            pass

    def zdiff_level(self, a):
        try:
            print(a)
            #if self.diban_inf != None:
            #    temp = a.split(": ")
            #    self.diban_inf.get(self.diban_new).setText(str(round(float(temp[1]), 2)))
            #    self.lineEdit_diban_show.setText(str(round(float(temp[1]), 2)))
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def set_time_line(self, a, b):  # 结束打印
        if a==0 and b==0:
            logger_a.info("Infor:a==0 and b==0,gcode file no lines!")
            return
        if int(a) >= int(b):
            self.timer_use_left.stop()
            self.label_sy.setText("0s")
            self.rece_E_flag = 0
            self.current_E_jichu = 0.0
            # self.total_E = 0.0
            self.print_time = 0  # 已打印时间
            self.print_left_time = 0  # 剩余打印时间
            self.print_total_time = 0  # 总打印时间
            if self.comboBox.currentText() == "中文":
                self.pushButton_startprint.setText("  开始")
            elif self.comboBox.currentText() == "English":
                self.pushButton_startprint.setText("START")
            elif self.comboBox.currentText() == "日本語.":
                self.pushButton_startprint.setText("スタート")

            self.p.send_now("G250 S891")  # 结束打印亮蓝灯
            self.p.send_now("G250 S900")  # 开空气过滤器
            self.p.send_now("M140 S0")  # 结束打印自动降温
            self.flag_printing = 0
            self.clogging_detection("stop")
            # self.timer_use_left.killTimer(self.timer_use_left.timerId())
            self.flag_ble = 0
            self.jichu_flag = 0
            self.progressBar.setMaximum(100)
            self.progressBar.setMinimum(0)
            self.progressBar.setValue(0)
            logger_a.info("打印结束，结束视频保存")
            #结束打印弹窗
            if self.comboBox.currentText() == "中文":
                self.ui_log_overprint = ui_dialog_log("zhuyi", "CN", "打印结束")
            else:
                self.ui_log_overprint = ui_dialog_log("zhuyi", "EN", "AFTER PRINTING")
            self.changeStartprintCaption(self.BT_STATE.START)
            self.ui_log_overprint.pushButton.clicked.connect(self.exit_log_overprint)
            self.ui_log_overprint.pushButton_2.clicked.connect(self.exit_log_overprint)
            self.ui_log_overprint.show()

    def exit_log_overprint(self):
        self.ui_log_overprint.deleteLater()

    def jisuan_print_time(self, a):
        try:
            if self.p.printing:
                self.rece_E_flag += 1
                if self.rece_E_flag == 1:
                    self.timer_use_left.start()
                # 暂停不计入
                if self.p.paused:
                    return
                logger_a.error(str(a))
                if "E-" not in a:
                    if "F" in a:
                        # 使用正则表达式提取 E 后面的数值
                        match = re.search(r'E([-+]?\d*\.?\d+)', a)
                        if match:
                            aa = float(match.group(1))
                            self.current_E_jichu += aa
                    else:
                        # 使用正则表达式提取 E 后面的数值
                        match = re.search(r'E([-+]?\d*\.?\d+)', a)
                        if match:
                            aa = float(match.group(1))
                            self.current_E_jichu += aa
                else:
                    if "F" in a:
                        # 使用正则表达式提取 E- 后面的数值
                        match = re.search(r'E-([-+]?\d*\.?\d+)', a)
                        if match:
                            bb = float(match.group(1))
                            self.current_E_jichu -= bb
                    else:
                        # 使用正则表达式提取 E- 后面的数值
                        match = re.search(r'E-([-+]?\d*\.?\d+)', a)
                        if match:
                            bb = float(match.group(1))
                            self.current_E_jichu -= bb
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def set_timer_line(self):
        try:
            # self.runtime_left += 1
            # self.runtime_left_shiji += 1
            '''
            b = self.second_string_time(int(self.time_totleuse))
            if int(self.time_totleuse-self.runtime_left) >0:
                a = self.second_string_time(int(self.time_totleuse-self.runtime_left))
            else:
                a = self.second_string_time(0)
            if int(self.runtime_left) >= int(self.time_totleuse):
                self.runtime_left = int(self.time_totleuse)
            #当前挤出量 总挤出量已获取
            #self.lineEdit_left.setText(a)
            #self.lineEdit_total.setText(b)
            '''
            print("self.p.online:",self.p.online,"self.p.printing:",self.p.printing)
            if DEBUG==1:
                self.p.online =True
                self.p.printing =True
            if self.p.online and self.p.printing:
                self.print_time += 60  # 已打印时间+60
                self.print_total_time = (float(self.total_E) / float(self.current_E_jichu)) * float(self.print_time)
                self.print_left_time = self.print_total_time - self.print_time
                print("self.print_total_time:", self.print_total_time, "self.print_time:", self.print_time,
                      "self.print_left_time:", self.print_left_time)
                if self.print_left_time >= self.print_total_time:
                    self.label_sy.setText("0s")
                    self.set_lefttime(self.second_string_time("0s"))
                    return
                left = self.second_string_time(int(self.print_left_time))
                total = self.second_string_time(int(self.print_total_time))
                self.label_sy.setText(str(left))
                self.set_lefttime(str(left))
                self.label_totletime.setText(str(total))
                self.progressBar.setValue(100-int(self.print_left_time * 100 / self.print_total_time))

        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def second_string_time(self, seconds):
        if seconds < 60:
            return str(seconds) + 's'
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h != 0:
            time_string = str(h) + "h  " + str(m) + "m  " + str(s) + "s"
            return time_string
        else:
            time_string = str(m) + "m  " + str(s) + "s"
            return time_string


    def _handle_camera_qp(self):
        try:
            if not self.is_fullscreen:
                print("进入全屏模式")

                # 创建一个新的全屏窗口
                self.fullscreen_window = QtWidgets.QMainWindow()
                self.fullscreen_window.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)

                # 创建一个中央部件
                central_widget = QtWidgets.QWidget()
                self.fullscreen_window.setCentralWidget(central_widget)

                # 创建布局
                layout = QtWidgets.QVBoxLayout(central_widget)
                layout.setContentsMargins(0, 0, 0, 0)

                # 创建全屏标签（克隆而非使用原始标签）
                self.fullscreen_label = QLabel("Camera View - 全屏")
                self.fullscreen_label.setStyleSheet("background-color: lightgray;")
                self.fullscreen_label.setScaledContents(True)
                self.fullscreen_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

                # 添加摄像头标签到全屏窗口
                layout.addWidget(self.fullscreen_label)

                def RealDataCallBack_V30_qp(lPlayHandle, dwDataType, pBuffer, dwBufSize, pUser):
                    try:
                        # 码流回调函数
                        if dwDataType == NET_DVR_SYSHEAD:
                            # 设置流播放模式
                            Playctrldll_qp.PlayM4_SetStreamOpenMode(PlayCtrl_Port, 0)
                            # 打开码流，送入40字节系统头数据
                            if Playctrldll_qp.PlayM4_OpenStream(PlayCtrl_Port, pBuffer, dwBufSize, 1024 * 1024):
                                global FuncDecCB
                                # 设置解码回调，可以返回解码后YUV视频数据
                                FuncDecCB = DECCBFUNWIN(lPlayHandle.DecCBFun)
                                Playctrldll_qp.PlayM4_SetDecCallBackExMend(PlayCtrl_Port, FuncDecCB, None, 0, None)
                                # 开始解码播放
                                if Playctrldll_qp.PlayM4_Play(PlayCtrl_Port, int(self.fullscreen_label.winId())):
                                    logger_a.info(u'播放库播放成功')
                                else:
                                    logger_a.error(u'播放库播放失败')
                            else:
                                logger_a.error(u'播放库打开流失败')
                        elif dwDataType == NET_DVR_STREAMDATA:
                            if not Playctrldll_qp.PlayM4_InputData(PlayCtrl_Port, pBuffer, dwBufSize):
                                logger_a.error(u'播放库输入数据失败')
                        else:
                            logger_a.info(u'其他数据,长度:', dwBufSize)
                    except Exception as e:
                        print(e)

                def OpenPreview_qp(Objdll, lUserId, callbackFun):
                    try:
                        '''
                        打开预览
                        '''
                        preview_info = NET_DVR_PREVIEWINFO()
                        preview_info.hPlayWnd = int(self.fullscreen_label.winId())
                        preview_info.lChannel = 1  # 通道号
                        preview_info.dwStreamType = 0  # 主码流
                        preview_info.dwLinkMode = 0  # TCP
                        preview_info.bBlocked = 1  # 阻塞取流
                        # 开始预览并且设置回调函数回调获取实时流数据
                        lRealPlayHandle = Objdll.NET_DVR_RealPlay_V40(lUserId, byref(preview_info), callbackFun, None)
                        return lRealPlayHandle
                    except Exception as e:
                        print(e)

                def SetSDKInitCfg():
                    retval = os.getcwd()
                    os.chdir(r'./lib22/win')
                    strPath = os.getcwd().encode('gbk')
                    sdk_ComPath = NET_DVR_LOCAL_SDK_PATH()
                    sdk_ComPath.sPath = strPath
                    Objdll_qp.NET_DVR_SetSDKInitCfg(2, byref(sdk_ComPath))
                    Objdll_qp.NET_DVR_SetSDKInitCfg(3, create_string_buffer(strPath + b'\libcrypto-1_1-x64.dll'))
                    Objdll_qp.NET_DVR_SetSDKInitCfg(4, create_string_buffer(strPath + b'\libssl-1_1-x64.dll'))
                    os.chdir(retval)

                def LoginDev(Objdll, DEV_IP, DEV_PORT, DEV_USER_NAME, DEV_PASSWORD):
                    # 登录注册设备
                    device_info = NET_DVR_DEVICEINFO_V30()
                    lUserId = Objdll.NET_DVR_Login_V30(DEV_IP, DEV_PORT, DEV_USER_NAME,
                                                       DEV_PASSWORD,
                                                       byref(device_info))
                    return lUserId, device_info

                # '''
                retval = os.getcwd()
                os.chdir(r'./lib22/win')
                Objdll_qp = ctypes.CDLL(r'./HCNetSDK.dll')  # 加载网络库
                Playctrldll_qp = ctypes.CDLL(r'./PlayCtrl.dll')  # 加载播放库
                os.chdir(retval)
                # print(self.cam_ip.encode("utf-8"))
                # DEV_IP = create_string_buffer(bytes(self.cam_ip.encode("utf-8")))
                DEV_IP = create_string_buffer(b'192.168.1.64')
                DEV_PORT = 8000
                DEV_USER_NAME = create_string_buffer(b'admin')
                DEV_PASSWORD = create_string_buffer(b'yl202501')
                funcRealDataCallBack_V30_qp = None  # 实时预览回调函数，需要定义为全局的
                PlayCtrl_Port = c_long(-1)  # 播放句柄
                SetSDKInitCfg()  # 设置组件库和SSL库加载路径
                # 初始化DLL
                returndata = Objdll_qp.NET_DVR_Init()
                if returndata != 1:
                    logger_a.info(str(returndata))
                # 启用SDK写日志
                Objdll_qp.NET_DVR_SetLogToFile(3, bytes('./SdkLog_Python/', encoding="utf-8"), False)
                # 获取一个播放句柄
                if not Playctrldll_qp.PlayM4_GetPort(byref(PlayCtrl_Port)):
                    logger_a.info(u'获取播放库句柄失败')
                logger_a.info(u'获取播放库句柄成功')
                # 登录设备
                (lUserId, device_info) = LoginDev(Objdll_qp, DEV_IP, DEV_PORT, DEV_USER_NAME, DEV_PASSWORD)
                if lUserId < 0:
                    err = Objdll_qp.NET_DVR_GetLastError()
                    logger_a.info('Login device fail, error code is: %d' % Objdll_qp.NET_DVR_GetLastError())
                    # 释放资源
                    Objdll_qp.NET_DVR_Cleanup()

                logger_a.info('Login device succesed')
                # 定义码流回调函数
                funcRealDataCallBack_V30_qp = REALDATACALLBACK(RealDataCallBack_V30_qp)
                # 开启预览
                lRealPlayHandle = OpenPreview_qp(Objdll_qp, lUserId, funcRealDataCallBack_V30_qp)
                if lRealPlayHandle < 0:
                    logger_a.info('Open preview fail, error code is: %d' % Objdll_qp.NET_DVR_GetLastError())
                    # 登出设备
                    Objdll_qp.NET_DVR_Logout(lUserId)
                    # 释放资源
                    Objdll_qp.NET_DVR_Cleanup()

                logger_a.info('Open preview successed')

                # 添加退出按钮
                self.fullscreen_close_btn = QtWidgets.QPushButton("退出全屏")
                self.fullscreen_close_btn.setStyleSheet('''
                       QPushButton {
                           background: rgba(0,0,0,0.3);
                           border-radius: 8px;
                           border: 1px solid rgba(255,255,255,0.2);
                           color: #FFF;
                           padding: 10px;
                       }
                       QPushButton:hover {
                           background: rgba(255,0,0,0.5);
                       }
                   ''')
                self.fullscreen_close_btn.clicked.connect(self.exit_fullscreen)
                layout.addWidget(self.fullscreen_close_btn, alignment=QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

                # 显示全屏窗口
                self.fullscreen_window.showFullScreen()
                self.is_fullscreen = True

                # 安装事件过滤器
                self.fullscreen_window.installEventFilter(self)

            else:
                print("退出全屏模式")
                self.exit_fullscreen()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(e)
    def exit_fullscreen(self):
        try:
            if not hasattr(self, 'fullscreen_window'):
                return

            # 关闭全屏窗口
            if hasattr(self, 'fullscreen_window'):
                self.fullscreen_window.close()
                self.fullscreen_window = None

            self.is_fullscreen = False
            print("已退出全屏")
        except Exception as e:
            print(f"退出全屏时发生错误: {e}")
            self.is_fullscreen = False

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Escape:
                self.exit_fullscreen()
                return True
        return super().eventFilter(obj, event)
    #点击使能提示框确认和取消事件
    def exit_log_poweron(self):
        try:
            self.ui_log_power.deleteLater()
            self.p.send_now("L110 S60")
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def exit_log_poweron_2(self):
        try:
            self.ui_log_power.deleteLater()
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def video_button(self):
        if self.flag_openclose_camera%2:
            self.label_showcamera_2.show()
            self.pushButton_closecamera.setText("关闭")
        else:
            self.label_showcamera_2.hide()
            self.pushButton_closecamera.setText("打开")
        self.flag_openclose_camera += 1

    def capture_photo(self):
        try:
            logger_a.info("点击'CAPTURE'按钮")
            # 确保capture目录存在
            capture_dir = os.path.join(os.getcwd(), "capture")
            if not os.path.exists(capture_dir):
                os.makedirs(capture_dir)

            # 设置截屏标志
            self.flag_jt = 1
            logger_a.info("设置截屏标志")

            # 打开capture目录
            os.startfile(capture_dir)
        except Exception as e:
            logger_a.error(f"截屏错误: {str(e)}")
            self.flag_jt = 0

    # 设置SDK初始化依赖库路径
    def SetSDKInitCfg(self):
        retval = os.getcwd()
        os.chdir(r'./lib22/win')
        strPath = os.getcwd().encode('gbk')
        sdk_ComPath = NET_DVR_LOCAL_SDK_PATH()
        sdk_ComPath.sPath = strPath
        self.Objdll.NET_DVR_SetSDKInitCfg(2, byref(sdk_ComPath))
        self.Objdll.NET_DVR_SetSDKInitCfg(3, create_string_buffer(strPath + b'\libcrypto-1_1-x64.dll'))
        self.Objdll.NET_DVR_SetSDKInitCfg(4, create_string_buffer(strPath + b'\libssl-1_1-x64.dll'))
        os.chdir(retval)
    def LoginDev(self, Objdll):
        # 登录注册设备
        device_info = NET_DVR_DEVICEINFO_V30()
        lUserId = Objdll.NET_DVR_Login_V30(self.DEV_IP, self.DEV_PORT, self.DEV_USER_NAME, self.DEV_PASSWORD,
                                           byref(device_info))
        return lUserId, device_info

    def update_ui(self, pixmap):
        """用于更新UI的槽函数"""
        self.label_showcamera_2.setPixmap(pixmap)
    def DecCBFun(self, nPort, pBuf, nSize, pFrameInfo, nUser, nReserved2):
        # 解码回调函数
        if pFrameInfo.contents.nType == 3:
            # 解码返回视频YUV数据，将YUV数据转成jpg图片保存到本地
            # 如果有耗时处理，需要将解码数据拷贝到回调函数外面的其他线程里面处理，避免阻塞回调导致解码丢帧
            sFileName = ('./capture/INLONG_CAPTURE[%d].jpg' % pFrameInfo.contents.nStamp)
            nWidth = pFrameInfo.contents.nWidth
            nHeight = pFrameInfo.contents.nHeight
            nType = pFrameInfo.contents.nType
            dwFrameNum = pFrameInfo.contents.dwFrameNum
            nStamp = pFrameInfo.contents.nStamp
            # 将数据传递给处理线程
            self.frame_processor.add_frame(
                pBuf, nSize, nWidth, nHeight, nType,
                sFileName, self.flag_jt
            )
            if self.flag_jt:
                lRet = self.Playctrldll.PlayM4_ConvertToJpegFile(pBuf, nSize, nWidth, nHeight, nType,
                                                                 c_char_p(sFileName.encode()))
                if lRet == 0:
                    logger_a.info('PlayM4_ConvertToJpegFile fail, error code is:' + str(
                        self.Playctrldll.PlayM4_GetLastError(nPort)))
                else:
                    logger_a.info('PlayM4_ConvertToJpegFile success')
                self.flag_jt = 0
    def RealDataCallBack_V30(self, lPlayHandle, dwDataType, pBuffer, dwBufSize, pUser):
        # 码流回调函数
        if dwDataType == NET_DVR_SYSHEAD:
            # 设置流播放模式
            self.Playctrldll.PlayM4_SetStreamOpenMode(self.PlayCtrl_Port, 0)
            # 打开码流，送入40字节系统头数据
            if self.Playctrldll.PlayM4_OpenStream(self.PlayCtrl_Port, pBuffer, dwBufSize, 1024 * 1024):
                global FuncDecCB
                # 设置解码回调，可以返回解码后YUV视频数据
                FuncDecCB = DECCBFUNWIN(self.DecCBFun)
                self.Playctrldll.PlayM4_SetDecCallBackExMend(self.PlayCtrl_Port, FuncDecCB, None, 0, None)
                # 开始解码播放
                if self.Playctrldll.PlayM4_Play(self.PlayCtrl_Port, int(self.label_showcamera.winId())):
                    logger_a.info(u'播放库播放成功')
                else:
                    logger_a.error(u'播放库播放失败')
            else:
                logger_a.error(u'播放库打开流失败')
        elif dwDataType == NET_DVR_STREAMDATA:
            if not self.Playctrldll.PlayM4_InputData(self.PlayCtrl_Port, pBuffer, dwBufSize):
                logger_a.error(u'播放库输入数据失败')
        else:
            logger_a.info(u'其他数据,长度:', dwBufSize)
    def OpenPreview(self, Objdll, lUserId, callbackFun):
        try:
            '''
            打开预览
            '''
            preview_info = NET_DVR_PREVIEWINFO()
            preview_info.hPlayWnd = int(self.label_showcamera.winId())
            preview_info.lChannel = 1  # 通道号
            preview_info.dwStreamType = 0  # 主码流
            preview_info.dwLinkMode = 0  # TCP
            preview_info.bBlocked = 1  # 阻塞取流
            preview_info.dwDisplayBufNum = 1
            preview_info.byProtoType = 0
            preview_info.byPreviewMode = 0
            # 开始预览并且设置回调函数回调获取实时流数据
            lRealPlayHandle = Objdll.NET_DVR_RealPlay_V40(lUserId, byref(preview_info), callbackFun, None)
            return lRealPlayHandle
        except Exception as e:
            print(e)
    def InputData(self, fileMp4, Playctrldll):
        while True:
            pFileData = fileMp4.read(4096)
            if pFileData is None:
                break
            if not Playctrldll.PlayM4_InputData(self.PlayCtrl_Port, pFileData, len(pFileData)):
                break

    def connect(self):
        try:

            """该部分为小车蓝牙连接部分，暂时不上"""
            try:
                self.p.connect(port="COM8", baud=115200, dtr=1)

                #pass
            except SerialException as e:
                # 串口错误弹窗

                if self.comboBox.currentText() == "中文":
                    self.ui_log_comerror = ui_dialog_log("cuowu", "CN", "串口连接错误，请确认COM8是否存在并重启连接")
                else:
                    self.ui_log_comerror = ui_dialog_log("zhuyi", "EN",
                                                "SerialPort is non-existing! \nPlease Confirm The serialport is COM8,\nThen Click OK to reconnect COM8!")

                self.ui_log_comerror.pushButton.clicked.connect(self.exit_connect_comerr)
                if DEBUG==0:
                    self.ui_log_comerror.show()

                logger_a.info("INLONG CONNECT FAILED!")

                return
            except OSError as e:
                # 无串口弹窗

                if self.checkBox_language.currentText() == "中文":
                    self.ui_log = ui_dialog_log("cuowu", "CN", "串口连接错误，请确认COM8是否存在并重启连接")
                else:
                    self.ui_log = ui_dialog_log("zhuyi", "EN",
                                                "SerialPort is non-existing! \nPlease Confirm The serialport is COM8,\nThen Click OK to reconnect COM8!")
                self.ui_log.pushButton.clicked.connect(self.exit_connect)
                self.ui_log.show()

                logger_a.info("INLONG CONNECT FAILED!")

                return
            self.statuscheck = True
            self.status_thread = threading.Thread(target=self.statuschecker,
                                                  name='status thread')
            self.status_thread.start()

            logger_a.info("INLONG CONNECT SUCCESS!")

        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def remove_local(self):
        try:
            if self.choose_local_name != "":
                if self.choose_local_name in os.listdir("./GCODE"):
                    os.remove("./GCODE/" + self.choose_local_name)
                    self.get_local()

                    logger_a.info("REMOVE:" + str("./GCODE/" + self.choose_local_name) + " SUCCESS!")

        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def statuschecker(self):
        try:
            while self.statuscheck:
                self.statuschecker_inner()
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def statuschecker_inner(self, do_monitoring=True):
        try:
            if self.p.online:
                if self.p.writefailures >= 4:
                    logger_a.info("Disconnecting after 4 failed writes.")
                    self.status_thread = None
                    self.p.disconnect()
                    return
                if do_monitoring:
                    if self.sdprinting and not self.p.paused:
                        self.p.send_now("M27\n")
                    if self.m105_waitcycles % 3 == 0:
                        self.p.send_now("M105\n")
                        # self.p.send_now("M114")
                    self.m105_waitcycles += 1
            cur_time = time.time()
            wait_time = 0
            while time.time() < cur_time + self.monitor_interval - 0.25:
                if not self.statuscheck:
                    break
                time.sleep(0.25)
                # Safeguard: if system time changes and goes back in the past,
                # we could get stuck almost forever
                wait_time += 0.25
                if wait_time > self.monitor_interval - 0.25:
                    break
            # Always sleep at least a bit, if something goes wrong with the
            # system time we'll avoid freezing the whole app this way
            time.sleep(0.25)
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def exit_connect_comerr(self):
        self.ui_log_comerror.deleteLater()
        self.connect()

    def setvalue_lineedit(self, a, b, c, d):
        #self.label_temppt.setText('当前温度：'+str(a)+'℃'+'  设置温度：' +str(b)+'℃')
        self.current_pengtou_temp=a
        self.current_bed_temp=b
        #self.label_temppt.setText('当前温度：'+str(a)+'℃')
        self.lineEdit_extru.setText(str(a) + '℃')
        self.lineEdit_ptset.setText(str(b)+'℃')
        #self.label_temprc.setText('当前温度：' + str(c) + '℃' + '  设置温度：' + str(d) + '℃')
        self.lineEdit_bed.setText(str(c) + '℃')
        self.lineEdit_rcset.setText(str(d) + '℃')

    def set_xyz_line(self, x, y, z):
        self.label_xyz.setText("X:" + x + "    Y:" + y + "    Z:" + z)
        if self.pushButton_startprint.text().strip() == "PAUSE" or self.pushButton_startprint.text().strip() == "暂停":
            #if self.filamentblock.isChecked():
                if 2 < float(z) < 5:
                    self.p.send_now("L110 S81")
                elif float(z) < 2:
                    #self.p.send_now("L110 S80")
                    pass

    def DrawButton(self,parentWnd,btn,width,height,radius,background):
        # self.pushButton_startprint.('''QPushButton{background: rgba(0,0,0,0.3);
        #                                setStyleSheet         border-radius: 15px;
        #                                         border: 0px solid rgba(0,0,0,0.05);color:#FFFFFF}''')
        #self.groupBox_6.setStyleSheet("background-color: transparent;border: none;border-width: 0px;")
        self.groupBox_11.setStyleSheet("background-color: transparent;border: none;border-width: 0px;")
        self.groupBox_13.setStyleSheet("background-color: transparent;border: none;border-width: 0px;")
        self.groupBox_4.setStyleSheet("background-color: transparent;border: none;border-width: 0px;")
        self.groupBox_24.setStyleSheet("background-color: transparent;border: none;border-width: 0px;")
        self.groupBox_23.setStyleSheet("background-color: transparent;border: none;border-width: 0px;")
        self.groupBox_25.setStyleSheet("background-color: transparent;border: none;border-width: 0px;")
        self.groupBox_26.setStyleSheet("background-color: transparent;border: none;border-width: 0px;")


        # self.lineEdit_pid.setStyleSheet('''QLineEdit{background: rgba(255,255,255,0.2);;
        #                                                                 border-radius: 8px;
        #                                                                 border: 1px solid rgba(0,0,0,0.05);color:#FFFFFF}''')
        self.label_printspeed.setStyleSheet("color:white;background-color: transparent;border: none;border-width: 0px;")
        self.label_espeed.setStyleSheet("color:white;background-color: transparent;border: none;border-width: 0px;")
        self.label_fanspeed.setStyleSheet("color:white;background-color: transparent;border: none;border-width: 0px;")
        self.lineEdit_jcl.setStyleSheet("color:white;background-color: transparent;border: none;border-width: 0px;")
        self.lineEdit_printspeed.setStyleSheet("color:white;background-color: transparent;border: none;border-width: 0px;")
        self.lineEdit_fanspeed.setStyleSheet("color:white;background-color: transparent;border: none;border-width: 0px;")
        self.label_36.setAlignment(Qt.AlignLeft)
        self.label_jcl.setAlignment(Qt.AlignLeft)
        self.label_37.setAlignment(Qt.AlignLeft)

        self.label_39.setAlignment(Qt.AlignLeft)
        self.label_print_targetspeed.setAlignment(Qt.AlignLeft)
        self.label_fan_speed.setAlignment(Qt.AlignLeft)
        self.comboBox_2.setEditable(True)  # 4
        self.ledit = self.comboBox_2.lineEdit()  # 5
        font = QFont()
        font.setPointSize(14)
        self.ledit.setFont(font)
        self.ledit.setAlignment(Qt.AlignCenter)  # 6
        self.comboBox_2.setLineEdit(self.ledit)

        self.comboBox_2.setStyleSheet(
            "QComboBox {"
                "   border: 0px solid #8f8f91;"
                "   border-radius: 25px;"
                "   padding: 0px;"
                "   min-width: 0em;"
                "   background: rgba(255, 255, 255, 0.2);"
                "   color: white;"
                "   opacity: 0.3;"

            "}"
            "QComboBox:on { /* shift the text when the popup is open */"
            "   padding-top: 0px;"
            "   padding-left: 0px;"
            "}"
            "QComboBox::drop-down {"
            "   subcontrol-origin: padding;"
            "   subcontrol-position: top right;"
            "   width: 35px;"
            "   border-left-width: 0px;"
            "   border-left-color: darkgray;"
            "   border-left-style: solid;"
            "   border-top-right-radius: 25px;"
            "   border-bottom-right-radius: 25px;"
            "}"
            "QComboBox::down-arrow {"
            "   image: url(./Image/down-arrow.png);"
            "   width: 40px;"
            "   height: 40px;"
            "}"
        )

        self.pushButton_dyk.setStyleSheet('''QPushButton{
                                            color:white;
                                            background: rgba(0,0,0,0.5);
                                            border-top-left-radius: 25px;
                                            border-top-right-radius: 0px;
                                            border-bottom-left-radius: 25px;
                                            border-bottom-right-radius: 0px;
                                            opacity: 0.5;}''')

        self.pushButton_dlg.setStyleSheet('''QPushButton{
                                            color:white;
                                            background: rgba(0,0,0,0.3);
                                            border-top-left-radius: 0px;
                                            border-top-right-radius: 25px;
                                            border-bottom-left-radius: 0px;
                                            border-bottom-right-radius: 25px;
                                            opacity: 0.5;}''')

        self.pushButton_pid.setStyleSheet('''QPushButton{
                                            color:white;
                                            background: rgba(0,0,0,0.6);
                                            border-top-left-radius: 0px;
                                            border-top-right-radius: 25px;
                                            border-bottom-left-radius: 0px;
                                            border-bottom-right-radius: 25px;
                                            opacity: 0.3;}''')
        self.pushButton_tp.setStyleSheet('''QPushButton{
                                            color:white;
                                            background: rgba(0,0,0,0.3);
                                            border-top-left-radius: 0px;
                                            border-top-right-radius: 25px;
                                            border-bottom-left-radius: 0px;
                                            border-bottom-right-radius: 25px;
                                            opacity: 0.5;}''')
        # self.groupBox_tp.setStyleSheet('''QGroupBox{
        #                                     color:white;
        #                                     #background: rgba(0,0,0,0.6);
        #                                     border-top-left-radius: 20px;
        #                                     border-top-right-radius: 20px;
        #                                     border-bottom-left-radius: 20px;
        #                                     border-bottom-right-radius:20px;
        #                                     padding: 10px;  /* 确保内部控件不会盖住边框 */
        #                                     opacity: 0.3;}''')
        self.groupBox_16.setStyleSheet("QGroupBox {"
                                                    "border: 0px solid gray;"
                                                    "border-top-left-radius: 30px;"
                                                    "border-top-right-radius: 0px;"
                                                    "border-bottom-left-radius: 30px;"
                                                    "border-bottom-right-radius:0px;"
                                                    "color:white;"
                                                    "background: rgba(0,0,0,0.1);"
                                                    "opacity: 0.5;"
                                                    "margin-top: 0em;}"
                                                    "QGroupBox:title {"
                                                    "subcontrol-origin: margin;"
                                                    "left: 0px;"
                                                    "padding: 0 0px 0 0px;}")
        self.groupBox_printspeed.setStyleSheet("QGroupBox {"
                                                    "border: 0px solid gray;"
                                                    "border-top-left-radius: 31px;"
                                                    "border-top-right-radius: 31px;"
                                                    "border-bottom-left-radius: 31px;"
                                                    "border-bottom-right-radius:31px;"
                                                    "color:white;"
                                                    "background: rgba(255,255,255,0.1);"
                                                    "opacity: 0.6;"
                                                    "margin-top: 0em;}"
                                                    "QGroupBox:title {"
                                                    "subcontrol-origin: margin;"
                                                    "left: 0px;"
                                                    "padding: 0 0px 0 0px;}")
        self.groupBox_jcl.setStyleSheet("QGroupBox {"
                                                    "border: 0px solid gray;"
                                                    "border-top-left-radius: 31px;"
                                                    "border-top-right-radius: 31px;"
                                                    "border-bottom-left-radius: 31px;"
                                                    "border-bottom-right-radius:31px;"
                                                    "color:white;"
                                                    "background: rgba(255,255,255,0.1);"
                                                    "opacity: 0.6;"
                                                    "margin-top: 0em;}"
                                                    "QGroupBox:title {"
                                                    "subcontrol-origin: margin;"
                                                    "left: 0px;"
                                                    "padding: 0 0px 0 0px;}")
        self.groupBox_fanspeed.setStyleSheet("QGroupBox {"
                                                    "border: 0px solid gray;"
                                                    "border-top-left-radius: 31px;"
                                                    "border-top-right-radius: 31px;"
                                                    "border-bottom-left-radius: 31px;"
                                                    "border-bottom-right-radius:31px;"
                                                    "color:white;"
                                                    "background: rgba(255,255,255,0.1);"
                                                    "opacity: 0.6;"
                                                    "margin-top: 0em;}"
                                                    "QGroupBox:title {"
                                                    "subcontrol-origin: margin;"
                                                    "left: 0px;"
                                                    "padding: 0 0px 0 0px;}")

        self.label_max.setStyleSheet('color: red;')  # 设置文字颜色为红色
        self.label_max_2.setStyleSheet('color: green;')  # 设置文字颜色为绿色


        self.lineEdit_pid.setStyleSheet('''
            border-top-left-radius: 25px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: 25px;
            border-bottom-right-radius: 0px;
            color:white;
            background: rgba(255,255,255,0.1);
            opacity: 0.3''')
        self.lineEdit_send.setStyleSheet('''
            border-top-left-radius: 25px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: 25px;
            border-bottom-right-radius: 0px;
            color:white;
            background: rgba(255,255,255,0.1);
            opacity: 0.5''')

        self.pushButton_send.setStyleSheet('''QPushButton{
                                            color:white;
                                            background: rgba(0,0,0,0.4);
                                            border-top-left-radius: 0px;
                                            border-top-right-radius: 30px;
                                            border-bottom-left-radius: 0px;
                                            border-bottom-right-radius: 30px;
                                            opacity: 0.3;}''')
        self.comboBox.setEditable(True)  # 4
        self.ledit = self.comboBox.lineEdit()  # 5
        font = QFont()
        font.setPointSize(14)
        self.ledit.setFont(font)
        self.ledit.setAlignment(Qt.AlignCenter)  # 6
        self.comboBox.setLineEdit(self.ledit)
        self.comboBox.setStyleSheet(
            "QComboBox {"
            "   border: 0px solid #8f8f91;"
            "   border-radius: 20px;"
            "   padding: 0px;"
            "   min-width: 0em;"
            "   background: rgba(255, 255, 255, 0.3);"
            "   color: white;"
            "}"
            "QComboBox:on { /* shift the text when the popup is open */"
            "   padding-top: 0px;"
            "   padding-left: 0px;"
            "}"
            "QComboBox::drop-down {"
            "   subcontrol-origin: padding;"
            "   subcontrol-position: top right;"
            "   width: 35px;"
            "   border-left-width: 0px;"
            "   border-left-color: white;"
            "   border-left-style: solid;"
            "   border-top-right-radius: 20px;"
            "   border-bottom-right-radius: 20px;"
            "}"

            "QComboBox::down-arrow {"
            "   image: url(./Image/down-arrow.png);"
            "   width: 40px;"
            "   height: 40px;"
            "}"
        )
        self.pushButton_pid.setStyleSheet('''QPushButton{
                                            color:white;
                                            background: rgba(0,0,0,0.6);
                                            border-top-left-radius: 0px;
                                            border-top-right-radius: 25px;
                                            border-bottom-left-radius: 0px;
                                            border-bottom-right-radius: 25px;
                                            opacity: 0.3;}''')
        #self.groupBox_4.setStyleSheet("background-color: transparent;border: none;border-width: 0px;")
        self.groupBox_5.setStyleSheet("""
                              QGroupBox {
                                 background-color: white;
                                 width: 90px;
                                 height: 288px;
                                 background: #FFFFFF;
                                 border-radius: 45px;
                              }
                              QGroupBox::title {
                                  subcontrol-origin: padding;
                                  left: 1px;
                              }
                          """)
        self.groupBox_22.setStyleSheet("""
                                    QGroupBox {
                                        border-radius: 8px;
                                        border: 1px solid rgba(255,255,255,0.2);
                                        background-color: rgba(255, 255, 255, 0.1);
                                        padding: 10px;  /* 确保内部控件不会盖住边框 */
                                    }
                                """)

        self.groupBox_7.setStyleSheet("""
                                    QGroupBox {
                                        border-radius: 8px;
                                        border: 1px solid rgba(255,255,255,0.2);
                                        background-color: rgba(255, 255, 255, 0.1);
                                        padding: 10px;  /* 确保内部控件不会盖住边框 */
                                    }
                                """)
        self.groupBox_8.setStyleSheet("""
                                    QGroupBox {
                                        border-radius: 8px;
                                        border: 1px solid rgba(255,255,255,0.2);
                                        background-color: rgba(255, 255, 255, 0.1);
                                        padding: 10px;  /* 确保内部控件不会盖住边框 */
                                    }
                                """)
        self.groupBox_9.setStyleSheet("""
                                    QGroupBox {
                                        border-radius: 8px;
                                        border: 1px solid rgba(255,255,255,0.2);
                                        background-color: rgba(255, 255, 255, 0.1);
                                        padding: 10px;  /* 确保内部控件不会盖住边框 */
                                    }
                                """)
        self.label_pengtou_targ_temp.setStyleSheet('''
            color:white;
            background: rgba(0,0,0,0.1);
            opacity: 0.3''')
        self.label_bed_targ_temp.setStyleSheet('''
            color:white;
            background: rgba(0,0,0,0.1);
            opacity: 0.3''')
        self.lineEdit_gcodefile.setStyleSheet('''
            border-top-left-radius: 40px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: 40px;
            border-bottom-right-radius: 0px;
            color:white;
            background: rgba(0,0,0,0.1);
            opacity: 0.1''')

        self.pushButton_choosefile.setStyleSheet('''QPushButton{
                                                    width: 80px;
                                                    height: 80px;
                                                    color:white;
                                                    background: rgba(0,0,0,0.3);
                                                    border-top-left-radius: 0px;
                                                    border-top-right-radius: 40px;
                                                    border-bottom-left-radius: 0px;
                                                    border-bottom-right-radius: 40px;
                                                    opacity: 0.3;}''')
        self.pushButton_startprint.setStyleSheet('''QPushButton{
                                            width: 80px;
                                            height: 80px;
                                            color:white;
                                            background: rgba(0,0,0,0.3);
                                            border-top-left-radius: 40px;
                                            border-top-right-radius: 40px;
                                            border-bottom-left-radius: 40px;
                                            border-bottom-right-radius: 40px;
                                            opacity: 0.3;}''')
        self.pushButton_stopprint.setStyleSheet('''QPushButton{
                                            width: 80px;
                                            height: 80px;
                                            color:white;
                                            background: rgba(0,0,0,0.3);
                                            border-top-left-radius: 40px;
                                            border-top-right-radius: 40px;
                                            border-bottom-left-radius: 40px;
                                            border-bottom-right-radius: 40px;
                                            opacity: 0.3;}''')
        self.label_temprc.setStyleSheet('''
            border-top-left-radius: 15px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: 15px;
            border-bottom-right-radius: 0px;
            color:white;
            background: rgba(0,0,0,0.1);
            opacity: 0.3''')
        # background: rgba(255, 255, 255, 50);
        self.label_temppt.setStyleSheet('''
            border-top-left-radius: 15px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: 15px;
            border-bottom-right-radius: 0px;
            color:white;
            background: rgba(0,0,0,0.1);
            opacity: 0.3''')
        self.lineEdit_ptset.setStyleSheet('''
            border-top-left-radius: 0px;
            border-top-right-radius: 15px;
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 15px;
            color:white;
            background: rgba(0,0,0,0.1);
            opacity: 0.3''')
        self.lineEdit_rcset.setStyleSheet('''
            border-top-left-radius: 0px;
            border-top-right-radius: 15px;
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 15px;
            color:white;
            background: rgba(0,0,0,0.1);
            opacity: 0.3''')

        self.lineEdit_extru.setStyleSheet('''
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
            color:white;
            background: rgba(0,0,0,0.1);
            opacity: 0.3''')
        self.lineEdit_bed.setStyleSheet('''
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
            color:white;
            background: rgba(0,0,0,0.1);
            opacity: 0.3''')
        # self.groupBox_4.setStyleSheet("""
        #                             QGroupBox {
        #                                 border-radius: 8px;
        #                                 border: 1px solid rgba(255,255,255,0.2);
        #                                 background-color: rgba(255, 255, 255, 0.1);
        #                                 padding: 10px;  /* 确保内部控件不会盖住边框 */
        #                             }
        #                         """)
        self.pushButton_microzup.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);
                                            width: 86px;
                                            height: 86px;
                                            background: rgba(0,0,0,0.3);
                                            border-radius: 43px 43px 43px 43px;
                                            opacity: 0.3;}''')
        self.pushButton_microzdown.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);
                                            width: 86px;
                                            height: 86px;
                                            background: rgba(0,0,0,0.3);
                                            border-radius: 43px 43px 43px 43px;
                                            opacity: 0.3;}''')
      ############

        self.groupBox_10.setStyleSheet("""
                              QGroupBox {
                                 background-color: white;
                                 width: 90px;
                                 height: 288px;
                                 background: #FFFFFF;
                                 border-radius: 45px;
                              }
                              QGroupBox::title {
                                  subcontrol-origin: padding;
                                  left: 1px;
                              }
                          """)
        self.groupBox_20.setStyleSheet("""
                         QGroupBox {
                            background-color: white;
                            width: 90px;
                            height: 288px;
                            background: #FFFFFF;
                            border-radius: 45px;
                         }
                         QGroupBox::title {
                             subcontrol-origin: padding;
                             left: 1px;
                         }
                     """)
        self.groupBox_18.setStyleSheet("""
                         QGroupBox {
                            background-color: white;
                            width: 90px;
                            height: 288px;
                            background: #FFFFFF;
                            border-radius: 45px;
                         }
                         QGroupBox::title {
                             subcontrol-origin: padding;
                             left: 1px;
                         }
                     """)
        self.groupBox_12.setStyleSheet("""
                         QGroupBox {
                            background-color: white;
                            width: 90px;
                            height: 288px;
                            background: #FFFFFF;
                            border-radius: 45px;
                         }
                         QGroupBox::title {
                             subcontrol-origin: padding;
                             left: 1px;
                         }
                     """)
        self.pushButton_eup.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);
                                                 width: 86px;
                                                 height: 86px;
                                                 background: rgba(0,0,0,0.3);
                                                 border-radius: 43px 43px 43px 43px;
                                                 opacity: 0.3;}''')
        self.pushButton_edown.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);
                                                 width: 86px;
                                                 height: 86px;
                                                 background: rgba(0,0,0,0.3);
                                                 border-radius: 43px 43px 43px 43px;
                                                 opacity: 0.3;}''')

        self.pushButton_yup.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);
                                                 width: 86px;
                                                 height: 86px;
                                                 background: rgba(0,0,0,0.3);
                                                 border-radius: 43px 43px 43px 43px;
                                                 opacity: 0.3;}''')
        self.pushButton_ydown.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);
                                                 width: 86px;
                                                 height: 86px;
                                                 background: rgba(0,0,0,0.3);
                                                 border-radius: 43px 43px 43px 43px;
                                                 opacity: 0.3;}''')

        self.pushButton_xleft.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);
                                                 width: 86px;
                                                 height: 86px;
                                                 background: rgba(0,0,0,0.3);
                                                 border-radius: 43px 43px 43px 43px;
                                                 opacity: 0.3;}''')
        self.pushButton_xright.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);
                                                 width: 86px;
                                                 height: 86px;
                                                 background: rgba(0,0,0,0.3);
                                                 border-radius: 43px 43px 43px 43px;
                                                 opacity: 0.3;}''')

        self.pushButton_zup.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);
                                                 width: 86px;
                                                 height: 86px;
                                                 background: rgba(0,0,0,0.3);
                                                 border-radius: 43px 43px 43px 43px;
                                                 opacity: 0.3;}''')
        self.pushButton_zdown.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);
                                                 width: 86px;
                                                 height: 86px;
                                                 background: rgba(0,0,0,0.3);
                                                 border-radius: 43px 43px 43px 43px;
                                                 opacity: 0.3;}''')

    def css_ui(self):
        try:
            # 背景
            self.setStyleSheet("QMainWindow {border-image: url(./Image/logo.png);}")
            #文件助手初始化
            self.openFile = ui_dialog_file()
            self.openFile.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
            self.openFile.listView_file.setStyleSheet(
                'border-image:none;border:none;background-color:transparent;color:white')
            self.openFile.pushButton_2.clicked.connect(self.confim_choose_gcodefile)
            self.openFile.hide()

            self.label_38.setStyleSheet('background-color: green;border-radius: 8px;')

            # LOGO
            pic = QPixmap("./Image/LOGO.svg")
            self.label_logo.setStyleSheet("background-image:transparent")
            self.label_logo.setPixmap(pic)
            self.label_logo.setScaledContents(1)

            self.pushButton_microzup_2.clicked.connect(self.do_move_x_fuwei)
            self.pushButton_microzup_3.clicked.connect(self.do_move_y_fuwei)
            self.pushButton_microzup_4.clicked.connect(self.do_move_z_fuwei)
            self.pushButton_microzup_5.clicked.connect(self.do_homeall)

            self.comboBox.currentIndexChanged.connect(self.changeLanguage)

            #主页按钮
            self.pushButton_vector.setStyleSheet("QPushButton{border-image:url(./Image/Vector.png);}")
            self.labelvector.setStyleSheet("color:#F25F0D")
            self.pushButton_vector.clicked.connect(self.MoveToVector)
            self.tabWidget.setCurrentIndex(0)
            # 任务按钮
            self.pushButton_task.setStyleSheet("QPushButton{border-image:url(./Image/taskOff.png);}")
            self.label_task.setStyleSheet("color:white")
            self.pushButton_task.clicked.connect(self.MoveToTask)
            # 调校按钮
            self.pushButton_change.setStyleSheet("QPushButton{border-image:url(./Image/changeOff.png);}")
            self.label_change.setStyleSheet("color:white")
            self.pushButton_change.clicked.connect(self.MoveToChange)
            #信息按钮
            self.pushButton_message.setStyleSheet("QPushButton{border-image:url(./Image/messageOff.png);}")
            self.label_message.setStyleSheet("color:white")
            self.pushButton_message.clicked.connect(self.MoveToMessage)
            # 系统按钮
            self.pushButton_system.setStyleSheet("QPushButton{border-image:url(./Image/systemOff.png);}")
            self.label_system.setStyleSheet("color:white")
            self.pushButton_system.clicked.connect(self.MoveToSystem)
            #设备编号
            self.label_sbbh.setStyleSheet("color:#A9A4A4")
            self.label_bhtext.setStyleSheet("color:#A9A4A4")
            #tabwidget
            self.tabWidget.setStyleSheet("""
                QTabWidget::pane { background: rgba(255, 255, 255, 0.1); border: none; }
                QTabBar::tab { width: 0; height: 0;}
            """)
            # 更新按钮
            self.pushButton_update.setStyleSheet("QPushButton{border-image:url(./Image/update.png);}")
            #self.label_update.setStyleSheet("border:none;color:white")
            self.pushButton_update.clicked.connect(self.soft_update)
            # 退出按钮
            self.pushButton_exit.setStyleSheet("QPushButton{border-image:url(./Image/exit.png);}")
            self.pushButton_exit.clicked.connect(self.sys_exit)
            # 复位按钮
            self.pushButton_reset.setStyleSheet("QPushButton{border-image:url(./Image/reset.png);}")
            # self.pushButton_reset.clicked.connect(self.MoveToSystem)
            # 关机按钮
            self.pushButton_shutdown.setStyleSheet("QPushButton{border-image:url(./Image/shutdown.png);}")
            self.pushButton_shutdown.clicked.connect(self.os_shutdown)
            # 重启按钮
            self.pushButton_restart.setStyleSheet("QPushButton{border-image:url(./Image/restart.png);}")
            self.pushButton_restart.clicked.connect(self.os_restart)

            self.groupBox.setStyleSheet("""
                QGroupBox {
                    border-radius: 8px;
                    border: 1px solid rgba(255,255,255,0.2);
                    background-color: rgba(255, 255, 255, 0.1);
                    padding: 10px;  /* 确保内部控件不会盖住边框 */
                }
            """)
            self.groupBox_2.setStyleSheet("""
                            QGroupBox {
                                border-radius: 8px;
                                border: 1px solid rgba(255,255,255,0.2);
                                background-color: rgba(255, 255, 255, 0.1);
                                padding: 10px;  /* 确保内部控件不会盖住边框 */
                            }
                        """)
            self.groupBox_3.setStyleSheet("""
                                        QGroupBox {
                                            border-radius: 8px;
                                            border: 1px solid rgba(255,255,255,0.2);
                                            background-color: rgba(255, 255, 255, 0.1);
                                            padding: 10px;  /* 确保内部控件不会盖住边框 */
                                        }
                                    """)
            #listwidgethistory
            self.listWidget_now_history.setStyleSheet("""
                QListWidget {
                    border-radius: 8px;
                    border: 3px solid rgba(255, 255, 255, 0.2);
                    background-color: rgba(255, 255, 255, 0.1);
                    padding: 5px;  /* 避免文字贴边 */
                }

                QListWidget::item {
                    background: transparent;
                    color: white;
                    padding: 5px;
                }

                QListWidget::item:selected {
                    background: rgba(255, 255, 255, 0.3);  /* 选中项高亮 */
                    color: black;
                }
            """)
            self.listWidget_now_history.clicked.connect(self.local_clickedlist_history)  # listview 的点击事件
            self.listView_now.setStyleSheet("""
                            QListView {
                                border-radius: 8px;
                                border: 3px solid rgba(255, 255, 255, 0.2);
                                background-color: rgba(255, 255, 255, 0.1);
                                padding: 5px;  /* 避免文字贴边 */
                            }

                            QListView::item {
                                background: transparent;
                                color: white;
                                padding: 5px;
                            }

                            QListView::item:selected {
                                background: rgba(255, 255, 255, 0.3);  /* 选中项高亮 */
                                color: black;
                            }
                        """)
            self.listView_udisk.setStyleSheet("""
                                        QListView {
                                            border-radius: 8px;
                                            border: 3px solid rgba(255, 255, 255, 0.2);
                                            background-color: rgba(255, 255, 255, 0.1);
                                            padding: 5px;  /* 避免文字贴边 */
                                        }

                                        QListView::item {
                                            background: transparent;
                                            color: white;
                                            padding: 5px;
                                        }

                                        QListView::item:selected {
                                            background: rgba(255, 255, 255, 0.3);  /* 选中项高亮 */
                                            color: black;
                                        }
                                    """)
            self.textEdit_history.setStyleSheet("""
                QTextEdit {
                    border-radius: 8px;
                    border: 3px solid rgba(255, 255, 255, 0.2);
                    background-color: rgba(255, 255, 255, 0.1); /* 半透明背景 */
                    color: white; /* 文本颜色 */
                    padding: 5px; /* 让文字不贴边 */
                }
            """)

            self.textEdit_send.setStyleSheet("""
                            QTextEdit {
                                border-radius: 8px;
                                border: 0px solid rgba(255, 255, 255, 0.2);
                                background-color: rgba(255, 255, 255, 0); /* 半透明背景 */
                                color: white; /* 文本颜色 */
                                padding: 0px; /* 让文字不贴边 */
                            }
                        """)
            #打开历史文件
            self.pushButton_history.setStyleSheet("QPushButton{border-image:url(./Image/openfile.png);}")
            self.pushButton_history.clicked.connect(self.open_file)

            #labelerr
            self.label_errx.setStyleSheet("background-color:white;border-radius: 15px;")
            self.label_erry.setStyleSheet("background-color:white;border-radius: 15px;")
            self.label_errz.setStyleSheet("background-color:white;border-radius: 15px;")
            self.label_erre.setStyleSheet("background-color:white;border-radius: 15px;")

            #刷新
            self.pushButton_refreshlocal.setStyleSheet("QPushButton{border-image:url(./Image/refresh.png);}")
            self.pushButton_refreshlocal.clicked.connect(self.get_local)
            self.pushButton_removelocal.setStyleSheet("QPushButton{border-image:url(./Image/deletelocal.png);}")
            self.pushButton_removelocal.clicked.connect(self.remove_local)
            #self.pushButton_removelocal.hide()
            self.pushButton_refreshu.setStyleSheet("QPushButton{border-image:url(./Image/refresh.png);}")
            self.pushButton_refreshu.clicked.connect(self.get_u)
            self.pushButton_insert.setStyleSheet("QPushButton{border-image:url(./Image/insert.png);}")
            self.pushButton_insert.clicked.connect(self.save_u)

            # self.pushButton_dyk.setStyleSheet('''QPushButton{background: rgba(255,255,255,0.5);;
            #                             border-radius: 15px;
            #                             border: 1px solid rgba(0,0,0,0.05);color:#FFFFFF}''')
            self.pushButton_dyk.clicked.connect(self.dyk_use)

            # self.pushButton_dlg.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);;
            #                                         border-radius: 15px;
            #                                         border: 1px solid rgba(0,0,0,0.05);color:#FFFFFF}''')
            self.pushButton_dlg.clicked.connect(self.dyg_use)

            # self.comboBox_2.setStyleSheet('''QComboBox{background: rgba(255,255,255,0.2);;
            #                                                     border-radius: 8px;
            #                                                     border: 1px solid rgba(0,0,0,0.05);color:#FFFFFF}''')
            # self.lineEdit_send.setStyleSheet('''QLineEdit{background: rgba(255,255,255,0.2);;
            #                                                                             border-radius: 8px;
            #                                                                             border: 1px solid rgba(0,0,0,0.05);color:#FFFFFF}''')

            #self.pushButton_choosefile.setStyleSheet("QPushButton{border-image:url(./Image/choosefile.png);}")
            icon = QIcon("./Image/choosefile.png")  # 设置startprint图标
            self.pushButton_choosefile.setIcon(icon)
            self.pushButton_choosefile.setIconSize(QSize(60, 60))  # 设置图标为 48x48 像素

            self.pushButton_choosefile.clicked.connect(self.loadGcodeFile)

            self.pushButton_closecamera.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);
                                                        border-radius: 8px;
                                                        border: 1px solid rgba(0,0,0,0.05);color:#FFFFFF}''')
            # self.pushButton_closecamera.clicked.connect(self.MoveToSystem)

            self.pushButton_jp.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);
                                                                    border-radius: 8px;
                                                                    border: 1px solid rgba(0,0,0,0.05);color:#FFFFFF}''')
            # self.pushButton_jp.clicked.connect(self.MoveToSystem)

            # self.pushButton_pid.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);
            #                                                     border-radius: 15px;
            #                                                     border: 1px solid rgba(0,0,0,0.05);color:#FFFFFF}''')
            self.pushButton_pid.clicked.connect(self.sys_pid)
            # 设置图标（请确保路径正确）
            icon = QIcon("./Image/pidright.png")  # 这里的 "icon.png" 是你的图标文件
            self.pushButton_pid.setIcon(icon)

            # 隐藏文本
            self.pushButton_pid.setText("")  # 或者使用 Qt.NoText

            self.pushButton_send.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);
                                                                            border-radius: 8px;
                                                                            border: 1px solid rgba(0,0,0,0.05);color:#FFFFFF}''')
            self.pushButton_send.clicked.connect(self.sendline)
            # 设置图标（请确保路径正确）
            icon = QIcon("./Image/pidright.png")  # 这里的 "icon.png" 是你的图标文件
            self.pushButton_send.setIcon(icon)

            self.lineEdit_ptset.selectionChanged.connect(self.lineEdit_ptset_use_set)
            self.lineEdit_rcset.selectionChanged.connect(self.lineEdit_rcset_use_set)
            self.lineEdit_send.selectionChanged.connect(self.lineEdit_send_use_set)

            self.lineEdit_printspeed.selectionChanged.connect(self.lineEdit_printspeed_use_set)
            self.lineEdit_jcl.selectionChanged.connect(self.lineEdit_jcl_use_set)
            self.lineEdit_fanspeed.selectionChanged.connect(self.lineEdit_fanspeed_use_set)

            self.lineEdit_pid.selectionChanged.connect(self.lineEdit_pid_use_set)

            # 隐藏文本
            self.pushButton_send.setText("")  # 或者使用 Qt.NoText

            self.pushButton_microzup.clicked.connect(self.micro_zzz)
            # 设置图标（请确保路径正确）
            icon = QIcon("./Image/up.png")  # 这里的 "icon.png" 是你的图标文件
            self.pushButton_microzup.setIcon(icon)

            # 隐藏文本
            self.pushButton_microzup.setText("")  # 或者使用 Qt.NoText

            self.pushButton_microzdown.clicked.connect(self.micro_zzz_down)
            # 设置图标（请确保路径正确）
            icon = QIcon("./Image/down.png")  # 这里的 "icon.png" 是你的图标文件
            self.pushButton_microzdown.setIcon(icon)

            # 隐藏文本
            self.pushButton_microzdown.setText("")  # 或者使用 Qt.NoText

            self.pushButton_eup.clicked.connect(self.do_move_e_left)
            # 设置图标（请确保路径正确）
            icon = QIcon("./Image/up.png")  # 这里的 "icon.png" 是你的图标文件
            self.pushButton_eup.setIcon(icon)

            # 隐藏文本
            self.pushButton_eup.setText("")  # 或者使用 Qt.NoText
            self.pushButton_edown.clicked.connect(self.do_move_e_right)
            # 设置图标（请确保路径正确）
            icon = QIcon("./Image/down.png")  # 这里的 "icon.png" 是你的图标文件
            self.pushButton_edown.setIcon(icon)

            # 隐藏文本
            self.pushButton_edown.setText("")  # 或者使用 Qt.NoText

            self.pushButton_zup.clicked.connect(self.do_move_z_left)
            # 设置图标（请确保路径正确）
            icon = QIcon("./Image/up.png")  # 这里的 "icon.png" 是你的图标文件
            self.pushButton_zup.setIcon(icon)

            # 隐藏文本
            self.pushButton_zup.setText("")  # 或者使用 Qt.NoText

            self.pushButton_zdown.clicked.connect(self.do_move_z_right)
            # 设置图标（请确保路径正确）
            icon = QIcon("./Image/down.png")  # 这里的 "icon.png" 是你的图标文件
            self.pushButton_zdown.setIcon(icon)

            # 隐藏文本
            self.pushButton_zdown.setText("")  # 或者使用 Qt.NoText

            self.pushButton_xleft.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);
                                                                                                    border-radius: 30px;
                                                                                border: 1px solid rgba(0,0,0,0.05);color:#FFFFFF}''')
            self.pushButton_xleft.clicked.connect(self.do_move_x_left)

            # 设置图标（请确保路径正确）
            icon = QIcon("./Image/left.png")  # 这里的 "icon.png" 是你的图标文件
            self.pushButton_xleft.setIcon(icon)

            # 隐藏文本
            self.pushButton_xleft.setText("")  # 或者使用 Qt.NoText
            self.pushButton_xright.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);
                                                                                                                border-radius: 30px;
                                                                                                                border: 1px solid rgba(0,0,0,0.05);color:#FFFFFF}''')
            self.pushButton_xright.clicked.connect(self.do_move_x_right)
            # 设置图标（请确保路径正确）
            icon = QIcon("./Image/right.png")  # 这里的 "icon.png" 是你的图标文件
            self.pushButton_xright.setIcon(icon)

            # 隐藏文本
            self.pushButton_xright.setText("")  # 或者使用 Qt.NoText

            self.pushButton_yup.clicked.connect(self.do_move_y_left)
            # 设置图标（请确保路径正确）
            icon = QIcon("./Image/up.png")  # 这里的 "icon.png" 是你的图标文件
            self.pushButton_yup.setIcon(icon)

            # 隐藏文本
            self.pushButton_yup.setText("")  # 或者使用 Qt.NoText

            self.pushButton_ydown.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);
                                                border-radius: 30px;
                                                border: 1px solid rgba(0,0,0,0.05);color:#FFFFFF}''')
            self.pushButton_ydown.clicked.connect(self.do_move_y_right)
            # 设置图标（请确保路径正确）
            icon = QIcon("./Image/down.png")  # 这里的 "icon.png" 是你的图标文件
            self.pushButton_ydown.setIcon(icon)

            # 隐藏文本
            self.pushButton_ydown.setText("")  # 或者使用 Qt.NoText

            # self.pushButton_startprint.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);
            #                                         border-radius: 15px;
            #                                         border: 0px solid rgba(0,0,0,0.05);color:#FFFFFF}''')
            # 设置图标
            icon = QIcon("./Image/startprint.png")  # 设置startprint图标
            self.pushButton_startprint.setIcon(icon)
            self.pushButton_startprint.setIconSize(QSize(60, 60))  # 设置图标为 48x48 像素
            # 隐藏文本
            self.pushButton_startprint.setText("  开始")
            self.pushButton_startprint.clicked.connect(self.printfile)


            # self.pushButton_stopprint.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);
            #                                                     border-radius: 15px;
            #                                                     border: 1px solid rgba(0,0,0,0.05);color:#FFFFFF}''')
            # 设置图标
            icon = QIcon("./Image/stop.png")  # 设置startprint图标
            self.pushButton_stopprint.setIcon(icon)
            self.pushButton_stopprint.setIconSize(QSize(60, 60))  # 设置图标为 48x48 像素
            # 隐藏文本
            self.pushButton_stopprint.setText("  停止")
            self.pushButton_stopprint.clicked.connect(self.cancelprint)

            self.groupBox_print.setStyleSheet("""
                                        QGroupBox {
                                            border-radius: 8px;
                                            border: 1px solid rgba(255,255,255,0.2);
                                            background-color: rgba(255, 255, 255, 0.1);
                                            padding: 10px;  /* 确保内部控件不会盖住边框 */
                                        }
                                    """)
            self.groupBox_14.setStyleSheet("""
                                                    QGroupBox {
                                                        border-radius: 8px;
                                                        border: 1px solid rgba(255,255,255,0.2);
                                                        background-color: rgba(255, 255, 255, 0.1);
                                                        padding: 10px;  /* 确保内部控件不会盖住边框 */
                                                    }
                                                """)
            self.groupBox_15.setStyleSheet("""
                                                                QGroupBox {
                                                                    border-radius: 8px;
                                                                    border: 1px solid rgba(255,255,255,0.2);
                                                                    background-color: rgba(255, 255, 255, 0.1);
                                                                    padding: 10px;  /* 确保内部控件不会盖住边框 */
                                                                }
                                                            """)
            self.groupBox_17.setStyleSheet("""
                                                                QGroupBox {
                                                                    border-radius: 8px;
                                                                    border: 1px solid rgba(255,255,255,0.2);
                                                                    background-color: rgba(255, 255, 255, 0.1);
                                                                    padding: 10px;  /* 确保内部控件不会盖住边框 */
                                                                }
                                                            """)
            self.groupBox_19.setStyleSheet("""
                                                                QGroupBox {
                                                                    border-radius: 8px;
                                                                    border: 1px solid rgba(255,255,255,0.2);
                                                                    background-color: rgba(255, 255, 255, 0.1);
                                                                    padding: 10px;  /* 确保内部控件不会盖住边框 */
                                                                }
                                                            """)
            self.lineEdit_gcodefile.setStyleSheet("border-radius: 16px;border: 3px solid rgba(255,255,255,0.2);background-color: #ccc;")
            # self.lineEdit_ptset.setStyleSheet(
            #     "border-radius: 15px;border: 1px solid rgba(255,255,255,0.2);background-color: white;")
            # self.lineEdit_rcset.setStyleSheet(
            #     "border-radius: 15px;border: 1px solid rgba(255,255,255,0.2);background-color: white;")

            # self.groupBox_5.setStyleSheet("""
            #                                     QGroupBox {
            #                                         border-radius: 8px;
            #                                         background-color: rgba(255, 255, 255, 0.1);
            #                                         padding: 10px;  /* 确保内部控件不会盖住边框 */
            #                                     }
            #                                 """)
            # self.groupBox_6.setStyleSheet("""
            #                                         QGroupBox {
            #                                             border-radius: 8px;
            #
            #                                             background-color: rgba(255, 255, 255, 0.1);
            #                                             padding: 10px;  /* 确保内部控件不会盖住边框 */
            #                                         }
            #                                     """)
            self.groupBox_12.setStyleSheet("""
                                                                QGroupBox {
                                                                    background:white;
                                                                    border-radius: 8px;
                                                                    border: 1px solid rgba(255,255,255,0.2);
                                                                    background-color: rgba(132,151,176,0.1);#background-color: white;
                                                                    padding: 10px;  /* 确保内部控件不会盖住边框 */
                                                                }
                                                            """)
            self.DrawButton(self.groupBox_5,self.pushButton_microzup,self.groupBox_5.geometry().width(),
                            self.groupBox_5.geometry().height(),(self.groupBox_5.geometry().width()-8)/2,0xffffff)
  ####################################################################
            self.label_showcamera.setStyleSheet(
                "border-image:url(./Image/camera.png);color:white")

            # self.label_temprc.setStyleSheet('''
            #     background: white;
            #     border-radius: 15px;
            #     border: 0px solid rgba(255,255,255,0.5);
            #     opacity: 0.1;
            #     color:black''')
            # # background: rgba(255, 255, 255, 50);
            # self.label_temppt.setStyleSheet('''
            #     background: white;
            #     border-radius: 15px;
            #     border: 0px solid rgba(255,255,255,0.5);
            #     opacity: 0.1;
            #     color:black''')

            # self.pushButton_tp.setStyleSheet('''
            #                                         background: rgba(255, 255, 255, 50);
            #                                         border-radius: 15px;
            #                                         border: 0px solid rgba(255,255,255,0.5);
            #                                         opacity: 0.1;
            #                                         color:white''')
            self.pushButton_tp.clicked.connect(self.g28xy)

        except Exception as e:
            print(e)

    def dyg_use(self):
        # self.pushButton_dlg.setStyleSheet('''QPushButton{background: rgba(255,255,255,0.5);;
        #                                            border-radius: 15px;
        #                                            border: 1px solid rgba(0,0,0,0.05);color:#FFFFFF}''')
        # self.pushButton_dyk.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);;
        #                                                        border-radius: 15px;
        #                                                        border: 1px solid rgba(0,0,0,0.05);color:#FFFFFF}''')
        self.pushButton_dyk.setStyleSheet('''QPushButton{
                                               width: 120px;
                                               height: 40px;
                                               color:white;
                                               background: rgba(0,0,0,0.3);
                                               border-top-left-radius: 20px;
                                               border-top-right-radius: 0px;
                                               border-bottom-left-radius: 20px;
                                               border-bottom-right-radius: 0px;
                                               opacity: 0.3;}''')

        self.pushButton_dlg.setStyleSheet('''QPushButton{
                                               width: 120px;
                                               height: 40px;
                                               color:white;
                                               background: rgba(0,0,0,0.5);
                                               border-top-left-radius: 0px;
                                               border-top-right-radius: 20px;
                                               border-bottom-left-radius: 0px;
                                               border-bottom-right-radius: 20px;
                                               opacity: 0.3;}''')
        self.p.send_now("L110 S61")
        self.p.send_now("L110 S61")
        self.p.send_now("L110 S61")
    def dyk_use(self):
        # self.pushButton_dyk.setStyleSheet('''QPushButton{background: rgba(255,255,255,0.5);;
        #                                         border-radius: 15px;
        #                                         border: 1px solid rgba(0,0,0,0.05);color:#FFFFFF}''')
        # self.pushButton_dlg.setStyleSheet('''QPushButton{background: rgba(0,0,0,0.3);;
        #                                                     border-radius: 15px;
        #                                                     border: 1px solid rgba(0,0,0,0.05);color:#FFFFFF}''')
        self.pushButton_dyk.setStyleSheet('''QPushButton{
                                            width: 120px;
                                            height: 40px;
                                            color:white;
                                            background: rgba(0,0,0,0.5);
                                            border-top-left-radius: 20px;
                                            border-top-right-radius: 0px;
                                            border-bottom-left-radius: 20px;
                                            border-bottom-right-radius: 0px;
                                            opacity: 0.5;}''')

        self.pushButton_dlg.setStyleSheet('''QPushButton{
                                            width: 120px;
                                            height: 40px;
                                            color:white;
                                            background: rgba(0,0,0,0.3);
                                            border-top-left-radius: 0px;
                                            border-top-right-radius: 20px;
                                            border-bottom-left-radius: 0px;
                                            border-bottom-right-radius: 20px;
                                            opacity: 0.5;}''')
        self.p.send_now("L110 S60")
        self.p.send_now("L110 S60")
        self.p.send_now("L110 S60")

    def changeLanguage(self):
            if self.comboBox.currentText() == "中文":
                self.labelvector.setText("主页")
                self.label_task.setText("任务")
                self.label_change.setText("调校")
                self.label_message.setText("信息")
                self.label_system.setText("系统")
                self.label_sbbh.setText("设备编号")
                self.label.setText("信息")
                self.label_2.setText("系统版本号:")
                self.label_5.setText("软件版本号:")
                self.label_6.setText("控制版本号:")
                self.label_9.setText("IP地址:")
                self.label_11.setText("授权:")

                self.label_12.setText("应用")
                self.label_13.setText("语言:")
                self.label_update.setText("更新")
                self.label_exit.setText("退出")
                self.label_reset.setText("复位")
                self.label_shutdown.setText("关机")
                self.label_restart.setText("重启")
                self.label_historyfile.setText("日志文件")
                self.label_historycontent.setText("内容")
                self.labelvector_2.setText("打开")
                self.label_errxc.setText("X轴故障")
                self.label_erryc.setText("Y轴故障")
                self.label_errzc.setText("Z轴故障")
                self.label_errec.setText("E轴故障")

                self.label_29.setText("打印速度")
                self.label_e255.setText("挤  出  率")
                self.label_31.setText("风扇速率")

                self.label_36.setText("当  前  值：")
                self.label_37.setText("当前速度：")
                self.label_39.setText("当前速率：")
                self.label_print_targetspeed.setText("目标速度：")
                self.label_jcl.setText("目  标  值：")
                self.label_fan_speed.setText("当前速率：")

                self.label_32.setText("断料检测")
                self.pushButton_dyk.setText("开")
                self.pushButton_dlg.setText("关")
                self.label_33.setText("喷嘴")
                self.lineEdit_pid.setPlaceholderText("在此输入")
                #self.pushButton_pid.setText("关")

                self.label_e255_3.setText("调平")
                self.pushButton_tp.setText("调平")
                self.lineEdit_send.setPlaceholderText("在此输入")
                self.label_e255_2.setText("控制台")

                self.label_historyfile_2.setText("本地")
                self.labelvector_3.setText("短按添加到本地")
                self.label_historyfile_3.setText("U盘")

                self.label_14.setText("总时间：")
                self.label_titlesy.setText("剩余时间:")
                self.label_17.setText("切  片")
                self.pushButton_startprint.setText("  开始")
                self.pushButton_stopprint.setText("  停止")
                self.pushButton_closecamera.setText("关闭")
                self.pushButton_jp.setText("截屏")
                self.label_18.setText("喷头")
                self.label_23.setText("热床")
                self.label_30.setText("当前温度")
                self.label_35.setText("设置温度")
                self.label_15.setText("复位")
                self.label_27.setText("喷头挤出")
                self.label_temppt_3.setText("单位:mm")
                self.label_pengtou_targ_temp.setText("目标温度")
                self.label_bed_targ_temp.setText("目标温度")
            else:
                self.labelvector.setText("Home")
                self.label_task.setText("Jobs")
                self.label_change.setText("Tune")
                self.label_message.setText("Info")
                self.label_system.setText("System")
                self.label_sbbh.setText("MachainID")
                self.label.setText("Info")
                self.label_2.setText("SystemVersion:")
                self.label_5.setText("SoftVersion:")
                self.label_6.setText("ControlVersion:")
                self.label_9.setText("IPAdress:")
                self.label_11.setText("Accredit:")
                self.label_12.setText("APP")
                self.label_13.setText("Language:")
                self.label_update.setText("update")
                self.label_exit.setText("Exit")
                self.label_reset.setText("Reset")
                self.label_shutdown.setText("ShutDown")
                self.label_restart.setText("Restart")
                self.label_historyfile.setText("Message")
                self.label_historycontent.setText("Content")
                self.labelvector_2.setText("Open")
                self.label_errxc.setText("X-axis fault")
                self.label_erryc.setText("Y-axis fault")
                self.label_errzc.setText("Z-axis fault")
                self.label_errec.setText("E-axis fault")

                self.label_29.setText("PrintSpeed")
                self.label_e255.setText("ESpeed")
                self.label_31.setText("FanSpeed")

                self.label_36.setText("CurrentValue")
                self.label_37.setText("SetValue")

                self.label_36.setText("CurrentValue：")
                self.label_37.setText("CurrentSpeed：")
                self.label_39.setText("CurrentRate：")
                self.label_print_targetspeed.setText("EndSpeed：")
                self.label_jcl.setText("EndValue：")
                self.label_fan_speed.setText("CurrentRate：")


                self.label_32.setText("Filament Broken")
                self.pushButton_dyk.setText("Open")
                self.pushButton_dlg.setText("Close")
                self.label_33.setText("Extrude")
                self.lineEdit_pid.setPlaceholderText("Input Here")
                #self.pushButton_pid.setText("Close")

                self.label_e255_3.setText("Level")
                self.pushButton_tp.setText("Leveling")
                self.lineEdit_send.setPlaceholderText("Input Here")
                self.label_e255_2.setText("Control")

                self.label_historyfile_2.setText("Local")
                self.labelvector_3.setText("UpdateToLocal")
                self.label_historyfile_3.setText("UDisk")

                self.label_14.setText("Totle：")
                self.label_titlesy.setText("Left:")
                self.label_17.setText("Gcode")
                self.pushButton_startprint.setText("START")
                self.pushButton_stopprint.setText("STOP")
                self.pushButton_closecamera.setText("X")
                self.pushButton_jp.setText("Capt")
                self.label_18.setText("Extrude")
                self.label_23.setText("Bed")
                self.label_30.setText("CTemp")
                self.label_35.setText("Stemp")
                self.label_15.setText("Reset")
                self.label_27.setText("E")
                self.label_temppt_3.setText("Unit:mm")
                self.label_pengtou_targ_temp.setText("Stemp：")
                self.label_bed_targ_temp.setText("Stemp：")
                self.label_temppt.setText("CTemp："+str(self.current_pengtou_temp)+"℃")
                self.label_temprc.setText("CTemp："+str(self.current_bed_temp)+"℃")



    def do_move_e_left(self, feed=3000):
        feed = 400
        self.p.send_now("G91")
        self.p.send_now("L1 " + 'E-' + str(self.distance_use) + " F" + str(feed))
        self.p.send_now("G90")
        logger_a.info("SEND" + str("G1 " + 'E-' + str(self.distance_use) + " F" + str(feed)) + "SUCCESS!")

    def do_move_e_right(self, feed=3000):
        feed = 200
        self.p.send_now("G91")
        self.p.send_now("L1 " + 'E' + str(self.distance_use) + " F" + str(feed))
        self.p.send_now("G90")
        logger_a.info("SEND" + str("G1 " + 'E' + str(self.distance_use) + " F" + str(feed)) + "SUCCESS!")


    def lineEdit_ptset_use_set(self):
        try:
            self.keyboard.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
            self.keyboard.show()
            self.keyboard.pushButton_ok.clicked.connect(self.ext_sure)
            self.set_ext_flag = 1
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def ext_sure(self):
        if self.set_ext_flag:
            wendu = self.keyboard.lineEdit.text()
            self.lineEdit_ptset.setText(wendu+"℃")
            self.set_extru_target()
            self.keyboard.lineEdit.setText("")
            self.keyboard.content_line = ""
            self.keyboard.hide()
            self.set_ext_flag = 0


            logger_a.info("SET EXTRU TEMP:" + str(wendu) + " success!")

    def set_extru_target(self):
        try:
            self.p.send_now("M104 S" + self.lineEdit_ptset.text())
        except Exception as e:
            logger_a.error(str(e), 'error file:{}'.format(e.__traceback__.tb_frame.f_globals["__file__"]),
                           'error line:{}'.format(e.__traceback__.tb_lineno))
            self.lineEdit_extru_target.setText("Err")

    def lineEdit_printspeed_use_set(self):
        try:
            self.keyboard.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
            self.keyboard.show()
            self.keyboard.pushButton_ok.clicked.connect(self.sss_sure)
            self.sss_flag = 1
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def sss_sure(self):
        if self.sss_flag:
            wendu = self.keyboard.lineEdit.text()
            self.lineEdit_printspeed.setText(wendu+"%")
            self.set_printspeed()
            self.keyboard.lineEdit.setText("")
            self.keyboard.content_line = ""
            self.keyboard.hide()
            self.sss_flag = 0

            logger_a.info("SET PRINT SPEED:" + str(wendu) + " success!")

    def set_printspeed(self):
        speed = self.lineEdit_printspeed.text()
        if speed != "":
            self.p.send_now('M220 S' + str(speed))

    def lineEdit_jcl_use_set(self):
        try:
            self.keyboard.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
            self.keyboard.show()
            self.keyboard.pushButton_ok.clicked.connect(self.fff_sure)
            self.fff_flag = 1
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def fff_sure(self):
        if self.fff_flag:
            wendu = self.keyboard.lineEdit.text()
            self.lineEdit_jcl.setText(wendu+"%")
            self.set_meflu()
            self.keyboard.lineEdit.setText("")
            self.keyboard.content_line = ""
            self.keyboard.hide()
            self.fff_flag = 0

    def set_meflu(self):
        speed = self.lineEdit_jcl.text()
        if speed != "":
            self.p.send_now('M221 S' + str(speed))

    def lineEdit_fanspeed_use_set(self):
        try:
            self.keyboard.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
            self.keyboard.show()
            self.keyboard.pushButton_ok.clicked.connect(self.fsfs_sure)
            self.fsfs_flag = 1
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def fsfs_sure(self):
        if self.fsfs_flag:
            wendu = self.keyboard.lineEdit.text()
            self.lineEdit_fanspeed.setText(wendu+"%")
            self.set_fanspeed()
            self.keyboard.lineEdit.setText("")
            self.keyboard.content_line = ""
            self.keyboard.hide()
            self.fsfs_flag = 0

            logger_a.info("SET FAN SPEED:", str(wendu), " success!")

    def set_fanspeed(self):
        speed = self.lineEdit_fanspeed.text()
        if speed != "":
            self.p.send_now('M106 S' + str(speed))

    def lineEdit_rcset_use_set(self):
        try:
            self.keyboard.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
            self.keyboard.show()
            self.keyboard.pushButton_ok.clicked.connect(self.bed_sure)
            self.set_bed_flag = 1
        except Exception as e:
            print(e)

    def bed_sure(self):
        if self.set_bed_flag:
            wendu = self.keyboard.lineEdit.text()
            if int(wendu)>=90:
                wendu = '90'
            self.lineEdit_rcset.setText(wendu+"℃")
            self.set_bed_target()
            self.keyboard.lineEdit.setText("")
            self.keyboard.content_line = ""
            self.keyboard.hide()
            self.set_bed_flag = 0

            logger_a.info("SET BED TEMP:" + str(wendu) + " success!")

    def set_bed_target(self):
        send_massage = self.lineEdit_rcset.text()
        self.p.send_now("M140 S" + send_massage)

    def lineEdit_pid_use_set(self):
        try:
            self.keyboard.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
            self.keyboard.show()
            self.keyboard.pushButton_ok.clicked.connect(self.sendpid_sure)
            self.keyboard.pushButton_cancel.clicked.connect(self.sendpid_sure)
            self.sendpid_flag = 1
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def sendpid_sure(self):
        try:
            if self.sendpid_flag:
                wendu = self.keyboard.lineEdit.text()
                self.lineEdit_pid.setText(wendu)
                self.keyboard.lineEdit.setText("")
                self.keyboard.content_line = ""
                self.keyboard.hide()
                self.sendpid_flag = 0
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def lineEdit_send_use_set(self):
        try:
            self.keyboard.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
            self.keyboard.show()
            self.keyboard.pushButton_ok.clicked.connect(self.sendline_sure)
            self.sendline_flag = 1
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def sendline_sure(self):
        try:
            if self.sendline_flag:
                wendu = self.keyboard.lineEdit.text()
                self.lineEdit_send.setText(wendu)
                self.keyboard.lineEdit.setText("")
                self.keyboard.content_line = ""
                self.keyboard.hide()
                self.sendline_flag = 0
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def g28xy(self):  # 开启底板调平
        self.p.send_now("G28")
        self.p.send_now("L29")
        self.diban_new = None

    def sendline(self):
        try:
            send_buff = self.lineEdit_send.text()
            aaa_content = self.textEdit_send.toPlainText()
            if aaa_content.count("\n") > 10:
                self.textEdit_sendline.clear()
            self.textEdit_send.append("Inlong:" + send_buff + "\n")
            if "G1" in send_buff:
                self.p.send_now("G91")
                self.p.send_now(send_buff)
                self.p.send_now("G90")
            else:
                self.p.send_now(send_buff)

            logger_a.info("SEND:" + str(send_buff) + " SUCCESS!")
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    # 暂停打印
    def cancelprint(self):
        try:
            if DEBUG==1:
                self.p.printing=True
            if self.p.printing or self.p.paused:
                logger_a.info("结束打印")
                if self.comboBox.currentText() == "中文":
                    self.ui_log_cancelprint = ui_dialog_log("zhuyi", "CN", "是否停止打印？")
                else:
                    self.ui_log_cancelprint = ui_dialog_log("yindao", "EN", "STOP PRINTING?")
                self.ui_log_cancelprint.pushButton_2.clicked.connect(self.exit_log_cancelprint)
                self.ui_log_cancelprint.pushButton.clicked.connect(self.exit_log_cancel_2)

                self.ui_log_cancelprint.show()
        except Exception as e:
            print(e)

    def exit_startprintno(self):
        try:
            self.ui_log_startprint.deleteLater()
        except Exception as e:
            print(e)
    #根据当前按钮状态，改变按钮图标和文字
    from enum import Enum

    class BT_STATE(Enum):
        START = 1
        PAUSE = 2
        RESUME = 3
    def changeStartprintCaption(self,istation):
        if self.BT_STATE.START==istation:#start
            self.pushButton_startprint.setStyleSheet('''QPushButton{
                                                width: 80px;
                                                height: 80px;
                                                color:white;
                                                background: rgba(0,0,0,0.3);
                                                border-top-left-radius: 40px;
                                                border-top-right-radius: 40px;
                                                border-bottom-left-radius: 40px;
                                                border-bottom-right-radius: 40px;
                                                opacity: 0.3;}''')

            icon = QIcon("./Image/startprint.png")  # 设置startprint图标
            self.pushButton_startprint.setIcon(icon)
            self.pushButton_startprint.setIconSize(QSize(60, 60))  # 设置图标为 48x48 像素
            #pass
        if self.BT_STATE.PAUSE == istation:#pause
            self.pushButton_startprint.setStyleSheet('''QPushButton{
                                                width: 80px;
                                                height: 80px;
                                                color:white;
                                                background:  #F25F0D;
                                                border-top-left-radius: 40px;
                                                border-top-right-radius: 40px;
                                                border-bottom-left-radius: 40px;
                                                border-bottom-right-radius: 40px;
                                                opacity: 0.3;}''')

            #############
            icon = QIcon("./Image/pause.png")  # 设置startprint图标
            self.pushButton_startprint.setIcon(icon)
            self.pushButton_startprint.setIconSize(QSize(60, 60))  # 设置图标为 48x48 像素
            #pass
        elif self.BT_STATE.RESUME==istation:#resume
                self.pushButton_startprint.setStyleSheet('''QPushButton{
                                                    width: 80px;
                                                    height: 80px;
                                                    color:white;
                                                    background: rgba(0,0,0,0.3);
                                                    border-top-left-radius: 40px;
                                                    border-top-right-radius: 40px;
                                                    border-bottom-left-radius: 40px;
                                                    border-bottom-right-radius: 40px;
                                                    opacity: 0.3;}''')

                icon = QIcon("./Image/startprint.png")  # 设置startprint图标
                self.pushButton_startprint.setIcon(icon)
                self.pushButton_startprint.setIconSize(QSize(60, 60))  # 设置图标为 48x48 像素

            #pass

    def printfile(self):
        try:
            if (self.pushButton_startprint.text().strip() == "START") or self.pushButton_startprint.text().strip() == "开始":
                logger_a.info("打印开始")
                if not self.fgcode:
                    logger_a.info("No file loaded. Please use load first.")
                    if DEBUG==0:
                        return
                if not self.p.online:
                    logger_a.info("Not connected to printer.")
                    if DEBUG == 0:
                        return
                if self.comboBox.currentText() == "中文":
                    self.ui_log_startprint = ui_dialog_log("zhuyi", "CN", "确认开始打印？")
                else:
                    self.ui_log_startprint = ui_dialog_log("zhuyi", "EN", "Please confirm that Start Print?")
                #self.flag_closedoor___ = 0
                self.p.send_now("L109 time:" + time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()) + "#" + str(
                    self.filename) + "#")
                self.ui_log_startprint.pushButton.clicked.connect(self.exit_startprintno)
                self.ui_log_startprint.pushButton_2.clicked.connect(self.exit_starprint_ok)
                self.ui_log_startprint.show()

            elif (self.pushButton_startprint.text().strip() == "PAUSE") or (self.pushButton_startprint.text().strip() == "暂停"):
                logger_a.info("打印暂停")
                if self.comboBox.currentText() == "中文":
                    self.ui_log_pauseprint = ui_dialog_log("zhuyi", "CN", "是否暂停打印？")
                else:
                    self.ui_log_pauseprint = ui_dialog_log("zhuyi", "EN", "PAUSE PRINTING?")
                self.ui_log_pauseprint.pushButton_2.clicked.connect(lambda: self.exit_log_pause("normal"))
                self.ui_log_pauseprint.pushButton.clicked.connect(self.exit_log_pause_2)
                self.ui_log_pauseprint.show()
                #############
            elif (self.pushButton_startprint.text().strip() == "RESUME") or (self.pushButton_startprint.text().strip() == "恢复"):
                logger_a.info("打印恢复")

                if self.comboBox.currentText() == "中文":
                    self.ui_log_resume = ui_dialog_log("zhuyi", "CN", "是否恢复打印？")
                else:
                    self.ui_log_resume = ui_dialog_log("zhuyi", "EN", "RESUME PRINTING?")
                self.ui_log_resume.pushButton_2.clicked.connect(self.exit_log_resume)
                self.ui_log_resume.pushButton.clicked.connect(self.exit_log_resume_2)
                self.ui_log_resume.show()

                # else:
                #    if self.checkBox_language.currentText() == "中文":
                #        self.ui_log = ui_dialog_log("zhuyi", "CN", "安全继电器状态错误\n恢复打印失败\n确定后请关门并确定状态")
                #    else:
                #        self.ui_log = ui_dialog_log("zhuyi", "EN",
                #                                    "Safety relay status error \n "
                #                                    "Print recovery failure \n "
                #                                    "After confirmation, please close the door and determine the status")
                #    self.ui_log.pushButton.clicked.connect(self.exit_log_pause_2)
                #    self.ui_log.pushButton_2.clicked.connect(self.exit_log_pause_2)
                #    self.ui_log.show()

        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def exit_log_resume_2(self):
        try:
            self.ui_log_resume.deleteLater()
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))


    def exit_log_resume(self):
        try:
            if self.comboBox.currentText() == "中文":
                self.pushButton_startprint.setText("  暂停")
            elif self.comboBox.currentText() == "English":
                self.pushButton_startprint.setText("PAUSE")
            elif self.comboBox.currentText() == "日本語.":
                self.pushButton_startprint.setText("休止")

            self.timer_use_left.start()
            self.p.send_now("L109")
            self.p.send_now("M109 S" + self.p.extru_temp_history)  # 恢复喷头温度

            self.p.resume()
            self.clogging_detection("start")
            logger_a.info("RESUME PRINT SUCCESS!")
            self.ui_log_resume.deleteLater()
            self.brokening = False
            self.changeStartprintCaption(self.BT_STATE.PAUSE)
        except Exception as e:
            print(e)

    def exit_log_pause_2(self):
        try:
            self.ui_log_pauseprint.deleteLater()
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def exit_log_pause(self, a):
        try:
            if self.comboBox.currentText() == "中文":
                self.pushButton_startprint.setText("  恢复")
            elif self.comboBox.currentText() == "English":
                self.pushButton_startprint.setText("RESUME")
            elif self.comboBox.currentText() == "日本語.":
                self.pushButton_startprint.setText("履歴")
            if self.flag_D == True:
                self.p.send_now("G91\n")
                self.p.send_now("G1 E270 F400\n")
                self.p.send_now("G90\n")
                self.flag_D = False
            self.jichu_flag = 0

            self.p.pause()
            self.timer_use_left.stop()
            if a == "sys":
                self.p.send_now("G250 S889\n")  # 红灯
            else:
                self.p.send_now("G250 S888\n")  # 暂停打印亮蓝灯

            self.clogging_detection("stop")
            logger_a.info("PAUSE PRINT SUCCESS!")
            self.ui_log_pauseprint.deleteLater()
            self.changeStartprintCaption(self.BT_STATE.RESUME)
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def exit_starprint_ok(self):
        try:
            if True:
                if True:
                    # 剩余时间初始化0s
                    self.label_totletime.setText("")
                    # 进度条置0隐藏
                    self.progressBar.setValue(0)
                    self.progressBar.show()
                    # 总时间显示
                    self.label_titlesy.show()
                    self.label_sy.show()
                    self.label_sy.setText("")

                    self.runtime_left = 0
                    if self.comboBox.currentText() == "中文":
                        self.pushButton_startprint.setText("暂停")
                    elif self.comboBox.currentText() == "English":
                        self.pushButton_startprint.setText("PAUSE")
                    elif self.comboBox.currentText() == "日本語.":
                        self.pushButton_startprint.setText("休止")

                    #已经在打印了  设置为暂停图标
                    # 设置图标
                    # icon = QIcon("./Image/pause.png")  # 设置startprint图标
                    # self.pushButton_startprint.setIcon(icon)
                    self.changeStartprintCaption(self.BT_STATE.PAUSE)

                    self.sdprinting = False
                    self.p.startprint(self.fgcode)
                    # self.p.send_now("G250 S901")
                    self.flag_printing = 1
                    self.time_tole_10min = 0
                    self.brokening = False
                    self.blocking = False
                    logger_a.info("START PRINT SUCCESS!")

                    self.data___ = str(time.strftime("%Y-%m-%d-%H-%M", time.localtime()))
                    self.flag_ble = 1

                    # M290补偿
                    file = open("./File/m209_save.txt", "r")
                    nnn = file.readlines()
                    file.close()
                    self.m209_save_num = float(nnn[0].split(":")[1].replace("\\n", ""))
                    num = round(round(self.m209_save_num, 1) / 0.1, 0)
                    self.clogging_detection("start")
                    self.ui_log_startprint.deleteLater()
                    self.p.send_now("L110 S81")
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def clogging_detection(self, identification):  # 开启和关闭堵料检测
        if identification == "start":
            self.p.send_now("M257 S1")  # 开始断堵料检测
        elif identification == "stop":
            self.p.send_now("M257 S0")  # 关闭断堵料检测

    def exit_log_cancel_2(self):
        try:
            self.ui_log_cancelprint.deleteLater()
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def exit_log_cancelprint(self):
        try:
            if self.comboBox.currentText() == "中文":
                self.pushButton_startprint.setText("  开始")
            elif self.comboBox.currentText() == "English":
                self.pushButton_startprint.setText("START")
            elif self.comboBox.currentText() == "日本語.":
                self.pushButton_startprint.setText("スタート")

            self.timer_use_left.stop()
            self.rece_E_flag = 0
            self.current_E_jichu = 0.0
            self.print_time = 0  # 已打印时间
            self.print_left_time = 0  # 剩余打印时间
            self.print_total_time = 0  # 总打印时间

            self.p.cancelprint()
            self.clogging_detection("stop")
            self.p.send_now("G250 S891")  # 结束打印亮蓝灯
            self.p.send_now("M104 S0")
            self.p.send_now("M140 S0")
            self.p.send_now("G250 S900")  # 开空气过滤器

            self.p.send_now("L109")
            self.brokening = False

            self.flag_printing = 0
            self.time_tole_10min = 0
            logger_a.info("CANCEL PRINT SUCCESS!")
            self.ui_log_cancelprint.deleteLater()

            self.flag_ble = 0,
            self.jichu_flag = 0
            self.p.send_now("L110 S81")

            # 剩余时间初始化0s
            self.label_totletime.setText("")
            # gcode初始化
            self.label_16.setText("")
            # 进度条置0隐藏
            self.progressBar.setMaximum(100)
            self.progressBar.setMinimum(0)
            self.progressBar.setValue(0)
            self.progressBar.hide()
            # 总时间隐藏
            self.label_titlesy.hide()
            self.label_sy.hide()
            self.changeStartprintCaption(self.BT_STATE.START)
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def confim_choose_gcodefile(self):
        try:
            self.openFile.hide()
            self.gcodename = "./GCODE/" + self.choose_gcodefile
            if self.gcodename == "./GCODE/":
                return

            #if self.checkBox_language.currentText() == "中文":
            #    #self.ui_log_tanchuang = ui_dialog_log("zhuyi", "CN", "Gcode正在加载，请稍等")
            #    self.lineEdit_gcode.setText("Gcode 加载中.....")
            #else:
            #    #self.ui_log_tanchuang = ui_dialog_log("zhuyi", "EN", "Gcode is loading， \n please wait for a moment")
            #    self.lineEdit_gcode.setText("Gcode loading.....")
            ## self.lineEdit_gcode.setText("Gcode loading.....")
            self.ui_log_loaggcode = ui_dialog_log("zhuyi", "CN","Gcode is loading， \n please wait for a moment")#20221020
            self.ui_log_loaggcode.pushButton.hide()  # 20221020
            self.ui_log_loaggcode.pushButton_2.hide()  # 20221020
            self.ui_log_loaggcode.show()  # 20221020
            self.load_gcode_async(self.gcodename)
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))


    def calculate_E_total(self, file):
        try:
            eeee = 0
            file = open(file, "r")
            readlines = file.readlines()
            file.close()
            for i in range(len(readlines)):
                add_num = ""
                if not readlines[i].startswith(";"):
                    if "G1" in readlines[i]:
                        if ";" in readlines[i]:
                            readlines[i] = readlines[i].split(";")[0]
                        if "E" in readlines[i]:
                            add_num += "E"
                            if "E-" not in readlines[i]:
                                e_dis = readlines[i].split("E")[1].split(" ")[0]
                                eeee += float(e_dis)
                            else:
                                e_dis = readlines[i].split("E-")[1].split(" ")[0]
                                eeee -= float(e_dis)
            logger_a.info("total E:" + str(eeee))
            return eeee
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def load_gcode(self, filename, layer_callback=None, gcode=None):
        try:
            if gcode is None:
                self.fgcode = gcoder.LightGCode(deferred=True)
            else:
                self.fgcode = gcode
                print(self.fgcode)
            extrusion_width = self.fgcode.prepare(open(filename, "r", encoding="utf-8"), layer_callback=layer_callback)
            self.fgcode.estimate_duration()
            self.filename = filename
            self.Extruder_gcode = float(
                extrusion_width.replace("; external perimeters extrusion width = ", "").replace("mm", ""))



            for i in range(5):
                if float(self.comboBox_2.itemText(i)) ==  self.Extruder_gcode:
                    self.comboBox_2.setCurrentIndex(i)
                    break
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))


    def load_gcode_async_thread(self, gcode):
        try:
            self.load_gcode(self.filename, gcode=gcode)
            self.total_E = self.calculate_E_total(self.filename)
            self.event_loadGcode_OK.emit("OK")

        except Exception as e:
            logger_a.error(str(e), 'error file:{}'.format(e.__traceback__.tb_frame.f_globals["__file__"]),
                           'error line:{}'.format(e.__traceback__.tb_lineno))
    def exit_tanchuang(self):
        try:
            self.ui_log_loaggcode.deleteLater()
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def loadGcode_ui_log(self, a):
        try:
            if a == "OK":
                self.exit_tanchuang()
                self.label_16.setText(self.filename.split("/")[-1])
                self.lineEdit_gcodefile.setText(self.filename.split("/")[-1])
        except Exception as e:
            logger_a.error(str(e), 'error file:{}'.format(e.__traceback__.tb_frame.f_globals["__file__"]),
                           'error line:{}'.format(e.__traceback__.tb_lineno))

    def load_gcode_async(self, filename):
        try:
            self.filename = filename
            gcode = self.pre_gcode_load()
            self.t1 = threading.Thread(target=self.load_gcode_async_thread, args=(gcode,))
            self.t1.start()
            logger_a.info("LOAD GCODE SUCCESS!")
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def pre_gcode_load(self):
        try:
            self.loading_gcode = True
            gcode = gcoder.GCode(deferred=1, cutting_as_extrusion=0)
            return gcode
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def save_u(self):
        try:
            if self.choose_name != "":
                # if not os.path.exists(self.lst_list[0]+self.choose_name):
                if not os.path.exists(self.usbpath() + self.choose_name):
                    self.ui_uuu = ui_dialog_log("zhuyi", "No existed file!\n Please update udisk!")
                    self.ui_uuu.pushButton.clicked.connect(self.exit_uuu_cance)
                    self.ui_uuu.pushButton_2.clicked.connect(self.exit_uuu_cance)
                    self.ui_uuu.show()
                    return
                self.pushButton_insert.setDisabled(True)
                file = open("./GCODE/" + self.choose_name, "a+")
                file.close()
                # copyfile(self.lst_list[0]+self.choose_name,"./GCODE/"+self.choose_name)
                copyfile(self.usbpath() + self.choose_name, "./GCODE/" + self.choose_name)

                logger_a.info("SAVE:" + str("./GCODE/" + self.choose_name) + " SUCCESS!")

                self.get_local()  # 导入后增加自己刷新本地记录
                self.pushButton_insert.setDisabled(False)
        except IOError as e:
            logger_a.info("Unable to copy file. %s" % e)

    def update_gcodefile(self):
        self.open_gcodefile = os.listdir("./GCODE")
        slm = QStringListModel()  # 创建mode
        self.open_gcodefile = sorted(self.open_gcodefile,
                                     key=lambda file: os.path.getmtime(os.path.join("./GCODE", file)))
        self.open_gcodefile.reverse()
        slm.setStringList(self.open_gcodefile)  # 将数据设置到model
        self.openFile.listView_file.setModel(slm)  # 绑定 listView 和 model
        self.openFile.listView_file.clicked.connect(self.clickedgcodefile)  # listview 的点击事件

    def clickedgcodefile(self, qModelIndex):
        try:
            self.choose_gcodefile = self.open_gcodefile[qModelIndex.row()]
            logger_a.info("UPDATE gcode:" + self.choose_gcodefile + "SUCCESS!")
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def loadGcodeFile(self):
        try:
            self.label_totletime.setText("")
            self.label_sy.setText("")
            self.current_E_jichu = 0.0  # clear total E when change gcode file, otherwise or not
            self.update_gcodefile()
            self.openFile.show()
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def get_u(self):
        try:
            # ret_driver = self.get_all_drives() #获取所有盘符
            # self.lst_list = self.get_u_disk(ret_driver) #遍历当前低于40G的盘符
            #
            # if len(self.lst_list) == 0:
            #     self.listView_udisk.hide()
            #     return
            # else:
            #     self.listView_udisk.show()
            # a = len(self.lst_list)
            # if len(self.lst_list) != 0:
            #     for i in range(a):
            #         if "C:" in self.lst_list[i]:
            #             self.lst_list.remove(self.lst_list[i])
            #             break
            self.file_use_u = []
            # self.file_list = os.listdir(self.lst_list[0])
            self.file_list = os.listdir(self.usbpath())
            # self.file_list = os.listdir(self.usbpath)
            for i in self.file_list:
                if ".gcode" in i:
                    self.file_use_u.append(i)
            slm = QStringListModel()  # 创建mode
            slm.setStringList(self.file_use_u)  # 将数据设置到model
            self.listView_udisk.setModel(slm)  ##绑定 listView 和 model
            self.listView_udisk.clicked.connect(self.u_clickedlist)  # listview 的点击事件
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def sh(self, command, print_msg=True):
        p = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        result = p.stdout.read().decode("GBK", errors="ignore")
        if print_msg:
            logger_a.info(result)
        return result

    def usbpath(self):
        if os.name == 'nt':
            disks = self.sh("wmic logicaldisk get deviceid, description",
                            print_msg=False).split('\n')
            for disk in disks:
                if '可移动磁盘' in disk or 'Removable' in disk:
                    return re.search(r'\w:', disk).group()
        elif os.name == 'posix':
            return self.sh('ll -a /media')[-1].strip()
        else:
            return self.sh('ls /Volumes')[-1].strip()

    def u_clickedlist(self, qModelIndex):
        try:
            self.choose_name = self.file_use_u[qModelIndex.row()]
            if os.path.exists(self.choose_name):
                logger_a.info("No exist file,please click enter!")
                return
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def get_local(self):
        self.file_list_now = os.listdir("./GCODE")
        slm = QStringListModel()  # 创建mode
        self.file_list_now = sorted(self.file_list_now,
                                    key=lambda file: os.path.getmtime(os.path.join("./GCODE", file)))
        self.file_list_now.reverse()
        slm.setStringList(self.file_list_now)
        # slm.setStringList(self.file_list_now)  # 将数据设置到model
        self.listView_now.setModel(slm)  # 绑定 listView 和 model
        self.listView_now.clicked.connect(self.local_clickedlist)  # listview 的点击事件

        logger_a.info("GET GCODE SUCCESS!")

    def local_clickedlist(self, qModelIndex):
        self.choose_local_name = self.file_list_now[qModelIndex.row()]

    def local_clickedlist_history(self, qModelIndex):
        try:
            self.choose_err_int = qModelIndex.row()
        except Exception as e:
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def update_log(self):
        self.listWidget_now_history.clear()
        self.unread_quantity = 0
        sel = Operational_Sqlite.select_date("SELECT ID, title, status FROM print_information ORDER BY ID DESC")
        for i in range(len(sel[1])):
            item = QListWidgetItem(sel[1][i][1].replace("LOBOTICS","INLONG") + "-" + str(sel[1][i][0]))
            if sel[1][i][2] == "True":
                item.setBackground(QColor(53, 116, 1))
                self.unread_quantity += 1
            else:
                item.setBackground(QColor(53, 116, 1, 0))
            self.listWidget_now_history.addItem(item)
            if i >= 100:
                break
        if self.unread_quantity > 0:
            #self.label_5.show()
            #self.label_5.setText(str(self.unread_quantity))
            pass
        else:
            #self.label_5.hide()
            pass

    def open_file(self):
        if self.choose_err_int is None:
            return
        self.textEdit_history.clear()
        ID = self.listWidget_now_history.item(self.choose_err_int).text().split("-")[1]
        sel = Operational_Sqlite.select_date("SELECT title, inf, time, status FROM print_information WHERE ID=" + ID)
        if sel[0] == 'ok':
            #self.label_CONTENT.setText(self.listWidget_now_history.item(self.choose_err_int).text().replace("LOBOTICS","INLONG"))
            self.textEdit_history.append(sel[1][0][0].replace("LOBOTICS","INLONG"))
            self.textEdit_history.append(sel[1][0][1])
            self.textEdit_history.append(sel[1][0][2])
            if sel[1][0][3] == "True":
                sql = "UPDATE print_information SET status = 'False' WHERE ID=" + ID
                up = Operational_Sqlite.update_date(sql)
                if up[0] == 'ok':
                    self.listWidget_now_history.item(self.choose_err_int).setBackground(QColor(53, 116, 1, 0))
                    self.unread_quantity -= 1
                    self.label_5.setText(str(self.unread_quantity))
                    if self.unread_quantity == 0:
                        self.label_5.hide()

    def sys_exit(self):
        logger_a.info("exit app")
        pid = os.getpid()
        prosess = psutil.Process(pid)
        prosess.terminate()
        self.destroy()
        sys.exit()

    def soft_update(self):
        try:
            pass
        except Exception as e:
            logger_a.error("Soft update fail!")
            logger_a.error(str(e) + '\nerror file:{}'.format(
                e.__traceback__.tb_frame.f_globals["__file__"]) + '\nerror line:{}'.format(e.__traceback__.tb_lineno))

    def os_shutdown(self):
        logger_a.info("shutdown")
        os.system("shutdown -s -t 3")  # 执行关机命令
        self.destroy()
        sys.exit()

    def os_restart(self):
        logger_a.info("os restart")
        os.system("shutdown -r")
        self.destroy()
        sys.exit()

    def sys_pid(self):
        if not self.lineEdit_pid.text() or self.lineEdit_pid.text() is None:
            pass
        else:
            self.p.send_now("M303 S" + self.lineEdit_pid.text())

    def MoveToVector(self):
        self.pushButton_vector.setStyleSheet("QPushButton{border-image:url(./Image/Vector.png);}")
        self.labelvector.setStyleSheet("color:#F25F0D")
        # 任务按钮
        self.pushButton_task.setStyleSheet("QPushButton{border-image:url(./Image/taskOff.png);}")
        self.label_task.setStyleSheet("color:white")
        # 调校按钮
        self.pushButton_change.setStyleSheet("QPushButton{border-image:url(./Image/changeOff.png);}")
        self.label_change.setStyleSheet("color:white")
        # 信息按钮
        self.pushButton_message.setStyleSheet("QPushButton{border-image:url(./Image/messageOff.png);}")
        self.label_message.setStyleSheet("color:white")
        # 系统按钮
        self.pushButton_system.setStyleSheet("QPushButton{border-image:url(./Image/systemOff.png);}")
        self.label_system.setStyleSheet("color:white")

        self.tabWidget.setCurrentIndex(0)

    def MoveToTask(self):
        self.pushButton_vector.setStyleSheet("QPushButton{border-image:url(./Image/VectorOff.png);}")
        self.labelvector.setStyleSheet("color:white")
        # 任务按钮
        self.pushButton_task.setStyleSheet("QPushButton{border-image:url(./Image/task.png);}")
        self.label_task.setStyleSheet("color:#F25F0D")
        # 调校按钮
        self.pushButton_change.setStyleSheet("QPushButton{border-image:url(./Image/changeOff.png);}")
        self.label_change.setStyleSheet("color:white")
        # 信息按钮
        self.pushButton_message.setStyleSheet("QPushButton{border-image:url(./Image/messageOff.png);}")
        self.label_message.setStyleSheet("color:white")
        # 系统按钮
        self.pushButton_system.setStyleSheet("QPushButton{border-image:url(./Image/systemOff.png);}")
        self.label_system.setStyleSheet("color:white")

        self.tabWidget.setCurrentIndex(1)

    def MoveToChange(self):
        self.pushButton_vector.setStyleSheet("QPushButton{border-image:url(./Image/VectorOff.png);}")
        self.labelvector.setStyleSheet("color:white")
        # 任务按钮
        self.pushButton_task.setStyleSheet("QPushButton{border-image:url(./Image/taskOff.png);}")
        self.label_task.setStyleSheet("color:white")
        # 调校按钮
        self.pushButton_change.setStyleSheet("QPushButton{border-image:url(./Image/change.png);}")
        self.label_change.setStyleSheet("color:#F25F0D")
        # 信息按钮
        self.pushButton_message.setStyleSheet("QPushButton{border-image:url(./Image/messageOff.png);}")
        self.label_message.setStyleSheet("color:white")
        # 系统按钮
        self.pushButton_system.setStyleSheet("QPushButton{border-image:url(./Image/systemOff.png);}")
        self.label_system.setStyleSheet("color:white")

        self.tabWidget.setCurrentIndex(2)

    def MoveToMessage(self):
        self.pushButton_vector.setStyleSheet("QPushButton{border-image:url(./Image/VectorOff.png);}")
        self.labelvector.setStyleSheet("color:white")
        # 任务按钮
        self.pushButton_task.setStyleSheet("QPushButton{border-image:url(./Image/taskOff.png);}")
        self.label_task.setStyleSheet("color:white")
        # 调校按钮
        self.pushButton_change.setStyleSheet("QPushButton{border-image:url(./Image/changeOff.png);}")
        self.label_change.setStyleSheet("color:white")
        # 信息按钮
        self.pushButton_message.setStyleSheet("QPushButton{border-image:url(./Image/message.png);}")
        self.label_message.setStyleSheet("color:#F25F0D")
        # 系统按钮
        self.pushButton_system.setStyleSheet("QPushButton{border-image:url(./Image/systemOff.png);}")
        self.label_system.setStyleSheet("color:white")

        self.tabWidget.setCurrentIndex(3)

    def MoveToSystem(self):
        self.pushButton_vector.setStyleSheet("QPushButton{border-image:url(./Image/VectorOff.png);}")
        self.labelvector.setStyleSheet("color:white")
        # 任务按钮
        self.pushButton_task.setStyleSheet("QPushButton{border-image:url(./Image/taskOff.png);}")
        self.label_task.setStyleSheet("color:white")
        # 调校按钮
        self.pushButton_change.setStyleSheet("QPushButton{border-image:url(./Image/changeOff.png);}")
        self.label_change.setStyleSheet("color:white")
        # 信息按钮
        self.pushButton_message.setStyleSheet("QPushButton{border-image:url(./Image/messageOff.png);}")
        self.label_message.setStyleSheet("color:white")
        # 系统按钮
        self.pushButton_system.setStyleSheet("QPushButton{border-image:url(./Image/system.png);}")
        self.label_system.setStyleSheet("color:#F25F0D")

        self.tabWidget.setCurrentIndex(4)

    def do_move_x_fuwei(self):
        print("0000000000")
        feed = 3000
        self.p.send_now("G91")
        self.p.send_now("G28 X")
        self.p.send_now("G90")
        logger_a.info("SEND" + str("G28 X") + "SUCCESS!")

    def do_move_y_fuwei(self):
        feed = 3000
        self.p.send_now("G91")
        self.p.send_now("G28 Y")
        self.p.send_now("G90")
        logger_a.info("SEND" + str("G28 Y") + "SUCCESS!")

    def do_move_z_fuwei(self):
        feed = 3000
        self.p.send_now("G91")
        self.p.send_now("G28 Z")
        self.p.send_now("G90")
        logger_a.info("SEND" + str("G28 Z") + "SUCCESS!")

    def do_homeall(self):
        self.p.send_now("G91")
        self.p.send_now("G28")
        self.p.send_now("G90")
        logger_a.info("HOME ALL SUCCESS!")

    def do_move_x_left(self, feed=3000):
        self.p.send_now("G91")
        self.p.send_now("L1 " + 'X-' + str(self.distance_use) + " F" + str(feed))
        self.p.send_now("G90")
        logger_a.info("SEND" + str("G1 " + 'X-' + str(self.distance_use) + " F" + str(feed)) + "SUCCESS!")

    def do_move_x_right(self, feed=3000):
        feed = 3000
        self.p.send_now("G91")
        self.p.send_now("L1 " + 'X' + str(self.distance_use) + " F" + str(feed))
        self.p.send_now("G90")
        logger_a.info("SEND" + str("G1 " + 'X' + str(self.distance_use) + " F" + str(feed)) + "SUCCESS!")

    def do_move_y_left(self, feed=3000):
        feed = 3000
        self.p.send_now("G91")
        self.p.send_now("L1 " + 'Y' + str(self.distance_use) + " F" + str(feed))
        self.p.send_now("G90")
        logger_a.info("SEND" + str("G1 " + 'Y-' + str(self.distance_use) + " F" + str(feed)) + "SUCCESS!")

    def do_move_y_right(self, feed=3000):
        feed = 3000
        self.p.send_now("G91")
        self.p.send_now("L1 " + 'Y-' + str(self.distance_use) + " F" + str(feed))
        self.p.send_now("G90")
        logger_a.info("SEND" + str("G1 " + 'Y' + str(self.distance_use) + " F" + str(feed)) + "SUCCESS!")

    def do_move_z_left(self, feed=3000):
        feed = 3000
        self.p.send_now("G91")
        self.p.send_now("L1 " + 'Z-' + str(self.distance_use) + " F" + str(feed))
        self.p.send_now("G90")
        logger_a.info("SEND" + str("G1 " + 'Z-' + str(self.distance_use) + " F" + str(feed)) + "SUCCESS!")

    def do_move_z_right(self, feed=3000):
        feed = 3000
        self.p.send_now("G91")
        self.p.send_now("L1 " + 'Z' + str(self.distance_use) + " F" + str(feed))
        self.p.send_now("G90")
        logger_a.info("SEND" + str("G1 " + 'Z' + str(self.distance_use) + " F" + str(feed)) + "SUCCESS!")

    def micro_zzz(self):
        self.p.send_now("M290 Z-0.1")
        logger_a.info("SEND ", "M290 Z-0.1", "SUCCESS!")

        if self.flag_printing:
            file = open("./File/m209_save.txt", "r")
            nnn = file.readlines()
            file.close()
            self.m209_save_num = float(nnn[0].split(":")[1].replace("\\n", ""))
            file = open("./File/m209_save.txt", "w")
            file.write("m209_save:" + str(self.m209_save_num - 0.1) + "\n")
            file.close()

    def micro_zzz_down(self):
        self.p.send_now("M290 Z0.1")
        logger_a.info("SEND ", "M290 Z0.1", "SUCCESS!")
        if self.flag_printing:
            file = open("./File/m209_save.txt", "r")
            nnn = file.readlines()
            file.close()
            self.m209_save_num = float(nnn[0].split(":")[1].replace("\\n", ""))
            file = open("./File/m209_save.txt", "w")
            file.write("m209_save:" + str(self.m209_save_num + 0.1) + "\n")
            file.close()
    
    def on_tp_button_clicked(self, button):
        # 获取按钮编号
        button_name = button.objectName()
        button_num = int(button_name.split('_')[-1])
        if button_num == 1:
            self.p.send_now("G1 X76.69 Y137.05 F15000")
            self.diban_new = "POS 1 "
        if button_num == 2:
            self.p.send_now("G1 X76.69 Y237.05 F15000")
            self.diban_new = "POS 2 "
        if button_num == 3:
            self.p.send_now("G1 X76.69 Y337.05 F15000")
            self.diban_new = "POS 3 "
        if button_num == 4:
            self.p.send_now("G1 X76.69 Y437.05 F15000")
            self.diban_new = "POS 4 "
        if button_num == 5:
            self.p.send_now("G1 X76.69 Y537.05 F15000")
            self.diban_new = "POS 5 "
        if button_num == 6:
            self.p.send_now("G1 X176.69 Y137.05 F15000")
            self.diban_new = "POS 10 "
        if button_num == 7:
            self.p.send_now("G1 X176.69 Y237.05 F15000")
            self.diban_new = "POS 9 "
        if button_num == 8:
            self.p.send_now("G1 X176.69 Y337.05 F15000")
            self.diban_new = "POS 8 "
        if button_num == 9:
            self.p.send_now("G1 X176.69 Y437.05 F15000")
            self.diban_new = "POS 7 "
        if button_num == 10:
            self.p.send_now("G1 X176.69 Y537.05 F15000")
            self.diban_new = "POS 6 "
        if button_num == 11:
            self.p.send_now("G1 X276.69 Y137.05 F15000")
            self.diban_new = "POS 11 "
        if button_num == 12:
            self.p.send_now("G1 X276.69 Y237.05 F15000")
            self.diban_new = "POS 12 "
        if button_num == 13:
            self.p.send_now("G1 X276.69 Y337.05 F15000")
            self.diban_new = "POS 13 "
        if button_num == 14:
            self.p.send_now("G1 X276.69 Y437.05 F15000")
            self.diban_new = "POS 14 "
        if button_num == 15:
            self.p.send_now("G1 X276.69 Y537.05 F15000")
            self.diban_new = "POS 5 "
        if button_num == 16:
            self.p.send_now("G1 X376.69 Y137.05 F15000")
            self.diban_new = "POS 20 "
        if button_num == 17:
            self.p.send_now("G1 X376.69 Y237.05 F15000")
            self.diban_new = "POS 19 "
        if button_num == 18:
            self.p.send_now("G1 X376.69 Y337.05 F15000")
            self.diban_new = "POS 18 "
        if button_num == 19:
            self.p.send_now("G1 X376.69 Y437.05 F15000")
            self.diban_new = "POS 17 "
        if button_num == 20:
            self.p.send_now("G1 X376.69 Y537.05 F15000")
            self.diban_new = "POS 16 "
        if button_num == 21:
            self.p.send_now("G1 X476.69 Y137.05 F15000")
            self.diban_new = "POS 21 "
        if button_num == 22:
            self.p.send_now("G1 X476.69 Y237.05 F15000")
            self.diban_new = "POS 22 "
        if button_num == 23:
            self.p.send_now("G1 X476.69 Y337.05 F15000")
            self.diban_new = "POS 23 "
        if button_num == 24:
            self.p.send_now("G1 X476.69 Y437.05 F15000")
            self.diban_new = "POS 24 "
        if button_num == 25:
            self.p.send_now("G1 X476.69 Y537.05 F15000")
            self.diban_new = "POS 25 "
        if button_num == 26:
            self.p.send_now("G1 X576.69 Y137.05 F15000")
            self.diban_new = "POS 30 "
        if button_num == 27:
            self.p.send_now("G1 X576.69 Y237.05 F15000")
            self.diban_new = "POS 29 "
        if button_num == 28:
            self.p.send_now("G1 X576.69 Y337.05 F15000")
            self.diban_new = "POS 28 "
        if button_num == 29:
            self.p.send_now("G1 X576.69 Y437.05 F15000")
            self.diban_new = "POS 27 "
        if button_num == 30:
            self.p.send_now("G1 X576.69 Y537.05 F15000")
            self.diban_new = "POS 26 "
        if button_num == 31:
            self.p.send_now("G1 X676.69 Y137.05 F15000")
            self.diban_new = "POS 31 "
        if button_num == 32:
            self.p.send_now("G1 X676.69 Y237.05 F15000")
            self.diban_new = "POS 32 "
        if button_num == 33:
            self.p.send_now("G1 X676.69 Y337.05 F15000")
            self.diban_new = "POS 33 "
        if button_num == 34:
            self.p.send_now("G1 X676.69 Y437.05 F15000")
            self.diban_new = "POS 34 "
        if button_num == 35:
            self.p.send_now("G1 X676.69 Y537.05 F15000")
            self.diban_new = "POS 35 "
        if button_num == 36:
            self.p.send_now("G1 X776.69 Y137.05 F15000")
            self.diban_new = "POS 40 "
        if button_num == 37:
            self.p.send_now("G1 X776.69 Y237.05 F15000")
            self.diban_new = "POS 39 "
        if button_num == 38:
            self.p.send_now("G1 X776.69 Y337.05 F15000")
            self.diban_new = "POS 38 "
        if button_num == 39:
            self.p.send_now("G1 X776.69 Y437.05 F15000")
            self.diban_new = "POS 37 "
        if button_num == 40:
            self.p.send_now("G1 X776.69 Y537.05 F15000")
            self.diban_new = "POS 36 "
        if button_num == 41:
            self.p.send_now("G1 X876.69 Y137.05 F15000")
            self.diban_new = "POS 41 "
        if button_num == 42:
            self.p.send_now("G1 X876.69 Y237.05 F15000")
            self.diban_new = "POS 42 "
        if button_num == 43:
            self.p.send_now("G1 X876.69 Y337.05 F15000")
            self.diban_new = "POS 43 "
        if button_num == 44:
            self.p.send_now("G1 X876.69 Y437.05 F15000")
            self.diban_new = "POS 44 "
        if button_num == 45:
            self.p.send_now("G1 X876.69 Y537.05 F15000")
            self.diban_new = "POS 45 "
        if button_num == 46:
            self.p.send_now("G1 X976.69 Y137.05 F15000")
            self.diban_new = "POS 50 "
        if button_num == 47:
            self.p.send_now("G1 X976.69 Y237.05 F15000")
            self.diban_new = "POS 49 "
        if button_num == 48:
            self.p.send_now("G1 X976.69 Y337.05 F15000")
            self.diban_new = "POS 48 "
        if button_num == 49:
            self.p.send_now("G1 X976.69 Y437.05 F15000")
            self.diban_new = "POS 47 "
        if button_num == 50:
            self.p.send_now("G1 X976.69 Y537.05 F15000")
            self.diban_new = "POS 46 "
        if button_num == 51:
            self.p.send_now("G1 X1076.69 Y137.05 F15000")
            self.diban_new = "POS 51 "
        if button_num == 52:
            self.p.send_now("G1 X1076.69 Y237.05 F15000")
            self.diban_new = "POS 52 "
        if button_num == 53:
            self.p.send_now("G1 X1076.69 Y337.05 F15000")
            self.diban_new = "POS 53 "
        if button_num == 54:
            self.p.send_now("G1 X1076.69 Y437.05 F15000")
            self.diban_new = "POS 54 "
        if button_num == 55:
            self.p.send_now("G1 X1076.69 Y537.05 F15000")
            self.diban_new = "POS 55 "

    def on_distance_button_clicked(self, button):
        # 获取按钮编号
        button_name = button.objectName()
        button_num = int(button_name.split('_')[-1])
        
        # 设置distance_use的值，对应关系：1-6 -> 0.1, 1, 10, 50, 100, 200
        distance_map = {
            8: 0.1,
            9: 1,
            10: 10,
            11: 50,
            12: 100,
            13: 200
        }
        #self.distance_use为选择的距离
        self.distance_use = distance_map.get(button_num)

if __name__ == "__main__":
    try:
        import sys
        app = QtWidgets.QApplication(sys.argv)
        first = Ui_mainwindow()
        first.show()
        first.showFullScreen()
        sys.exit(app.exec_())
    except Exception as e:
        print(e)