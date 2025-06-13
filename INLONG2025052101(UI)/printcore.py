__version__ = "2.0.0rc8"

import comm_with_machine
import sys

if sys.version_info.major < 3:
    print("You need to run this on Python 3")
    sys.exit(-1)
import threading
# from comm_with_DJ import starting
from serial import Serial, SerialException, PARITY_ODD, PARITY_NONE
from select import error as SelectError
from queue import Queue, Empty as QueueEmpty
import time
import platform
import os
import traceback
import errno
import socket
import re
import selectors
import datetime
from functools import wraps, reduce
from collections import deque
import gcoder
from utils import set_utf8_locale, install_locale, decode_utf8
from loguru import logger

logger.add("./Log/core_Log/file_{time}.log", format="{time} {level} {message}", level="DEBUG", rotation="100MB",
           retention="15 days", filter=lambda record: record["extra"].get("name") == "c", catch=True, enqueue=True)

logger_c = logger.bind(name="c")
from PyQt5.QtCore import pyqtSignal, QThread

try:
    set_utf8_locale()
except:
    pass
install_locale('pronterface')
from plugins import PRINTCORE_HANDLER


def locked(f):
    @wraps(f)
    def inner(*args, **kw):
        with inner.lock:
            return f(*args, **kw)

    inner.lock = threading.Lock()
    return inner


def control_ttyhup(port, disable_hup):
    """Controls the HUPCL"""
    if platform.system() == "Linux":
        if disable_hup:
            os.system("stty -F %s -hup" % port)
        else:
            os.system("stty -F %s hup" % port)


def enable_hup(port):
    control_ttyhup(port, False)


def disable_hup(port):
    control_ttyhup(port, True)


PR_EOF = None  # printrun's marker for EOF
PR_AGAIN = b''  # printrun's marker for timeout/no data
SYS_EOF = b''  # python's marker for EOF
SYS_AGAIN = None  # python's marker for timeout/no data


