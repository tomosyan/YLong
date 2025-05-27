__version__ = "2.0.0rc8"

import sys
import time

import serial
import serial.tools.list_ports
if sys.version_info.major < 3:
    print("You need to run this on Python 3")
    sys.exit(-1)
import threading
from queue import Queue, Empty as QueueEmpty
from utils import set_utf8_locale, install_locale, decode_utf8
from loguru import logger

logger.remove(handler_id=None)
logger.add("./ServoLog/file_{time}.log", format="{time} {level} {message}", filter=lambda record: record["extra"].get("name") == "b", level="DEBUG", rotation="00:00",
           retention="15 days", catch=True,enqueue=True)
logger_b = logger.bind(name="b")
from PyQt5.QtCore import pyqtSignal, QThread

try:
    set_utf8_locale()
except:
    pass
install_locale('pronterface')

class printcore(QThread):

    def __init__(self):
        super(printcore, self).__init__()
        self.send_thread_1 = None
        self.send_thread_2 = None
        self.send_thread_3 = None
        self.priqueue_20 = Queue(0)
        self.priqueue_30 = Queue(0)
        self.priqueue_40 = Queue(0)

    def start_sender(self):
        port_list = list(serial.tools.list_ports.comports())
        self.port_name_list = [port[0] for port in port_list]
        if "COM20" in self.port_name_list:
            self.send_thread_1 = threading.Thread(target=self._sendnext_com20,
                                                  name='send thread 20')
            self.send_thread_1.start()
        if "COM30" in self.port_name_list:
            self.send_thread_2 = threading.Thread(target=self._sendnext_com30,
                                                  name='send thread 30')
            self.send_thread_2.start()
        if "COM40" in self.port_name_list:
            self.send_thread_3 = threading.Thread(target=self._sendnext_com40,
                                                  name='send thread 40')
            self.send_thread_3.start()

    def Parameter_transfer(self, command, wait=0):
        if "COM20" in self.port_name_list:
            self.priqueue_20.put_nowait(command)
        if "COM30" in self.port_name_list:
            self.priqueue_30.put_nowait(command)
        if "COM40" in self.port_name_list:
            self.priqueue_40.put_nowait(command)

    def _sendnext_com20(self):
        temp_statu = 0
        while True:
            if temp_statu == 0:
                ser = serial.Serial("com20", 115200, timeout=0.1)  # 连接端口

            if not self.priqueue_20.empty():
                temp_statu = 1
                com = self.priqueue_20.get_nowait()
                try:
                    RS232_Command = {
                        'pfb': [0x70, 0x66, 0x62, 0x0D, 0x0A],
                        'iq': [0x69, 0x71, 0x0D, 0x0A],
                        've': [0x76, 0x65, 0x0D, 0x0A],
                        'pe': [0x70, 0x65, 0x0D, 0x0A],
                        'st': [0x73, 0x74, 0x0D, 0x0A],
                        'vbusreadout': [0x76, 0x62, 0x75, 0x73, 0x72, 0x65, 0x61, 0x64, 0x6F, 0x75, 0x74, 0x0D, 0x0A],
                        'hwpext': [0x68, 0x77, 0x70, 0x65, 0x78, 0x74, 0x0D, 0x0A],
                    }
                    data3 = []
                    for i in RS232_Command.keys():
                        var = RS232_Command["%s" % i]
                        # encode()函数是编码，把字符串数据转换成bytes数据流
                        ser.write(var)
                        data = ser.read(90)

                        data1 = str(data, encoding="utf-8")
                        data1 = data1.replace("\n", "#")
                        data1 = data1.replace("\r", "")
                        data1 = data1.replace(" ", "#")
                        index = data1.find(i)
                        if index != -1:
                            data1 = data1[index:]
                        else:continue
                        data2 = data1.split("#")
                        data3.append(data2[:3])
                    logger_b.info("com20-" + str(data3) + "-" + str(com))

                except Exception as e:
                    logger_b.error("com20电机信息读取和写入故障" + str(e) + com)

            else:
                ser.close()
                temp_statu = 0

    def _sendnext_com30(self):
        temp_statu = 0
        while True:
            if temp_statu == 0:
                ser = serial.Serial("com30", 115200, timeout=0.1)  # 连接端口

            if not self.priqueue_30.empty():
                temp_statu = 1
                com = self.priqueue_30.get_nowait()
                try:
                    RS232_Command = {
                        'pfb': [0x70, 0x66, 0x62, 0x0D, 0x0A],
                        'iq': [0x69, 0x71, 0x0D, 0x0A],
                        've': [0x76, 0x65, 0x0D, 0x0A],
                        'pe': [0x70, 0x65, 0x0D, 0x0A],
                        'st': [0x73, 0x74, 0x0D, 0x0A],
                        'vbusreadout': [0x76, 0x62, 0x75, 0x73, 0x72, 0x65, 0x61, 0x64, 0x6F, 0x75, 0x74, 0x0D, 0x0A],
                        'hwpext': [0x68, 0x77, 0x70, 0x65, 0x78, 0x74, 0x0D, 0x0A],
                        # 'flthist': [0x66, 0x6C, 0x74, 0x68, 0x69, 0x73, 0x74, 0x0D, 0x0A]
                    }
                    data3 = []
                    for i in RS232_Command.keys():
                        var = RS232_Command["%s" % i]
                        # encode()函数是编码，把字符串数据转换成bytes数据流
                        ser.write(var)
                        data = ser.read(90)

                        data1 = str(data, encoding="utf-8")
                        data1 = data1.replace("\n", "#")
                        data1 = data1.replace("\r", "")
                        data1 = data1.replace(" ", "#")
                        index = data1.find(i)
                        if index != -1:
                            data1 = data1[index:]
                        else:continue
                        data2 = data1.split("#")
                        data3.append(data2[:3])
                    logger_b.info("com30-" + str(data3) + "-" + str(com))

                except Exception as e:
                    logger_b.error("com30电机信息读取和写入故障" + str(e) + com)

            else:
                ser.close()
                temp_statu = 0

    def _sendnext_com40(self):
        temp_statu = 0
        while True:
            if temp_statu == 0:
                ser = serial.Serial("com40", 115200, timeout=0.1)  # 连接端口

            if not self.priqueue_40.empty():
                temp_statu = 1
                com = self.priqueue_40.get_nowait()
                try:
                    RS232_Command = {
                        'pfb': [0x70, 0x66, 0x62, 0x0D, 0x0A],
                        'iq': [0x69, 0x71, 0x0D, 0x0A],
                        've': [0x76, 0x65, 0x0D, 0x0A],
                        'pe': [0x70, 0x65, 0x0D, 0x0A],
                        'st': [0x73, 0x74, 0x0D, 0x0A],
                        'vbusreadout': [0x76, 0x62, 0x75, 0x73, 0x72, 0x65, 0x61, 0x64, 0x6F, 0x75, 0x74, 0x0D, 0x0A],
                        'hwpext': [0x68, 0x77, 0x70, 0x65, 0x78, 0x74, 0x0D, 0x0A],
                        # 'flthist': [0x66, 0x6C, 0x74, 0x68, 0x69, 0x73, 0x74, 0x0D, 0x0A]
                    }
                    data3 = []
                    for i in RS232_Command.keys():
                        var = RS232_Command["%s" % i]
                        # encode()函数是编码，把字符串数据转换成bytes数据流
                        ser.write(var)
                        data = ser.read(90)

                        data1 = str(data, encoding="utf-8")
                        data1 = data1.replace("\n", "#")
                        data1 = data1.replace("\r", "")
                        data1 = data1.replace(" ", "#")
                        index = data1.find(i)
                        if index != -1:
                            data1 = data1[index:]
                        else:continue
                        data2 = data1.split("#")
                        data3.append(data2[:3])
                    logger_b.info("com40-" + str(data3) + "-" + str(com))

                except Exception as e:
                    logger_b.error("com40电机信息读取和写入故障" + str(e) + com)

            else:
                ser.close()
                temp_statu = 0