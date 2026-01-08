"""
解析buble.log日志文件，提取OCR模型耗时并累加
"""

import sys
import re
import argparse
from pathlib import Path
from typing import Tuple, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def parse_ocr_time(log_path: Path) -> Tuple[List[Tuple[int, float]], int, float]:
    """
    解析日志文件，提取所有OCR模型的图片数量和耗时并累加

    Args:
        log_path: 日志文件路径

    Returns:
        (记录列表[(图片数, 耗时), ...], 总图片数, 总耗时)
    """
    if not log_path.exists():
        raise FileNotFoundError(f"日志文件不存在: {log_path}")

    # 正则表达式匹配：并发调用ocr模型效率：XXX张图片，耗时YYY
    pattern = r'并发调用ocr模型效率：(\d+)张图片，耗时([\d.]+)'

    records = []  # 存储(图片数, 耗时)的元组列表
    total_images = 0
    total_time = 0.0

    print(f"正在读取日志文件: {log_path}")

    with open(log_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            match = re.search(pattern, line)
            if match:
                images = int(match.group(1))
                time_value = float(match.group(2))
                records.append((images, time_value))
                total_images += images
                total_time += time_value

    return records, total_images, total_time


def format_time(seconds: float) -> str:
    """
    格式化时间显示

    Args:
        seconds: 秒数

    Returns:
        格式化后的时间字符串
    """
    if seconds < 60:
        return f"{seconds:.2f} 秒"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes} 分 {secs:.2f} 秒"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours} 小时 {minutes} 分 {secs:.2f} 秒"


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="解析OCR模型日志文件，提取图片数量和耗时统计",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s scripts/data/buble2.log
  %(prog)s scripts/data/buble.log
        """
    )
    parser.add_argument(
        'log_file',
        type=str,
        nargs='?',
        default='scripts/data/buble2.log',
        help='日志文件路径（默认: scripts/data/buble2.log）'
    )
    
    args = parser.parse_args()
    
    # 处理文件路径（支持相对路径和绝对路径）
    log_file_path = Path(args.log_file)
    if log_file_path.is_absolute():
        # 绝对路径，直接使用
        log_file = log_file_path
    else:
        # 相对路径，先尝试相对于当前工作目录
        log_file = Path.cwd() / log_file_path
        if not log_file.exists():
            # 如果不存在，再尝试相对于脚本所在目录
            script_dir = Path(__file__).parent
            log_file = script_dir / log_file_path

    # 检查文件是否存在
    if not log_file.exists():
        print(f"错误: 文件不存在 {log_file}")
        sys.exit(1)

    try:
        # 解析日志文件
        records, total_images, total_time = parse_ocr_time(log_file)

        if not records:
            print("未找到任何OCR模型耗时记录")
            sys.exit(0)

        # 提取时间和图片数量列表用于统计
        times = [record[1] for record in records]
        images_list = [record[0] for record in records]

        # 输出结果
        print(f"\n找到 {len(records)} 条OCR模型记录")
        
        # 图片统计
        print(f"\n图片统计:")
        print(f"  总图片数: {total_images:,} 张")
        print(f"  平均每次处理图片数: {total_images / len(records):.2f} 张")
        print(f"  最大单次图片数: {max(images_list):,} 张")
        print(f"  最小单次图片数: {min(images_list):,} 张")
        
        # 耗时统计
        print(f"\n耗时统计:")
        print(f"  总耗时: {total_time:.6f} 秒")
        print(f"  总耗时（格式化）: {format_time(total_time)}")
        print(f"  平均耗时: {total_time / len(times):.6f} 秒")
        print(f"  最大耗时: {max(times):.6f} 秒")
        print(f"  最小耗时: {min(times):.6f} 秒")
        
        # 效率统计
        if total_time > 0:
            avg_speed = total_images / total_time
            print(f"\n处理效率:")
            print(f"  平均处理速度: {avg_speed:.2f} 张/秒")
            print(f"  平均处理速度: {avg_speed * 60:.2f} 张/分钟")

        # 显示所有记录
        if len(records) > 0:
            print(f"\n所有记录 (共{len(records)}条):")
            print(f"  {'序号':<5} {'图片数':<10} {'耗时(秒)':<15} {'效率(张/秒)':<15}")
            print(f"  {'-'*45}")
            for i, (img_count, time_val) in enumerate(records, 1):
                speed = img_count / time_val if time_val > 0 else 0
                print(f"  {i:<5} {img_count:<10,} {time_val:<15.6f} {speed:<15.2f}")

    except Exception as e:
        print(f"处理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

