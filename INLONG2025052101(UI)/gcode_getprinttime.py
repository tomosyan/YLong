import math
import os

from PyQt5.QtWidgets import QWidget
import re

class GCodeParser:
    def __init__(self):
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_z = 0.0
        self.current_feedrate = 0.0
        self.current_E=0.0
        self.total_time = 0.0
        self.perLinetime=0.0
        self.line = 0
        self.m_total_extrusion = 0.0
        self.m_prev_e = None  # 用于记录前一个E值
        self.m_is_reset = False  # 标记是否遇到重置指令
    def parse_line(self, line):
        parts = line.split()
        if len(parts[0])==2:
            cmd=parts[0]
            if cmd.startswith('G1') or cmd.startswith('G0'):
                # 直线移动
                self._parse_linear_move(line)
            if cmd.startswith('G2') or cmd.startswith('G3'):
                # 圆弧移动
                self._parse_arc_move(line)
        return self.total_time

    def extract_arc_parameters(self,gcode):
        pattern = r"(G2|G3) X([\d.-]+) Y([\d.-]+) I([\d.-]+) J([\d.-]+) F([\d.-]+)"
        matches = re.findall(pattern, gcode)
        arc_parameters = []
        for match in matches:
            g_code = match[0]
            x = float(match[1])
            y = float(match[2])
            i = float(match[3])
            j = float(match[4])
            F = float(match[5])
            E = float(match[6])
            is_g2 = g_code == "G2"
            # 假设起点为 (0, 0)
            x1, y1 = 0, 0
            x2, y2 = x, y
            xc = x1 + i
            yc = y1 + j
            t = self.calculate_print_time(x1, y1, x2, y2, xc, yc, F, is_g2)
            arc_parameters.append((g_code, x, y, i, j, F, t))
        return arc_parameters

    #i, j: 圆心相对于起点的偏移量(G3指令中的I, J)

    def calculate_arc_length(self,x1, y1, x2, y2, xc, yc, is_g2):
        # 计算起点和终点相对于圆心的向量
        dx1 = x1 - xc
        dy1 = y1 - yc
        dx2 = x2 - xc
        dy2 = y2 - yc

        # 计算起点和终点的角度
        theta1 = math.atan2(dy1, dx1)
        theta2 = math.atan2(dy2, dx2)

        # 计算圆心角
        if is_g2:  # G2 顺时针圆弧
            if theta2 > theta1:
                theta2 -= 2 * math.pi
        else:  # G3 逆时针圆弧
            if theta2 < theta1:
                theta2 += 2 * math.pi

        delta_theta = abs(theta2 - theta1)

        # 计算圆弧半径
        R = math.sqrt(dx1 ** 2 + dy1 ** 2)

        # 计算圆弧长度
        L = R * delta_theta

        return L

    def calculate_print_time(self,x1, y1, x2, y2, xc, yc, F, is_g2):
        L = self.calculate_arc_length(x1, y1, x2, y2, xc, yc, is_g2)
        # F 是进给速度，单位通常为 mm/min，转换为 mm/s
        F = F / 60
        t = L / F
        return t
    def _parse_linear_move(self, line):
        parts = line.split()
        x = self._get_value(parts, 'X', self.current_x)
        y = self._get_value(parts, 'Y', self.current_y)
        z = self._get_value(parts, 'Z', self.current_z)
        f = self._get_value(parts, 'F', self.current_feedrate)
        E = self._get_value(parts, 'E', self.current_E)
        # 计算距离
        distance = math.sqrt((x - self.current_x) ** 2 +
                             (y - self.current_y) ** 2 +
                             (z - self.current_z) ** 2)
        if E<0:
            tmp_time1 = abs(E) / (f/60.0)
        else:
            tmp_time1 = abs(E-self.current_E) / (f/60.0)
        # 计算时间 (分钟转秒)
        tmp_time2 = distance / (f / 60.0) if f > 0 else 0
        time = max(abs(tmp_time1), abs(tmp_time2))
        self.perLinetime=time
        # 更新状态
        self.current_x, self.current_y, self.current_z, self.current_E = x, y, z, E
        self.current_feedrate = f
        self.total_time += time
        #print(f"每行打印时间: { self.perLinetime:.2f} 秒  linetime:{time:.2f} 秒 \n")

    def _parse_arc_move(self, line):
        parts = line.split()
        cmdname='G2'
        if(parts[0].startswith('G2')):
            cmdname='G2'
        else:
            cmdname='G3'
        x = self._get_value(parts, 'X', self.current_x)
        y = self._get_value(parts, 'Y', self.current_y)
        i = self._get_value(parts, 'I', 0)
        j = self._get_value(parts, 'J', 0)
        f = self._get_value(parts, 'F', self.current_feedrate)
        E = self._get_value(parts, 'E', self.current_E)

        # 计算距离
        distance = math.sqrt((x - self.current_x) ** 2 +
                             (y - self.current_y) ** 2 )
        tmp_time1=0.0
        tmp_time2 = 0.0

        tmp_time1 = abs(E-self.current_E) / (f/60.0)
        x1,y1 = self.current_x,self.current_y
        x2,y2 = x, y
        xc = x1 + i
        yc = y1 + j
        # 计算圆弧时间
        tmp_time2 = self.calculate_arc_time(
            x1, y1,
            x, y, xc, yc, f,cmdname
        )
        time=max(abs(tmp_time1),abs(tmp_time2))
        # 更新状态
        self.current_x, self.current_y = x, y
        self.current_feedrate = f
        self.total_time += abs(time)
        self.line +=1


    def calculate_arc_time(self,start_x, start_y, end_x, end_y, i, j, feedrate,is_g2):
        """
        计算G3圆弧指令的打印时间

        参数:
        start_x, start_y: 起点坐标
        end_x, end_y: 终点坐标 (G3指令中的X,Y)
        i, j: 圆心相对于起点的偏移量 (G3指令中的I,J)
        feedrate: 进给速度 (mm/min) (G3指令中的F值)

        返回:
        时间(秒)
        """
        # # 1. 计算圆心坐标 (起点 + 偏移量)
        # center_x = start_x + i
        # center_y = start_y + j
        #
        # # 2. 计算半径 (圆心到起点的距离)
        # radius = math.sqrt(i ** 2 + j ** 2)
        #
        # # 3. 计算起点和终点相对于圆心的角度
        # start_angle = math.atan2(start_y - center_y, start_x - center_x)
        # end_angle = math.atan2(end_y - center_y, end_x - center_x)
        #
        #
        # # 4. 计算圆弧角度 (确保角度在0-2π范围内)
        # angle_diff = end_angle - start_angle
        # if angle_diff < 0:
        #     angle_diff += 2 * math.pi

        # 5. 计算圆弧长度 (弧长 = 半径 × 角度(弧度))
        #arc_length = radius * angle_diff

        # pattern = r"(G2|G3) X([\d.-]+) Y([\d.-]+) I([\d.-]+) J([\d.-]+) F([\d.-]+)"
        # matches = re.findall(pattern, gcode)
        # arc_parameters = []
        # for match in matches:
        #     g_code = match[0]
        #     x = float(match[1])
        #     y = float(match[2])
        #     i = float(match[3])
        #     j = float(match[4])
        #     F = float(match[5])
        #     E = float(match[6])
        #     is_g2 = g_code == "G2"
        #     # 假设起点为 (0, 0)
        #     x1, y1 = 0, 0
        #     x2, y2 = x, y
        #     xc = x1 + i
        #     yc = y1 + j
        #x1, y1, x2, y2, xc, yc, is_g2
        #start_x, start_y, end_x, end_y, i, j, feedrate
        bool_g2  = is_g2=='G2'
        arc_length = self.calculate_arc_length(start_x, start_y, end_x, end_y, i, j,bool_g2)
        # 6. 计算时间 (时间 = 距离 / 速度)
        # 进给速度是 mm/min, 需要转换为 mm/sec
        feedrate_mm_per_sec = feedrate / 60.0
        time_seconds = arc_length / feedrate_mm_per_sec
        return time_seconds
    def _get_value(self, parts, prefix, default):
        for p in parts:
            if p.startswith(prefix):
                try:
                    return float(p[1:])
                except ValueError:
                    continue
        return default




    def parse_gcode_line(self,line):
        """解析G-code行，提取命令和参数"""
        command = None
        params = {}
        if line.startswith('G'):
            parts = line.split()
            if len(parts)>=2:
                command = parts[0]
                for part in parts[1:]:
                    if part[0] in 'XYZEF':
                        if len(part[1:].strip())>0:
                            params[part[0]] = float(part[1:])
        return command, params

    def calculate_time_for_move(self,distance, speed):
        """计算移动所需的时间（秒）"""
        if speed == 0:
            return 0
        # 6. 计算时间 (时间 = 距离 / 速度)
        # 进给速度是 mm/min, 需要转换为 mm/sec
        feedrate_mm_per_sec = speed / 60.0
        return distance / feedrate_mm_per_sec   # 转换为秒

    def calculate_total_print_time(self,gcode_file_path):
        """计算G-code文件的总打印时间"""
        #total_time = 0.0
        current_speed = 0.0
        with open(gcode_file_path, 'r') as file:

            for line in file:
                line = line.strip()

                if not line or line.startswith(';'):
                    continue  # 跳过注释和空行
                if line=='G1 E-1 F300':
                    self.parse_line(line)
                else :
                    self.parse_line(line)

                #print(f"计算出总打印时间: {self.total_time:.2f} 秒  \n")
        return self.total_time

    def init_extrusion(self):
        self.m_total_extrusion = 0.0
        self.m_prev_e = None  # 用于记录前一个E值
        self.m_is_reset = False  # 标记是否遇到重置指令

    def calculate_current_extrusion(self,gcode_line):
        """
        计算G-code中的总挤出量，正确处理G92 E0重置指令
        :param gcode_line: 包含G-code指令的列表
        :return: 总挤出量（单位：mm）
        """
        line = gcode_line.strip()
        # 处理G92重置指令
        if line.startswith('G92 '):
            if ' E' in line:
                # 提取重置后的E值
                e_pos = line.find(' E')
                self.m_prev_e = float(line[e_pos + 2:].split()[0])
                self.m_is_reset = True
            return self.m_total_extrusion
        # 只处理G1指令
        if not line.startswith('G1 ') and not line.startswith('G2 ') and not line.startswith('G3 '):
            return self.m_total_extrusion
        # 查找E参数
        e_pos = line.find(' E')
        if e_pos == -1:  # 如果没有E参数则跳过
            return self.m_total_extrusion

        # 提取E值
        current_e = float(line[e_pos + 2:].split()[0])

        # 计算增量
        if self.m_prev_e is not None:
            if self.m_is_reset:
                # 重置后的第一次挤出，直接取当前E值
                self.m_total_extrusion += current_e
                self.m_is_reset = False
            else:
                self.m_total_extrusion += current_e - self.m_prev_e

        self.m_prev_e = current_e

        return self.m_total_extrusion
    def calculate_total_extrusion(self,gcode_file_path):
        """
        计算G-code中的总挤出量，正确处理G92 E0重置指令
        :param gcode_lines: 包含G-code指令的列表
        :return: 总挤出量（单位：mm）
        """
        total_extrusion = 0.0
        prev_e = None  # 用于记录前一个E值
        is_reset = False  # 标记是否遇到重置指令
        with open(gcode_file_path, 'r') as file:
            for line in file:
                line = line.strip()
                # 处理G92重置指令
                if line.startswith('G92 '):
                    if ' E' in line:
                        # 提取重置后的E值
                        e_pos = line.find(' E')
                        prev_e = float(line[e_pos + 2:].split()[0])
                        is_reset = True
                    continue

                # 只处理G1指令
                if not line.startswith('G1 ') and not line.startswith('G2 ') and not line.startswith('G3 '):
                    continue

                # 查找E参数
                e_pos = line.find(' E')
                if e_pos == -1:  # 如果没有E参数则跳过
                    continue

                # 提取E值
                current_e = float(line[e_pos + 2:].split()[0])

                # 计算增量
                if prev_e is not None:
                    if is_reset:
                        # 重置后的第一次挤出，直接取当前E值
                        total_extrusion += current_e
                        is_reset = False
                    else:
                        total_extrusion += current_e - prev_e

                prev_e = current_e

        return total_extrusion

    # 从gcode文件读取总时间
    def get_print_time(self,gcode_file_path):
        cura_pattern = r";TIME:(\d+\.?\d*)"  # 匹配Cura格式
        prusa_pattern = r"; estimated printing time \(.*\) = (?:(\d+)h ?)?(?:(\d+)m ?)?(?:(\d+)s)?"  # 匹配Prusa格式
        simplify3d_pattern = r";   Build Time: (?:(\d+) hours?)? ?(?:(\d+) minutes?)? ?(?:(\d+) seconds?)?"  # 匹配Simplify3D
        #OrcaSlicer
        with open(gcode_file_path, 'r') as f:
            gcode = f.read()

            # 尝试匹配Cura格式
            cura_match = re.search(cura_pattern, gcode)
            if cura_match:
                return float(cura_match.group(1))

            # 尝试匹配Prusa格式
            prusa_match = re.search(prusa_pattern, gcode)
            if prusa_match:
                h = int(prusa_match.group(1) or 0)
                m = int(prusa_match.group(2) or 0)
                s = int(prusa_match.group(3) or 0)
                return h * 3600 + m * 60 + s

            # 尝试匹配Simplify3D格式
            simplify_match = re.search(simplify3d_pattern, gcode)
            if simplify_match:
                h = int(simplify_match.group(1) or 0)
                m = int(simplify_match.group(2) or 0)
                s = int(simplify_match.group(3) or 0)
                return h * 3600 + m * 60 + s

        return self.calculate_total_print_time(gcode_file_path)  # 未找到时间信息，直接计算

if __name__ == '__main__':
    #gcode_file_path = 'D:\git\YLong\INLONG2025052101(UI)\GCODE\LC-GR3005通用-16分钟.gcode'
    gcode_file_path = 'e:\pacf双座车尾2-1d19h-1949g.gcode'
    if os.path.exists(gcode_file_path):
        print(f"文件 {gcode_file_path} 存在。")
    else:
        print(f"文件 {gcode_file_path} 不存在。")

    parser = GCodeParser()
    #time_seconds = parser.calculate_total_print_time(gcode_file_path)

    total_ext = parser.calculate_total_extrusion(gcode_file_path)
    print(f"挤出量: {total_ext}mm")

    parser.init_extrusion()
    total_ext1=0
    with open(gcode_file_path, 'r') as file:
        for line1 in file:
            line = line1.strip()
            total_ext1 = parser.calculate_current_extrusion(line)
        print(f"total_ext1挤出量: {total_ext1}mm")

    # 示例使用

    # if time_seconds:
    #     print(f"打印总时间: {time_seconds // 3600}小时 {(time_seconds % 3600) // 60}分钟 {time_seconds % 60}秒")
    #     #print(f"打印总时间: {time_seconds}秒")
    # else:
    #      print("未找到打印时间信息")

