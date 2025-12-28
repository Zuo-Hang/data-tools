"""
CSV输入便捷函数
提供简化的CSV读取接口
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Iterator
import csv

from data_tools.input.csv_reader import CSVReader


def read_csv(
    file_path: Union[str, Path],
    encoding: str = "utf-8",
    delimiter: str = ",",
    as_dict: bool = True,
) -> Union[List[Dict[str, Any]], List[List[str]]]:
    """
    读取CSV文件

    Args:
        file_path: CSV文件路径
        encoding: 文件编码，默认utf-8
        delimiter: 分隔符，默认逗号
        as_dict: 是否以字典形式返回，True返回List[Dict]，False返回List[List]

    Returns:
        CSV文件内容，格式取决于as_dict参数
    """
    reader = CSVReader(file_path, encoding=encoding, delimiter=delimiter)
    if as_dict:
        return reader.read_all()
    else:
        # 返回列表形式
        data = []
        with open(file_path, "r", encoding=encoding, newline="") as f:
            csv_reader = csv.reader(f, delimiter=delimiter)
            data = list(csv_reader)
        return data


def load_csv_file(file_path: Union[str, Path], encoding: str = "utf-8", delimiter: str = ",") -> CSVReader:
    """
    加载CSV文件，返回CSVReader对象

    Args:
        file_path: CSV文件路径
        encoding: 文件编码，默认utf-8
        delimiter: 分隔符，默认逗号

    Returns:
        CSVReader对象，可用于更高级的操作
    """
    return CSVReader(file_path, encoding=encoding, delimiter=delimiter)


def read_csv_chunks(
    file_path: Union[str, Path],
    chunk_size: int = 1000,
    encoding: str = "utf-8",
    delimiter: str = ",",
):
    """
    分块读取CSV文件（适用于大文件）

    Args:
        file_path: CSV文件路径
        chunk_size: 每块的大小
        encoding: 文件编码，默认utf-8
        delimiter: 分隔符，默认逗号

    Yields:
        包含多行数据的列表块
    """
    reader = CSVReader(file_path, encoding=encoding, delimiter=delimiter)
    yield from reader.read_chunks(chunk_size=chunk_size)

