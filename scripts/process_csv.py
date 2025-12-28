"""
CSV处理脚本示例
演示如何使用数据输入模块处理CSV文件
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_tools.input import read_csv, CSVReader


def main():
    """主函数"""
    # 示例：使用便捷函数读取CSV
    # data = read_csv("path/to/your/file.csv")
    # for row in data:
    #     print(row)

    # 示例：使用CSVReader进行高级操作
    # reader = CSVReader("path/to/your/file.csv")
    # 
    # # 获取列头
    # headers = reader.get_headers()
    # print(f"列头: {headers}")
    #
    # # 获取行数
    # count = reader.get_row_count()
    # print(f"总行数: {count}")
    #
    # # 迭代读取
    # for row in reader.read_iterator():
    #     print(row)
    #
    # # 分块读取大文件
    # for chunk in reader.read_chunks(chunk_size=1000):
    #     process_chunk(chunk)
    #
    # # 过滤数据
    # filtered = reader.filter_rows(lambda row: int(row.get("age", 0)) > 18)
    
    print("CSV处理脚本示例")
    print("请根据实际需求修改代码")


if __name__ == "__main__":
    main()

