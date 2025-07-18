from datetime import datetime


def calculate_time_elapsed(start_time_str):
    """计算从开始时间到当前时间的时间差"""
    try:
        # 解析开始时间（支持多种格式）
        formats = [
            "%Y-%m-%d %H:%M:%S",  # 2023-01-01 12:30:45
            "%Y/%m/%d %H:%M:%S",  # 2023/01/01 12:30:45
            "%Y%m%d%H%M%S",  # 20230101123045
            "%H:%M:%S",  # 如果只输入时间，自动添加当前日期
        ]

        start_time = None
        for fmt in formats:
            try:
                start_time = datetime.strptime(start_time_str, fmt)
                # 如果只输入了时间，添加当前日期
                if fmt == "%H:%M:%S":
                    today = datetime.now()
                    start_time = start_time.replace(year=today.year, month=today.month, day=today.day)
                break
            except ValueError:
                continue

        if start_time is None:
            return "错误：时间格式无法识别，请使用 YYYY-MM-DD HH:MM:SS 格式"

        # 获取当前时间
        now = datetime.now()

        # 检查开始时间是否在未来
        if start_time > now:
            return "错误：开始时间不能晚于当前时间"

        # 计算时间差
        delta = now - start_time

        # 转换为易读格式
        days = delta.days
        seconds = delta.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        # 构建结果字符串
        result = []
        if days > 0:
            result.append(f"{days}天")
        if hours > 0:
            result.append(f"{hours}小时")
        if minutes > 0:
            result.append(f"{minutes}分钟")
        if seconds > 0 or not result:  # 确保即使只有秒数也显示
            result.append(f"{seconds}秒")

        return "总共花费时间: " + " ".join(result)

    except Exception as e:
        return f"发生错误: {str(e)}"


def convert_seconds(seconds):
    """
    将秒数转换为天、小时、分钟、秒的格式

    参数:
        seconds (int/float): 要转换的秒数

    返回:
        str: 格式化后的时间字符串
    """
    # 计算各个时间单位
    days = seconds // (24 * 3600)
    seconds = seconds % (24 * 3600)

    hours = seconds // 3600
    seconds %= 3600

    minutes = seconds // 60
    seconds %= 60

    # 四舍五入秒数到小数点后两位
    seconds = round(seconds, 2)

    # 构建结果列表
    parts = []
    if days > 0:
        parts.append(f"{int(days)}天")
    if hours > 0:
        parts.append(f"{int(hours)}小时")
    if minutes > 0:
        parts.append(f"{int(minutes)}分钟")

    # 处理秒数（避免显示0秒）
    if seconds > 0 or not parts:
        parts.append(f"{int(seconds)}秒")

    # 组合结果
    return " ".join(parts)
# 示例使用
if __name__ == "__main__":
    # 获取用户输入（实际使用时替换为输入函数）
    start_time_input = input("请输入开始时间 (格式: YYYY-MM-DD HH:MM:SS): ")
    start_time_input='20250705105200'
    # 计算并显示结果
    result = calculate_time_elapsed(start_time_input)
    print(result)

    time_seconds=218412
    result = convert_seconds(time_seconds)
    print(f'秒算时间：{result}')