class printcore(QThread):
    changeValue = pyqtSignal(str, str, str, str)  # 创建槽信号
    changeValue_xyz = pyqtSignal(str, str, str)  # 创建槽信号
    changeValue_time = pyqtSignal(str, str)  # 创建槽信号
    changeValue_motoroff = pyqtSignal(str)  # 创建槽信号(断料堵料检测）
    changeValue_jichu = pyqtSignal(str)  # 开始挤出信号
    Evevt_jichuliang = pyqtSignal(str)
    infor_error = pyqtSignal(str)
    dibanlevel = pyqtSignal(str)
    msgdone = pyqtSignal(str)
    zdiff = pyqtSignal(str)
    system_state = pyqtSignal(str)
    infor_safeDoor = pyqtSignal(str)
    printer_offline = pyqtSignal(str)
    infor_firmware = pyqtSignal(str)  # 返回下位机的回复的信息

    def __init__(self, port=None, baud=None, dtr=None):
        super(printcore, self).__init__()
        """Initializes a printcore instance. Pass the port and baud rate to
           connect immediately"""
        self.baud = baud
        self.dtr = dtr
        self.port = port
        self.analyzer = gcoder.GCode()
        # Serial instance connected to the printer, should be None when
        # disconnected
        self.printer = None
        self.extru_temp_history = "0"
        # clear to send, enabled after responses
        # FIXME: should probably be changed to a sliding window approach
        self.clear = 0
        # The printer has responded to the initial command and is active
        self.online = False
        # is a print currently running, true if printing, false if paused
        self.printing = False
        self.mainqueue = None
        self.priqueue = Queue(0)
        self.queueindex = 0
        self.lineno = 0
        self.resendfrom = -1
        self.paused = False
        self.sentlines = {}
        self.log = deque(maxlen=10000)
        self.sent = []
        self.writefailures = 0
        self.sendfailures = 0
        self.currentcommand = ""
        self.currentlineno = 0
        self.tempcb = None  # impl (wholeline)
        self.recvcb = None  # impl (wholeline)
        self.sendcb = None  # impl (wholeline)
        self.preprintsendcb = None  # impl (wholeline)
        self.printsendcb = None  # impl (wholeline)
        self.layerchangecb = None  # impl (wholeline)
        self.errorcb = None  # impl (wholeline)
        self.startcb = None  # impl ()
        self.endcb = None  # impl ()
        self.onlinecb = None  # impl ()
        self.loud = False  # emit sent and received lines to terminal
        self.tcp_streaming_mode = False
        self.greetings = ['start', 'Grbl ']
        self.wait = 0  # default wait period for send(), send_now()
        self.read_thread = None
        self.stop_read_thread = False
        self.send_thread = None
        self.stop_send_thread = False
        self.print_thread = None
        self.readline_buf = []
        self.selector = None
        self.event_handler = PRINTCORE_HANDLER
        # Not all platforms need to do this parity workaround, and some drivers
        # don't support it.  Limit it to platforms that actually require it
        # here to avoid doing redundant work elsewhere and potentially breaking
        # things.
        self.needs_parity_workaround = platform.system() == "linux" and os.path.exists("/etc/debian")
        for handler in self.event_handler:
            try:
                handler.on_init()
            except:
                logger_c.error(traceback.format_exc())
        if port is not None and baud is not None:
            self.connect(port, baud)
        self.xy_feedrate = None
        self.z_feedrate = None

        # 添加温度全局
        self.wendu_ext_now = 0
        self.wendu_ext_target = 0
        self.wendu_bed_now = 0
        self.wendu_bed_target = 0

    def addEventHandler(self, handler):
        '''
        Adds an event handler.
        
        @param handler: The handler to be added.
        '''
        self.event_handler.append(handler)

    def logError(self, error):
        for handler in self.event_handler:
            try:
                handler.on_error(error)
            except:
                logger_c.error(traceback.format_exc())
        if self.errorcb:
            try:
                self.errorcb(error)
            except:
                logger_c.error(traceback.format_exc())
        else:
            logger_c.error(error)

    @locked
    def disconnect(self):
        """Disconnects from printer and pauses the print
        """
        if self.printer:
            if self.read_thread:
                self.stop_read_thread = True
                if threading.current_thread() != self.read_thread:
                    self.read_thread.join()
                self.read_thread = None
            if self.print_thread:
                self.printing = False
                self.print_thread.join()
            self._stop_sender()
            try:
                if self.selector is not None:
                    self.selector.unregister(self.printer_tcp)
                    self.selector.close()
                    self.selector = None
                if self.printer_tcp is not None:
                    self.printer_tcp.close()
                    self.printer_tcp = None
                self.printer.close()
            except socket.error:
                # logger.error(traceback.format_exc())
                pass
            except OSError:
                # logger.error(traceback.format_exc())
                pass
        for handler in self.event_handler:
            try:
                handler.on_disconnect()
            except:
                logger_c.error(traceback.format_exc())
        self.printer = None
        self.online = False
        self.printing = False

    @locked
    def connect(self, port=None, baud=None, dtr=None):
        """Set port and baudrate if given, then connect to printer
        """
        if self.printer:
            self.disconnect()
        if port is not None:
            self.port = port
        if baud is not None:
            self.baud = baud
        if dtr is not None:
            self.dtr = dtr
        if self.port is not None and self.baud is not None:
            # Connect to socket if "port" is an IP, device if not
            host_regexp = re.compile(
                "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$|^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$")
            is_serial = True
            if ":" in self.port:
                bits = self.port.split(":")
                if len(bits) == 2:
                    hostname = bits[0]
                    try:
                        port_number = int(bits[1])
                        if host_regexp.match(hostname) and 1 <= port_number <= 65535:
                            is_serial = False
                    except:
                        pass
            self.writefailures = 0
            if not is_serial:
                self.printer_tcp = socket.socket(socket.AF_INET,
                                                 socket.SOCK_STREAM)
                self.printer_tcp.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.timeout = 0.25
                self.printer_tcp.settimeout(1.0)
                try:
                    self.printer_tcp.connect((hostname, port_number))
                    # a single read timeout raises OSError for all later reads
                    # probably since python 3.5
                    # use non blocking instead
                    self.printer_tcp.settimeout(0)
                    self.printer = self.printer_tcp.makefile('rwb', buffering=0)
                    self.selector = selectors.DefaultSelector()
                    self.selector.register(self.printer_tcp, selectors.EVENT_READ)
                except socket.error as e:
                    if (e.strerror is None): e.strerror = ""
                    logger_c.info(("Could not connect to %s:%s:") % (hostname, port_number) +
                                  "\n" + ("Socket error %s:") % e.errno +
                                  "\n" + e.strerror)
                    self.printer = None
                    self.printer_tcp = None
                    return
            else:
                disable_hup(self.port)
                self.printer_tcp = None
                # try:
                if self.needs_parity_workaround:
                    self.printer = Serial(port=self.port,
                                          baudrate=self.baud,
                                          timeout=0.25,
                                          parity=PARITY_ODD)
                    self.printer.close()
                    self.printer.parity = PARITY_NONE
                else:
                    self.printer = Serial(baudrate=self.baud,
                                          timeout=0.25,
                                          parity=PARITY_NONE,
                                          write_timeout=0)
                    self.printer.port = self.port
                try:
                    self.printer.dtr = dtr
                except:
                    logger_c.info("Could not set DTR on this platform")
                    pass
                self.printer.open()
                logger_c.info("设备已成功连接")
            for handler in self.event_handler:
                try:
                    handler.on_connect()
                except:
                    logger_c.error(traceback.format_exc())
            self.stop_read_thread = False
            self.read_thread = threading.Thread(target=self._listen,
                                                name='read thread')
            self.read_thread.start()
            self._start_sender()

            # self.st_com_machine = comm_with_machine.printcore()
            # self.st_com_machine.start_sender()

    def reset(self):
        """Reset the printer
        """
        if self.printer and not self.printer_tcp:
            self.printer.dtr = 1
            time.sleep(0.2)
            self.printer.dtr = 0

    def _readline_buf(self):
        "Try to readline from buffer"
        if len(self.readline_buf):
            chunk = self.readline_buf[-1]
            eol = chunk.find(b'\n')
            if eol >= 0:
                line = b''.join(self.readline_buf[:-1]) + chunk[:(eol + 1)]
                self.readline_buf = []
                if eol + 1 < len(chunk):
                    self.readline_buf.append(chunk[(eol + 1):])
                return line
        return PR_AGAIN

    def _readline_nb(self):
        "Non blocking readline. Socket based files do not support non blocking or timeouting readline"
        if self.printer_tcp:
            line = self._readline_buf()
            if line:
                return line
            chunk_size = 256
            while True:
                chunk = self.printer.read(chunk_size)
                if chunk is SYS_AGAIN and self.selector.select(self.timeout):
                    chunk = self.printer.read(chunk_size)
                # logger_c.info('_readline_nb chunk', chunk, type(chunk))
                if chunk:
                    self.readline_buf.append(chunk)
                    line = self._readline_buf()
                    if line:
                        return line
                elif chunk is SYS_AGAIN:
                    return PR_AGAIN
                else:
                    # chunk == b'' means EOF
                    line = b''.join(self.readline_buf)
                    self.readline_buf = []
                    self.stop_read_thread = True
                    return line if line else PR_EOF
        else:  # serial port
            return self.printer.readline()

    def _readline(self):
        try:
            line_bytes = self._readline_nb()
            if line_bytes is PR_EOF:
                logger_c.info("Can't read from printer (disconnected?). line_bytes is None")
                return PR_EOF
            line = line_bytes.decode('utf-8', "ignore")  # 读到不属于编码字符集中的部分，忽略该部分
            if len(line) > 1:
                if "filament exchange sucess, wait gcode" in line:
                    logger_c.info("wait gcode")
                    self.changeValue_motoroff.emit("filament exchange sucess, wait gcode")

                if "filament error, broken" in line:  # 接收到断料信号
                    logger_c.info("断料信号")
                    self.changeValue_motoroff.emit("filament error, broken")
                    print("发生断料，time:",time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
                if "filament error, block" in line:  # 接收到堵料信号
                    logger_c.info("堵料信号")
                    self.changeValue_motoroff.emit("filament error, block")
                if "MOTOR POWER OFF" in line:
                    self.changeValue_motoroff.emit("LOBOTICS MOTOR POWER OFF")
                if "MOTOR ERROR" in line:
                    self.changeValue_motoroff.emit(line)
                if "INLONG" in line:
                    print("1111222333:",line)
                for handler in self.event_handler:
                    try:
                        handler.on_recv(line)
                    except:
                        logger_c.error(traceback.format_exc())
                if self.recvcb:
                    try:
                        self.recvcb(line)
                    except:
                        logger_c.error(traceback.format_exc())
                if self.loud: logger_c.info("RECV: %s" % line.rstrip())
            return line
        except UnicodeDecodeError as e:
            logger_c.error(str(e))  # 2022
            logger_c.info(("Got rubbish reply from %s at baudrate %s:") % (self.port, self.baud) +
                          "\n" + ("Maybe a bad baudrate?"))
            return None
        except SerialException as e:
            logger_c.error(str(e))
            logger_c.info(
                ("Can't read from printer (disconnected?) (SerialException): {0}").format(decode_utf8(str(e))))
            return None
        except socket.error as e:
            logger_c.error(str(e))
            logger_c.info(("Can't read from printer (disconnected?) (Socket error {0}): {1}").format(e.errno,
                                                                                                     decode_utf8(
                                                                                                         e.strerror)))
            return None
        except (OSError, SelectError) as e:
            logger_c.error(str(e))
            # OSError and SelectError are the same thing since python 3.3
            if self.printer_tcp:
                # SelectError branch, assume select is used only for socket printers
                if len(e.args) > 1 and 'Bad file descriptor' in e.args[1]:
                    logger_c.info(("Can't read from printer (disconnected?) (SelectError {0}): {1}").format(e.errno,
                                                                                                            decode_utf8(
                                                                                                                e.strerror)))
                    return None
                else:
                    logger_c.info(("SelectError ({0}): {1}").format(e.errno, decode_utf8(e.strerror)))
                    raise
            else:
                # OSError branch, serial printers
                if e.errno == errno.EAGAIN:  # Not a real error, no data was available
                    return ""
                logger_c.info(
                    ("Can't read from printer (disconnected?) (OS Error {0}): {1}").format(e.errno, e.strerror))
                return None

    def _listen_can_continue(self):
        if self.printer_tcp:
            return not self.stop_read_thread and self.printer
        return (not self.stop_read_thread
                and self.printer
                and self.printer.is_open)

    def _listen_until_online(self):
        while not self.online and self._listen_can_continue():
            self._send("M105")
            self._send("G250 S21")
            self._send("G250 S800")
            self._send('M154 S1')
            #self._send(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            if self.writefailures >= 4:
                logger_c.error(("Aborting connection attempt after 4 failed writes."))
                return
            empty_lines = 0
            while self._listen_can_continue():
                line = self._readline()
                if line is None:
                    break  # connection problem
                # workaround cases where M105 was sent before printer Serial
                # was online an empty line means read timeout was reached,
                # meaning no data was received thus we count those empty lines,
                # and once we have seen 15 in a row, we just break and send a
                # new M105
                # 15 was chosen based on the fact that it gives enough time for
                # Gen7 bootloader to time out, and that the non received M105
                # issues should be quite rare so we can wait for a long time
                # before resending
                if not line:
                    empty_lines += 1
                    if empty_lines == 15: break
                else:
                    empty_lines = 0
                if line.startswith(tuple(self.greetings)) \
                        or line.startswith('ok') or "T:" in line:
                    if "T:" in line and "B" in line and "@" in line and "/" in line:
                        try:
                            self.wendu_ext_now = line.split(":")[1].replace(" ", "").strip('B').split("/")[0]
                            self.wendu_ext_target = line.split(":")[1].replace(" ", "").strip('B').split("/")[1]
                            self.wendu_bed_now = line.split(":")[2].replace(" ", "").strip("@").split("/")[0]
                            self.wendu_bed_target = line.split(":")[2].replace(" ", "").strip("@").split("/")[1]
                            self.changeValue.emit(str(self.wendu_ext_now), str(self.wendu_ext_target),
                                                  str(self.wendu_bed_now),
                                                  str(self.wendu_bed_target))
                        except Exception as e:
                            pass
                    self.online = True
                    for handler in self.event_handler:
                        try:
                            handler.on_online()
                        except:
                            logger_c.error(traceback.format_exc())
                    if self.onlinecb:
                        try:
                            self.onlinecb()
                        except:
                            logger_c.error(traceback.format_exc())
                    return

    def return_tem(self):
        return [self.wendu_ext_now, self.wendu_ext_target, self.wendu_bed_now, self.wendu_bed_target]

    #从串口获取底层信息，主要解析坐标和状态等信息
    def _listen(self):
        """This function acts on messages from the firmware
        """
        try:
            self.temp = 0
            self.clear = True
            if not self.printing:
                self._listen_until_online()
            while self._listen_can_continue():
                line = self._readline()
                if not line:
                    logger_c.error("empty readline %s" % self.sendfailures)
                    self.sendfailures += 1
                    if self.sendfailures >= 50:
                        logger_c.error("resend command: %s" % self.currentcommand)
                        self._send(self.currentcommand, self.currentlineno, True)
                        self.sendfailures = 0
                else:
                    logger_c.error("readline %s" % line)
                    if line.startswith('X:') and "Y:" in line and "Z:" in line and "Count" in line:
                        self.sendfailures += 0
                    else:
                        self.sendfailures = 0
                if line is not None:
                    self.infor_firmware.emit(line)
                if line is None:
                    logger_c.debug('_readline() is None, exiting _listen()')
                    self.printer_offline.emit("2")
                    break
                if line.startswith('DEBUG_'):
                    continue
                # if line.startswith(tuple(self.greetings)) or line.startswith('ok'):
                if line.startswith(tuple(self.greetings)) or 'ok' in line:
                    self.clear = True
                    self.temp = 0
                else:
                    self.temp += 1
                    if self.temp ==200:
                        logger_c.error("开始超时计数了")
                        self.clear = True

                if line.startswith('ok') and "T:" in line:
                    for handler in self.event_handler:
                        try:
                            handler.on_temp(line)
                        except:
                            logger_c.error(traceback.format_exc())
                    if self.tempcb:
                        logger_c.info("self.tempcb" + self.tempcb)
                        # callback for temp, status, whatever
                        try:
                            self.tempcb(line)
                        except:
                            logger_c.error(traceback.format_exc())
                if "T:" in line and "B" in line and "@" in line and "/" in line:
                    try:
                        self.wendu_ext_now = str(round(float(line.split(":")[1].replace(" ", "").strip('B').split("/")[0]), 2))
                        self.wendu_ext_target = line.split(":")[1].replace(" ", "").strip('B').split("/")[1]
                        self.wendu_bed_now = str(round(float(line.split(":")[2].replace(" ", "").strip("@").split("/")[0]), 2))
                        self.wendu_bed_target = line.split(":")[2].replace(" ", "").strip("@").split("/")[1]
                        self.changeValue.emit(str(self.wendu_ext_now), str(self.wendu_ext_target), str(self.wendu_bed_now),
                                              str(self.wendu_bed_target))
                        self.system_state.emit(line)
                    except Exception as e:
                        # logger_c.error(e)
                        logger_c.error(traceback.format_exc())
                elif line.startswith('X:') and "Y:" in line and "Z:" in line and "Count" in line:
                    try:
                        tm_x = line.split("X:")[1].split("Y")[0]
                        tm_y = line.split("Y:")[1].split("Z")[0]
                        tm_z = line.split("Z:")[1].split("E")[0]
                        self.changeValue_xyz.emit(tm_x, tm_y, tm_z)
                        self.system_state.emit(line)
                    except Exception as e:
                        # logger_c.error(e)
                        logger_c.error(traceback.format_exc())
                elif "LOBOTICS SAFETY UNLOCKED" in line:
                    self.infor_safeDoor.emit("UNLOCKED")
                elif "LOBOTICS SAFETY LOCKED" in line:
                    self.infor_safeDoor.emit("LOCKED")
                elif "LOBOTICS SAFETY ERROR" in line:
                    self.infor_safeDoor.emit("ERROR")
                elif line.startswith('Error'):
                    self.infor_error.emit(line)
                elif line.startswith('Warn'):
                    self.infor_error.emit(line)
                elif "LASER POWER ON FAILED" in line or "coff calc failed" in line:
                    self.infor_error.emit(line)
                    self.dibanlevel.emit("fail done")
                elif "msgdone" in line:
                    self.msgdone.emit("msgdone")
                elif "zdiff" in line:
                    self.zdiff.emit(line)
                elif "POS" in line or "|BEDLEVEL| done" in line or "PID" in line:
                    # print(line)
                    self.dibanlevel.emit(line)
                if line.lower().startswith("resend") or line.startswith("rs"):
                    for haystack in ["N:", "N", ":"]:
                        line = line.replace(haystack, " ")
                    linewords = line.split()
                    while len(linewords) != 0:
                        try:
                            toresend = int(linewords.pop(0))
                            self.resendfrom = toresend
                            break
                        except:
                            pass
                    self.clear = True
            self.clear = True
            logger_c.debug('Exiting read thread')
        except Exception as e:
            logger_c.error(e)
            logger_c.error("In printcore._listen err")

    def _start_sender(self):
        self.stop_send_thread = False
        self.send_thread = threading.Thread(target=self._sender,
                                            name='send thread')
        self.send_thread.start()

    def _stop_sender(self):
        if self.send_thread:
            self.stop_send_thread = True
            self.send_thread.join()
            self.send_thread = None

    def _sender(self):
        while not self.stop_send_thread:
            try:
                command = self.priqueue.get(True, 0.1)
            except QueueEmpty:
                continue
            while self.printer and self.printing and not self.clear:
                time.sleep(0.001)
            self._send(command)
            while self.printer and self.printing and not self.clear:
                time.sleep(0.001)

    def _checksum(self, command):
        return reduce(lambda x, y: x ^ y, map(ord, command))

    def startprint(self, gcode, startindex=0):
        """Start a print, gcode is an array of gcode commands.
        returns True on success, False if already printing.
        The print queue will be replaced with the contents of the data array,
        the next line will be set to 0 and the firmware notified. Printing
        will then start in a parallel thread.
        """
        self._send("G250 S31")
        if self.printing or not self.online or not self.printer:
            return False
        self.queueindex = startindex
        self.mainqueue = gcode
        self.gcodeLineMax = len(gcode)
        self.printing = True
        self.lineno = 0
        self.resendfrom = -1
        if not gcode or not gcode.lines:
            return True

        self.clear = False
        self._send("M110", -1, True)
        resuming = (startindex != 0)
        self.print_thread = threading.Thread(target=self._print,
                                             name='print thread',
                                             kwargs={"resuming": resuming})
        self.print_thread.start()
        return True

    def cancelprint(self):
        self.pause()
        self.paused = False
        self.mainqueue = None
        self.clear = True

    # run a simple script if it exists, no multithreading
    def runSmallScript(self, filename):
        if not filename: return
        try:
            with open(filename) as f:
                for i in f:
                    l = i.replace("\n", "")
                    l = l.partition(';')[0]  # remove comments
                    self.send_now(l)
        except:
            pass

    def pause(self, Fla=None):
        """Pauses the print, saving the current position.
        """
        if not self.printing: return False
        self.paused = True
        self.printing = False

        # ';@pause' in the gcode file calls pause from the print thread
        if not threading.current_thread() is self.print_thread:
            try:
                self.print_thread.join()
            except:
                logger_c.error(traceback.format_exc())

        self.print_thread = None

        self.pauseX = round(self.analyzer.abs_x, 4)
        self.pauseY = round(self.analyzer.abs_y, 4)
        self.pauseZ = round(self.analyzer.abs_z, 4)
        self.pauseE = round(self.analyzer.abs_e, 4)
        self.pauseF = round(self.analyzer.current_f, 4)
        self.pauseRelative = round(self.analyzer.relative, 4)
        self.pauseRelativeE = round(self.analyzer.relative_e, 4)
        if Fla == None:
            self._send("G91")
            self._send('G1 Z50 F1800')
            self._send("G90")
            self._send('G1 X600 Y10 F3000')

    def resume(self):
        """Resumes a paused print."""
        if not self.paused:
            return False
        self.send_now("G90")  # go to absolute coordinates

        xyFeed = " F3000"  # '' if self.xy_feedrate is None else ' F' + str(self.xy_feedrate)
        zFeed = " F1800"  # '' if self.z_feedrate is None else ' F' + str(self.z_feedrate)

        self.send_now("G1 X%s Y%s%s" % (self.pauseX, self.pauseY, xyFeed))
        self.send_now("G1 Z" + str(self.pauseZ) + zFeed)
        self.send_now("G92 E" + str(self.pauseE))

        # go back to relative if needed
        if self.pauseRelative:
            self.send_now("G91")
        if self.pauseRelativeE:
            self.send_now('M83')
        # reset old feed rate
        self.send_now("G1 F" + str(self.pauseF))

        self.paused = False
        self.printing = True
        self.print_thread = threading.Thread(target=self._print,
                                             name='print thread',
                                             kwargs={"resuming": True})
        self.print_thread.start()

    def send(self, command, wait=0):
        """Adds a command to the checksummed main command queue if printing, or
        sends the command immediately if not printing"""
        if self.online:
            if self.printing:
                self.mainqueue.append(command)
            else:
                self.priqueue.put_nowait(command)
        else:
            logger_c.info("Not connected to printer.")

    def send_now(self, command, wait=0):
        logger_c.info(command)
        """Sends a command to the printer ahead of the command queue, without a
        checksum"""
        if self.online:
            self.priqueue.put_nowait(command)
        else:
            logger_c.info("Not connected to printer.")

    def _print(self, resuming=False):
        self._stop_sender()
        try:
            for handler in self.event_handler:
                try:
                    handler.on_start(resuming)
                except:
                    logger_c.error(traceback.format_exc())
            if self.startcb:
                # callback for printing started
                try:
                    self.startcb(resuming)
                except:
                    logger_c.info("Print start callback failed with:" +
                                  "\n" + traceback.format_exc())
            while self.printing and self.printer and self.online:
                self._sendnext()
            self.sentlines = {}
            self.sent = []
            for handler in self.event_handler:
                try:
                    handler.on_end()
                except:
                    logger_c.error(traceback.format_exc())
            if self.endcb:
                # callback for printing done
                try:
                    self.endcb()
                except:
                    logger_c.info("Print end callback failed with:" +
                                  "\n" + traceback.format_exc())
        except:
            logger_c.error("Print thread died due to the following error:" +
                           "\n" + traceback.format_exc())
        finally:
            self.print_thread = None
            self._start_sender()

    def process_host_command(self, command):
        """only ;@pause command is implemented as a host command in printcore, but hosts are free to reimplement this method"""
        command = command.lstrip()
        if command.startswith(";@pause"):
            self.pause()

    def _sendnext(self):
        if not self.printer:
            return
        while self.printer and self.printing and not self.clear:
            time.sleep(0.001)
        # Only wait for oks when using serial connections or when not using tcp
        # in streaming mode
        if not self.printer_tcp or not self.tcp_streaming_mode:
            self.clear = False
        if not (self.printing and self.printer and self.online):
            self.clear = True
            return
        if self.resendfrom < self.lineno and self.resendfrom > -1:
            self._send(self.sentlines[self.resendfrom], self.resendfrom, False)
            self.resendfrom += 1
            return
        self.resendfrom = -1
        if not self.priqueue.empty():
            self._send(self.priqueue.get_nowait())
            self.priqueue.task_done()
            return
        if self.printing and self.mainqueue.has_index(self.queueindex):
            (layer, line) = self.mainqueue.idxs(self.queueindex)
            gline = self.mainqueue.all_layers[layer][line]
            if self.queueindex > 0:
                (prev_layer, prev_line) = self.mainqueue.idxs(self.queueindex - 1)
                if prev_layer != layer:
                    for handler in self.event_handler:
                        try:
                            handler.on_layerchange(layer)
                        except:
                            logger_c.error(traceback.format_exc())
            if self.layerchangecb and self.queueindex > 0:
                (prev_layer, prev_line) = self.mainqueue.idxs(self.queueindex - 1)
                if prev_layer != layer:
                    try:
                        self.layerchangecb(layer)
                    except:
                        logger_c.error(traceback.format_exc())
            for handler in self.event_handler:
                try:
                    handler.on_preprintsend(gline, self.queueindex, self.mainqueue)
                except:
                    logger_c.error(traceback.format_exc())
            if self.preprintsendcb:
                if self.mainqueue.has_index(self.queueindex + 1):
                    (next_layer, next_line) = self.mainqueue.idxs(self.queueindex + 1)
                    next_gline = self.mainqueue.all_layers[next_layer][next_line]
                else:
                    next_gline = None
                gline = self.preprintsendcb(gline, next_gline)
            if gline is None:
                self.queueindex += 1
                self.changeValue_time.emit(str(self.queueindex), str(len(self.mainqueue)))
                self.clear = True
                return
            tline = gline.raw
            if tline.lstrip().startswith(";@"):  # check for host command
                self.process_host_command(tline)
                self.queueindex += 1
                self.clear = True
                return

            # Strip comments
            tline = gcoder.gcode_strip_comment_exp.sub("", tline).strip()
            if tline:
                self._send(tline, self.lineno, True)
                # self.st_com_machine.Parameter_transfer(tline)
                self.currentcommand = tline
                self.currentlineno = self.lineno
                self.lineno += 1
                for handler in self.event_handler:
                    try:
                        handler.on_printsend(gline)
                    except:
                        logger_c.error(traceback.format_exc())
                if self.printsendcb:
                    try:
                        self.printsendcb(gline)
                    except:
                        logger_c.error(traceback.format_exc())
            else:
                self.clear = True
            self.queueindex += 1
            self.changeValue_time.emit(str(self.queueindex), str(len(self.mainqueue)))
        else:
            self.printing = False
            self.clear = True
            if not self.paused:
                print("print job is OK")
                self.queueindex = 0
                self.lineno = 0
                self._send("M110", -1, True)
                self.changeValue_time.emit("0", "0")

    def _send(self, command, lineno=0, calcchecksum=False):
        # Only add checksums if over serial (tcp does the flow control itself)
        if calcchecksum and not self.printer_tcp:
            prefix = "N" + str(lineno) + " " + command
            command_temp = prefix + "*" + str(self._checksum(prefix))
            if "M110" not in command_temp:
                self.sentlines[lineno] = command_temp
        else:
            command_temp = command
        if self.printer:
            self.sent.append(command_temp)
            logger_c.error("SENT: %s" % command_temp)
            # run the command through the analyzer
            gline = None
            try:
                gline = self.analyzer.append(command_temp, store=False)
            except:
                logger_c.warning(("Could not analyze command %s:") % command_temp +
                                 "\n" + traceback.format_exc())
            if self.loud:
                logger_c.info("SENT: %s" % command_temp)

            for handler in self.event_handler:
                try:
                    handler.on_send(command_temp, gline)
                except:
                    logger_c.error(traceback.format_exc())
            if self.sendcb:
                try:
                    self.sendcb(command_temp, gline)
                except:
                    logger_c.info(traceback.format_exc())
            try:
                # from urllib.parse import quote
                # tmp = quote(command + "\n")
                # self.printer.write(tmp.encode('ascii'))
                logger_c.error("write command %s" % command_temp)
                self.printer.write((command_temp + "\n").encode('gbk'))
                logger_c.error("second command %s" % command_temp)

                if "E" in command_temp:
                    self.changeValue_jichu.emit("jichu")
                    self.Evevt_jichuliang.emit(command_temp)
                if "M109" in command_temp or "M104" in command_temp:
                    tempStr = command_temp.split("S")[1].split("*")[0]
                    if tempStr and tempStr.strip() and int(tempStr) > 200:
                        self.extru_temp_history = tempStr
                if self.printer_tcp:
                    try:
                        self.printer.flush()
                    except socket.timeout:
                        pass
                self.writefailures = 0
                self.sendfailures = 0
                logger_c.error("finish command %s" % command_temp)
            except socket.error as e:
                self.writefailures += 1
                logger_c.error("socket error %s" % e + "command %s" % command_temp)
                if e.errno is None:
                    logger_c.error("Can't write to printer (disconnected ?):" +
                                   "\n" + traceback.format_exc())
                else:
                    logger_c.info(("Can't write to printer (disconnected?) (Socket error {0}): {1}").format(e.errno,
                                                                                                            decode_utf8(
                                                                                                                e.strerror)))
                # self.writefailures += 1
            except SerialException as e:
                self.writefailures += 1
                logger_c.error("serial error %s" % e + "command %s" % command_temp)
                logger_c.error(
                    ("Can't write to printer (disconnected?) (SerialException): {0}").format(decode_utf8(str(e))))
                # self.writefailures += 1
            except RuntimeError as e:
                self.writefailures += 1
                logger_c.error("runtime error %s" % e + "command %s" % command_temp)
                logger_c.error(
                    ("Socket connection broken, disconnected. ({0}): {1}").format(e.errno, decode_utf8(e.strerror)))
                # self.writefailures += 1
            except Exception as e:
                self.writefailures += 1
            if self.writefailures >= 4:
                self.printer_offline.emit("1")
